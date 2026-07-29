"""Execution state machine — pure mechanism, no I/O.

The ADR-0003 machine (as amended in the W1 review) as data plus legality
logic, and nothing else: no SQLite, no storage, no side effects. The split is
the mechanism-vs-policy rule at module scale — this module says what is
*legal*, the store enforces it at the write boundary, and the dispatcher
(policy) chooses among `legal_targets`.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "TERMINAL",
    "TRANSITIONS",
    "IllegalTransition",
    "State",
    "assert_legal",
    "legal_targets",
]


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


def legal_targets(state: State) -> frozenset[State]:
    """Every state legally reachable from `state`, including human cancel."""
    targets = TRANSITIONS[state]
    if state not in TERMINAL:
        targets = targets | {State.CANCELLED}
    return targets


def assert_legal(current: State, to: State) -> None:
    """Raise IllegalTransition unless `current -> to` is an accepted edge."""
    if to not in legal_targets(current):
        raise IllegalTransition(f"{current.value} -> {to.value}")
