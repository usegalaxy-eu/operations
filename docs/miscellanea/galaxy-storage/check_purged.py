#!/usr/bin/env python3
"""Verify that purged datasets are actually gone from disk.

Reads a CSV export of purged datasets (id, uuid, object_store_id),
computes the expected on-disk path for each by cross-referencing
object_store.yml, and reports any dataset whose .dat file or _files/
directory still exists.

Sharding rules (mirroring Galaxy's directory_hash_id / directory_hash_uuid):
  - store_by: id   -> shard dirs are 3-digit numeric (e.g. 022/467)
  - store_by: uuid -> shard dirs are single hex chars  (e.g. 9/2/f)

The full path is: <files_dir>/<shards>/dataset_<id_or_uuid>.dat
and optionally:   <files_dir>/<shards>/dataset_<id_or_uuid>_files/

Datasets with a NULL object_store_id are skipped.

The CSV is streamed row by row on the main thread — no dataset list is
held in memory. Each backend (object store) gets its own bounded queue
and pool of worker threads that do the actual filesystem checks. This
matters because these paths live on NFS: the bottleneck is round-trip
latency, not CPU, so a single-threaded process spends nearly all its
time blocked waiting on the network. Since ``stat``/``isdir`` release
the GIL while blocked, plain threads let many checks be in flight at
once — one thread pool per backend so a slow/overloaded mount doesn't
steal concurrency from a healthy one. A small per-backend cache of
shard-dir existence results (guarded by a lock) still avoids redundant
directory checks. Findings are written to the output file incrementally
as they're found, from whichever worker thread finds them.

Environment variables:
    GALAXY_CHECK_WORKERS     worker threads per backend (default 8)
    GALAXY_CHECK_QUEUE       max rows queued per backend before the
                             reader blocks, i.e. backpressure (default 2000)
    GALAXY_CHECK_HEARTBEAT   heartbeat interval in seconds (default 30)

Usage:
    uv run check_purged.py [-o OUTPUT_DIR] <purged.csv> [object_store.yml]

Output directory (default: output_check_purged).
"""

from __future__ import annotations

import argparse
import csv
import os
import queue
import re
import resource
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

JINJA_RE = re.compile(r"\{\{.*?\}\}")
JINJA_PLACEHOLDER = "__JINJA_TEMPLATE__"

PROGRESS_EVERY = 100_000

WORKERS_PER_BACKEND = int(os.environ.get("GALAXY_CHECK_WORKERS", "12"))
QUEUE_MAXSIZE = int(os.environ.get("GALAXY_CHECK_QUEUE", "2000"))
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
    files_dir: str,
    store_by: str,
) -> tuple[str, str, str]:
    """Return (shard_dir, dat_name, files_dir_name) for a dataset."""
    if store_by == "id":
        shards = shard_id(dataset_id)
        basename = f"dataset_{dataset_id}"
    else:
        shards = shard_uuid(uuid)
        basename = f"dataset_{format_uuid(uuid)}"
    shard_dir = os.path.join(files_dir, *shards)
    return shard_dir, basename + ".dat", basename + "_files"


def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


class Stats:
    """Thread-safe run counters, updated by the reader and worker threads."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.total = 0
        self.null_store = 0
        self.unknown_store = 0
        self.still_exist = 0
        self.dat_count = 0
        self.files_count = 0

    def incr(self, **fields: int) -> None:
        with self.lock:
            for key, value in fields.items():
                setattr(self, key, getattr(self, key) + value)

    def snapshot(self) -> dict[str, int]:
        with self.lock:
            return {
                "total": self.total,
                "null_store": self.null_store,
                "unknown_store": self.unknown_store,
                "still_exist": self.still_exist,
                "dat_count": self.dat_count,
                "files_count": self.files_count,
            }


class ExistWriter:
    """Serializes writes to the "still exists" output file across threads."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.fh = None

    def write_lines(self, lines: list[str]) -> None:
        with self.lock:
            if self.fh is None:
                self.fh = self.path.open("w")
                self.fh.write("dataset_id\tuuid\tobject_store_id\tkind\tpath\n")
            self.fh.writelines(lines)

    def close(self) -> None:
        with self.lock:
            if self.fh is not None:
                self.fh.close()


