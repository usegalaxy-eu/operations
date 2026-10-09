#!/usr/bin/env python3
"""Check Galaxy object-store files_dir trees for:

  1. Unexpected entries — anything that is not a ``.dat`` file, a
     ``<dataset>_files`` directory, or a shard subdirectory.
  2. Orphan ``_files`` directories — a ``<name>_files`` folder whose
     matching ``<name>.dat`` file is missing in the same parent directory.

Both legacy (store_by: id, 3-digit numeric shards) and non-legacy
(store_by: uuid, single hex char shards) disk backends are checked.

Several backend ids in object_store.yml can point at the same physical
``files_dir`` (e.g. after config history/migrations). ``collect_files_dirs``
collapses those into one entry so the same tree is only walked once.

Each distinct storage path is walked concurrently with the others using
a bounded pool of worker threads (one pool per path), consuming a shared
queue of pending directories -- this matters because these trees live on
NFS: the bottleneck is round-trip latency, not CPU, so many directory
reads in flight at once (across paths, and within one large path) cuts
wall time substantially versus one directory at a time.

Because a per-directory hang has to be handled across threads, the
previous SIGALRM-based timeout (which only works on a process's main
thread) is replaced with a cooperative watchdog: a background heartbeat
thread notices workers stuck in ``os.scandir`` past the timeout, logs
them, gives up on that directory (it won't be recursed into), and starts
a replacement worker so a mount's overall concurrency is topped back up.
The stuck OS thread itself is abandoned (harmless: it's a daemon thread)
since Python has no way to forcibly interrupt a blocked syscall from
another thread the way a signal can on the main thread.

Environment variables:
    GALAXY_CHECK_WORKERS     worker threads per distinct storage path (default 8)
    GALAXY_CHECK_TIMEOUT     per-directory timeout in seconds (default 120)
    GALAXY_CHECK_HEARTBEAT   heartbeat interval in seconds (default 30)

Usage:
    uv run check_datasets.py [-o OUTPUT_DIR] [object_store.yml]

Output directory (default: /storage/output_check_datasets).
"""

from __future__ import annotations

import argparse
import os
import queue
import re
import resource
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

JINJA_RE = re.compile(r"\{\{.*?\}\}")
JINJA_PLACEHOLDER = "__JINJA_TEMPLATE__"

WORKERS_PER_MOUNT = int(os.environ.get("GALAXY_CHECK_WORKERS", "8"))
PER_DIR_TIMEOUT = float(os.environ.get("GALAXY_CHECK_TIMEOUT", "120"))
HEARTBEAT_INTERVAL = float(os.environ.get("GALAXY_CHECK_HEARTBEAT", "30"))

SHARD_CHECKS: dict[str, set[str]] = {
    "uuid": set("0123456789abcdef"),
    "id": {f"{i:03d}" for i in range(1000)},
}

DAT_SUFFIX = ".dat"
FILES_SUFFIX = "_files"

_SENTINEL = object()


@dataclass
class DirResult:
    dirpath: str
    entries_scanned: int = 0
    dat_count: int = 0
    files_dirs: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)
    orphan_files_dirs: list[str] = field(default_factory=list)
    shard_subdirs: list[str] = field(default_factory=list)


@dataclass
class BackendStats:
    backend_ids: list[str]
    files_dir: str
    store_by: str
    exists: bool
    entries_scanned: int = 0
    dirs_visited: int = 0
    dat_files: int = 0
    files_dirs: int = 0
    unexpected: int = 0
    orphan_files_dirs: int = 0
    read_errors: int = 0
    timeout_errors: int = 0
    error_paths: list[str] = field(default_factory=list)
    timeout_paths: list[str] = field(default_factory=list)
    elapsed_s: float = 0.0


def load_backends(config_path: Path) -> list[dict]:
    """Parse object_store.yml, neutralising Jinja2 templates so PyYAML can load it."""
    raw = config_path.read_text()
    neutralised = JINJA_RE.sub(JINJA_PLACEHOLDER, raw)
    doc = yaml.safe_load(neutralised)
    if not isinstance(doc, dict):
        return []
    return doc.get("backends") or []


