#!/usr/bin/env python3
r"""Extract dataset ids and uuids from a file of Galaxy object-store paths.

Reads paths (one per line) from a file or stdin and extracts the dataset
identifier from each basename, recognising three on-disk naming patterns:

    dataset_<id>.dat[.<suffix>...]        -> numeric id
    dataset_<uuid>.dat[.<suffix>...]      -> uuid (dashed, as on disk)
    data_id_<id>_<rest>                   -> numeric id  (job-work files)

Ids are written to ``ids.txt`` and uuids to ``uuids.txt`` (in the current
directory by default).  Uuids are emitted without dashes, matching the
Galaxy ``dataset.uuid`` DB column form.

Lines that match neither pattern are skipped (and counted as ``unmatched``).
Output is deduplicated, preserving first-seen order.

Usage:
    uv run usefull/extract_ids.py <paths.txt> [-o ids.txt] [-u uuids.txt]
    uv run usefull/extract_ids.py -            # read from stdin
    find /data -name 'dataset_*' | uv run usefull/extract_ids.py -
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

UUID_RE = re.compile(
    r"dataset_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.dat"
)
ID_DAT_RE = re.compile(r"dataset_(\d+)\.dat")
DATA_ID_RE = re.compile(r"data_id_(\d+)_")


def extract(line: str) -> tuple[str | None, str | None]:
    """Return (kind, value) where kind is 'id' or 'uuid', else (None, None).

    Kind is determined by which pattern matches first (uuid checked before
    id so a dashed uuid is never mis-parsed as a numeric id).
    """
    basename = line.rsplit("/", 1)[-1]
    m = UUID_RE.search(basename)
    if m:
        return "uuid", m.group(1).replace("-", "")
    m = ID_DAT_RE.search(basename)
    if m:
        return "id", m.group(1)
    m = DATA_ID_RE.search(basename)
    if m:
        return "id", m.group(1)
    return None, None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Extract dataset ids and uuids from a file of paths.",
    )
    parser.add_argument(
        "input",
        help="file of paths (use '-' for stdin)",
    )
    parser.add_argument(
        "-o", "--ids-out", default="ids.txt",
        help="output file for ids (default: ids.txt)",
    )
    parser.add_argument(
        "-u", "--uuids-out", default="uuids.txt",
        help="output file for uuids (default: uuids.txt)",
    )
    parser.add_argument(
        "--no-dedup", action="store_true",
        help="keep duplicate identifiers (default: dedup, first-seen order)",
    )
    args = parser.parse_args(argv[1:])

    if args.input == "-":
        in_fh = sys.stdin
    else:
        path = Path(args.input)
        if not path.is_file():
            print(f"error: {path} not found", file=sys.stderr)
            return 2
        in_fh = path.open("r")

    ids: list[str] = []
    uuids: list[str] = []
    seen_ids: set[str] = set()
    seen_uuids: set[str] = set()
    id_matches = 0
    uuid_matches = 0
    unmatched = 0
    matched = 0
    n = 0

    for line in in_fh:
        n += 1
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        kind, value = extract(line)
        if kind is None:
            unmatched += 1
            continue
        matched += 1
        if kind == "id":
            id_matches += 1
            if args.no_dedup or value not in seen_ids:
                if not args.no_dedup:
                    seen_ids.add(value)
                ids.append(value)
        else:
            uuid_matches += 1
            if args.no_dedup or value not in seen_uuids:
                if not args.no_dedup:
                    seen_uuids.add(value)
                uuids.append(value)

    if args.input != "-":
        in_fh.close()

    with open(args.ids_out, "w") as fh:
        for v in ids:
            fh.write(v + "\n")
    with open(args.uuids_out, "w") as fh:
        for v in uuids:
            fh.write(v + "\n")

    print(f"Lines read:     {n}")
    print(f"Matched:        {matched}")
    print(f"  ids:          {len(ids)}" + (f" (from {id_matches} matches)" if not args.no_dedup and id_matches != len(ids) else ""))
    print(f"  uuids:        {len(uuids)}" + (f" (from {uuid_matches} matches)" if not args.no_dedup and uuid_matches != len(uuids) else ""))
    print(f"Unmatched:      {unmatched}")
    print(f"ids written to:   {args.ids_out}")
    print(f"uuids written to: {args.uuids_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
