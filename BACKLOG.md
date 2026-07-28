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

## Runtime scaffolding

- **FastAPI service shell** — `FastAPIKwArgs`-style ready-made init from
  Settings; the likely HTTP surface if/when the mediator exposes one.
