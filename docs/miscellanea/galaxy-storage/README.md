# galaxy-storage

Scripts for auditing Galaxy distributed object-store backends defined in
`object_store.yml`.  The tools walk the on-disk `files_dir` trees of every
`type: disk` backend and report integrity problems.

## Index

| script                            | description                                                              |
|-----------------------------------|--------------------------------------------------------------------------|
| [`check_symlinks.py`](#check_symlinkspy) | report symbolic links inside shard directories                     |
| [`check_datasets.py`](#check_datasetspy) | find unexpected entries and orphan `_files/` dirs                  |
| [`check_folder_size.py`](#check_folder_sizepy) | per-subdirectory size, file count and newest-file mtime      |
| [`check_files_timeouts.py`](#check_files_timeoutspy) | find `_files/` dirs whose scans exceed the timeout     |
| [`check_purged.py`](#check_purgedpy) | verify purged datasets are actually gone from disk                    |
| [`check_totalsize.py`](#check_totalsizepy) | verify DB `total_size` matches the real on-disk size            |

See also [NFS hardening](#nfs-hardening) and the [stats file format](#stats-file-format).

## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (used to manage the virtualenv)
- PyYAML (installed automatically into the project venv)

## Setup

```bash
uv venv          # creates .venv (kept for future runs)
uv pip install pyyaml
```

## object_store.yml

Galaxy's distributed object-store config.  Each `type: disk` backend
declares a `files_dir` path and a `store_by` mode (`id` or `uuid`) that
determines the on-disk sharding layout:

| `store_by` | shard directories        | example path                                          |
|------------|--------------------------|-------------------------------------------------------|
| `id`       | 3-digit numeric groups   | `files/000/777/dataset_777777.dat`                   |
| `uuid`     | single hex-char dirs     | `files/1/3/5/dataset_135ee48a-….dat`                 |

Both kinds are walked.

Per-dataset auxiliary folders (`<dataset>_files/`) are **not** descended
into — only the shard directories and the `.dat` / `_files` entries
directly inside them are examined.

**!! s3 based storage backends are not supported by these scripts, since they do not have a local filesystem - remove them from the object_store.yml if you want to use these scripts **

## Scripts

### check_symlinks.py

Walks every disk `files_dir` tree and reports any symbolic links found
inside the shard directories.

```bash
uv run check_symlinks.py [-o OUTPUT_DIR] [object_store.yml]
```

**Output** (written to `output_check_symlinks/`):

| file                          | content                                      |
|-------------------------------|----------------------------------------------|
| `symlinks_<stamp>.txt`        | one `path -> target` line per symlink found  |
| `stats_<stamp>.txt`           | run summary + per-backend stats (see below)  |

Exit code: `0` clean · `1` symlinks found · `2` config error

### check_datasets.py

Walks every disk `files_dir` tree and checks for:

1. **Unexpected entries** — anything that is not a `.dat` file, a
   `<dataset>_files` directory, or a shard subdirectory.
2. **Orphan `_files` dirs** — a `<name>_files` folder with no matching
   `<name>.dat` file in the same parent directory.

```bash
uv run check_datasets.py [-o OUTPUT_DIR] [object_store.yml]
```

**Output** (written to `output_check_datasets/`):

| file                                | content                                       |
|-------------------------------------|-----------------------------------------------|
| `unexpected_<stamp>.txt`            | full path of every unexpected entry           |
| `orphan_files_dirs_<stamp>.txt`     | full path of every orphan `_files` directory  |
| `stats_<stamp>.txt`                 | run summary + per-backend stats (see below)   |

Exit code: `0` clean · `1` problems found · `2` config error

### check_folder_size.py

Measures the total recursive size, file count, and newest-file mtime of
every immediate subdirectory of a given path (one depth level only).
Files directly inside the given path are not measured.  Useful for
surveying how space is distributed across object-store backends or shard
roots.

Size and newest-file are obtained in a **single streaming `find` pass**
(`find -type f -printf '%s %T@ %p\n'`), so each subtree is walked only
once and memory stays constant regardless of file count.  Sizes match
`du -sb` (apparent size in bytes).

```bash
uv run check_folder_size.py [-o OUTPUT_DIR] <path>
```

**Output** (written to `output_check_folder_size/`):

| file                    | content                                                              |
|-------------------------|----------------------------------------------------------------------|
| `sizes_<stamp>.txt`     | TSV: `path  size_bytes  human  file_count  newest_mtime  newest_file  elapsed_s  status` per subdir |
| `stats_<stamp>.txt`     | run summary + per-subdir table sorted by size descending    |

Console also prints a live per-subdir progress line (size, file count,
newest file date) and a top-10 largest summary at the end.

Each `find` invocation is bounded by `GALAXY_CHECK_TIMEOUT` (default
1800s); the timeout is checked on every line, so a hung NFS directory is
killed mid-stream and the walk continues.

Exit code: `0` all measured · `1` timeouts/errors occurred · `2` bad path

### `check_files_timeouts.py`

Scans every disk backend's shard tree, finds `dataset_*_files/` directories,
and attempts to measure each directory in one streaming `find` pass.  It is a
focused way to identify `_files/` directories whose scans exceed the configured
window; these are candidates for very large directories, although NFS or I/O
problems can also cause a timeout.

```bash
GALAXY_CHECK_TIMEOUT=120 uv run check_files_timeouts.py [-o OUTPUT_DIR] [object_store.yml]
```

**Output** (written to `output_check_files_timeouts/`):

| file | content |
|------|---------|
| `timeouts_<stamp>.tsv` | timed-out `_files/` path, partial bytes/files seen, and elapsed time |
| `errors_<stamp>.tsv` | `_files/` paths whose scan ended in an error |
| `stats_<stamp>.txt` | run summary, including shard scan problems |

Exit code: `0` all measured · `1` a timeout or error occurred · `2` config error

### check_purged.py

Verifies that datasets marked as purged in the Galaxy database are
actually gone from disk.  Takes a CSV export produced by:

```bash
psql -c "\copy (SELECT id, uuid, object_store_id FROM dataset WHERE purged = 't') TO '/tmp/dataset_export_purged.csv' WITH CSV HEADER;"
```

For each dataset, the script computes the expected on-disk path by
cross-referencing `object_store.yml` (looking up the backend by
`object_store_id`, then applying the correct sharding rule) and checks
whether `dataset_<id_or_uuid>.dat` and/or `dataset_<id_or_uuid>_files/`
still exist.  Datasets with a NULL `object_store_id` are skipped.

The CSV is streamed row by row on the main thread (constant memory
regardless of file size). State is grouped by **physical storage path**
(`files_dir` + `store_by`), not by `object_store_id` — several backend
ids in `object_store.yml` can point at the same underlying mount (e.g.
after Galaxy config history/migrations), and treating them separately
would both duplicate shard-dir existence checks for the same on-disk
directory and multiply worker concurrency against that one mount by
however many ids alias it. Each distinct path gets its own bounded queue,
shard-dir existence cache, and pool of worker threads — since these
paths live on NFS, the bottleneck is round-trip latency, not CPU, so
parallel `stat`/`isdir` calls (which release the GIL while blocked) cut
wall time dramatically compared to checking one path at a time.

```bash
uv run check_purged.py [-o OUTPUT_DIR] <purged.csv> [object_store.yml]
```

Environment variables:

| variable                 | meaning                                                | default |
|--------------------------|---------------------------------------------------------|-------|
| `GALAXY_CHECK_WORKERS`   | worker threads per distinct storage path                 | `8`  |
| `GALAXY_CHECK_QUEUE`     | max rows queued per storage path before the reader blocks| `2000`|
| `GALAXY_CHECK_HEARTBEAT` | heartbeat interval in seconds                            | `30`  |

**Output** (written to `output_check_purged/`):

| file                       | content                                                          |
|----------------------------|------------------------------------------------------------------|
| `still_exist_<stamp>.txt`  | TSV: `dataset_id  uuid  object_store_id  kind  path` for each dataset still on disk |
| `stats_<stamp>.txt`        | run summary (checked, NULL store, unknown store, still on disk)  |

Exit code: `0` all purged datasets gone · `1` some still on disk · `2` config error

### check_totalsize.py

Verifies that the database `total_size` column matches what is actually
on disk for datasets where `file_size = 0` but `total_size > 0` (and
not purged).  Galaxy's columns should satisfy:

```
total_size = file_size + (size of the _files/ directory)
```

When `file_size` is wrongly recorded as `0` but the `.dat` file has
bytes on disk, `total_size` ends up missing the `.dat` contribution and
only reflects the `_files/` directory.  Takes a CSV export produced by:

```bash
psql -c "\copy (SELECT id, uuid, object_store_id, file_size, total_size FROM dataset WHERE file_size = 0 AND total_size > 0 AND purged = 'f') TO '/tmp/dataset_export_totalsize.csv' WITH CSV HEADER;"
```

For each dataset the script computes the expected on-disk paths by
cross-referencing `object_store.yml`, measures the real `.dat` size
(`stat`) and the real `_files/` directory size (a single streaming
`find -printf '%s'` pass, matching `du -sb` apparent size), and compares
`actual_dat_size + actual_folder_size` against `db_total_size`.
Datasets with a NULL `object_store_id` are skipped.

At the end the script reports `sum should-be file_size` — the sum of
every `actual_dat_size` that was `> 0`, i.e. the total `file_size` the
database should have recorded as non-zero.

```bash
uv run check_totalsize.py [-o OUTPUT_DIR] <totalsize.csv> [object_store.yml]
```

**Output** (written to `output_check_totalsize/`):

| file                       | content                                                                                  |
|----------------------------|------------------------------------------------------------------------------------------|
| `mismatch_<stamp>.txt`     | One dataset `.dat` path per line for each dataset whose on-disk total differs from the DB |
| `stats_<stamp>.txt`        | run summary (checked, missing, timeouts, mismatches, sums of db vs actual sizes)         |

Exit code: `0` all totals match · `1` mismatches, timeouts or errors found · `2` config error

## Concurrent checks

All check scripts use worker threads to overlap filesystem I/O:

- `check_purged.py` and `check_totalsize.py` stream CSV rows into bounded
  queues with one worker pool per distinct `(files_dir, store_by)` path.
  Backend IDs that share that path share the same pool.
- `check_symlinks.py` and `check_datasets.py` scan shard directories
  concurrently within each storage path and across paths.
- `check_files_timeouts.py` scans shard directories and measures
  discovered `_files/` directories concurrently in each path's pool.
- `check_folder_size.py` measures immediate subdirectories concurrently
  using one pool for the supplied root.

Set `GALAXY_CHECK_WORKERS` to control concurrency (default `8`, except
`check_purged.py`, whose current default is `12`). Set
`GALAXY_CHECK_QUEUE` to control producer backpressure in the CSV checks
(default `2000` queued rows per path). Recursive shard discovery maintains
a pending-directory frontier rather than blocking workers on a full queue.
Outputs are written safely as results arrive, so their order may vary.

```bash
GALAXY_CHECK_WORKERS=8 GALAXY_CHECK_QUEUE=2000 uv run check_totalsize.py -o results totalsize.csv object_store.yml
```

## Output directories

Every script writes its findings to `output_<script_name>/`.  The
output location can be overridden with the `-o` / `--output-dir`
argument (all scripts accept it); the defaults for the main scripts
are `/storage/output_<script_name>/`.

## NFS hardening

The storage backends are NFS mounts that can become unresponsive
(stale file handles, hung servers, etc.).

- **Shard-directory timeout** — threaded directory walkers use a watchdog
  to abandon scans that exceed the limit and start replacement daemon
  workers. Late results from abandoned tasks are ignored. Python cannot
  interrupt a blocked filesystem syscall in another thread. Set via:

  ```bash
  GALAXY_CHECK_TIMEOUT=60 uv run check_symlinks.py
  ```

  Default: `120` seconds.

  Size measurements run `find` under the system `timeout` command.
  The CSV checks' direct filesystem metadata calls follow the same
  behavior as `check_purged.py` and can wait for the mount to respond.

- **Heartbeat** — prints a progress line every N seconds so you always
  know the script is alive and where it's working, even when a single
  directory contains millions of entries.  Set via:

  ```bash
  GALAXY_CHECK_HEARTBEAT=10 uv run check_symlinks.py
  ```

  Default: `30` seconds.

The symlink and dataset checks list timed-out and unreadable directories
in a `# problematic directories` section of the stats file. The `_files`
timeout check writes measurement problems to its TSV reports.

## Stats file format

Each run writes a TSV stats file with a header block (run timestamp,
config path, timeout/heartbeat settings, aggregate totals, wall/CPU
time, peak RSS) followed by a per-`files_dir` table.  Example:

```
# check_symlinks run 20260813_120338
config: object_store.yml
per-dir timeout: 120s
heartbeat interval: 30s
unique files_dirs checked: 16
…
wall time: 1h23m45s
cpu user time: 0h45m12s
peak rss: 45.2 MB

# per-dir stats (a dir may be shared by multiple backends)
# backend_ids	files_dir	store_by	exists	entries_scanned	dirs_visited	symlinks_found	read_errors	timeout_errors	elapsed_s
files11	/data/dnb05/galaxy_db/files	uuid	True	482103	1847	0	0	0	312.45
files23,files24,files25,files26	/data/dnb09/galaxy_db/files	uuid	True	911204	3102	2	0	0	598.10
```

## Notes

- Duplicate `files_dir` paths (multiple backends pointing at the same
  directory) are walked **once**; all sharing backend ids are listed in
  the output.
- `os.scandir` is used instead of `os.walk` so that `DirEntry.is_symlink()`
  reuses the stat already fetched during the directory read, avoiding a
  redundant `lstat` per entry.
- Symlink output is streamed to disk incrementally; memory usage does not
  grow with the number of findings.
- `check_folder_size.py` uses a single streaming `find -printf` pass per
  subdirectory (size + newest file in one tree walk, constant memory)
  rather than separate `du` + `find` invocations.
- `check_symlinks.py` and `check_datasets.py` accept an optional config
  path argument (default: `object_store.yml` in the current directory).
- `check_folder_size.py` takes a required path argument.
