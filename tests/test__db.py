"""Tests for the SQL plumbing: migration runner + named-query loader (W14)."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mydayos import TicketStore
from mydayos.db import load_queries, run_migrations


class MigrationRunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def fake_pkg(self, migrations: dict[str, str]) -> Path:
        pkg = self.root / "pkg"
        (pkg / "migrations").mkdir(parents=True)
        for name, sql in migrations.items():
            (pkg / "migrations" / name).write_text(sql, encoding="utf-8")
        return pkg

    def conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        return conn

    def test_fresh_store_reaches_latest_real_version(self) -> None:
        store = TicketStore(self.root / "sor.sqlite")
        self.addCleanup(store.close)
        version = store._conn.execute("PRAGMA user_version").fetchone()[0]
        self.assertGreaterEqual(version, 1)

    def test_reopen_applies_nothing_new(self) -> None:
        TicketStore(self.root / "sor.sqlite").close()
        store = TicketStore(self.root / "sor.sqlite")  # would raise on re-CREATE
        self.addCleanup(store.close)

    def test_applies_in_order_and_bumps_version(self) -> None:
        pkg = self.fake_pkg(
            {
                "0001_a.sql": "CREATE TABLE a (x INTEGER);",
                "0002_b.sql": "CREATE TABLE b (y INTEGER);",
            }
        )
        conn = self.conn()
        with mock.patch("mydayos.db.resources.files", return_value=pkg):
            self.assertEqual(run_migrations(conn), 2)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        self.assertEqual(tables, {"a", "b"})
        self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)

    def test_migration_gap_raises(self) -> None:
        pkg = self.fake_pkg(
            {
                "0001_a.sql": "CREATE TABLE a (x INTEGER);",
                "0003_c.sql": "CREATE TABLE c (z INTEGER);",
            }
        )
        with (
            mock.patch("mydayos.db.resources.files", return_value=pkg),
            self.assertRaisesRegex(RuntimeError, "migration gap"),
        ):
            run_migrations(self.conn())

    def test_partial_history_only_applies_pending(self) -> None:
        pkg = self.fake_pkg({"0001_a.sql": "CREATE TABLE a (x INTEGER);"})
        conn = self.conn()
        with mock.patch("mydayos.db.resources.files", return_value=pkg):
            run_migrations(conn)
            (pkg / "migrations" / "0002_b.sql").write_text(
                "CREATE TABLE b (y INTEGER);", encoding="utf-8"
            )
            self.assertEqual(run_migrations(conn), 2)


class QueryLoaderTest(unittest.TestCase):
    def test_real_tickets_queries_parse(self) -> None:
        queries = load_queries("tickets")
        self.assertEqual(
            set(queries),
            {
                "get_ticket",
                "list_tickets",
                "list_tickets_by_state",
                "journal_for",
                "insert_ticket",
                "set_ticket_state",
                "insert_journal",
            },
        )
        for statement in queries.values():
            self.assertTrue(
                statement.upper().startswith(("SELECT", "INSERT", "UPDATE"))
            )


if __name__ == "__main__":
    unittest.main()
