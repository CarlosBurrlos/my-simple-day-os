#!/usr/bin/env python3
"""Configure (or clear) authenticated push access to the `origin` remote.

Single responsibility: wire the credential git uses to PUSH to GitHub, reading
a personal access token from the GITHUB_TOKEN environment variable. Nothing
else - cloning and fetching a public repo need no auth, so this script is only
for write-back.

The token is written ONLY to the repo-local `.git/config` (which is never
tracked and never committed) and is injected as an HTTP auth header so it does
not appear in `git remote -v`. This mirrors the pattern CI systems use.

Usage
-----
    GITHUB_TOKEN=github_pat_xxx python scripts/configure_remote.py     # set up
    python scripts/configure_remote.py --clear                        # remove

Use a fine-grained, repo-scoped, short-lived token and REVOKE it when the
sandbox is done. This script writes no secret to any tracked file.
"""
from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys

# Applies the header to all github.com HTTPS traffic for this repo only.
CONFIG_KEY = "http.https://github.com/.extraheader"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], text=True, capture_output=True, check=True)


def _inside_repo() -> bool:
    return _git("rev-parse", "--is-inside-work-tree").returncode == 0


def clear() -> int:
    _git("config", "--local", "--unset-all", CONFIG_KEY)
    print("Cleared push credential from local .git/config.")
    return 0


def configure() -> int:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print(
            "GITHUB_TOKEN is not set.\n"
            "Export a fine-grained, repo-scoped PAT, then re-run:\n"
            "    export GITHUB_TOKEN=github_pat_xxx\n"
            "    python scripts/configure_remote.py",
            file=sys.stderr,
        )
        return 1

    header = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    result = _git("config", "--local", CONFIG_KEY, f"Authorization: Basic {header}")
    if result.returncode != 0:
        print(f"Failed to set git config: {result.stderr.strip()}", file=sys.stderr)
        return 1

    print("Push auth configured (token stored only in local .git/config).")
    origin = _git("remote", "get-url", "origin")
    if origin.returncode == 0:
        print(f"origin: {origin.stdout.strip()}")
    print("Verify with:  git push --dry-run")
    print("When finished: python scripts/configure_remote.py --clear  (and revoke the PAT)")
    return 0


def main() -> int:
    if not _inside_repo():
        print("Not inside a git repository.", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description="Configure PAT-based push auth for origin.")
    parser.add_argument("--clear", action="store_true", help="remove the configured push credential")
    args = parser.parse_args()
    return clear() if args.clear else configure()


if __name__ == "__main__":
    raise SystemExit(main())
