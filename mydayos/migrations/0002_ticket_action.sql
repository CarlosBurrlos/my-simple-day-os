-- Migration 0002: tickets gain an `action` slot — the automation registry
-- key a dispatcher uses to find the deterministic callable for an
-- automation-executor ticket. NULL for human (and future agent) tickets.

ALTER TABLE tickets ADD COLUMN action TEXT;
