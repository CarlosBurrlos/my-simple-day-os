"""SQL plumbing: the migration runner and the named-query loader.

Two kinds of SQL, two homes (W14):

- **Migrations** (`mydayos/migrations/NNNN_*.sql`) — schema history. Cohesion
  axis is *time*: numbered, append-only, never renumbered. Applied in order
  by `run_migrations`, gated by SQLite's built-in ``PRAGMA user_version``,
  inside the sole-writer open path (single writer of truth, L1). Roll-forward
  only: a bad migration is fixed by the next number, never by editing history.
- **Named queries** (`mydayos/sql/<component>.sql`) — operational statements.
  Cohesion axis is the *component*: the file lives beside its owning module
  and is parsed by `load_queries` from ``-- name: <query_name>`` sections.
"""

from __future__ import annotations

import functools
import re
import sqlite3
import types
from collections.abc import Mapping
from importlib import resources

_NAME_RE = re.compile(r"^--\s*name:\s*(\w+)\s*$", re.MULTILINE)


@functools.cache
def load_queries(component: str) -> Mapping[str, str]:
    """Parse ``mydayos/sql/<component>.sql`` into {query_name: statement}.

    Cached per component (SQL is static per process) and returned as a
    read-only mapping — the cached object is safe to share because nobody
    can mutate it (no shared *mutable* state, in miniature).
    """
    text = (resources.files("mydayos") / "sql" / f"{component}.sql").read_text(
        encoding="utf-8"
    )
    parts = _NAME_RE.split(text)
    # parts = [preamble, name1, body1, name2, body2, ...]
    return types.MappingProxyType(
        {name: body.strip() for name, body in zip(parts[1::2], parts[2::2], strict=True)}
    )


def run_migrations(conn: sqlite3.Connection) -> int:
    """Apply pending migrations in order; return the resulting schema version.

    Each migration runs as a script followed by its ``user_version`` bump.
    Forward-only by design (DDL is not compensated; see W14 discussion).
    """
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    migration_dir = resources.files("mydayos") / "migrations"
    pending: list[tuple[int, str]] = []
    for entry in migration_dir.iterdir():
        match = re.match(r"^(\d{4})_.+\.sql$", entry.name)
        if match and int(match.group(1)) > current:
            pending.append((int(match.group(1)), entry.read_text("utf-8")))
    for version, sql in sorted(pending):
        if version != current + 1:
            msg = f"migration gap: have version {current}, next file is {version:04d}"
            raise RuntimeError(msg)
        conn.executescript(sql)
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()
        current = version
    return current
