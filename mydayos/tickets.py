"""Ticket store + execution state machine — the process control block.

This module is the **ring-0 storage driver**: the single choke point through
which ticket truth is written, enforcing in code what the canon declares:

- Single writer of truth (L1): all mutations go through `TicketStore`;
  nothing else touches the SQLite file.
- Write-ahead before act (L9), internal form: every mutation and its journal
  record commit in one transaction — no state change exists without its
  journal row.
- The execution state machine (ADR-0003, as amended in the W1 review):
  transitions outside `TRANSITIONS` raise; human cancel is legal from any
  non-terminal state; terminal states are final.

Schema lives in numbered migrations (mydayos/migrations/, applied on open
via PRAGMA user_version); operational SQL lives in the colocated named-query
file mydayos/sql/tickets.sql (see mydayos.db, W14).

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
from enum import StrEnum
from pathlib import Path
from typing import Self

from mydayos.db import load_queries, run_migrations

__all__ = ["IllegalTransition", "State", "Ticket", "TicketStore", "UnknownTicket"]

_Q = load_queries("tickets")


class State(StrEnum):
    """Ticket execution states, verbatim from the accepted ADR-0003 machine."""

    ISSUED = "Issued"
    READY = "Ready"
    DEFERRED = "Deferred"
    DISPATCHED = "Dispatched"
    RUNNING = "Running"
    BLOCKED = "Blocked"
    WAITING_HUMAN = "WaitingHuman"
    DONE = "Done"
    FAILED = "Failed"
    RETRYING = "Retrying"
    COMPENSATING = "Compensating"
    DROPPED = "Dropped"
    CANCELLED = "Cancelled"


TERMINAL: frozenset[State] = frozenset({State.DONE, State.DROPPED, State.CANCELLED})

# Non-cancel edges, one per arrow in the accepted state diagram.
TRANSITIONS: dict[State, frozenset[State]] = {
    State.ISSUED: frozenset({State.READY}),
    State.READY: frozenset({State.DEFERRED, State.DISPATCHED}),
    State.DEFERRED: frozenset({State.READY}),
    State.DISPATCHED: frozenset({State.RUNNING, State.FAILED}),
    State.RUNNING: frozenset(
        {State.BLOCKED, State.WAITING_HUMAN, State.DONE, State.FAILED}
    ),
    State.BLOCKED: frozenset({State.READY}),
    State.WAITING_HUMAN: frozenset({State.RUNNING}),
    State.FAILED: frozenset({State.RETRYING, State.COMPENSATING}),
    State.RETRYING: frozenset({State.READY}),
    State.COMPENSATING: frozenset({State.DROPPED}),
    State.DONE: frozenset(),
    State.DROPPED: frozenset(),
    State.CANCELLED: frozenset(),
}


class IllegalTransition(ValueError):
    """The requested state change has no edge in the accepted machine."""


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


def _default_tick() -> int:
    return int(time.monotonic())  # placeholder quantum: 1 s (C8 value is SPEC-level)


class TicketStore:
    """Sole writer of ticket truth (L1). All mutations journal atomically (L9)."""

    def __init__(
        self, path: str | Path, *, now_tick: Callable[[], int] = _default_tick
    ) -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        run_migrations(self._conn)
        self._now_tick = now_tick

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- reads ------------------------------------------------------------

    def get(self, ticket_id: int) -> Ticket:
        row = self._conn.execute(_Q["get_ticket"], (ticket_id,)).fetchone()
        if row is None:
            raise UnknownTicket(ticket_id)
        return _to_ticket(row)

    def list(self, state: State | None = None) -> list[Ticket]:
        if state is None:
            rows = self._conn.execute(_Q["list_tickets"]).fetchall()
        else:
            rows = self._conn.execute(
                _Q["list_tickets_by_state"], (state.value,)
            ).fetchall()
        return [_to_ticket(r) for r in rows]

    def journal_for(self, ticket_id: int) -> list[dict[str, object]]:
        rows = self._conn.execute(_Q["journal_for"], (ticket_id,)).fetchall()
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
    ) -> Ticket:
        tick = self._now_tick()
        with self._conn:
            cur = self._conn.execute(
                _Q["insert_ticket"],
                (
                    title,
                    executor_kind,
                    State.ISSUED.value,
                    priority,
                    deadline_tick,
                    tick,
                    tick,
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
        with self._conn:
            current = self.get(ticket_id).state
            legal = to in TRANSITIONS[current] or (
                to is State.CANCELLED and current not in TERMINAL
            )
            if not legal:
                raise IllegalTransition(f"{current.value} -> {to.value}")
            self._conn.execute(_Q["set_ticket_state"], (to.value, tick, ticket_id))
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
        self._conn.execute(
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
    )
