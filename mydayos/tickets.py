"""Ticket store — the process control block, composed from the plumbing.

`TicketStore` is the **single write facade** for ticket truth (single writer
of truth, L1): composition inside, one choke point outside. It composes the
generic `Database` plumbing (mydayos.db: connection, migrations-on-open,
execution ergonomics) with the pure state machine (mydayos.machine: legality
only), and adds what is genuinely its own — journaled mutation: every write
and its journal record commit in one transaction (internal form of
write-ahead before act, L9).

Schema lives in numbered migrations (mydayos/migrations/); operational SQL
in the colocated named-query file mydayos/sql/tickets.sql.

The tick source is injected (the Clock device, ADR-0004, arrives later);
the default derives a placeholder tick from the host monotonic clock at a
1-second quantum — the real scheduler tick quantum (C8) value is SPEC-level.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from mydayos.db import Database, load_queries
from mydayos.machine import (
    TERMINAL,
    TRANSITIONS,
    IllegalTransition,
    State,
    assert_legal,
)

# Machine names re-exported from their historic home for existing importers.
__all__ = [
    "TERMINAL",
    "TRANSITIONS",
    "IllegalTransition",
    "State",
    "Ticket",
    "TicketStore",
    "UnknownTicket",
]

_Q = load_queries("tickets")


class UnknownTicket(KeyError):
    """No ticket with that ID exists."""


@dataclass(frozen=True, slots=True)
class Ticket:
    id: int
    title: str
    executor_kind: str
    state: State
    priority: int
    deadline_tick: int | None
    created_tick: int
    updated_tick: int
    action: str | None


def _default_tick() -> int:
    return int(time.monotonic())  # placeholder quantum: 1 s (C8 value is SPEC-level)


class TicketStore:
    """Sole writer of ticket truth (L1). All mutations journal atomically (L9)."""

    def __init__(
        self, path: str | Path, *, now_tick: Callable[[], int] = _default_tick
    ) -> None:
        self._db = Database(path)
        self._now_tick = now_tick

    @property
    def path(self) -> Path:
        """Filesystem home of this store's SQLite file."""
        return self._db.path

    def now_tick(self) -> int:
        """Current tick from the injected source (the Clock device's seam)."""
        return self._now_tick()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- reads ------------------------------------------------------------

    def get(self, ticket_id: int) -> Ticket:
        row = self._db.one(_Q["get_ticket"], (ticket_id,))
        if row is None:
            raise UnknownTicket(ticket_id)
        return _to_ticket(row)

    def list(self, state: State | None = None) -> list[Ticket]:
        if state is None:
            rows = self._db.all(_Q["list_tickets"])
        else:
            rows = self._db.all(_Q["list_tickets_by_state"], (state.value,))
        return [_to_ticket(r) for r in rows]

    def journal_for(self, ticket_id: int) -> list[dict[str, object]]:
        rows = self._db.all(_Q["journal_for"], (ticket_id,))
        return [
            {
                "seq": r["seq"],
                "kind": r["kind"],
                "payload": json.loads(r["payload"]),
                "created_tick": r["created_tick"],
            }
            for r in rows
        ]

    # -- writes (each journals atomically) --------------------------------

    def issue(
        self,
        title: str,
        *,
        executor_kind: str = "human",
        priority: int = 0,
        deadline_tick: int | None = None,
        action: str | None = None,
    ) -> Ticket:
        tick = self._now_tick()
        with self._db.transaction():
            cur = self._db.execute(
                _Q["insert_ticket"],
                (
                    title,
                    executor_kind,
                    State.ISSUED.value,
                    priority,
                    deadline_tick,
                    tick,
                    tick,
                    action,
                ),
            )
            ticket_id = cur.lastrowid
            assert ticket_id is not None
            self._journal(
                ticket_id,
                "issued",
                {"title": title, "executor_kind": executor_kind},
                tick,
            )
        return self.get(ticket_id)

    def transition(self, ticket_id: int, to: State, *, reason: str = "") -> Ticket:
        tick = self._now_tick()
        with self._db.transaction():
            current = self.get(ticket_id).state
            assert_legal(current, to)
            self._db.execute(_Q["set_ticket_state"], (to.value, tick, ticket_id))
            self._journal(
                ticket_id,
                "transition",
                {"from": current.value, "to": to.value, "reason": reason},
                tick,
            )
        return self.get(ticket_id)

    def cancel(self, ticket_id: int, *, reason: str = "job-control") -> Ticket:
        return self.transition(ticket_id, State.CANCELLED, reason=reason)

    # -- internals --------------------------------------------------------

    def _journal(
        self,
        ticket_id: int,
        kind: str,
        payload: dict[str, object],
        tick: int,
        idempotency_key: str | None = None,
    ) -> None:
        self._db.execute(
            _Q["insert_journal"],
            (
                ticket_id,
                kind,
                json.dumps(payload, sort_keys=True),
                idempotency_key,
                tick,
                ticket_id,
            ),
        )


def _to_ticket(row: sqlite3.Row) -> Ticket:
    return Ticket(
        id=row["id"],
        title=row["title"],
        executor_kind=row["executor_kind"],
        state=State(row["state"]),
        priority=row["priority"],
        deadline_tick=row["deadline_tick"],
        created_tick=row["created_tick"],
        updated_tick=row["updated_tick"],
        action=row["action"],
    )
