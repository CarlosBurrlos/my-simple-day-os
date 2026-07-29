-- Named operational queries for mydayos.tickets (CSS-modules-style locality:
-- this file lives with its owning component). Sections are delimited by
-- `-- name: <query_name>` and loaded by mydayos.db.load_queries.

-- name: get_ticket
SELECT * FROM tickets WHERE id = ?;

-- name: list_tickets
SELECT * FROM tickets ORDER BY priority DESC, id;

-- name: list_tickets_by_state
SELECT * FROM tickets WHERE state = ? ORDER BY priority DESC, id;

-- name: journal_for
SELECT seq, kind, payload, created_tick
FROM journal
WHERE ticket_id = ?
ORDER BY seq;

-- name: insert_ticket
INSERT INTO tickets (title, executor_kind, state, priority,
                     deadline_tick, created_tick, updated_tick)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- name: set_ticket_state
UPDATE tickets SET state = ?, updated_tick = ? WHERE id = ?;

-- name: insert_journal
INSERT INTO journal (ticket_id, seq, kind, payload, idempotency_key,
                     created_tick)
SELECT ?, COALESCE(MAX(seq), 0) + 1, ?, ?, ?, ?
FROM journal
WHERE ticket_id = ?;
