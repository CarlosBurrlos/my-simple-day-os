-- Migration 0001: initial schema (extracted from the W13 walking skeleton).
-- Migration numbers are append-only and never renumbered (the ID-permanence
-- rule). IF NOT EXISTS appears ONLY in this bridging migration so that
-- pre-migration skeleton databases adopt cleanly; from 0002 on, use plain DDL.

CREATE TABLE IF NOT EXISTS tickets (
    id            INTEGER PRIMARY KEY,
    title         TEXT    NOT NULL,
    executor_kind TEXT    NOT NULL CHECK (executor_kind IN
                          ('agent', 'automation', 'human')),
    state         TEXT    NOT NULL,
    priority      INTEGER NOT NULL DEFAULT 0,
    deadline_tick INTEGER,
    created_tick  INTEGER NOT NULL,
    updated_tick  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS journal (
    id              INTEGER PRIMARY KEY,
    ticket_id       INTEGER NOT NULL REFERENCES tickets (id),
    seq             INTEGER NOT NULL,
    kind            TEXT    NOT NULL,
    payload         TEXT    NOT NULL,
    idempotency_key TEXT    UNIQUE,
    created_tick    INTEGER NOT NULL,
    UNIQUE (ticket_id, seq)
);

CREATE INDEX IF NOT EXISTS ix_tickets_state ON tickets (state, priority);
