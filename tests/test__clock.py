"""Tests for the Clock device + timer service (W16, implementing ADR-0004).

The fake clock ADR-0004 promised: every test drives time by hand, so timing
behavior is fully deterministic and nothing sleeps.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mydayos import State, TicketStore
from mydayos.clock import QUANTUM_SECONDS, Clock, tick_now


class ManualClock:
    """Time under test control — advance() moves the world forward."""

    def __init__(self, start: int = 1000) -> None:
        self.tick = start

    def __call__(self) -> int:
        return self.tick

    def advance(self, ticks: int) -> None:
        self.tick += ticks


class ClockTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.now = ManualClock()
        self.store = TicketStore(Path(tmp.name) / "sor.sqlite", now_tick=self.now)
        self.addCleanup(self.store.close)
        self.clock = Clock(self.store)

    def ready(self, title: str, **kwargs) -> int:
        ticket = self.store.issue(title, **kwargs)
        self.store.transition(ticket.id, State.READY)
        return ticket.id

    # -- deferral ---------------------------------------------------------

    def test_defer_parks_ticket_then_fires_it_ready(self) -> None:
        ticket_id = self.ready("prep for standup")
        self.clock.defer(ticket_id, until_tick=self.now.tick + 10)
        self.assertEqual(self.store.get(ticket_id).state, State.DEFERRED)

        self.assertEqual(self.clock.tick(), [])  # nothing due yet
        self.assertEqual(self.store.get(ticket_id).state, State.DEFERRED)

        self.now.advance(10)
        [readied] = self.clock.tick()
        self.assertEqual(readied.id, ticket_id)
        self.assertEqual(readied.state, State.READY)

    def test_one_shot_timer_is_consumed(self) -> None:
        ticket_id = self.ready("water the plants")
        self.clock.defer(ticket_id, until_tick=self.now.tick + 1)
        self.now.advance(1)
        self.clock.tick()
        self.assertEqual(self.clock.timers(), [])
        self.assertEqual(self.clock.tick(), [])  # no double-fire

    def test_overdue_timer_fires_once_on_next_tick(self) -> None:
        """Boot reconciliation: a sleeping host makes timers overdue, not lost."""
        ticket_id = self.ready("take out the trash")
        self.clock.defer(ticket_id, until_tick=self.now.tick + 5)
        self.now.advance(500)  # host asleep for a long while
        [readied] = self.clock.tick()
        self.assertEqual(readied.state, State.READY)

    def test_fire_on_cancelled_ticket_is_a_noop(self) -> None:
        ticket_id = self.ready("obsolete errand")
        self.clock.defer(ticket_id, until_tick=self.now.tick + 2)
        self.store.cancel(ticket_id)
        self.now.advance(2)
        self.assertEqual(self.clock.tick(), [])
        self.assertEqual(self.store.get(ticket_id).state, State.CANCELLED)

    # -- recurrence -------------------------------------------------------

    def test_recurrence_issues_a_fresh_ticket_each_fire(self) -> None:
        self.clock.every("morning standup", every_ticks=100)
        self.now.advance(100)
        [first] = self.clock.tick()
        self.now.advance(100)
        [second] = self.clock.tick()

        self.assertNotEqual(first.id, second.id)  # fresh ticket, not resurrected
        self.assertEqual(first.title, second.title)
        self.assertEqual(second.state, State.READY)
        self.assertEqual(len(self.store.list()), 2)

    def test_recurrence_survives_missed_periods_without_storming(self) -> None:
        self.clock.every("hourly check", every_ticks=10)
        self.now.advance(95)  # nine periods missed while asleep
        readied = self.clock.tick()
        self.assertEqual(len(readied), 1)  # coalesced, not nine tickets
        [timer] = self.clock.timers()
        self.assertGreater(timer.fire_tick, self.now.tick)

    def test_recurrence_template_carries_executor_and_action(self) -> None:
        self.clock.every(
            "compact the journal",
            every_ticks=5,
            executor_kind="automation",
            action="compact",
        )
        self.now.advance(5)
        [ticket] = self.clock.tick()
        self.assertEqual(ticket.executor_kind, "automation")
        self.assertEqual(ticket.action, "compact")

    # -- tickless contract ------------------------------------------------

    def test_sleep_seconds_reports_time_to_next_timer(self) -> None:
        self.assertIsNone(self.clock.sleep_seconds())  # nothing armed = no wakeup
        ticket_id = self.ready("later")
        self.clock.defer(ticket_id, until_tick=self.now.tick + 30)
        self.assertEqual(self.clock.sleep_seconds(), 30 * QUANTUM_SECONDS)
        self.now.advance(30)
        self.assertEqual(self.clock.sleep_seconds(), 0.0)

    def test_timers_survive_reopen(self) -> None:
        ticket_id = self.ready("tomorrow's promise")
        self.clock.defer(ticket_id, until_tick=self.now.tick + 7)
        self.store.close()

        reopened = TicketStore(self.store.path, now_tick=self.now)
        self.addCleanup(reopened.close)
        clock = Clock(reopened)
        self.assertEqual(len(clock.timers()), 1)
        self.now.advance(7)
        [readied] = clock.tick()
        self.assertEqual(readied.id, ticket_id)

    def test_tick_now_is_derived_not_maintained(self) -> None:
        self.assertIsInstance(tick_now(), int)
        self.assertGreaterEqual(tick_now(quantum=1000.0), 0)


if __name__ == "__main__":
    unittest.main()
