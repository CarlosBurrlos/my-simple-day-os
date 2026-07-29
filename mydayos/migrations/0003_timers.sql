-- Migration 0003: the timer set (ADR-0004). Timer definitions are the
-- ticket's property recorded in the SoR, not the clock's — the timer service
-- rebuilds its queue from this table on boot (queue is a view of truth).
--
-- `every_ticks` NULL means one-shot; non-NULL makes the row a recurrence
-- template: each fire issues a FRESH ticket from `template_title` and
-- re-arms `fire_tick`, so ticket IDs stay permanent and history stays honest.

CREATE TABLE timers (
  id INTEGER PRIMARY KEY,
  ticket_id INTEGER REFERENCES tickets (id),
  fire_tick INTEGER NOT NULL,
  every_ticks INTEGER,
  template_title TEXT,
  template_kind TEXT,
  template_action TEXT,
  fired_count INTEGER NOT NULL DEFAULT 0,
  created_tick INTEGER NOT NULL
);

CREATE INDEX ix_timers_fire ON timers (fire_tick);