def collect_files_dirs(
    backends: list[dict],
) -> list[tuple[str, str, list[str]]]:
    """Return (files_dir, store_by, backend_ids) for disk backends.

    Duplicate files_dir paths are collapsed (each unique dir appears once).
    All backends sharing a dir must agree on store_by, otherwise a warning
    is printed and the first backend's store_by wins.
    """
    seen: dict[str, tuple[str, list[str]]] = {}
    for be in backends:
        if not isinstance(be, dict):
            continue
        if be.get("type") != "disk":
            continue
        files_dir = be.get("files_dir")
        if not files_dir or JINJA_PLACEHOLDER in str(files_dir) or "{{" in str(files_dir):
            continue
        store_by = be.get("store_by", "uuid")
        key = os.path.normpath(str(files_dir))
        bid = be.get("id", "<no-id>")
        if key in seen:
            prev_store_by, ids = seen[key]
            ids.append(bid)
            if prev_store_by != store_by:
                print(
                    f"WARNING: {key} shared by backends with different store_by "
                    f"({prev_store_by} vs {store_by}); using {prev_store_by}",
                    file=sys.stderr,
                )
        else:
            seen[key] = (store_by, [bid])
    return [(d, sb, ids) for d, (sb, ids) in seen.items()]


def scan_one_dir(dirpath: str, shard_set: set[str]) -> DirResult:
    """Classify the entries of a single directory (no recursion).

    Classification is name-first: ``.dat`` and ``_files`` entries are
    identified by suffix without any stat call. Only entries whose name is
    in *shard_set* require an ``is_dir`` check (to decide whether to
    recurse). This avoids an ``lstat`` per entry on NFS (where d_type is
    DT_UNKNOWN), which is the main bottleneck at petabyte scale.

    Raises ``OSError`` if the directory can't be read. A hang inside this
    call (e.g. an unresponsive NFS export) is *not* handled here -- see
    ``check_mount_timeouts`` for how the caller's worker pool copes with
    that from another thread.
    """
    result = DirResult(dirpath=dirpath)
    dat_names: set[str] = set()
    pending_files_dirs: list[str] = []
    with os.scandir(dirpath) as scandir_it:
        for entry in scandir_it:
            result.entries_scanned += 1
            name = entry.name
            if name in shard_set:
                if entry.is_dir(follow_symlinks=False):
                    result.shard_subdirs.append(entry.path)
                else:
                    result.unexpected.append(entry.path)
            elif name.endswith(DAT_SUFFIX):
                result.dat_count += 1
                dat_names.add(name)
            elif name.endswith(FILES_SUFFIX):
                result.files_dirs.append(name)
                pending_files_dirs.append(name)
            else:
                result.unexpected.append(entry.path)
    for fd_name in pending_files_dirs:
        expected_dat = fd_name[: -len(FILES_SUFFIX)] + DAT_SUFFIX
        if expected_dat not in dat_names:
            result.orphan_files_dirs.append(os.path.join(dirpath, fd_name))
    return result


class LineWriter:
    """Serializes buffered line writes to one output file across threads."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.fh = None

    def write_lines(self, lines: list[str]) -> None:
        if not lines:
            return
        with self.lock:
            if self.fh is None:
                self.fh = self.path.open("w")
            self.fh.writelines(lines)

    def close(self) -> None:
        with self.lock:
            if self.fh is not None:
                self.fh.close()

    @property
    def has_content(self) -> bool:
        return self.fh is not None


class InFlightToken:
    """Tracks one worker's currently-in-progress directory for the watchdog."""

    __slots__ = ("dirpath", "start", "abandoned")

    def __init__(self, dirpath: str) -> None:
        self.dirpath = dirpath
        self.start = time.monotonic()
        self.abandoned = False


class MountRunner:
    """Queue, live stats, in-flight tracking, and worker threads for one path.

    One runner per distinct ``(files_dir, store_by)`` pair (see
    ``collect_files_dirs``), so backend ids that alias the same physical
    mount share a single queue, counters, and worker pool instead of
    redundantly walking the same directory tree once per alias.
    """

    def __init__(
        self,
        files_dir: str,
        store_by: str,
        backend_ids: list[str],
        exists: bool,
        shard_set: set[str] | None,
    ) -> None:
        self.files_dir = files_dir
        self.store_by = store_by
        self.backend_ids = backend_ids
        self.exists = exists
        self.shard_set = shard_set
        self.work_queue: queue.Queue = queue.Queue()
        self.lock = threading.Lock()
        self.in_flight: dict[int, InFlightToken] = {}
        self.threads: list[threading.Thread] = []
        self.stats = {
            "entries_scanned": 0,
            "dirs_visited": 0,
            "dat_files": 0,
            "files_dirs": 0,
            "unexpected": 0,
            "orphan_files_dirs": 0,
            "read_errors": 0,
            "timeout_errors": 0,
            "error_paths": [],
            "timeout_paths": [],
        }

    @property
    def runnable(self) -> bool:
        return self.exists and self.shard_set is not None


