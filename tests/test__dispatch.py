"""Tests for the dispatcher skeleton + notification driver (W15)."""

from __future__ import annotations

import itertools
import tempfile
import unittest
from pathlib import Path

from mydayos import State, TicketStore
from mydayos.dispatch import Dispatcher, WorkerResult
from mydayos.notify import MacNotifier


class RecordingNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str | None]] = []

    def notify(self, title: str, message: str, subtitle: str | None = None) -> None:
        self.sent.append((title, message, subtitle))


class DispatcherTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        clock = itertools.count(1000)
        self.store = TicketStore(
            Path(tmp.name) / "sor.sqlite", now_tick=lambda: next(clock)
        )
        self.addCleanup(self.store.close)
        self.notifier = RecordingNotifier()

    def dispatcher(self, **automations) -> Dispatcher:
        return Dispatcher(self.store, notifier=self.notifier, automations=automations)

    def ready(self, title: str, **kwargs) -> int:
        ticket = self.store.issue(title, **kwargs)
        self.store.transition(ticket.id, State.READY)
        return ticket.id

    def test_human_ticket_notifies_and_waits(self) -> None:
        ticket_id = self.ready("call the dentist", executor_kind="human")
        [after] = self.dispatcher().drain()
        self.assertEqual(after.state, State.WAITING_HUMAN)
        [(title, message, subtitle)] = self.notifier.sent
        self.assertEqual(title, "my-day-os")
        self.assertEqual(message, "call the dentist")
        self.assertIn(f"#{ticket_id}", subtitle)

    def test_automation_success_reaches_done(self) -> None:
        self.ready("morning digest", executor_kind="automation", action="digest")
        [after] = self.dispatcher(digest=lambda ticket: WorkerResult.DONE).drain()
        self.assertEqual(after.state, State.DONE)
        self.assertEqual(self.notifier.sent, [])

    def test_automation_exception_becomes_failed(self) -> None:
        def boom(ticket) -> WorkerResult:
            msg = "kaput"
            raise RuntimeError(msg)

        self.ready("flaky job", executor_kind="automation", action="boom")
        [after] = self.dispatcher(boom=boom).drain()
        self.assertEqual(after.state, State.FAILED)
        journal = self.store.journal_for(after.id)
        self.assertIn("kaput", journal[-1]["payload"]["reason"])

    def test_unregistered_kind_stays_ready(self) -> None:
        self.ready("think about ontology", executor_kind="agent")
        self.assertEqual(self.dispatcher().drain(), [])
        [ticket] = self.store.list(State.READY)
        self.assertEqual(ticket.state, State.READY)

    def test_priority_orders_dispatch(self) -> None:
        self.ready("low", executor_kind="human", priority=1)
        self.ready("high", executor_kind="human", priority=9)
        self.dispatcher().drain()
        self.assertEqual([msg for _, msg, _ in self.notifier.sent], ["high", "low"])

    def test_issued_tickets_are_not_dispatched(self) -> None:
        self.store.issue("not admitted yet", executor_kind="human")
        self.assertEqual(self.dispatcher().drain(), [])
        self.assertEqual(self.notifier.sent, [])


class MacNotifierTest(unittest.TestCase):
    def test_builds_escaped_osascript_command(self) -> None:
        calls: list[list[str]] = []
        notifier = MacNotifier(
            runner=lambda argv, **kw: calls.append(argv), sound=False
        )
        notifier.notify("my-day-os", 'say "hi"', subtitle="ticket #1")
        [argv] = calls
        self.assertEqual(argv[:2], ["osascript", "-e"])
        self.assertIn('display notification "say \\"hi\\""', argv[2])
        self.assertIn('with title "my-day-os"', argv[2])
        self.assertIn('subtitle "ticket #1"', argv[2])


if __name__ == "__main__":
    unittest.main()
