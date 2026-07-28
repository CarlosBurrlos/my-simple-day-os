# CLAUDE.md

Guidance for Claude Code (claude.ai/code) working in this repository.

**Context is currency.** This file is a lean index: the few rules agents need on
every session live inline; everything else is a pointer. Read linked docs on
demand — do not expect this file to hold their content.

## What this project is

**my-day-os** — a personal "attention OS" (deli-ticket promises, attention
scheduling, ring-0 mediator). Currently in the **planning/design phase**: there
is no application code yet; the work product is the design canon in `docs/`.

| Where | What |
| --- | --- |
| `Overview.md` | Human-readable project overview |
| `docs/adr/` | ADRs — RFC-style proposals (ADR-0001..0003; all Proposed) |
| `docs/POLICY.md` | Policy dictionary (Laws `L*`, Limits `C*`, Levers `K*`) |
| `docs/templates/` | Document templates (SPEC; ADR template pending) |
| `docs/diagrams/` | Mermaid sources + rendered HTML |
| `TODO.md` / `GAPS.md` | FIFO work queue + its depth partner (protocol below) |
| `BACKLOG.md` | Future-capabilities parking lot — unscheduled, no work IDs |
| `AGENTS.md` | Sandbox git flow (remote setup, PAT) + agent guardrails |
| `COMMIT_CONVENTION.md` | Self-contained Conventional Commits rules |

## Session start

At the start of a session (or after a long gap), run **`just status`** before
picking up work: it prints the last commits, the work-queue head (next up),
the working-tree state, and ID high-water marks. Then read the head row's
GAPS entry if it has one. This is the "here we are & here's what's ready"
report — prefer it over re-deriving state by browsing.

## Tooling

Python 3.12.0 (pinned), managed by **uv**; linted/formatted by **Ruff**. Use
`uv add`, not `pip install`; `uv.lock` is the lockfile. The `justfile` wraps
the common commands — prefer its recipes:

```bash
just            # list recipes (default)
just sync       # uv sync — install/sync dependencies
just lint       # uv run ruff check .
just lint-fix   # uv run ruff check . --fix
just fmt        # uv run ruff format .
just fmt-check  # uv run ruff format . --check (no writes)
just test       # unittest suite (tests/)
just check      # lint + fmt-check + tests — CI-safe, no writes
just audit      # read-only canon audit: origins, DAG, sequences, blast radius (--json for graph)
just ids        # show next available ID in every sequence (no allocation)
just next-id L  # allocate next ID in a sequence (L, C, K, ADR, SPEC); optional count arg
just peek-id L  # show a sequence's next ID without allocating
```

**ID allocation rule**: policy and document IDs (`L*`, `C*`, `K*`, `ADR-*`,
`SPEC-*`) are permanent — never renumbered or reused; gaps are fine. Always
allocate via `just next-id <SEQ>` (backed by the atomic store
`docs/sequences.json`) instead of guessing the next number.

**Policy ID citation style**: refer to policies by their human-readable name
with the ID as a parenthetical cite — "single writer of truth (L1)", "flush
cadence (K4)", "the WIP cap (C3)" — on **every** mention, not just the first.
Never a bare ID; the reader should never have to look up what a naked "C2"
means.

## Work Queue Protocol (TODO.md + GAPS.md)

`TODO.md` at the repo root is a **FIFO work queue**, not a conventional checklist — this deliberately breaks the usual TODO convention. `GAPS.md` is its depth partner. Rules:

- **Shape**: TODO.md holds one CSV-shaped row per work item inside a `csv` code block: `id,name,context,blocked_by,depth`.
- **FIFO discipline**: pop work from the **top**; append new work to the **bottom**. Reordering is allowed only as an explicit prioritization decision (e.g., blast-radius ordering), never silently.
- **Work IDs**: `W<n>` — monotonically increasing, never reused. These are **informal** and workspace-scoped: NOT part of the formal ID system, NOT in `docs/sequences.json`. The next available `W<n>` is tracked in TODO.md's header comment; bump it when appending.
- **Done = deleted**: completed rows are removed, not checked off. Git history is the archive. The head of the file always means "next up."
- **GAPS.md**: one `## W<n> — <name>` section per work item that needs more depth than a one-line row (what the gap is, why it matters, what "done" looks like). Not every row needs an entry. A row's `depth` column points at its entry (`GAPS#W<n>`). Delete the entry when its work item completes.
- **Scaling pattern**: each feature (or feature set) gets its own VSCode workspace; on starting work there, a fresh TODO.md/GAPS.md pair is created in that workspace as the landing zone for its queued items. Work-ID sequences are per-queue.
- **Agents**: when picking up work, start from the top of TODO.md unless told otherwise; when discovering new work mid-task, append a row (and a GAPS entry if it has depth) instead of losing it or starting it immediately.
- **Three horizons**: `BACKLOG.md` (someday/concepts, unscheduled) → `TODO.md` (queued, committed-to) → `GAPS.md` (depth on what's queued). Backlog items graduate by getting a `W<n>` row in TODO.md; they never carry work IDs while parked.
- **Backlog priority**: BACKLOG.md opens with a "Suggested priority" section — an *advisory* graduation order (usage rules documented in-place there). It never overrides TODO.md's FIFO; re-ranking it is always legal.

## Commit Messages — Conventional Commits

All commits follow the convention in [COMMIT_CONVENTION.md](COMMIT_CONVENTION.md) — a self-contained, lift-and-shift copy of Conventional Commits v1.0.0 plus this repo's scopes and house style. Read it before committing. Quick shape: `<type>[scope][!]: <description>`; in this planning-phase repo most commits are `docs` or `chore`. Do **not** add `Co-Authored-By` or other AI-attribution trailers to commits — AI co-authoring is acknowledged once, in `README.md`.

## Memory Policy

- All persistent memory lives **in this project** (repo files), never in the
  home-directory auto-memory location.
- Keep memory writes to a minimum.
- **Always prompt the user for approval before making any memory update.**
