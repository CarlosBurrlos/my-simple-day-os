"""Dispatcher skeleton — the expo: routes Ready tickets to workers.

Policy-side counterpart to the pure machine (mydayos.machine): the store
enforces what is *legal*; the dispatcher chooses what *happens*. This
skeleton is deliberately synchronous and single-slot — the worker
concurrency level (K6) and worker ceiling (C5) are ratified but valueless
(TBD), so concurrency arrives with them.

Routing per the polymorphic Worker model (ADR-0003):

- `automation` -> a registered deterministic callable; Done or Failed.
- `human`      -> deliver via the notification driver, then WaitingHuman —
                  dispatch-to-human MEANS surface-to-human; the human is the
                  worker and the OS is the expo. Completion arrives later
                  through job control (the future CLI's `done`).
- `agent`      -> not yet registered; tickets stay Ready until that worker
                  kind exists (skipped, never failed — absence of a worker
                  is not a ticket's fault).

All state changes go through the TicketStore facade — the dispatcher never
touches SQL (single writer of truth, L1).
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum

from mydayos.machine import State
from mydayos.notify import Notifier
from mydayos.tickets import Ticket, TicketStore

__all__ = ["Dispatcher", "WorkerResult"]


class WorkerResult(StrEnum):
    """What a worker reports back to the expo."""

    DONE = "done"
    FAILED = "failed"
    WAITING_HUMAN = "waiting_human"


_RESULT_TO_STATE: dict[WorkerResult, State] = {
    WorkerResult.DONE: State.DONE,
    WorkerResult.FAILED: State.FAILED,
    WorkerResult.WAITING_HUMAN: State.WAITING_HUMAN,
}

Automation = Callable[[Ticket], WorkerResult]


class Dispatcher:
    """Pull Ready tickets by priority; route by executor kind; report truth."""

    def __init__(
        self,
        store: TicketStore,
        *,
        notifier: Notifier,
        automations: dict[str, Automation] | None = None,
    ) -> None:
        self._store = store
        self._notifier = notifier
        self._automations = automations or {}

    def drain(self) -> list[Ticket]:
        """Dispatch every Ready ticket once, highest priority first.

        Returns the tickets in their post-dispatch states. Tickets with no
        available worker are left Ready and omitted.
        """
        dispatched: list[Ticket] = []
        for ticket in self._store.list(State.READY):
            result = self._dispatch_one(ticket)
            if result is not None:
                dispatched.append(result)
        return dispatched

    def _dispatch_one(self, ticket: Ticket) -> Ticket | None:
        if ticket.executor_kind == "human":
            self._store.transition(ticket.id, State.DISPATCHED)
            self._store.transition(ticket.id, State.RUNNING)
            self._notifier.notify(
                "my-day-os",
                ticket.title,
                subtitle=f"deli ticket #{ticket.id} — in your hands",
            )
            return self._store.transition(
                ticket.id, State.WAITING_HUMAN, reason="surfaced to human"
            )

        automation = self._automations.get(ticket.action) if ticket.action else None
        if ticket.executor_kind == "automation" and automation is not None:
            self._store.transition(ticket.id, State.DISPATCHED)
            self._store.transition(ticket.id, State.RUNNING)
            try:
                result = automation(ticket)
            except Exception as exc:  # noqa: BLE001 — worker faults become Failed, not crashes
                return self._store.transition(
                    ticket.id, State.FAILED, reason=f"automation raised: {exc}"
                )
            return self._store.transition(ticket.id, _RESULT_TO_STATE[result])

        return None  # no worker for this kind yet — stays Ready, not its fault
