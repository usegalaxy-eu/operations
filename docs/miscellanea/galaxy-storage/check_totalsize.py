#!/usr/bin/env python3
r"""Verify that ``total_size`` on disk matches the database record for
datasets where ``file_size = 0`` but ``total_size > 0`` (and not purged).

Galaxy stores a dataset's primary content in ``dataset_<id_or_uuid>.dat``
and any auxiliary/extra-files content in ``dataset_<id_or_uuid>_files/``.
The database columns should satisfy:

    total_size = file_size + (size of the _files/ directory)

When ``file_size`` is wrongly recorded as ``0`` but the ``.dat`` file
actually has bytes on disk, ``total_size`` ends up missing the ``.dat``
contribution — so ``total_size`` only reflects the ``_files/`` directory.

This script reads a CSV export produced by, e.g.:

    psql -c "\copy (SELECT id, uuid, object_store_id, file_size, total_size \
      FROM dataset WHERE file_size = 0 AND total_size > 0 AND purged = 'f') \
      TO '/tmp/dataset_export_totalsize.csv' WITH CSV HEADER;"

For each dataset it computes the expected on-disk paths (cross-referencing
``object_store.yml``), measures the real ``.dat`` size (``stat``) and the
real ``_files/`` directory size (a single streaming ``find -printf '%s'``
pass, matching ``du -sb`` apparent size), and checks:

    db_total_size == actual_dat_size + actual_folder_size

Datasets where this does not hold are recorded.  At the end the script
reports the sum of every ``actual_dat_size`` that was > 0 — i.e. the total
``file_size`` that the database should have recorded as non-zero.

Sharding rules (mirroring Galaxy's directory_hash_id / directory_hash_uuid):
  - store_by: id   -> shard dirs are 3-digit numeric (e.g. 022/467)
  - store_by: uuid -> shard dirs are single hex chars  (e.g. 9/2/f)

The CSV is streamed row by row — no dataset list is held in memory.
Findings are written to the output file incrementally.

Environment variables:
    GALAXY_CHECK_WORKERS     worker threads per distinct storage path (default 8)
    GALAXY_CHECK_QUEUE       max queued rows per storage path (default 2000)
    GALAXY_CHECK_TIMEOUT     per-directory timeout in seconds (default 120)
    GALAXY_CHECK_HEARTBEAT   heartbeat interval in seconds (default 30)

Usage:
    uv run check_totalsize.py [-o OUTPUT_DIR] <totalsize.csv> [object_store.yml]

Output directory (default: output_check_totalsize).
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import resource
import select
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from check_workers import LineWriter, WorkerPool, WORKERS, QUEUE_SIZE

JINJA_RE = re.compile(r"\{\{.*?\}\}")
JINJA_PLACEHOLDER = "__JINJA_TEMPLATE__"

PER_DIR_TIMEOUT = int(os.environ.get("GALAXY_CHECK_TIMEOUT", "120"))
HEARTBEAT_INTERVAL = float(os.environ.get("GALAXY_CHECK_HEARTBEAT", "30"))


@dataclass
class Backend:
    id: str
    files_dir: str
    store_by: str


def load_backends(config_path: Path) -> dict[str, Backend]:
    """Return {backend_id: Backend} for disk backends from object_store.yml."""
    raw = config_path.read_text()
    neutralised = JINJA_RE.sub(JINJA_PLACEHOLDER, raw)
    doc = yaml.safe_load(neutralised)
    if not isinstance(doc, dict):
        return {}
    backends: dict[str, Backend] = {}
    for be in doc.get("backends") or []:
        if not isinstance(be, dict):
            continue
        if be.get("type") != "disk":
            continue
        files_dir = be.get("files_dir")
        if not files_dir or JINJA_PLACEHOLDER in str(files_dir):
            continue
        bid = be.get("id", "")
        backends[bid] = Backend(
            id=bid,
            files_dir=str(files_dir),
            store_by=be.get("store_by", "uuid"),
        )
    return backends


def shard_id(id_str: str) -> list[str]:
    """Compute 3-digit numeric shard dirs for a numeric dataset id."""
    s = str(int(id_str))
    while len(s) % 3 != 0:
        s = "0" + s
    s = s[:-3]
    shards = [s[i : i + 3] for i in range(0, len(s), 3)]
    return shards or ["000"]


def shard_uuid(uuid_str: str) -> list[str]:
    """Compute single-hex-char shard dirs for a dataset uuid."""
    return list(uuid_str[0:3])


def format_uuid(uuid_str: str) -> str:
    """Insert standard dashes into a 32-char hex uuid (as stored in the DB).

    Galaxy's ``dataset.uuid`` column stores the UUID without dashes
    (e.g. ``936e21af36e04e719c16a07658a3383e``) but the on-disk filename
    uses the dashed form (``936e21af-36e0-4e71-9c16-a07658a3383e``).
    Sharding uses the raw hex; only the filename needs dashes.
    """
    s = uuid_str.replace("-", "")
    if len(s) != 32:
        return uuid_str
    return f"{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}"


def compute_shard_dir_and_names(
    dataset_id: str,
    uuid: str,
    backend: Backend,
) -> tuple[str, str, str]:
    """Return (shard_dir, dat_name, files_dir_name) for a dataset."""
    if backend.store_by == "id":
        shards = shard_id(dataset_id)
        basename = f"dataset_{dataset_id}"
    else:
        shards = shard_uuid(uuid)
        basename = f"dataset_{format_uuid(uuid)}"
    shard_dir = os.path.join(backend.files_dir, *shards)
    return shard_dir, basename + ".dat", basename + "_files"


def fmt_size(n: int) -> str:
    f = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if f < 1024:
            return f"{f:.1f} {unit}"
        f /= 1024
    return f"{f:.1f} EiB"


def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def measure_dir_size(path: str, label: str = "") -> tuple[int, bool, str | None]:
    """Measure the apparent size of a subtree in a single streaming find pass.

    Returns (size_bytes, timed_out, error).  Size matches ``du -sb``.
    ``find`` is run under ``timeout`` so the OS kills it even if stuck in
    D state on NFS.  ``select`` is used on the pipe so the Python side
    never blocks indefinitely and can emit heartbeats.
    """
    cmd = [
        "timeout", "-k", "5", str(PER_DIR_TIMEOUT),
        "find", path, "-type", "f", "-printf", "%s\n",
    ]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return 0, False, str(exc)

    assert proc.stdout is not None
    fd = proc.stdout.fileno()
    size = 0
    start = time.perf_counter()
    last_heartbeat = time.monotonic()

    while True:
        ready, _, _ = select.select([fd], [], [], HEARTBEAT_INTERVAL)
        if not ready:
            now = time.monotonic()
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                last_heartbeat = now
                print(
                    f"      ... [{label or path}] waiting, "
                    f"{fmt_duration(time.perf_counter() - start)} elapsed",
                    flush=True,
                )
            if proc.poll() is not None:
                break
            continue
        line = proc.stdout.readline()
        if not line:
            break
        try:
            size += int(line)
        except ValueError:
            pass

    proc.wait()
    timed_out = proc.returncode in (124, 137, -9, -15)
    error = None
    if not timed_out and proc.returncode not in (0, None):
        if proc.stderr:
            error = proc.stderr.read().decode("utf-8", "replace").strip() or None
    return size, timed_out, error


def check_dataset(item, publish):
    """Measure one dataset; return counters for serialized aggregation."""
    row, be = item
    dataset_id = row["id"].strip()
    uuid = row["uuid"].strip()
    shard_dir, dat_name, files_name = compute_shard_dir_and_names(dataset_id, uuid, be)
    dat_path = os.path.join(shard_dir, dat_name)
    files_path = os.path.join(shard_dir, files_name)
    counters = dict(checked=1, missing_dat=0, missing_files=0, timeout_count=0,
                    error_count=0, mismatches=0, sum_mismatch_dat=0)
    actual_dat_size = 0
    if os.path.isfile(dat_path):
        try:
            actual_dat_size = os.path.getsize(dat_path)
        except OSError:
            counters["error_count"] += 1
    else:
        counters["missing_dat"] = 1
    actual_folder_size = 0
    timed_out = False
    error = None
    if os.path.isdir(files_path):
        actual_folder_size, timed_out, error = measure_dir_size(files_path, label=uuid)
        counters["timeout_count"] = int(timed_out)
        counters["error_count"] += int(bool(error))
    else:
        counters["missing_files"] = 1
    for column in ("file_size", "total_size"):
        key = "sum_db_filesize" if column == "file_size" else "sum_db_total"
        try:
            counters[key] = int(row.get(column) or "0")
        except ValueError:
            counters[key] = 0
    counters["sum_actual_dat"] = actual_dat_size
    counters["sum_actual_folder"] = actual_folder_size
    counters["sum_shouldbe_filesize"] = actual_dat_size if actual_dat_size > 0 else 0
    mismatch = (not timed_out and not error and not counters["error_count"]
                and actual_dat_size + actual_folder_size != counters["sum_db_total"])
    counters["mismatches"] = int(mismatch)
    counters["sum_mismatch_dat"] = actual_dat_size if mismatch else 0
    return counters, dat_path if mismatch else None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that DB total_size matches the real on-disk size."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output_check_totalsize",
        help="directory for the output files (default: output_check_totalsize)",
    )
    parser.add_argument("csv", help="CSV export of datasets with file_size=0 and total_size>0")
    parser.add_argument(
        "config",
        nargs="?",
        default="object_store.yml",
        help="object_store.yml path (default: object_store.yml)",
    )
    args = parser.parse_args(argv[1:])

    csv_path = Path(args.csv)
    config_path = Path(args.config)

    if not csv_path.is_file():
        print(f"error: {csv_path} not found", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"error: {config_path} not found", file=sys.stderr)
        return 2

    backends = load_backends(config_path)
    if not backends:
        print("error: no disk backends found in object_store.yml", file=sys.stderr)
        return 2

    print(f"Loaded {len(backends)} disk backend(s) from {config_path}")
    print(f"Streaming datasets from {csv_path}...")
    print(f"  per-dir timeout: {PER_DIR_TIMEOUT}s, "
          f"heartbeat: {HEARTBEAT_INTERVAL:.0f}s\n")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mismatch_file = out_dir / f"mismatch_{stamp}.txt"

    counters = dict.fromkeys((
        "total", "null_store", "unknown_store", "checked", "mismatches",
        "timeout_count", "error_count", "missing_dat", "missing_files",
        "sum_shouldbe_filesize", "sum_db_filesize", "sum_actual_dat",
        "sum_actual_folder", "sum_db_total", "sum_mismatch_dat",
    ), 0)
    stats_lock = threading.Lock()
    writer = LineWriter(mismatch_file)
    total_start = time.perf_counter()

    def consume(item, result):
        values, mismatch_path = result
        with stats_lock:
            for key, value in values.items():
                counters[key] += value
        if mismatch_path:
            writer.write(mismatch_path + "\n")

    pools = {}
    for be in backends.values():
        key = (os.path.normpath(be.files_dir), be.store_by)
        if key not in pools:
            pools[key] = WorkerPool(be.files_dir, check_dataset, consume,
                                    heartbeat=HEARTBEAT_INTERVAL)
    print(f"  {len(pools)} distinct storage path(s), {WORKERS} workers/path, "
          f"queue size/path: {QUEUE_SIZE}")
    try:
        with csv_path.open(newline="") as fh:
            for row in csv.DictReader(fh):
                if not (row.get("id") or "").strip() or not (row.get("uuid") or "").strip():
                    continue
                object_store_id = (row.get("object_store_id") or "").strip()
                be = backends.get(object_store_id)
                with stats_lock:
                    counters["total"] += 1
                    if not object_store_id:
                        counters["null_store"] += 1
                    elif be is None:
                        counters["unknown_store"] += 1
                if be is not None:
                    pools[(os.path.normpath(be.files_dir), be.store_by)].submit((row, be))
        for pool in pools.values():
            pool.wait()
    finally:
        for pool in pools.values():
            pool.close()
        writer.close()

    total = counters["total"]
    null_store = counters["null_store"]
    unknown_store = counters["unknown_store"]
    checked = counters["checked"]
    mismatches = counters["mismatches"]
    timeout_count = counters["timeout_count"]
    error_count = counters["error_count"]
    missing_dat = counters["missing_dat"]
    missing_files = counters["missing_files"]
    sum_shouldbe_filesize = counters["sum_shouldbe_filesize"]
    sum_db_filesize = counters["sum_db_filesize"]
    sum_actual_dat = counters["sum_actual_dat"]
    sum_actual_folder = counters["sum_actual_folder"]
    sum_db_total = counters["sum_db_total"]
    sum_mismatch_dat = counters["sum_mismatch_dat"]

    total_elapsed = time.perf_counter() - total_start

    print(f"\nDatasets read:             {total}")
    print(f"  NULL object_store_id:    {null_store} (skipped)")
    print(f"  Unknown object_store_id: {unknown_store} (skipped)")
    print(f"Datasets checked:          {checked}")
    print(f"  .dat missing:            {missing_dat}")
    print(f"  _files/ missing:         {missing_files}")
    print(f"  _files/ timed out:       {timeout_count}")
    print(f"  _files/ errors:          {error_count}")
    print(f"Mismatches (total_size):   {mismatches}")
    print()
    print(f"Sum db file_size:          {sum_db_filesize} ({fmt_size(sum_db_filesize)})")
    print(f"Sum db total_size:         {sum_db_total} ({fmt_size(sum_db_total)})")
    print(f"Sum actual .dat size:      {sum_actual_dat} ({fmt_size(sum_actual_dat)})")
    print(f"Sum actual _files/ size:   {sum_actual_folder} ({fmt_size(sum_actual_folder)})")
    print()
    print(f"Sum of .dat sizes the db reports as 0 (actual > 0): "
          f"{sum_shouldbe_filesize} ({fmt_size(sum_shouldbe_filesize)})")
    print(f"  (across {mismatches} mismatched datasets the db total_size "
          f"is missing {fmt_size(sum_mismatch_dat)} of .dat bytes)")
    print(f"Wall time: {fmt_duration(total_elapsed)}")

    if mismatches:
        print(f"\nMismatches written to {mismatch_file}")

    usage = resource.getrusage(resource.RUSAGE_SELF)
    stats_file = out_dir / f"stats_{stamp}.txt"
    stats_lines = [
        f"# check_totalsize run {stamp}",
        f"csv: {csv_path}",
        f"config: {config_path}",
        f"distinct storage paths: {len(pools)}",
        f"workers per path: {WORKERS}",
        f"queue size per path: {QUEUE_SIZE}",
        f"per-dir timeout: {PER_DIR_TIMEOUT}s",
        f"heartbeat interval: {HEARTBEAT_INTERVAL:.0f}s",
        f"datasets read: {total}",
        f"null object_store_id: {null_store}",
        f"unknown object_store_id: {unknown_store}",
        f"datasets checked: {checked}",
        f"dat missing: {missing_dat}",
        f"files missing: {missing_files}",
        f"files timed out: {timeout_count}",
        f"files errors: {error_count}",
        f"mismatches: {mismatches}",
        f"sum db file_size: {sum_db_filesize}",
        f"sum db total_size: {sum_db_total}",
        f"sum actual dat size: {sum_actual_dat}",
        f"sum actual folder size: {sum_actual_folder}",
        f"sum dat sizes db reports as 0 (actual>0): {sum_shouldbe_filesize}",
        f"sum mismatch dat bytes: {sum_mismatch_dat}",
        f"wall time: {fmt_duration(total_elapsed)}",
        f"cpu user time: {fmt_duration(usage.ru_utime)}",
        f"cpu sys time: {fmt_duration(usage.ru_stime)}",
        f"peak rss: {usage.ru_maxrss / 1024:.1f} MB",
    ]
    stats_file.write_text("\n".join(stats_lines) + "\n")
    print(f"Stats written to {stats_file}")

    return 1 if (mismatches or timeout_count or error_count) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
