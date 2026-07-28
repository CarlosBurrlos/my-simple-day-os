# AGENTS.md — start here

Entry point for any AI agent (or human) picking up **my-day-os** in a fresh cloud sandbox. Read this file first, then `Overview.md`.

## What this project is

An operating system for a personal day: instead of scheduling CPU and managing memory/devices, it schedules **attention** and manages calendar, email, and tasks. Work is modeled as a **deli ticket** — a *future promise* of completion; the set of open tickets is the OS **process table**. The design leans on OS concepts, but only the ones that *apply* — we do not port every classic-OS idea.

## Current state — planning phase, no application code yet

- Decisions live in `docs/adr/` as ADRs; all are currently **Proposed** (nothing locked):
  - **ADR-0001** Backbone — SQLite as system of record (Notion is not the backbone)
  - **ADR-0002** Device taxonomy & latency hierarchy — Notion as HID, mediator in ring 0, message-passing
  - **ADR-0003** Execution & orchestration — polymorphic Worker (agent/automation/human), dispatcher, durable journal
- `docs/POLICY.md` — the living "kernel contract": **Laws** (inviolable) / **Limits** (hard constants) / **Levers** (tunable) / **Protocol** (event consumption).
- `Overview.md` — one-glance master table + orchestration-gap analysis. **Read right after this file.**
- `docs/diagrams/` — mermaid sources (`.mermaid`) + a rendered `my-day-os-diagrams.html`.
- Next planned: **ADR-0004** Timer/Clock device, **ADR-0005** Masking & priority policy.

## How we work here — conventions, follow these

- **Planning/research before code.** Interrogate the user on *why* any code is needed before writing it.
- **Minimal code, strict SRP** — every module maps to one and only one purpose.
- **Python 3.12.0 only** (see `.python-version`); portable across mac / windows / linux.
- Virtual environment at `./.venv`.
- **ADRs are immutable records** — amend via a new or superseding ADR, never by rewriting history. In `POLICY.md`, **Laws** change only via an accepted ADR; **Levers** are tunable freely.
- Keep `docs/diagrams/*.mermaid` in sync with any inline copies embedded in the ADRs/POLICY.

## Sandbox + git workflow — the cloud flow

This project is worked in an **ephemeral cloud sandbox**. The GitHub remote is the source of truth; the sandbox clones, works, and pushes back. No local machine or device bridge is involved.

```
# 1. Clone (public read — no auth needed)
git clone https://github.com/CarlosBurrlos/my-simple-day-os.git
cd my-simple-day-os

# 2. Environment
python -m venv .venv
# macOS/Linux:  source .venv/bin/activate
# Windows:      .venv\Scripts\activate

# 3. Push auth — only needed to write back. Export a fine-grained,
#    repo-scoped, short-lived GitHub PAT, then wire it:
export GITHUB_TOKEN=github_pat_xxxxx
python scripts/configure_remote.py

# 4. Work on a branch, commit, push
git switch -c my-change
# ... make changes ...
git commit -m "..."
git push -u origin my-change

# 5. When finished, clear the credential
python scripts/configure_remote.py --clear
```

`scripts/configure_remote.py` stores the token **only** in the local `.git/config` (never tracked, never committed) and keeps it out of `git remote -v`. **Revoke the PAT when the sandbox is done.**

Commit-message trailer convention (attribution for AI-assisted commits):

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Guardrails

- Never commit secrets, the PAT, `.venv/`, or `*.sqlite` — the first is on you; the rest are already in `.gitignore`.
- The SQLite system-of-record is local and ephemeral — it is **not** tracked in git.
- Ask before introducing a new dependency or any non-Python code.

## Read next

`Overview.md` → `docs/adr/ADR-0001` … `ADR-0003` in order → `docs/POLICY.md`.
