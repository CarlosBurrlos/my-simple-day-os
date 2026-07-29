-- Named queries for mydayos.clock (colocated with its owning component).

-- name: insert_timer
INSERT INTO timers (
  ticket_id, fire_tick, every_ticks, template_title,
  template_kind, template_action, created_tick
)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- name: due_timers
SELECT * FROM timers
WHERE fire_tick <= ?
ORDER BY fire_tick ASC, id ASC;

-- name: next_fire_tick
SELECT MIN(fire_tick) AS fire_tick FROM timers;

-- name: rearm_timer
UPDATE timers
SET fire_tick = ?, fired_count = fired_count + 1
WHERE id = ?;

-- name: delete_timer
DELETE FROM timers
WHERE id = ?;

-- name: list_timers
SELECT * FROM timers
ORDER BY fire_tick ASC, id ASC;
