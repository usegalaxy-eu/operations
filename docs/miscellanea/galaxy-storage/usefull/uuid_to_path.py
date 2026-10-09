#!/usr/bin/env python3
"""Convert a dataset UUID to its Galaxy object-store shard path.

Usage:
    uv run uuid_to_path.py <uuid> [<files_dir>]

Example:
    uv run uuid_to_path.py 135ee48a-4f51-470c-ae2f-ce8bd78799e6 /data/dnb05/galaxy_db/files
    -> /data/dnb05/galaxy_db/files/1/3/5/dataset_135ee48a-4f51-470c-ae2f-ce8bd78799e6.dat
"""

import sys


def format_uuid(uuid: str) -> str:
    """Normalise a UUID to 8-4-4-4-12 hyphenated form.

    Accepts both ``936e21af36e04e719c16a07658a3383e`` and
    ``936e21af-36e0-4e71-9c16-a07658a3383e``.
    """
    h = uuid.replace("-", "")
    if len(h) != 32:
        return uuid
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def main(argv):
    if len(argv) < 2:
        print("usage: uuid_to_path.py <uuid> [<files_dir>]", file=sys.stderr)
        return 1
    raw = argv[1].strip()
    uuid = format_uuid(raw)
    prefix = argv[2].rstrip("/") if len(argv) > 2 else ""
    shards = "/".join(raw[0:3])
    path = f"{shards}/dataset_{uuid}.dat"
    print(f"{prefix}/{path}" if prefix else path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
