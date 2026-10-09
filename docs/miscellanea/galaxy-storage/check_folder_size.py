#!/usr/bin/env python3
"""Check the size of every immediate subdirectory of a given path.

Only one depth level is measured: for ``/foo`` the script reports the
total recursive size of ``/foo/bar/``, ``/foo/baz/``, etc.  Files
directly inside ``/foo`` (not in a subdirectory) are not measured.

Size and newest-file mtime are obtained in a **single streaming pass**
via ``find -type f -printf '%s %T@ %p\\n'``, so each subtree is walked
only once and memory stays constant regardless of file count.

Each ``find`` is wrapped by the system ``timeout`` command so that a
hung NFS directory is killed at the OS level even if the ``find``
process is in uninterruptible-sleep (D) state.

Environment variables:
    GALAXY_CHECK_WORKERS     concurrent subdirectory measurements (default 8)
    GALAXY_CHECK_TIMEOUT     per-directory timeout in seconds (default 120)
    GALAXY_CHECK_HEARTBEAT   heartbeat interval in seconds (default 30)

Usage:
    uv run check_folder_size.py [-o OUTPUT_DIR] <path>

Output directory (default: /storage/output_check_folder_size).
"""

from __future__ import annotations

import argparse
import os
import resource
import select
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from check_workers import WorkerPool, WORKERS

PER_DIR_TIMEOUT = int(os.environ.get("GALAXY_CHECK_TIMEOUT", "120"))
HEARTBEAT_INTERVAL = float(os.environ.get("GALAXY_CHECK_HEARTBEAT", "30"))


@dataclass
class DirSize:
    path: str
    name: str
    size_bytes: int = 0
    file_count: int = 0
    newest_file: str | None = None
    newest_mtime: float | None = None
    timed_out: bool = False
    error: str | None = None
    elapsed_s: float = 0.0


def fmt_size(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} EiB"


