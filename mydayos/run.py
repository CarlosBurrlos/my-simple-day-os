"""The loop: clock fires timers, dispatcher routes what became Ready.

This is the whole OS in twenty lines — the two organs composed. Tickless by
construction: `Clock.sleep_seconds()` says exactly how long until the next
timer is due, so an idle system sleeps rather than polls.

Demo (no daemon yet, no scheduling of your real life — a proof of life):

    just demo
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from mydayos.clock import Clock
from mydayos.dispatch import Dispatcher, WorkerResult
from mydayos.machine import State
from mydayos.notify import MacNotifier
from mydayos.tickets import Ticket, TicketStore


def run_once(clock: Clock, dispatcher: Dispatcher) -> list[Ticket]:
    """One turn of the crank: fire due timers, then dispatch what is Ready."""
    clock.tick()
    return dispatcher.drain()


def demo(db_path: str = "demo.sqlite") -> int:
    """Issue a deferred promise and a recurrence, then watch them surface."""
    path = Path(db_path)
    store = TicketStore(path)
    clock = Clock(store)
    automations = {"digest": _digest}
    dispatcher = Dispatcher(store, notifier=MacNotifier(), automations=automations)

    now = store.now_tick()
    reminder = store.issue("call the dentist", executor_kind="human")
    store.transition(reminder.id, State.READY)
    clock.defer(reminder.id, until_tick=now + 3)
    clock.every(
        "daily digest", every_ticks=5, executor_kind="automation", action="digest"
    )

    print(f"store: {path}  ·  two promises armed  ·  ctrl-c to stop")
    try:
        for _ in range(4):
            wait = clock.sleep_seconds()
            if wait:
                print(f"  sleeping {wait:.0f}s until the next timer …")
                time.sleep(min(wait, 10))
            for ticket in run_once(clock, dispatcher):
                print(f"  → #{ticket.id} {ticket.title!r} is now {ticket.state}")
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        store.close()
    return 0


def _digest(ticket: Ticket) -> WorkerResult:
    print(f"  [automation] composing digest for #{ticket.id}")
    return WorkerResult.DONE


if __name__ == "__main__":
    sys.exit(demo(*sys.argv[1:]))
