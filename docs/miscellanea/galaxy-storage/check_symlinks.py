#!/usr/bin/env python3
"""Check that files_dir paths declared in Galaxy's object_store.yml
(and their subdirectories) do not contain any symbolic links.

Walking is limited to the Galaxy object-store shard directories so
that per-dataset ``*_files`` auxiliary folders are not descended into.

Sharding rules (mirroring Galaxy's directory_hash_id / directory_hash_uuid):
  - store_by: id   -> shard dirs are 3-digit numeric (e.g. 000/777/777)
  - store_by: uuid -> shard dirs are single hex chars  (e.g. 0/1/4)

Environment variables:
    GALAXY_CHECK_WORKERS     worker threads per distinct storage path (default 8)
    GALAXY_CHECK_TIMEOUT     per-directory timeout in seconds (default 120)
    GALAXY_CHECK_HEARTBEAT   heartbeat interval in seconds (default 30)

Usage:
    uv run check_symlinks.py [-o OUTPUT_DIR] [object_store.yml]

Output directory (default: /storage/output_check_symlinks).
"""

from __future__ import annotations

import argparse
import os
import re
import resource
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from check_workers import LineWriter, WorkerPool, WORKERS

JINJA_RE = re.compile(r"\{\{.*?\}\}")
JINJA_PLACEHOLDER = "__JINJA_TEMPLATE__"

PER_DIR_TIMEOUT = float(os.environ.get("GALAXY_CHECK_TIMEOUT", "120"))
HEARTBEAT_INTERVAL = float(os.environ.get("GALAXY_CHECK_HEARTBEAT", "30"))

SHARD_CHECKS: dict[str, set[str]] = {
    "uuid": set("0123456789abcdef"),
    "id": {f"{i:03d}" for i in range(1000)},
}


@dataclass
class BackendStats:
    backend_ids: list[str]
    files_dir: str
    store_by: str
    exists: bool
    files_scanned: int = 0
    dirs_visited: int = 0
    symlinks_found: int = 0
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
    is printed and the first backend's store_by wins.  Both legacy (store_by:
    id, 3-digit numeric shards) and non-legacy (store_by: uuid, single hex
    char shards) backends are included.
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


def start_scan(stats: BackendStats, writer: LineWriter) -> WorkerPool:
    shard_set = SHARD_CHECKS[stats.store_by]

    def work(dirpath, publish):
        subdirs = []
        count = 0
        try:
            with os.scandir(dirpath) as entries:
                for entry in entries:
                    count += 1
                    if entry.is_symlink():
                        try:
                            target = os.readlink(entry.path)
                        except OSError:
                            target = None

                        def found(path=entry.path, target=target):
                            writer.write(f"{path} -> {target}\n")
                            stats.symlinks_found += 1

                        publish(found)
                    elif entry.name in shard_set and entry.is_dir(follow_symlinks=False):
                        subdirs.append(entry.path)
        except OSError:
            return count, subdirs, True
        return count, subdirs, False

    def consume(dirpath, result):
        count, subdirs, error = result
        stats.files_scanned += count
        stats.dirs_visited += 1
        if error:
            stats.read_errors += 1
            stats.error_paths.append(dirpath)
        return subdirs

    def timed_out(dirpath):
        stats.timeout_errors += 1
        stats.timeout_paths.append(dirpath)
        print(f"    TIMEOUT: {dirpath}", flush=True)

    pool = WorkerPool(
        ",".join(stats.backend_ids), work, consume, timeout=PER_DIR_TIMEOUT,
        on_timeout=timed_out, heartbeat=HEARTBEAT_INTERVAL,
    )
    pool.submit(stats.files_dir)
    return pool


def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Report symbolic links inside Galaxy object-store shard directories."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="/storage/output_check_symlinks",
        help="directory for the output files (default: /storage/output_check_symlinks)",
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

    print(f"Checking {len(files_dirs)} unique files_dir path(s) for symlinks...")
    print(f"  per-dir timeout: {PER_DIR_TIMEOUT:.0f}s, heartbeat: {HEARTBEAT_INTERVAL:.0f}s\n")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    symlinks_file = out_dir / f"symlinks_{stamp}.txt"
    writer = LineWriter(symlinks_file)

    all_stats: list[BackendStats] = []
    total_start = time.perf_counter()
    pools = []

    for files_dir, store_by, backend_ids in files_dirs:
        exists = os.path.isdir(files_dir)
        ids = ",".join(backend_ids)
        print(f"[{ids}] {files_dir}  (store_by={store_by}, {'ok' if exists else 'MISSING'})")
        stats = BackendStats(
            backend_ids=list(backend_ids),
            files_dir=files_dir,
            store_by=store_by,
            exists=exists,
        )
        all_stats.append(stats)
        if not exists:
            continue

        shard_set = SHARD_CHECKS.get(store_by)
        if shard_set is None:
            print(f"    ERROR: unknown store_by={store_by!r}, skipping")
            continue
        pools.append((stats, start_scan(stats, writer), time.perf_counter()))

    try:
        for stats, pool, started in pools:
            pool.wait()
            stats.elapsed_s = time.perf_counter() - started
    finally:
        for _, pool, _ in pools:
            pool.close()
        writer.close()

    total_elapsed = time.perf_counter() - total_start
    total_symlinks = sum(s.symlinks_found for s in all_stats)
    if writer.fh is not None:
        print(f"Symlink paths written to {symlinks_file}")
    print(f"\nTotal symlinks found: {total_symlinks}")

    usage = resource.getrusage(resource.RUSAGE_SELF)
    total_files = sum(s.files_scanned for s in all_stats)
    total_dirs = sum(s.dirs_visited for s in all_stats)
    total_errors = sum(s.read_errors for s in all_stats)
    total_timeouts = sum(s.timeout_errors for s in all_stats)
    stats_lines = [
        f"# check_symlinks run {stamp}",
        f"config: {config_path}",
        f"workers per path: {WORKERS}",
        f"per-dir timeout: {PER_DIR_TIMEOUT:.0f}s",
        f"heartbeat interval: {HEARTBEAT_INTERVAL:.0f}s",
        f"unique files_dirs checked: {len(files_dirs)}",
        f"backends present: {sum(1 for s in all_stats if s.exists)}",
        f"backends missing: {sum(1 for s in all_stats if not s.exists)}",
        f"total entries scanned: {total_files}",
        f"total dirs visited: {total_dirs}",
        f"total unreadable dirs: {total_errors}",
        f"total timed-out dirs: {total_timeouts}",
        f"total symlinks found: {total_symlinks}",
        f"wall time: {fmt_duration(total_elapsed)}",
        f"cpu user time: {fmt_duration(usage.ru_utime)}",
        f"cpu sys time: {fmt_duration(usage.ru_stime)}",
        f"peak rss: {usage.ru_maxrss / 1024:.1f} MB",
        "",
        "# per-dir stats (a dir may be shared by multiple backends)",
        "# backend_ids\tfiles_dir\tstore_by\texists\tentries_scanned\t"
        "dirs_visited\tsymlinks_found\tread_errors\ttimeout_errors\telapsed_s",
    ]
    for s in all_stats:
        stats_lines.append(
            f"{','.join(s.backend_ids)}\t{s.files_dir}\t{s.store_by}\t{s.exists}\t"
            f"{s.files_scanned}\t{s.dirs_visited}\t{s.symlinks_found}\t"
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

    return 1 if total_symlinks else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