class MountState:
    """Queue, shard-dir cache, and worker threads for one physical mount.

    Several ``object_store_id`` values in object_store.yml can alias the
    same underlying ``files_dir`` (e.g. multiple backend ids pointing at
    the same NetApp export). State is keyed by ``(files_dir, store_by)``
    — the actual filesystem resource — rather than by backend id, so:

      - the shard-dir existence cache is shared across all aliased ids
        (no redundant ``isdir`` calls for the same physical directory), and
      - concurrency (worker threads) is bounded per physical mount, not
        multiplied by however many backend ids happen to alias it.
    """

    def __init__(
        self, files_dir: str, store_by: str, workers: int, queue_maxsize: int
    ) -> None:
        self.files_dir = files_dir
        self.store_by = store_by
        self.backend_ids: list[str] = []
        self.workers = workers
        self.work_queue: queue.Queue = queue.Queue(maxsize=queue_maxsize)
        self.lock = threading.Lock()
        self.dir_present: set[str] = set()
        self.dir_absent: set[str] = set()
        self.threads: list[threading.Thread] = []


def worker_loop(state: MountState, stats: Stats, writer: ExistWriter) -> None:
    while True:
        item = state.work_queue.get()
        try:
            if item is None:  # sentinel: shut down
                return

            dataset_id, uuid, object_store_id = item
            shard_dir, dat_name, files_name = compute_shard_dir_and_names(
                dataset_id, uuid, state.files_dir, state.store_by
            )

            with state.lock:
                if shard_dir in state.dir_absent:
                    continue
                known_present = shard_dir in state.dir_present

            if not known_present:
                exists = os.path.isdir(shard_dir)
                with state.lock:
                    if exists:
                        state.dir_present.add(shard_dir)
                    else:
                        state.dir_absent.add(shard_dir)
                if not exists:
                    continue

            dat_path = os.path.join(shard_dir, dat_name)
            files_path = os.path.join(shard_dir, files_name)
            dat_exists = os.path.lexists(dat_path)
            files_exists = os.path.lexists(files_path)

            if not (dat_exists or files_exists):
                continue

            lines = []
            if dat_exists:
                lines.append(
                    f"{dataset_id}\t{uuid}\t{object_store_id}\tdat\t{dat_path}\n"
                )
            if files_exists:
                lines.append(
                    f"{dataset_id}\t{uuid}\t{object_store_id}\tfiles_dir\t{files_path}\n"
                )
            writer.write_lines(lines)
            stats.incr(
                still_exist=len(lines),
                dat_count=int(dat_exists),
                files_count=int(files_exists),
            )
        finally:
            state.work_queue.task_done()