def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def measure_dir(path: str, label: str = "") -> DirSize:
    """Measure a subtree in a single streaming ``find`` pass.

    ``find`` is run under ``timeout`` so the OS kills it (SIGKILL after
    a grace period) even if it's stuck in D state on NFS.  The Python
    side uses ``select`` on the pipe so it never blocks indefinitely —
    if no data arrives within the heartbeat interval, a progress line
    is printed so the user knows which directory is slow.
    """
    start = time.perf_counter()
    result = DirSize(path=path, name=os.path.basename(path))

    cmd = [
        "timeout", "-k", "5", str(PER_DIR_TIMEOUT),
        "find", path, "-type", "f", "-printf", "%s %T@ %p\n",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        result.error = str(exc)
        result.elapsed_s = time.perf_counter() - start
        return result

    assert proc.stdout is not None
    fd = proc.stdout.fileno()
    newest_mtime = -1.0
    last_heartbeat = time.monotonic()

    while True:
        # Use select so we don't block forever on a hung NFS pipe.
        # Wait at most HEARTBEAT_INTERVAL seconds; if no data, print
        # a heartbeat and try again (until the overall timeout fires).
        ready, _, _ = select.select([fd], [], [], HEARTBEAT_INTERVAL)

        if not ready:
            # No data — either find is still working (slow NFS) or hung.
            elapsed = time.perf_counter() - start
            now = time.monotonic()
            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                last_heartbeat = now
                print(
                    f"      ... [{label or path}] waiting: "
                    f"{result.file_count} files so far, "
                    f"{fmt_duration(elapsed)} elapsed",
                    flush=True,
                )
            if elapsed >= PER_DIR_TIMEOUT:
                # timeout command should have killed find already;
                # force-kill just in case.
                proc.kill()
                result.timed_out = True
                break
            # Check if find exited (timeout killed it)
            if proc.poll() is not None:
                result.timed_out = True
                break
            continue

        line = proc.stdout.readline()
        if not line:
            # EOF — find finished (or was killed)
            break

        result.file_count += 1
        parts = line.rstrip(b"\n").split(b" ", 2)
        if len(parts) == 3:
            try:
                result.size_bytes += int(parts[0])
                mtime = float(parts[1])
                if mtime > newest_mtime:
                    newest_mtime = mtime
                    result.newest_file = parts[2].decode("utf-8", "replace")
            except (ValueError, IndexError):
                pass

    proc.wait()

    # timeout exits with 124 on timeout, 137 on SIGKILL (-k)
    if proc.returncode in (124, 137, -9, -15):
        result.timed_out = True
    elif proc.returncode not in (0, None):
        stderr = proc.stderr.read().strip() if proc.stderr else b""
        stderr_text = stderr.decode("utf-8", "replace").strip()
        if stderr_text:
            result.error = stderr_text

    if newest_mtime >= 0:
        result.newest_mtime = newest_mtime

    result.elapsed_s = time.perf_counter() - start
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Measure size, file count and newest-file mtime of every immediate subdirectory of a path."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="/storage/output_check_folder_size",
        help="directory for the output files (default: /storage/output_check_folder_size)",
    )
    parser.add_argument("path", help="path whose immediate subdirectories are measured")
    args = parser.parse_args(argv[1:])

    root = args.path
    if not os.path.isdir(root):
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    root = os.path.abspath(root)

    try:
        entries = list(os.scandir(root))
    except OSError as exc:
        print(f"error: cannot read {root}: {exc}", file=sys.stderr)
        return 2

    subdirs = sorted(
        e.path for e in entries if e.is_dir(follow_symlinks=False)
    )

    if not subdirs:
        print(f"No subdirectories found in {root}")
        return 0

    print(f"Measuring {len(subdirs)} subdirectory(ies) of {root}...")
    print(f"  per-dir timeout: {PER_DIR_TIMEOUT}s, heartbeat: {HEARTBEAT_INTERVAL:.0f}s\n")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sizes_file = out_dir / f"sizes_{stamp}.txt"

    results: list[DirSize] = []
    total_start = time.perf_counter()

    with sizes_file.open("w") as fh:
        fh.write(
            "# path\tsize_bytes\thuman\tfile_count\t"
            "newest_mtime\tnewest_file\telapsed_s\tstatus\n"
        )
        def consume(path, res):
            results.append(res)
            status = "ok"
            if res.timed_out:
                status = "TIMEOUT"
            elif res.error:
                status = "ERROR"
            newest = ""
            if res.newest_mtime:
                newest = (
                    f"  newest: {datetime.fromtimestamp(res.newest_mtime).strftime('%Y-%m-%d %H:%M:%S')}"
                )
            print(
                f"  [{len(results)}/{len(subdirs)}] {res.name}: {fmt_size(res.size_bytes)}"
                f"  ({res.file_count} files)"
                + (f"  ({status})" if status != "ok" else "")
                + newest
                + f"  [{fmt_duration(res.elapsed_s)}]"
            )
            mtime_str = (
                datetime.fromtimestamp(res.newest_mtime).isoformat()
                if res.newest_mtime else ""
            )
            fh.write(
                f"{res.path}\t{res.size_bytes}\t{fmt_size(res.size_bytes)}\t"
                f"{res.file_count}\t{mtime_str}\t{res.newest_file or ''}\t"
                f"{res.elapsed_s:.2f}\t{status}\n"
            )
            fh.flush()

        pool = WorkerPool(root, lambda path, publish: measure_dir(path, label=os.path.basename(path)),
                          consume, heartbeat=HEARTBEAT_INTERVAL)
        try:
            for path in subdirs:
                pool.submit(path)
            pool.wait()
        finally:
            pool.close()

    total_elapsed = time.perf_counter() - total_start

    ok_results = [r for r in results if not r.timed_out and not r.error]
    timed_out = [r for r in results if r.timed_out]
    errored = [r for r in results if r.error and not r.timed_out]
    total_size = sum(r.size_bytes for r in ok_results)
    total_files = sum(r.file_count for r in ok_results)

    print(f"\nTotal size: {fmt_size(total_size)} ({total_size} bytes)")
    print(f"Total files: {total_files}")
    print(f"Measured: {len(ok_results)}, timed out: {len(timed_out)}, errors: {len(errored)}")
    print(f"Wall time: {fmt_duration(total_elapsed)}")
    print(f"Sizes written to {sizes_file}")

    if ok_results:
        print("\nTop 10 largest:")
        for r in sorted(ok_results, key=lambda x: x.size_bytes, reverse=True)[:10]:
            newest = ""
            if r.newest_mtime:
                newest = f"  newest: {datetime.fromtimestamp(r.newest_mtime).strftime('%Y-%m-%d')}"
            print(f"  {fmt_size(r.size_bytes):>12}  {r.name}{newest}")

    usage = resource.getrusage(resource.RUSAGE_SELF)
    stats_file = out_dir / f"stats_{stamp}.txt"
    stats_lines = [
        f"# check_folder_size run {stamp}",
        f"path: {root}",
        f"workers: {WORKERS}",
        f"per-dir timeout: {PER_DIR_TIMEOUT}s",
        f"heartbeat interval: {HEARTBEAT_INTERVAL:.0f}s",
        f"subdirectories measured: {len(subdirs)}",
        f"ok: {len(ok_results)}",
        f"timed out: {len(timed_out)}",
        f"errors: {len(errored)}",
        f"total size: {total_size} bytes ({fmt_size(total_size)})",
        f"total files: {total_files}",
        f"wall time: {fmt_duration(total_elapsed)}",
        f"cpu user time: {fmt_duration(usage.ru_utime)}",
        f"cpu sys time: {fmt_duration(usage.ru_stime)}",
        f"peak rss: {usage.ru_maxrss / 1024:.1f} MB",
        "",
        "# per-subdir stats",
        "# name\tpath\tsize_bytes\thuman\tfile_count\t"
        "newest_mtime\tnewest_file\telapsed_s\tstatus",
    ]
    for r in sorted(results, key=lambda x: x.size_bytes, reverse=True):
        status = "ok" if not r.timed_out and not r.error else (
            "timeout" if r.timed_out else "error"
        )
        mtime_str = (
            datetime.fromtimestamp(r.newest_mtime).isoformat()
            if r.newest_mtime else ""
        )
        stats_lines.append(
            f"{r.name}\t{r.path}\t{r.size_bytes}\t{fmt_size(r.size_bytes)}\t"
            f"{r.file_count}\t{mtime_str}\t{r.newest_file or ''}\t"
            f"{r.elapsed_s:.2f}\t{status}"
        )
    stats_file.write_text("\n".join(stats_lines) + "\n")
    print(f"Stats written to {stats_file}")

    return 1 if (timed_out or errored) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
