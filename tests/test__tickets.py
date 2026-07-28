"""Tests for the ticket store + state machine (the first organ).

Proves the canon in code: transitions outside the accepted machine raise,
human cancel works from any non-terminal state, terminal states are final,
every mutation is journaled atomically, and truth survives a reopen.
"""

from __future__ import annotations

import itertools
import tempfile
import unittest
from pathlib import Path

from mydayos import IllegalTransition, State, TicketStore, UnknownTicket
from mydayos.tickets import TERMINAL, TRANSITIONS


class FakeClock:
    """Injected tick source — the fake clock ADR-0004 promised tests."""

    def __init__(self) -> None:
        self._tick = itertools.count(1000)

    def __call__(self) -> int:
        return next(self._tick)


class TicketStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "sor.sqlite"
        self.store = TicketStore(self.db, now_tick=FakeClock())
        self.addCleanup(self.store.close)

    def issue(self) -> int:
        ticket = self.store.issue("call the dentist", executor_kind="human")
        return ticket.id

    def walk(self, ticket_id: int, *states: State) -> None:
        for state in states:
            self.store.transition(ticket_id, state)

    def test_issue_starts_issued_and_journals(self) -> None:
        ticket_id = self.issue()
        ticket = self.store.get(ticket_id)
        self.assertEqual(ticket.state, State.ISSUED)
        journal = self.store.journal_for(ticket_id)
        self.assertEqual([e["kind"] for e in journal], ["issued"])

    def test_happy_path_to_done(self) -> None:
        ticket_id = self.issue()
        self.walk(ticket_id, State.READY, State.DISPATCHED, State.RUNNING, State.DONE)
        self.assertEqual(self.store.get(ticket_id).state, State.DONE)

    def test_illegal_transition_raises_and_mutates_nothing(self) -> None:
        ticket_id = self.issue()
        with self.assertRaises(IllegalTransition):
            self.store.transition(ticket_id, State.RUNNING)
        self.assertEqual(self.store.get(ticket_id).state, State.ISSUED)
        self.assertEqual(len(self.store.journal_for(ticket_id)), 1)

    def test_terminal_states_are_final(self) -> None:
        ticket_id = self.issue()
        self.walk(ticket_id, State.READY, State.DISPATCHED, State.RUNNING, State.DONE)
        for target in State:
            with self.assertRaises(IllegalTransition):
                self.store.transition(ticket_id, target)

    def test_cancel_from_every_non_terminal_state(self) -> None:
        paths: dict[State, tuple[State, ...]] = {
            State.ISSUED: (),
            State.READY: (State.READY,),
            State.DEFERRED: (State.READY, State.DEFERRED),
            State.DISPATCHED: (State.READY, State.DISPATCHED),
            State.RUNNING: (State.READY, State.DISPATCHED, State.RUNNING),
            State.BLOCKED: (
                State.READY,
                State.DISPATCHED,
                State.RUNNING,
                State.BLOCKED,
            ),
            State.WAITING_HUMAN: (
                State.READY,
                State.DISPATCHED,
                State.RUNNING,
                State.WAITING_HUMAN,
            ),
        }
        for start, path in paths.items():
            ticket_id = self.issue()
            self.walk(ticket_id, *path)
            self.assertEqual(self.store.get(ticket_id).state, start)
            cancelled = self.store.cancel(ticket_id)
            self.assertEqual(cancelled.state, State.CANCELLED)

    def test_failure_retry_and_compensation_paths(self) -> None:
        ticket_id = self.issue()
        self.walk(
            ticket_id,
            State.READY,
            State.DISPATCHED,
            State.RUNNING,
            State.FAILED,
            State.RETRYING,
            State.READY,
        )
        self.assertEqual(self.store.get(ticket_id).state, State.READY)
        self.walk(
            ticket_id,
            State.DISPATCHED,
            State.RUNNING,
            State.FAILED,
            State.COMPENSATING,
            State.DROPPED,
        )
        self.assertEqual(self.store.get(ticket_id).state, State.DROPPED)

    def test_journal_seq_is_monotonic_per_ticket(self) -> None:
        ticket_id = self.issue()
        self.walk(ticket_id, State.READY, State.DISPATCHED, State.RUNNING)
        seqs = [e["seq"] for e in self.store.journal_for(ticket_id)]
        self.assertEqual(seqs, [1, 2, 3, 4])

    def test_truth_survives_reopen(self) -> None:
        ticket_id = self.issue()
        self.walk(ticket_id, State.READY)
        self.store.close()
        reopened = TicketStore(self.db, now_tick=FakeClock())
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.get(ticket_id).state, State.READY)
        self.assertEqual(len(reopened.journal_for(ticket_id)), 2)

    def test_unknown_ticket_raises(self) -> None:
        with self.assertRaises(UnknownTicket):
            self.store.get(999)

    def test_machine_shape_matches_canon(self) -> None:
        self.assertEqual(len(State), 13)
        self.assertEqual(TERMINAL, {State.DONE, State.DROPPED, State.CANCELLED})
        for terminal in TERMINAL:
            self.assertEqual(TRANSITIONS[terminal], frozenset())


if __name__ == "__main__":
    unittest.main()
