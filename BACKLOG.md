# BACKLOG — future capabilities parking lot

<!-- Protocol: the third horizon of the work system.
     BACKLOG (someday / concepts) -> TODO.md (queued, committed-to) ->
     GAPS.md (depth on what's queued).
     Items here are IMPORTANT but deliberately unscheduled: no work IDs, no
     ordering guarantees, no blocked_by. When an item's time comes, it
     graduates: append a W<n> row to TODO.md (and a GAPS entry if it has
     depth), then delete or shrink it here. Concepts matter more than the
     exact tools named — swap implementations freely at graduation time. -->

These capabilities were originally sketched in the pre-trim CLAUDE.md (exact
original text recoverable via `git show 5dcf468^:CLAUDE.md`). None exist today;
all are wanted once the project has application code to deserve them.

## Suggested priority (advisory)

**How this section is used:** this is a *suggestion* of graduation order, not a
queue — TODO.md's FIFO remains the only committed ordering. When pulling from
the backlog, start reading here; when an item graduates (gets its `W<n>` row in
TODO.md), remove it from this list. Re-rank freely — reordering here is always
legal because nothing here is promised. Ranking rationale: what unblocks other
work first, then design notes in the order their host ADR/SPEC will need them,
then infrastructure that only pays off at scale.

**Tier 1 — graduate alongside the first application code:**

1. **Testing infrastructure** — the first line of app code deserves a test
   harness; `scripts/next_id.py` is already an untested customer.
2. **Pre-commit hooks** — cheap; locks `just check` in at commit time.
3. **Type checking (ty)** — cheapest while the codebase is small.

**Tier 2 — design notes, in the order their host documents will want them:**

4. **Gate protocol / lifecycle ABI** — the execution-SPEC backbone; most other
   scheduling entries hang off it.
5. **Graph-structured workers (per-axis determinism)** — feeds the worker
   manifest + routing rule (ADR-0003 action item 5).
6. **Context compression + agent retirement/revival** — pairs with the
   ADR-0004/0005 feature set (urgency-aged alerting needs revival).
7. **Boot protocol, watchdog, zombie reaping** — dispatcher-skeleton hardening;
   wanted the week the dispatcher first runs.
8. **Housekeeping daemon, worker affinity/pooling, dispatch batching** —
   optimizations that need a working skeleton to optimize.
9. **Priority inheritance, EDF, load shedding, panic/fail-closed mode** —
   scheduling maturity; inheritance moves up if resource leases land early.
10. **Speculative execution, memoization** — luxury tier; needs idle capacity
    and the daemon.
11. **A2A device driver** — interop; waits for an actual external agent to
    talk to.

**Tier 3 — project infrastructure that pays off at scale:**

12. **`tools/` package** — Logger first (the dispatcher's logging story),
    Config and Tracer as code grows.
13. **CI/CD** — once there's a test suite worth running remotely.
14. **Docs site (MkDocs)** — once the canon has outside readers.
15. **SQL tooling, FastAPI shell, Docker/Dev Container** — when their
    subjects exist.

## Testing infrastructure

- **pytest with enforced coverage** — 75% minimum including branch coverage;
  HTML + terminal reports; `test__*.py` (double underscore) naming; tests
  mirror the package structure. First real customers: `scripts/next_id.py`
  and the future dispatcher/ticket state machine.
- **Task-runner integration** — test sessions runnable through the task
  runner (originally nox; today that role belongs to `just`), with JUnit XML
  output for CI.

## Reusable `tools/` package

Production-ready utilities, each mapping cleanly onto my-day-os needs:

- **Logger (dual-mode)** — extends `logging.Logger`; colored console
  formatter for local dev, structured-JSON formatter for production, switched
  by environment. This is the future audit/WAL-adjacent logging story for the
  dispatcher.
- **Config (Settings)** — Pydantic `BaseSettings` loading from `.env`
  (tracked) + `.env.local` (gitignored overrides); type-safe; extended per
  project. Key env vars sketched: `IS_LOCAL`, `DEBUG`, FastAPI kwargs
  (`TITLE`, `VERSION`, `API_PREFIX_V1`).
- **Tracer (Timer)** — decorator + context manager logging execution time at
  DEBUG; nestable for overall-vs-component timing. Directly serves the
  ADR-0002 latency-hierarchy measurements.

## Type checking

- **ty** across source and test packages, excluding caches; wired into lint
  tasks and CI.

## SQL tooling

- **SQLFluff** — lint/format SQL (originally BigQuery dialect; here the SoR
  is SQLite, so re-dialect at graduation). Max line 80, 2-space indent,
  custom rules for join qualification and unused joins.

## Pre-commit hooks

- Ruff format/check (and future lint tools) enforced at commit time via
  `pre-commit`, matching whatever `just check` runs.

## Documentation site

- **MkDocs** — `docs/` served locally, built, and deployed to GitHub Pages;
  structure: index, getting-started, guides (per tool), configurations,
  usecases. The design canon (ADRs/POLICY/SPECs) would publish through this.

## CI/CD

- GitHub Actions mirroring local `just` recipes: format check, lint
  (Ruff + ty), tests with coverage, actionlint, labeler, docs deploy.
- **Docker build validation** and **Dev Container** configuration for
  reproducible environments.

## Scheduling & interop (post-ADR-0003 design notes)

- **Worker affinity & pooling** — route new tickets to an already-warm worker
  with similar in-flight context instead of cold-starting per ticket (thread
  pool, not fork-per-request). The L9 journal is the affinity index (ring-0
  queries its own state; no agent-to-agent gossip — scheduling stays in the
  kernel); L11 keeps it safe (lease binds to the *ticket*, so reuse the
  process/context, re-issue authority per ticket). Lands as an affinity term
  in the routing rule (ADR-0003 action item 5).
- **Dispatch batching** — group similar tickets per worker invocation
  (candidate Lever) when agent-invocation overhead proves dominant.
- **A2A as a device driver, not kernel IPC** — foreign/third-party agents
  speak A2A at the ring-3 edge as one more device in the ADR-0002 taxonomy:
  inbound tasks enter via the capture path, outbound calls are leased,
  confirmed external actions. Internal worker↔ring-0 messaging needs no
  protocol ceremony.
- **Gate protocol / lifecycle ABI** — formalize each ticket-state transition
  as either a **gate** (synchronous, kernel-owned, enumerable: admission,
  dispatch, act/commit, confirm — may hold/reorder/batch/refuse work) or a
  **signal** (async transition event any subsystem may observe, none may
  block — feeds telemetry, notification feed, masking). Gates accept
  pluggable **strategies** (mechanism = the gate, policy = the strategy;
  K4/K5 flush batching is the existing instance; dispatch batching the
  next). Any strategy that holds work carries a max-hold Limit in ticks
  (Nagle-style bound) so batching can never starve latency. Extends
  ADR-0003 action items 4–5; execution-SPEC territory.
- **Compensation prefers deterministic executors** — failure handling SHOULD
  route to automation workers, never an improvising agent (execution-SPEC
  rule when the compensation schema is formalized).

## Work optimizations & kernel completeness (late-night OS sweep, 2026-07-28)

- **Memoization** — cache deterministic automation results; idempotency keys
  (L10) double as cache keys.
- **Speculative execution with in-order retirement** — the system MAY
  speculatively perform reversible internal work (draft replies, pre-compute
  plans); L5's confirm gate is the retirement stage. Agents execute out of
  order; effects retire in order.
- **Graph-structured workers: determinism per axis** — a worker graph has two
  independent determinism axes: topology (fixed vs LLM-routed edges) and
  nodes (deterministic tool vs judgment). Fixed graph + deterministic nodes
  = `automation` regardless of framework (LangGraph is substrate, not
  classification); fixed graph + LLM nodes contains non-determinism inside
  node boundaries; LLM-routed topology = fully agentic. Node boundary =
  journal step boundary (worker-internal checkpoints are scratch; ring-0
  journal stays truth per L9). Deterministic subgraphs are the prime
  speculation targets (cheap, replayable, cancellable); judgment-node
  speculation spends tokens — candidate "speculation budget" Lever, spent by
  the housekeeping daemon at idle. Worker manifests declare their quadrant.
- **Priority inheritance** — priorities (K1) + resource leases guarantee
  priority inversion; boost a lease holder to its highest waiter's priority
  (Mars Pathfinder rule). Dispatch-SPEC material.
- **Deadline scheduling (EDF)** — tickets gain real deadlines with the clock
  (ADR-0004); EDF as K1's evolution.
- **Context compression (VM metaphor returns, for context only)** — agent
  context window = RAM: working-set selection at dispatch (need-to-know as
  informational L6), journal-backed digests as swap-out, demand paging from
  the SoR. Contradicts POLICY's no-VM scope rule for *data*; must re-enter
  via an ADR paragraph justifying the distinction. **Direction endorsed by
  Carlos 2026-07-28** — rationale to record: VM concepts manage *scarcity*;
  data (SQLite on disk) isn't scarce, while context windows and human
  attention are fixed-size and expensive — the same resource class at two
  tiers, and the very thing this OS schedules.
- **Agent retirement & revival (suspend-to-journal)** — an agent's durable
  state IS the journal, so retire = surrender lease (L11) + exit, and revive
  = spin a fresh agent rehydrated from the journal digest (demand paging).
  No long-lived processes waiting on humans. Enables completion-decoupled
  alerting (see GAPS#W10): finished work parks silently and preempts only
  when deadline-aged urgency crosses K1.
- **Watchdog** — nothing watches ring 0; external heartbeat on the
  dispatcher's journal tick.
- **Housekeeping daemon (kernel-threads analog: kswapd/writeback/journald)** —
  a separate process, asleep by default, woken by transition **signals** or
  by an empty queue (the idle task is this daemon's second wake source).
  Owns the expensive async work gate strategies must not do inline: batch
  assembly, queue re-optimization between ticks, memoization warmup, journal
  compaction, digest generation, speculation. Observes signals freely, but
  its *actions* re-enter as system-originated tickets/messages through
  ring 0 — journaled, auditable, budgeted (L1/L7 hold even for the janitor).
  Implementable as a privileged automation worker with a standing
  maintenance lease.
- **Load shedding (OOM-killer analog)** — policy for global budget pressure
  mid-flight: shed lowest-priority reversible work first; never shed
  awaiting-confirmation work.
- **Zombie reaping** — lease expiry as the universal reaper: ring 0 reclaims,
  journals the death, routes to retry/compensate.
- **Panic / fail-closed mode** — on detected Law violation: halt all external
  actions, keep capturing (inputs always safe to record; outputs are what
  hurt). Law-shaped; candidate for a future ADR.
- **Boot protocol** — startup ordering: integrity scan → reconcile
  attempted-unconfirmed suspects → resume in-flight → admit new work.
  Pairs with ADR-0004.

## SQLite side quest — "many DB files, one protocol" (2026-07-28)

The OS metaphor lands hard here: an OS has a filesystem, and SQLite DBs *are
files* — so the storage layer can be treated as a mounted-filesystem model:

- **Many DB files, one protocol.** Subsystems may get their own DB files
  (SoR/tickets, journal+audit, future content stores) unified behind a single
  client layer — SQLite's `ATTACH DATABASE` is literally `mount`, and its VFS
  layer is the exact analog of a filesystem driver. One protocol to rule them
  all; per-file lifecycle (backup, compaction, retention) stays independent.
- **Innovation room**: custom client wrapper as the ring-0 storage driver
  (sole writer, L1/L9 enforcement in one choke point), WAL tuning, FTS5,
  per-DB integrity checks as housekeeping-daemon work.
- **References found (evaluate later):** [sqlitecloud.io](https://sqlitecloud.io)
  (hosted SQLite + dashboard) and a Rails-based SQLite portal on GitHub
  (link TBD). Constraint for any such tool: the SoR is local-first and
  ring 0 is the sole writer — a cloud/portal product can only ever be a
  **ring-3 read-only view** (or a backup target), never a second writer.

## Runtime scaffolding

- **FastAPI service shell** — `FastAPIKwArgs`-style ready-made init from
  Settings; the likely HTTP surface if/when the mediator exposes one.