def mount_worker(
    runner: MountRunner, unexpected_writer: LineWriter, orphan_writer: LineWriter
) -> None:
    while True:
        dirpath = runner.work_queue.get()
        if dirpath is _SENTINEL:
            runner.work_queue.task_done()
            return

        tid = threading.get_ident()
        token = InFlightToken(dirpath)
        with runner.lock:
            runner.in_flight[tid] = token

        try:
            result = scan_one_dir(dirpath, runner.shard_set)
            error = None
        except OSError as exc:
            result = None
            error = exc

        with runner.lock:
            runner.in_flight.pop(tid, None)
            abandoned = token.abandoned

        if abandoned:
            # The watchdog already timed this directory out and released
            # its queue slot on our behalf; don't double-count stats or
            # call task_done() a second time for the same item.
            continue

        if error is not None:
            with runner.lock:
                runner.stats["read_errors"] += 1
                runner.stats["error_paths"].append(dirpath)
        else:
            with runner.lock:
                runner.stats["dirs_visited"] += 1
                runner.stats["entries_scanned"] += result.entries_scanned
                runner.stats["dat_files"] += result.dat_count
                runner.stats["files_dirs"] += len(result.files_dirs)
                runner.stats["unexpected"] += len(result.unexpected)
                runner.stats["orphan_files_dirs"] += len(result.orphan_files_dirs)
            if result.unexpected:
                unexpected_writer.write_lines([p + "\n" for p in result.unexpected])
            if result.orphan_files_dirs:
                orphan_writer.write_lines([p + "\n" for p in result.orphan_files_dirs])
            for subdir in result.shard_subdirs:
                runner.work_queue.put(subdir)

        runner.work_queue.task_done()


def check_mount_timeouts(
    runner: MountRunner, unexpected_writer: LineWriter, orphan_writer: LineWriter
) -> None:
    """Give up on directories whose scan has been stuck past the timeout.

    Called periodically (from the heartbeat thread) for every runnable
    mount. Any worker that's been blocked in ``os.scandir`` on the same
    directory for longer than ``PER_DIR_TIMEOUT`` is treated the way the
    old SIGALRM handler treated a timeout: the directory is logged and
    skipped (not recursed into), and the queue slot is released so the
    walk can finish even though that one thread never returns. A fresh
    worker is started to replace the presumed-stuck one.
    """
    now = time.monotonic()
    with runner.lock:
        stuck = [
            (tid, tok)
            for tid, tok in runner.in_flight.items()
            if not tok.abandoned and now - tok.start >= PER_DIR_TIMEOUT
        ]
        for _tid, tok in stuck:
            tok.abandoned = True
            runner.stats["timeout_errors"] += 1
            runner.stats["timeout_paths"].append(tok.dirpath)
        for tid, _tok in stuck:
            runner.in_flight.pop(tid, None)

    for _tid, tok in stuck:
        runner.work_queue.task_done()
        t = threading.Thread(
            target=mount_worker,
            args=(runner, unexpected_writer, orphan_writer),
            daemon=True,
        )
        t.start()
        with runner.lock:
            runner.threads.append(t)
        print(
            f"    [{','.join(runner.backend_ids)}] TIMEOUT: {tok.dirpath} "
            f"exceeded {PER_DIR_TIMEOUT:.0f}s, skipping and starting a replacement worker",
            flush=True,
        )


def heartbeat_loop(
    runners: list[MountRunner],
    unexpected_writer: LineWriter,
    orphan_writer: LineWriter,
    stop_event: threading.Event,
    interval: float,
    start_time: float,
) -> None:
    active = [r for r in runners if r.runnable]
    last_entries = 0
    last_time = start_time
    while not stop_event.wait(interval):
        for runner in active:
            check_mount_timeouts(runner, unexpected_writer, orphan_writer)

        now = time.perf_counter()
        dt = now - last_time
        total_entries = 0
        total_dirs = 0
        pending = []
        for runner in active:
            with runner.lock:
                entries = runner.stats["entries_scanned"]
                dirs = runner.stats["dirs_visited"]
                in_flight = len(runner.in_flight)
            total_entries += entries
            total_dirs += dirs
            qsize = runner.work_queue.qsize()
            pending.append(f"{','.join(runner.backend_ids)}={qsize}+{in_flight}")

        rate = (total_entries - last_entries) / dt if dt > 0 else 0.0
        elapsed = now - start_time
        print(
            f"    [heartbeat +{fmt_duration(elapsed)}] "
            f"entries={total_entries} ({rate:.0f}/s) dirs={total_dirs} "
            f"queued+active=[{', '.join(pending)}]",
            flush=True,
        )
        last_entries = total_entries
        last_time = now


