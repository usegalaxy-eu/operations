#!/usr/bin/env python3
"""Identify Galaxy ``_files/`` directories that exceed a size-scan timeout.

The script walks the shard trees of every ``type: disk`` backend in
``object_store.yml``.  Each discovered ``dataset_*_files/`` directory is
measured in one streaming ``find`` pass.  If that pass exceeds
``GALAXY_CHECK_TIMEOUT``, the directory is written immediately to the
``timeouts_<stamp>.tsv`` output file.

A timeout is not proof that a directory is large: NFS latency or an I/O
problem can also cause one.  It is, however, a useful shortlist of
``_files/`` directories that need closer inspection.

Environment variables:
    GALAXY_CHECK_WORKERS     worker threads per distinct storage path (default 8)
    GALAXY_CHECK_TIMEOUT     per-_files directory timeout in seconds (default 120)
    GALAXY_CHECK_HEARTBEAT   progress/heartbeat interval in seconds (default 30)

Usage:
    uv run usefull/check_files_timeouts.py [-o OUTPUT_DIR] [object_store.yml]

Output directory (default: output_check_files_timeouts).
"""

from __future__ import annotations

import argparse
import os
import re
import resource
import select
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

# Allow direct execution from usefull/ while sharing the root worker helper.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from check_workers import LineWriter, WorkerPool, WORKERS

JINJA_RE = re.compile(r"\{\{.*?\}\}")
JINJA_PLACEHOLDER = "__JINJA_TEMPLATE__"

PER_DIR_TIMEOUT = int(os.environ.get("GALAXY_CHECK_TIMEOUT", "120"))
HEARTBEAT_INTERVAL = float(os.environ.get("GALAXY_CHECK_HEARTBEAT", "30"))

SHARD_NAMES: dict[str, set[str]] = {
    "uuid": set("0123456789abcdef"),
    "id": {f"{i:03d}" for i in range(1000)},
}
FILES_SUFFIX = "_files"


@dataclass
class Backend:
    ids: list[str]
    files_dir: str
    store_by: str


@dataclass
class ScanStats:
    shard_dirs: int = 0
    files_dirs: int = 0
    measured: int = 0
    timed_out: int = 0
    errors: int = 0
    shard_timeouts: int = 0
    shard_errors: int = 0
    non_dirs: int = 0


def load_backends(config_path: Path) -> list[Backend]:
    """Return unique disk ``files_dir`` paths and their backend IDs."""
    raw = config_path.read_text()
    doc = yaml.safe_load(JINJA_RE.sub(JINJA_PLACEHOLDER, raw))
    if not isinstance(doc, dict):
        return []

    by_dir: dict[str, Backend] = {}
    for item in doc.get("backends") or []:
        if not isinstance(item, dict) or item.get("type") != "disk":
            continue
        files_dir = item.get("files_dir")
        if not files_dir or JINJA_PLACEHOLDER in str(files_dir):
            continue

        path = os.path.normpath(str(files_dir))
        backend_id = str(item.get("id", "<no-id>"))
        store_by = str(item.get("store_by", "uuid"))
        previous = by_dir.get(path)
        if previous is None:
            by_dir[path] = Backend([backend_id], path, store_by)
        else:
            previous.ids.append(backend_id)
            if previous.store_by != store_by:
                print(
                    f"WARNING: {path} is shared by backends with different "
                    f"store_by values ({previous.store_by!r}, {store_by!r}); "
                    f"using {previous.store_by!r}",
                    file=sys.stderr,
                )
    return list(by_dir.values())


def start_scan(backend, stats, timeout_writer, error_writer):
    shard_names = SHARD_NAMES[backend.store_by]

    def work(item, publish):
        kind, path = item
        if kind == "measure":
            return measure_dir(path)
        children = []
        non_dirs = 0
        error = False
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.name in shard_names:
                        if entry.is_dir(follow_symlinks=False):
                            children.append(("scan", entry.path))
                    elif entry.name.endswith(FILES_SUFFIX):
                        if entry.is_dir(follow_symlinks=False):
                            children.append(("measure", entry.path))
                        else:
                            non_dirs += 1
        except OSError:
            error = True
        return children, non_dirs, error

    def consume(item, result):
        kind, path = item
        if kind == "scan":
            children, non_dirs, error = result
            stats.shard_dirs += 1
            stats.non_dirs += non_dirs
            stats.shard_errors += int(error)
            stats.files_dirs += sum(kind == "measure" for kind, _ in children)
            return children
        size, file_count, timed_out, error, elapsed = result
        stats.measured += 1
        if timed_out:
            stats.timed_out += 1
            timeout_writer.write(f"{path}\t{size}\t{file_count}\t{elapsed:.2f}\n")
            print(f"    TIMEOUT: {path} ({file_count} files, at least {fmt_size(size)})")
        elif error:
            stats.errors += 1
            error_writer.write(f"{path}\t{error.replace(chr(10), ' ')}\n")
            print(f"    ERROR: {path}: {error}")

    def timed_out(item):
        stats.shard_timeouts += 1
        print(f"    SHARD TIMEOUT: {item[1]}", flush=True)

    pool = WorkerPool(
        ",".join(backend.ids), work, consume,
        timeout=lambda item: PER_DIR_TIMEOUT if item[0] == "scan" else None,
        on_timeout=timed_out, heartbeat=HEARTBEAT_INTERVAL,
    )
    pool.submit(("scan", backend.files_dir))
    return pool


def fmt_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} EiB"


def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m{seconds:02d}s"