def heartbeat_loop(
    stats: Stats,
    mount_states: list[MountState],
    stop_event: threading.Event,
    interval: float,
    start_time: float,
) -> None:
    last_total = 0
    last_time = start_time
    while not stop_event.wait(interval):
        snap = stats.snapshot()
        now = time.perf_counter()
        dt = now - last_time
        rate = (snap["total"] - last_total) / dt if dt > 0 else 0.0
        elapsed = now - start_time
        pending = ", ".join(
            f"{'+'.join(st.backend_ids)}={st.work_queue.qsize()}"
            for st in mount_states
        )
        print(
            f"    [heartbeat +{fmt_duration(elapsed)}] "
            f"checked={snap['total']} ({rate:.0f}/s) "
            f"still_exist={snap['still_exist']} "
            f"queued=[{pending}]",
            flush=True,
        )
        last_total = snap["total"]
        last_time = now


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that purged datasets are actually gone from disk."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output_check_purged",
        help="directory for the output files (default: output_check_purged)",
    )
    parser.add_argument("csv", help="CSV export of purged datasets (id, uuid, object_store_id)")
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

    mount_states: dict[tuple[str, str], MountState] = {}
    for bid, be in sorted(backends.items()):
        key = (be.files_dir, be.store_by)
        state = mount_states.get(key)
        if state is None:
            state = MountState(be.files_dir, be.store_by, WORKERS_PER_BACKEND, QUEUE_MAXSIZE)
            mount_states[key] = state
        state.backend_ids.append(bid)

    backend_to_mount: dict[str, MountState] = {
        bid: state for state in mount_states.values() for bid in state.backend_ids
    }

    aliased = [state for state in mount_states.values() if len(state.backend_ids) > 1]
    print(
        f"  {len(mount_states)} distinct storage path(s) "
        f"(workers/path: {WORKERS_PER_BACKEND}, "
        f"queue size: {QUEUE_MAXSIZE}, heartbeat: {HEARTBEAT_INTERVAL:.0f}s)"
    )
    if aliased:
        print("  backend ids sharing the same physical path (pooled together):")
        for state in aliased:
            print(f"    {'+'.join(state.backend_ids)} -> {state.files_dir}")
    print(f"Streaming purged datasets from {csv_path}...\n")

    script_stem = Path(__file__).stem
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exist_file = out_dir / f"still_exist_{stamp}.txt"

    stats = Stats()
    writer = ExistWriter(exist_file)

    for state in mount_states.values():
        for _ in range(state.workers):
            t = threading.Thread(
                target=worker_loop, args=(state, stats, writer), daemon=True
            )
            t.start()
            state.threads.append(t)

    total_start = time.perf_counter()
    stop_heartbeat = threading.Event()
    heartbeat_thread = threading.Thread(
        target=heartbeat_loop,
        args=(
            stats,
            list(mount_states.values()),
            stop_heartbeat,
            HEARTBEAT_INTERVAL,
            total_start,
        ),
        daemon=True,
    )
    heartbeat_thread.start()

    with csv_path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            dataset_id = (row.get("id") or "").strip()
            uuid = (row.get("uuid") or "").strip()
            object_store_id = (row.get("object_store_id") or "").strip()

            if not dataset_id or not uuid:
                continue
            stats.incr(total=1)

            if not object_store_id:
                stats.incr(null_store=1)
                continue

            state = backend_to_mount.get(object_store_id)
            if state is None:
                stats.incr(unknown_store=1)
                continue

            # Blocks if the mount's queue is full (backpressure), so the
            # reader never buffers more than a bounded window of rows ahead
            # of what the workers for that physical path can keep up with.
            state.work_queue.put((dataset_id, uuid, object_store_id))

            if stats.total % PROGRESS_EVERY == 0:
                snap = stats.snapshot()
                print(
                    f"    ... progress: {snap['total']} datasets read, "
                    f"{snap['still_exist']} still on disk so far"
                )

    # Signal every worker thread to stop, then wait for them to drain.
    for state in mount_states.values():
        for _ in range(state.workers):
            state.work_queue.put(None)
    for state in mount_states.values():
        for t in state.threads:
            t.join()

    stop_heartbeat.set()
    heartbeat_thread.join()

    writer.close()

    total_elapsed = time.perf_counter() - total_start
    snap = stats.snapshot()
    dir_present_total = sum(len(st.dir_present) for st in mount_states.values())
    dir_absent_total = sum(len(st.dir_absent) for st in mount_states.values())

    print(f"\nDatasets checked:    {snap['total']}")
    print(f"  NULL object_store: {snap['null_store']} (skipped)")
    print(f"  Unknown store_id:  {snap['unknown_store']} (skipped)")
    print(f"  Shard dirs exist:  {dir_present_total}")
    print(f"  Shard dirs absent: {dir_absent_total} (skipped all datasets in them)")
    print(f"  Still on disk:     {snap['still_exist']}")
    print(f"    .dat files:      {snap['dat_count']}")
    print(f"    _files dirs:     {snap['files_count']}")
    print(f"Wall time: {fmt_duration(total_elapsed)}")

    if snap["still_exist"]:
        print(f"\nPaths written to {exist_file}")

    usage = resource.getrusage(resource.RUSAGE_SELF)
    stats_file = out_dir / f"stats_{stamp}.txt"
    stats_lines = [
        f"# check_purged run {stamp}",
        f"csv: {csv_path}",
        f"config: {config_path}",
        f"distinct storage paths: {len(mount_states)}",
        f"workers per path: {WORKERS_PER_BACKEND}",
        f"queue size per path: {QUEUE_MAXSIZE}",
        f"datasets checked: {snap['total']}",
        f"null object_store_id: {snap['null_store']}",
        f"unknown object_store_id: {snap['unknown_store']}",
        f"shard dirs exist: {dir_present_total}",
        f"shard dirs absent: {dir_absent_total}",
        f"still on disk: {snap['still_exist']}",
        f"  .dat files: {snap['dat_count']}",
        f"  _files dirs: {snap['files_count']}",
        f"wall time: {fmt_duration(total_elapsed)}",
        f"cpu user time: {fmt_duration(usage.ru_utime)}",
        f"cpu sys time: {fmt_duration(usage.ru_stime)}",
        f"peak rss: {usage.ru_maxrss / 1024:.1f} MB",
    ]
    stats_file.write_text("\n".join(stats_lines) + "\n")
    print(f"Stats written to {stats_file}")

    return 1 if snap["still_exist"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
