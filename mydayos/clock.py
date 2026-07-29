"""Clock device + timer service — ADR-0004 made real.

The tick is a **unit of account, not a heartbeat**: `tick = floor(monotonic /
quantum)`, derived on demand from the host's monotonic clock (the host is our
hardware; its clock is our oscillator). Nothing wakes per quantum — the
tickless-kernel lesson. `sleep_seconds()` reports how long until the next due
timer so a runner can sleep exactly that long; an idle system costs nothing.

Timer definitions live in the SoR (`timers` table, migration 0003): the
service rebuilds its queue from truth on every open, so a restart resumes
rather than restarts. Firing is idempotent by construction — a fire is a
`Deferred -> Ready` transition (already-Ready tickets are skipped, never
double-readied), and recurrences issue a FRESH ticket per fire from a
template, keeping ticket IDs permanent and history honest.

Wall-time lives at exactly one edge: `at_wall(dt)` translates a datetime into
a target tick. DST and timezones may only ever be a problem in that function.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

from mydayos.db import load_queries
from mydayos.machine import State
from mydayos.tickets import Ticket, TicketStore

__all__ = ["QUANTUM_SECONDS", "Clock", "Timer", "tick_now"]

# Placeholder value for the scheduler tick quantum (C8); real value is
# SPEC-level. Human-scale by design — this OS needs no millisecond precision.
QUANTUM_SECONDS = 1.0

_Q = load_queries("clock")


def tick_now(quantum: float = QUANTUM_SECONDS) -> int:
    """Derive the current tick on demand. No process maintains this."""
    return int(time.monotonic() / quantum)


@dataclass(frozen=True, slots=True)
class Timer:
    id: int
    ticket_id: int | None
    fire_tick: int
    every_ticks: int | None
    template_title: str | None
    template_kind: str | None
    template_action: str | None
    fired_count: int
    created_tick: int


class Clock:
    """Ring-0 timer service: arms timers, fires due ones through the store."""

    def __init__(self, store: TicketStore) -> None:
        self._store = store
        self._db = store._db

    # -- arming -----------------------------------------------------------

    def defer(self, ticket_id: int, *, until_tick: int) -> Timer:
        """Park a ticket until `until_tick` (Ready -> Deferred + a one-shot)."""
        now = self._store.now_tick()
        with self._db.transaction():
            self._db.execute(
                _Q["insert_timer"],
                (ticket_id, until_tick, None, None, None, None, now),
            )
        if self._store.get(ticket_id).state is State.READY:
            self._store.transition(
                ticket_id, State.DEFERRED, reason=f"deferred to tick {until_tick}"
            )
        return self.timers()[-1]

    def every(
        self,
        title: str,
        *,
        every_ticks: int,
        first_fire_tick: int | None = None,
        executor_kind: str = "human",
        action: str | None = None,
    ) -> Timer:
        """Register a recurrence: each fire issues a fresh ticket from a template."""
        now = self._store.now_tick()
        first = now + every_ticks if first_fire_tick is None else first_fire_tick
        with self._db.transaction():
            self._db.execute(
                _Q["insert_timer"],
                (None, first, every_ticks, title, executor_kind, action, now),
            )
        return self.timers()[-1]

    @staticmethod
    def at_wall(when: datetime, *, now: datetime | None = None) -> int:
        """Translate wall-time to a target tick — the ONLY wall-time edge."""
        reference = now or datetime.now(tz=when.tzinfo)
        delta_seconds = (when - reference).total_seconds()
        return tick_now() + max(0, int(delta_seconds / QUANTUM_SECONDS))

    # -- firing -----------------------------------------------------------

    def tick(self, now_tick: int | None = None) -> list[Ticket]:
        """Fire every due timer once; return the tickets made Ready.

        Boot reconciliation is the same code path: overdue timers (a sleeping
        host, a crashed process) are simply due, and fire once on the next call.
        """
        now = self._store.now_tick() if now_tick is None else now_tick
        readied: list[Ticket] = []
        for row in self._db.all(_Q["due_timers"], (now,)):
            timer = _to_timer(row)
            ticket = (
                self._fire_recurrence(timer, now)
                if timer.every_ticks
                else self._fire_one_shot(timer)
            )
            if ticket is not None:
                readied.append(ticket)
        return readied

    def sleep_seconds(self, now_tick: int | None = None) -> float | None:
        """Seconds until the next timer is due; None when nothing is armed.

        This is the tickless contract: a runner sleeps exactly this long
        instead of polling, so an idle clock costs nothing.
        """
        row = self._db.one(_Q["next_fire_tick"])
        if row is None or row["fire_tick"] is None:
            return None
        now = self._store.now_tick() if now_tick is None else now_tick
        return max(0.0, (row["fire_tick"] - now) * QUANTUM_SECONDS)

    def timers(self) -> list[Timer]:
        return [_to_timer(r) for r in self._db.all(_Q["list_timers"])]

    # -- internals --------------------------------------------------------

    def _fire_one_shot(self, timer: Timer) -> Ticket | None:
        with self._db.transaction():
            self._db.execute(_Q["delete_timer"], (timer.id,))
        if timer.ticket_id is None:
            return None
        ticket = self._store.get(timer.ticket_id)
        if ticket.state is not State.DEFERRED:
            return None  # cancelled, already running, etc. — fire is a no-op
        return self._store.transition(
            timer.ticket_id, State.READY, reason="timer fired"
        )

    def _fire_recurrence(self, timer: Timer, now: int) -> Ticket:
        assert timer.every_ticks is not None
        assert timer.template_title is not None
        next_fire = timer.fire_tick + timer.every_ticks
        while next_fire <= now:  # host asleep for several periods: coalesce
            next_fire += timer.every_ticks
        with self._db.transaction():
            self._db.execute(_Q["rearm_timer"], (next_fire, timer.id))
        issued = self._store.issue(
            timer.template_title,
            executor_kind=timer.template_kind or "human",
            action=timer.template_action,
        )
        return self._store.transition(issued.id, State.READY, reason="recurrence fired")


def _to_timer(row: object) -> Timer:
    return Timer(
        id=row["id"],
        ticket_id=row["ticket_id"],
        fire_tick=row["fire_tick"],
        every_ticks=row["every_ticks"],
        template_title=row["template_title"],
        template_kind=row["template_kind"],
        template_action=row["template_action"],
        fired_count=row["fired_count"],
        created_tick=row["created_tick"],
    )
