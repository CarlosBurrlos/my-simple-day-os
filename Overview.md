# my-day-os — Overview

An operating system for a personal day. Instead of scheduling CPU and managing memory/devices, it schedules **attention** and manages calendar, email, and tasks. Work is a **deli ticket** — a *future promise* of completion; the set of open tickets is the OS **process table**.

This is the one-glance summary. Detail lives in the ADRs (`docs/adr/`), the operating rules (`docs/POLICY.md`), and the rendered diagrams (`docs/diagrams/`).

> **Note on filename:** this file is `Overview.md`. On a case-insensitive filesystem (macOS default) `OVERVIEW.md` refers to the same file — there is intentionally only one.

---

## 1. The model at a glance

| Layer / Concept | OS analogy | Chosen tech / model | Decision | Why | Status |
|---|---|---|---|---|---|
| **System of record** | RAM + process table (fast tier) | SQLite — one local file | Authoritative ticket store | Fast, consistent, SQL for scheduling, fully owned/portable; the local cache tier | ADR-0001 (Proposed) |
| **Privileged core** | Kernel, ring 0 | Mediator agent | Adjudicates every event, sole writer of truth | Non-deterministic judgment needs elevated, audited authority | ADR-0002 (Proposed) |
| **Mechanism vs policy** | Trap vs scheduler | Deterministic capture + agent policy | Split them | Determinism at the edges makes the non-deterministic middle trustworthy | ADR-0002 |
| **Human input** | Keyboard & mouse (HID) | Notion | Primary input surface; edits = **input events** | Demoting Notion from store to device dissolves the second-source-of-truth trap | ADR-0002 / L4 |
| **Control surface** | Terminal | Small local web app | Act + answer mediator context-switch prompts | Only surface that closes the write loop cleanly and is real-time | Proposed |
| **Read / glance mirrors** | Monitor | Obsidian (Bases); Notion mirror | Read-only, one-way | Obsidian = owned local + future notes home; Notion = free cross-device glance | Proposed |
| **I/O devices** | Disk / network | Email, Calendar (Google vs Outlook TBD) | Event sources, **not** backbone | External data the OS reads/writes; never the system of record | Open |
| **Event** | Input / IRQ signal | Source-agnostic "something happened" | First-class record | Decouples the core from email/invite/deadline specifics | ADR-0002 |
| **Interrupt** | IRQ | Webhook / push (poll = fallback) | Async delivery of an event | Keeps the system real-time; poll only when a device has no line | ADR-0002 |
| **Context switch** | Preemption | Scheduler decision (priority / masking) | **Not** automatic per interrupt | Protects attention — only a few events earn the right to preempt | ADR-0003 (planned) |
| **Latency** | Memory hierarchy (ns→ms→…) | Tiered delays (ms → hours), scaled ~10⁹ | Design *around* it | Eventual consistency = a write-back cache that hasn't flushed yet | ADR-0002 |
| **Concurrency** | Shared memory vs message passing | Message passing (edits are messages) | Message passing | Notion-as-input-device creates a cache-coherency problem; messages avoid it | ADR-0002 / L4 |
| **Operating rules** | Kernel contract | `POLICY.md`: Laws / Limits / Levers / Protocol | Living spec | Laws firewall the system; ADRs ratify values in | POLICY.md (living) |

---

## 2. Agentic-orchestration readiness

**Verdict:** the current design is strong *substrate* (state, governance, event intake) but is a **single-agent, reactive** model. It covers the deli's *front of house* — taking and triaging tickets — and is largely silent on the *back of house*: **executing** promises with agents. The kernel exists; the **execution runtime does not yet**.

Critical gaps, mapped only to OS concepts that apply:

| Gap | Applicable OS concept | Why critical | Status |
|---|---|---|---|
| **Executor / worker model** | Dispatcher + process execution | We define promises but nothing that *fulfills* them | Missing |
| **Execution state machine** | Process states (ready/running/blocked/failed/zombie) | Agents need blocked/failed/retrying/waiting states, not just done | Sketched |
| **Dispatch & run-queue** | Scheduler run queue | Which ready ticket runs next, by whom, at what concurrency | Missing |
| **Failure semantics** | Timeouts, sagas / compensation | Agents hang, fail, half-finish; real-world actions aren't transactional | Missing |
| **Durable / resumable journal** | Write-ahead log / checkpoint-restore | Ephemeral hosts must resume in-flight work without double-acting | Partial (audit log ≠ resumable journal) |
| **Per-agent budgets** | rlimits / cgroups / quotas | Runaway loops; token/cost/time control | Missing (C1–C3 = rate/WIP only) |
| **Timer / clock device** | Timer interrupt / cron | A day is mostly time-triggered, not event-triggered | Missing (model is purely reactive) |
| **Capability delegation** | Capability passing / privilege drop | Mediator grants a bounded subset to a worker, then revokes | Partial (L6 static least-privilege) |
| **Concurrency & locks** | Mutex/semaphore, dependency graph | Parallel agents contend on shared devices (e.g. calendar) | Missing |
| **Live observability / job control** | `top`/`ps`, job control | See/inspect/intervene on running agent work | Named (Web) not modeled |

---

## 3. Decisions of record

- **ADR-0001 — Backbone:** SQLite is the system of record; Notion is *not* the backbone. *(Proposed)*
- **ADR-0002 — Device Taxonomy & Latency Hierarchy:** every component gets an OS device role; Notion = HID; delay is a managed latency hierarchy; concurrency is message-passing. *(Proposed)*
- **Operating rules:** `docs/POLICY.md` — the living "kernel contract": Laws (inviolable firewalls), Limits (hard constants), Levers (tunable knobs), and the event-consumption Protocol.

---

## 4. Guiding constraints

Single user, personal scale · minimal code, single-responsibility components · Python 3.12, portable across mac/windows/linux · research/planning before any code.

---

## 5. Open questions / next

- **Execution & orchestration model** — the front-of-house/back-of-house gap above. Now the critical-path decision; candidate **ADR-0003 (Execution & Orchestration)**, ahead of the masking/priority work.
- **Masking / priority policy** — ratifies Levers K1–K3 and Limit C3 (context-switch behavior).
- **Email/calendar provider** — Google vs Outlook, the concrete I/O driver.
- **Timer/clock device** — the time-triggered event source a day OS needs.