def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Find unexpected entries and orphan _files dirs in Galaxy object-store shard trees."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="/storage/output_check_datasets",
        help="directory for the output files (default: /storage/output_check_datasets)",
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
    files_dirs = collect_files_dirs(backends)

    if not files_dirs:
        print("No disk files_dir entries found.")
        return 0

    print(f"Checking {len(files_dirs)} unique files_dir path(s)...")
    print(
        f"  workers/path: {WORKERS_PER_MOUNT}, per-dir timeout: {PER_DIR_TIMEOUT:.0f}s, "
        f"heartbeat: {HEARTBEAT_INTERVAL:.0f}s\n"
    )

    script_stem = Path(__file__).stem
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unexpected_file = out_dir / f"unexpected_{stamp}.txt"
    orphan_file = out_dir / f"orphan_files_dirs_{stamp}.txt"
    unexpected_writer = LineWriter(unexpected_file)
    orphan_writer = LineWriter(orphan_file)

    runners: list[MountRunner] = []
    for files_dir, store_by, backend_ids in files_dirs:
        exists = os.path.isdir(files_dir)
        ids = ",".join(backend_ids)
        shard_set = SHARD_CHECKS.get(store_by)
        print(f"[{ids}] {files_dir}  (store_by={store_by}, {'ok' if exists else 'MISSING'})")
        if exists and shard_set is None:
            print(f"    ERROR: unknown store_by={store_by!r}, skipping")
        runners.append(MountRunner(files_dir, store_by, backend_ids, exists, shard_set))

    total_start = time.perf_counter()
    stop_heartbeat = threading.Event()
    heartbeat_thread = threading.Thread(
        target=heartbeat_loop,
        args=(
            runners,
            unexpected_writer,
            orphan_writer,
            stop_heartbeat,
            HEARTBEAT_INTERVAL,
            total_start,
        ),
        daemon=True,
    )
    heartbeat_thread.start()

    # Start every runnable mount's worker pool and seed its queue with the
    # root directory up front. Since these are real OS threads, all mounts
    # make progress in parallel from this point on -- the order we `join()`
    # their queues in below doesn't serialize the actual work.
    for runner in runners:
        if not runner.runnable:
            continue
        for _ in range(WORKERS_PER_MOUNT):
            t = threading.Thread(
                target=mount_worker,
                args=(runner, unexpected_writer, orphan_writer),
                daemon=True,
            )
            t.start()
            runner.threads.append(t)
        runner.work_queue.put(runner.files_dir)

    all_stats: list[BackendStats] = []
    for runner in runners:
        stats = BackendStats(
            backend_ids=list(runner.backend_ids),
            files_dir=runner.files_dir,
            store_by=runner.store_by,
            exists=runner.exists,
        )
        if runner.runnable:
            be_start = time.perf_counter()
            runner.work_queue.join()

            # Stop this mount's workers. We don't wait for the OS threads to
            # actually exit: a worker stuck in a hung syscall (see
            # check_mount_timeouts) may never observe its sentinel, and
            # blocking on it here would defeat the whole point of the
            # watchdog. They're daemon threads, so they're cleaned up
            # automatically at process exit.
            with runner.lock:
                thread_count = len(runner.threads)
            for _ in range(thread_count):
                runner.work_queue.put(_SENTINEL)

            with runner.lock:
                s = runner.stats
                stats.entries_scanned = s["entries_scanned"]
                stats.dirs_visited = s["dirs_visited"]
                stats.dat_files = s["dat_files"]
                stats.files_dirs = s["files_dirs"]
                stats.unexpected = s["unexpected"]
                stats.orphan_files_dirs = s["orphan_files_dirs"]
                stats.read_errors = s["read_errors"]
                stats.timeout_errors = s["timeout_errors"]
                stats.error_paths = list(s["error_paths"])
                stats.timeout_paths = list(s["timeout_paths"])
            stats.elapsed_s = time.perf_counter() - be_start

            ids = ",".join(runner.backend_ids)
            if stats.timeout_errors:
                print(
                    f"    [{ids}] TIMEOUT: {stats.timeout_errors} dir(s) timed out "
                    f"({PER_DIR_TIMEOUT:.0f}s each): "
                    f"{stats.timeout_paths[:5]}{'...' if len(stats.timeout_paths) > 5 else ''}"
                )
            if stats.read_errors:
                print(
                    f"    [{ids}] WARNING: {stats.read_errors} unreadable dir(s): "
                    f"{stats.error_paths[:5]}{'...' if len(stats.error_paths) > 5 else ''}"
                )
            print(
                f"    [{ids}] {stats.dat_files} .dat files, {stats.files_dirs} _files dirs, "
                f"{stats.unexpected} unexpected, {stats.orphan_files_dirs} orphan "
                f"in {fmt_duration(stats.elapsed_s)}"
            )
        all_stats.append(stats)

    stop_heartbeat.set()
    heartbeat_thread.join()

    total_elapsed = time.perf_counter() - total_start
    unexpected_writer.close()
    orphan_writer.close()
    total_unexpected = sum(s.unexpected for s in all_stats)
    total_orphan = sum(s.orphan_files_dirs for s in all_stats)

    if unexpected_writer.has_content:
        print(f"Unexpected entries written to {unexpected_file}")
    if orphan_writer.has_content:
        print(f"Orphan _files dirs written to {orphan_file}")
    print(
        f"\nTotal: {total_unexpected} unexpected entries, "
        f"{total_orphan} orphan _files dirs"
    )

    usage = resource.getrusage(resource.RUSAGE_SELF)
    total_entries = sum(s.entries_scanned for s in all_stats)
    total_dirs = sum(s.dirs_visited for s in all_stats)
    total_dats = sum(s.dat_files for s in all_stats)
    total_files_dirs = sum(s.files_dirs for s in all_stats)
    total_errors = sum(s.read_errors for s in all_stats)
    total_timeouts = sum(s.timeout_errors for s in all_stats)
    stats_lines = [
        f"# check_datasets run {stamp}",
        f"config: {config_path}",
        f"workers per path: {WORKERS_PER_MOUNT}",
        f"per-dir timeout: {PER_DIR_TIMEOUT:.0f}s",
        f"heartbeat interval: {HEARTBEAT_INTERVAL:.0f}s",
        f"unique files_dirs checked: {len(files_dirs)}",
        f"backends present: {sum(1 for s in all_stats if s.exists)}",
        f"backends missing: {sum(1 for s in all_stats if not s.exists)}",
        f"total entries scanned: {total_entries}",
        f"total dirs visited: {total_dirs}",
        f"total .dat files: {total_dats}",
        f"total _files dirs: {total_files_dirs}",
        f"total unexpected entries: {total_unexpected}",
        f"total orphan _files dirs: {total_orphan}",
        f"total unreadable dirs: {total_errors}",
        f"total timed-out dirs: {total_timeouts}",
        f"wall time: {fmt_duration(total_elapsed)}",
        f"cpu user time: {fmt_duration(usage.ru_utime)}",
        f"cpu sys time: {fmt_duration(usage.ru_stime)}",
        f"peak rss: {usage.ru_maxrss / 1024:.1f} MB",
        "",
        "# per-dir stats (a dir may be shared by multiple backends)",
        "# backend_ids\tfiles_dir\tstore_by\texists\tentries_scanned\t"
        "dirs_visited\tdat_files\tfiles_dirs\tunexpected\torphan_files_dirs\t"
        "read_errors\ttimeout_errors\telapsed_s",
    ]
    for s in all_stats:
        stats_lines.append(
            f"{','.join(s.backend_ids)}\t{s.files_dir}\t{s.store_by}\t{s.exists}\t"
            f"{s.entries_scanned}\t{s.dirs_visited}\t{s.dat_files}\t"
            f"{s.files_dirs}\t{s.unexpected}\t{s.orphan_files_dirs}\t"
            f"{s.read_errors}\t{s.timeout_errors}\t{s.elapsed_s:.2f}"
        )
    all_err_paths = [
        (p, "unreadable", s) for s in all_stats for p in s.error_paths
    ] + [
        (p, "timeout", s) for s in all_stats for p in s.timeout_paths
    ]
    if all_err_paths:
        stats_lines.append("")
        stats_lines.append("# problematic directories")
        stats_lines.append("# path\treason\tshared_by")
        for p, reason, s in all_err_paths:
            stats_lines.append(f"{p}\t{reason}\t{','.join(s.backend_ids)}")
    stats_file = out_dir / f"stats_{stamp}.txt"
    stats_file.write_text("\n".join(stats_lines) + "\n")
    print(f"Stats written to {stats_file}")

    return 1 if (total_unexpected or total_orphan) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