def measure_dir(path: str) -> tuple[int, int, bool, str | None, float]:
    """Return size, file count, timed-out state, error, and elapsed time."""
    start = time.perf_counter()
    cmd = [
        "timeout", "-k", "5", str(PER_DIR_TIMEOUT),
        "find", path, "-type", "f", "-printf", "%s\\n",
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        return 0, 0, False, str(exc), time.perf_counter() - start

    assert proc.stdout is not None
    size = 0
    file_count = 0
    fd = proc.stdout.fileno()
    last_heartbeat = time.monotonic()

    while True:
        ready, _, _ = select.select([fd], [], [], HEARTBEAT_INTERVAL)
        if not ready:
            now = time.monotonic()
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                last_heartbeat = now
                print(
                    f"      ... [{path}] waiting: {file_count} files, "
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
            file_count += 1
        except ValueError:
            pass

    proc.wait()
    elapsed = time.perf_counter() - start
    timed_out = proc.returncode in (124, 137, -9, -15)
    error = None
    if not timed_out and proc.returncode not in (0, None):
        assert proc.stderr is not None
        error = proc.stderr.read().decode("utf-8", "replace").strip() or None
    return size, file_count, timed_out, error, elapsed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Identify Galaxy _files/ directories whose size scan exceeds the timeout."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output_check_files_timeouts",
        help="directory for the output files (default: output_check_files_timeouts)",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default="object_store.yml",
        help="object_store.yml path (default: object_store.yml)",
    )
    args = parser.parse_args(argv[1:])

    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"error: {config_path} not found", file=sys.stderr)
        return 2

    backends = load_backends(config_path)
    if not backends:
        print("error: no disk backends found in object_store.yml", file=sys.stderr)
        return 2

    script_stem = Path(__file__).stem
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timeout_file = out_dir / f"timeouts_{stamp}.tsv"
    error_file = out_dir / f"errors_{stamp}.tsv"

    print(f"Scanning {len(backends)} disk backend(s) from {config_path}...")
    print(
        f"  per-_files timeout: {PER_DIR_TIMEOUT}s, "
        f"heartbeat: {HEARTBEAT_INTERVAL:.0f}s\n"
    )

    total_stats = ScanStats()
    total_start = time.perf_counter()
    timeout_writer = LineWriter(timeout_file, "# path\tpartial_size_bytes\tfiles_seen\telapsed_s\n")
    error_writer = LineWriter(error_file, "# path\terror\n")
    pools = []

    try:
        for backend in backends:
            label = ",".join(backend.ids)
            if not os.path.isdir(backend.files_dir):
                print(f"[{label}] {backend.files_dir} (MISSING; skipped)")
                total_stats.shard_errors += 1
                continue

            shard_names = SHARD_NAMES.get(backend.store_by)
            if shard_names is None:
                print(f"[{label}] unknown store_by={backend.store_by!r}; skipped")
                total_stats.shard_errors += 1
                continue

            print(f"[{label}] {backend.files_dir} (store_by={backend.store_by})")
            stats = ScanStats()
            pools.append((stats, start_scan(backend, stats, timeout_writer, error_writer)))

        for stats, pool in pools:
            pool.wait()
            print(
                f"    {stats.files_dirs} _files found, {stats.measured} measured, "
                f"{stats.timed_out} timed out, {stats.errors} errors"
            )
            for field in ScanStats.__dataclass_fields__:
                setattr(total_stats, field, getattr(total_stats, field) + getattr(stats, field))
    finally:
        for _, pool in pools:
            pool.close()
        timeout_writer.close()
        error_writer.close()

    total_elapsed = time.perf_counter() - total_start
    print(f"\n_files/ directories found: {total_stats.files_dirs}")
    print(f"_files/ directories measured: {total_stats.measured}")
    print(f"_files/ timeouts:            {total_stats.timed_out}")
    print(f"_files/ errors:              {total_stats.errors}")
    print(f"Shard scan timeouts:         {total_stats.shard_timeouts}")
    print(f"Shard scan errors:           {total_stats.shard_errors}")
    print(f"Non-directory *_files names: {total_stats.non_dirs}")
    print(f"Wall time: {fmt_duration(total_elapsed)}")
    if timeout_writer.fh is not None:
        print(f"Timed-out _files paths written to {timeout_file}")
    if error_writer.fh is not None:
        print(f"_files errors written to {error_file}")

    usage = resource.getrusage(resource.RUSAGE_SELF)
    stats_file = out_dir / f"stats_{stamp}.txt"
    stats_file.write_text(
        "\n".join(
            [
                f"# {script_stem} run {stamp}",
                f"config: {config_path}",
                f"workers per path: {WORKERS}",
                f"per-_files timeout: {PER_DIR_TIMEOUT}s",
                f"heartbeat interval: {HEARTBEAT_INTERVAL:.0f}s",
                f"files dirs found: {total_stats.files_dirs}",
                f"files dirs measured: {total_stats.measured}",
                f"files timeouts: {total_stats.timed_out}",
                f"files errors: {total_stats.errors}",
                f"shard dirs scanned: {total_stats.shard_dirs}",
                f"shard scan timeouts: {total_stats.shard_timeouts}",
                f"shard scan errors: {total_stats.shard_errors}",
                f"non-directory *_files names: {total_stats.non_dirs}",
                f"wall time: {fmt_duration(total_elapsed)}",
                f"cpu user time: {fmt_duration(usage.ru_utime)}",
                f"cpu sys time: {fmt_duration(usage.ru_stime)}",
                f"peak rss: {usage.ru_maxrss / 1024:.1f} MB",
            ]
        )
        + "\n"
    )
    print(f"Stats written to {stats_file}")

    return 1 if (total_stats.timed_out or total_stats.errors or total_stats.shard_timeouts or total_stats.shard_errors) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
