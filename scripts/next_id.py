"""Allocate the next ID in a project numbering sequence (L, C, K, ADR, SPEC).

IDs are ABI: never renumbered, never reused, gaps are fine. This script is the
single allocator — humans and agents peel numbers from here instead of guessing,
so two in-flight ADRs can never claim the same ID.

State lives in docs/sequences.json (tracked in git: a fresh clone knows the
high-water marks, and concurrent branches that both allocate will surface the
collision as a merge conflict instead of a silent dupe). Writes are atomic:
an O_EXCL lock file guards the read-modify-write, temp-file + os.replace
publishes it.

Usage:
    python scripts/next_id.py L              # allocate one Law ID -> L12
    python scripts/next_id.py ADR --count 2  # allocate ADR-0004, ADR-0005
    python scripts/next_id.py SPEC --peek    # show next without allocating
    python scripts/next_id.py --list         # show all sequence high-water marks
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

STORE = Path(__file__).resolve().parent.parent / "docs" / "sequences.json"
LOCK = STORE.with_suffix(".json.lock")
FORMATS = {
    "L": "L{n}",
    "C": "C{n}",
    "K": "K{n}",
    "ADR": "ADR-{n:04d}",
    "SPEC": "SPEC-{n:04d}",
}
LOCK_RETRIES = 50
LOCK_WAIT_S = 0.1


def acquire_lock() -> None:
    for _ in range(LOCK_RETRIES):
        try:
            os.close(os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return
        except FileExistsError:
            time.sleep(LOCK_WAIT_S)
    sys.exit(f"Could not acquire {LOCK}; remove it if stale.")


def release_lock() -> None:
    LOCK.unlink(missing_ok=True)


def read_store() -> dict[str, int]:
    return json.loads(STORE.read_text(encoding="utf-8"))


def write_store(state: dict[str, int]) -> None:
    fd, tmp = tempfile.mkstemp(dir=STORE.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, STORE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sequence", nargs="?", choices=sorted(FORMATS))
    parser.add_argument("--count", type=int, default=1, help="IDs to allocate")
    parser.add_argument(
        "--peek", action="store_true", help="show next ID without allocating"
    )
    parser.add_argument(
        "--list", action="store_true", help="show all next-available IDs"
    )
    args = parser.parse_args()

    if args.list:
        state = read_store()
        for seq, nxt in sorted(state.items()):
            print(f"{seq}: next {FORMATS[seq].format(n=nxt)}")
        return 0
    if not args.sequence:
        parser.error("a sequence is required unless using --list")
    if args.count < 1:
        parser.error("--count must be >= 1")

    fmt = FORMATS[args.sequence]
    if args.peek:
        print(fmt.format(n=read_store()[args.sequence]))
        return 0

    acquire_lock()
    try:
        state = read_store()
        start = state[args.sequence]
        state[args.sequence] = start + args.count
        write_store(state)
    finally:
        release_lock()
    for n in range(start, start + args.count):
        print(fmt.format(n=n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
