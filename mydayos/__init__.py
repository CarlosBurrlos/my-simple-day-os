"""my-day-os — an operating system for a personal day.

First organ: the ticket store (`mydayos.tickets`) — the process table and
its state machine, per ADR-0001/0003.
"""

from mydayos.tickets import (
    IllegalTransition,
    State,
    Ticket,
    TicketStore,
    UnknownTicket,
)

__all__ = ["IllegalTransition", "State", "Ticket", "TicketStore", "UnknownTicket"]
