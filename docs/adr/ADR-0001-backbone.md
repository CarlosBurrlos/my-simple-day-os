---
id: ADR-0001
title: Backbone (System of Record) for my-day-os
status: Accepted
date: 2026-07-26
accepted: 2026-07-28
proposes: [L1, L3]
depends-on: []
supersedes: []
defers-to: []
---

# ADR-0001: Backbone (System of Record) for my-day-os

**Status:** Accepted (2026-07-28 — backfill review per ADR-0006 action item 6)
**Date:** 2026-07-26
**Deciders:** Carlos
**Supersedes:** —
**Amended:** 2026-07-26 — see *Amendments* below

> **Amendments (2026-07-26).** Later design work (now ADR-0002) refined two things in this ADR without overturning its decision:
> 1. **Notion is reclassified from "presentation layer" to primary HID (keyboard & mouse).** A Notion edit is an *input event / message*, not a write to truth — which is the clean resolution to the "second source of truth" risk noted under Option A. The core remains the only writer.
> 2. **Delay is reframed as a scaled OS latency hierarchy.** The "eventual consistency" weakness listed against Notion is really *a write-back cache that hasn't flushed yet* — a managed property, not a defect. This strengthens (does not weaken) the SQLite-as-fast-tier choice below.
>
> The recommendation (SQLite as system of record) stands unchanged.

---

## Context

`my-day-os` treats a personal life the way an operating system treats a machine. Instead of scheduling CPU time and managing memory and devices, it schedules *attention* and manages calendar, email, and tasks. The central abstraction is the **deli ticket**: when work is promised, a ticket is issued and recorded as a *future promise* of completion. The set of open tickets is, in effect, the OS **process table**; deciding what to work on next is **scheduling**.

For any OS, one question dominates the architecture before all others: **where does the authoritative state live** — the process table, the ticket queue, the record of what has been promised and what is done? This is the *backbone*, or system of record (SoR). Everything else (schedulers, notifiers, views) is downstream of that choice.

A framing distinction that drives this whole decision:

| OS concept | my-day-os equivalent | Who owns the truth |
|---|---|---|
| Process table / run queue | Tickets (promises) + their state | **The backbone — this is what we're choosing** |
| Scheduler | Logic that picks the next ticket | Our code (out of scope here) |
| Devices (I/O) | Email inbox, calendar (and later: anything that emits events) | **External services** (Gmail/Google Calendar or Outlook) — *not* the backbone |
| Event | A source-agnostic "something happened" (email/invite/deadline are just *types*) | First-class record in the backbone |
| Interrupt | The async *delivery* of an event — a webhook/push arriving. Polling is the fallback line when a device has none (or its channel expired) | The device signals; our handler receives |
| Mode switch (ring 3 → ring 0) | Entering the privileged core to durably record the event and issue/adjust a ticket, then return | The trusted core (the SQLite "kernel") owns the write |
| Context switch | A *separate* scheduler decision: does this event preempt what you're doing right now? | The scheduler — a policy call, deliberately **not** automatic |
| Display / terminal | The human-facing view of the day | A presentation layer (ring 3) — may or may not be the backbone |

Two insights this mapping encodes:

**Email and calendar are not backbone candidates.** They are external "devices" the OS reads from and writes to. The backbone is where *my-day-os's own state* — the tickets — lives. The original project vision names Notion as that backbone; this ADR evaluates whether that is the right call or whether an alternative serves better.

**An interrupt is not a context switch.** A webhook/push arriving is the *interrupt* (the async signal). It triggers a *mode switch* into the privileged core, which does one trusted, minimal job: record the event and, if warranted, issue or adjust a ticket — this is the move into the "more privileged ring." Whether that event then causes a *context switch* — actually preempting your current focus — is a distinct decision the scheduler makes via priority/masking. This separation is the point of an *attention* OS: every event is captured cheaply in the core, but only a few earn the right to interrupt what you're doing. Collapsing interrupt into context-switch would let every ping hijack the day. The system stays real-time by being interrupt-driven at the core; eventual consistency is tolerated only where a device forces it (e.g. Notion's eventually-consistent reads, or expiring watch channels that require a reconciliation poll).

### Constraints (from project charter)

- **Single user, personal scale.** Realistically tens to low-hundreds of tickets and state changes per day, not thousands per second.
- **Minimal code, single responsibility.** Each component maps to exactly one purpose. The backbone choice should not force a sprawling sync engine.
- **Python 3.12, machine-portable.** Must work on mac/windows/linux.
- **Research/planning before code.** This document is a decision aid, not an implementation.
- **Longevity.** This is an ongoing system meant to be maintained and scaled over time, so lock-in and data ownership matter.

---

## Decision

**Proposed:** Adopt a **local-first system of record** — a single SQLite database (plus plain files for documents) as the authoritative ticket/process store — and treat **Notion as a view and (per ADR-0002) the primary input device (HID)**, not as the backbone itself. Email and calendar remain external I/O devices accessed through their own APIs.

This is a *layered* answer rather than a single-tool answer. It is deliberately framed as **Proposed**, not Accepted, because a defensible simpler path (pure Notion as backbone) exists and the trade-off is worth your explicit sign-off. Both are analyzed below.

---

## Options Considered

### Option A: Notion as the backbone

Notion databases hold the tickets directly; our Python scheduler reads and writes tickets through the Notion API. Notion is simultaneously the store and the UI.

| Dimension | Assessment |
|---|---|
| Complexity | **Low to start, medium at scale** — no store to build, but sync/consistency logic creeps in |
| Cost | Free personal plan viable; paid if API/automation needs grow |
| Latency / throughput | **Weak** — ~3 requests/sec average per integration; eventually-consistent reads |
| Data ownership / portability | **Weak** — data lives in a vendor workspace; export is possible but lossy |
| Human interface | **Excellent** — polished, cross-device UI for free |
| Offline / reliability | **Weak** — no network, no state |
| Event delivery (real-time) | **Now viable** — Notion shipped official webhooks (2025) |

**Pros:** Zero UI to build; instantly usable on every device; the vision already assumes it; database automations and webhooks exist for triggering work.
**Cons:** The scheduler would run its hot loop against a rate-limited (~3 req/sec), eventually-consistent remote API with a 500KB / 1000-block payload ceiling and a 2000-character rich-text cap per field. Offline means dead. Your process table lives on someone else's server, and the query model (filter/sort over a database) is far weaker than SQL for the kind of "what should I do next" scheduling queries this system is built around.

### Option B: Local-first — SQLite + plain files (recommended core)

A single SQLite file is the authoritative ticket store; documents/notes live as plain files beside it. The scheduler runs against local, transactional, zero-latency state. Notion (Option A's strength) is bolted on *as a view*, kept in sync one-way or two-way.

| Dimension | Assessment |
|---|---|
| Complexity | **Low core, medium if two-way Notion sync is added** |
| Cost | **Free**, no vendor tier |
| Latency / throughput | **Excellent** — local, transactional, no rate limits |
| Data ownership / portability | **Excellent** — one file, yours, trivially backed up/versioned |
| Human interface | **None built-in** — must add a view (Notion, CLI, or web) |
| Offline / reliability | **Excellent** — works fully offline; ACID |
| Event delivery (real-time) | Via the external device APIs (Gmail/Calendar push), independent of the store |

**Pros:** SQLite is in the Python 3.12 standard library (`sqlite3`) — zero dependencies, perfectly portable across mac/windows/linux, one-file backups, and full SQL for scheduling queries. The scheduler ("kernel") never blocks on a network. Clean single-responsibility split: store = truth, Notion = display, APIs = I/O.
**Cons:** No interface out of the box — you must choose and build a view. If you want Notion two-way (edit a ticket in Notion, have it reflect back), you take on sync/conflict logic, which is real work and the main cost of this option.

### Option C: Airtable as the backbone

Structurally like Notion but more database-shaped (typed fields, better views, a cleaner API).

| Dimension | Assessment |
|---|---|
| Complexity | Low to start |
| Cost | **Weakest** — meaningfully more expensive than Notion at paid tiers; automation limits on free |
| Latency / throughput | Rate-limited (~5 req/sec per base); remote |
| Data ownership / portability | Vendor-hosted, same lock-in concern as Notion |
| Human interface | Good, database-centric |
| Event delivery (real-time) | Webhooks available |

**Pros:** A genuinely better *database* than Notion if a hosted DB is what you want. **Cons:** All of Notion's remote/lock-in/latency drawbacks, plus higher cost and a less pleasant general-purpose "workspace" feel. It doesn't beat Notion as a *view* or SQLite as a *store*, so it wins on neither axis for this project.

### Option D: Obsidian / Markdown vault as the backbone

Tickets as markdown files with frontmatter in an Obsidian vault.

**Pros:** Maximal ownership and portability; great for the *notes/knowledge* resource; human-editable in plain text. **Cons:** Poor as a queryable *process table* — "give me all open tickets due today, sorted by priority" is awkward over markdown frontmatter compared to SQL. Better suited as the future notes layer than as the ticket backbone.

---

## Trade-off Analysis

The decision reduces to one tension: **hosted convenience (Notion/Airtable) vs. local authority (SQLite).**

At personal scale, Notion's rate limits will not break you — a few requests per second is plenty for a human's day. So throughput is *not* the deciding factor. The deciding factors are:

1. **Where the scheduler's truth lives.** The heart of `my-day-os` is the logic that decides *what to work on next*. That logic wants fast, consistent, richly-queryable state. SQL over a local file gives you exactly that; a rate-limited, eventually-consistent remote database fights you at precisely the layer that matters most.

2. **Ownership and longevity.** This is explicitly a long-lived, evolving system. A single SQLite file you own — versionable in the same repo, backed up by copying one file — is a stronger foundation for something you intend to maintain for years than state trapped in a vendor workspace.

3. **Single responsibility.** The layered model gives each piece one job: **SQLite = the truth**, **Notion = the display**, **Gmail/Calendar = the I/O devices**. Making Notion the backbone collapses "truth" and "display" into one vendor and muddies that boundary.

The cost of the recommended path is the **view**: SQLite gives you no UI. Two honest ways to pay that cost:
- **Cheapest:** start with a CLI / read-only view and skip Notion entirely until the core works.
- **Richest:** sync SQLite → Notion (one-way first) so you get Notion's polished cross-device UI without making it authoritative. Add two-way editing later only if you find you want it — that's where the sync complexity lives, and it's optional.

Notion is not being rejected — it's being **repositioned** from backbone to interface, which is the role it's genuinely excellent at.

---

## Consequences

**What becomes easier**
- The scheduler runs against local, transactional, no-rate-limit state — the core logic stays simple and fast.
- Backups, versioning, and portability are trivial (one file, standard library, no external account required to run).
- Clean layer boundaries make each future component single-purpose and independently testable.

**What becomes harder**
- You must choose and build a view; there's no free UI on day one (mitigated by starting CLI-first, adding Notion-as-view later).
- If/when you want two-way Notion editing, you own the sync and conflict-resolution logic.
- Event delivery (email/calendar push) relies on watch channels that expire and must be renewed, with reconciliation polling as the fallback — a small recurring maintenance concern regardless of backbone choice.

**What we'll need to revisit**
- The email/calendar provider decision (Google vs Outlook) — deferred; it affects the *device* layer, not the backbone.
- Whether Notion sync is one-way or two-way — defer until the core store and scheduler exist.
- Obsidian/markdown as the eventual **notes/knowledge** resource — a separate future ADR.

---

## Review Notes (backfill, per ADR-0006 §4)

**Reviewed:** 2026-07-28 · **Verdict:** Accepted · **Reviewer:** Carlos (human-conducted). The layered decision (SQLite-as-backbone + Notion-as-view) is confirmed as-is — "perfect," in the reviewer's words. This ADR predates the ADR-0006 required shape; its Options table serves as the alternatives analysis, and its seeded Laws (L1–L8 foundations, formalized via ADR-0002 into POLICY.md) were already treated as stable canon by the accepted ADR-0003, so no conflicts exist by construction. Action-item dispositions below.

## Action Items (research/planning — no code yet)

1. [x] **Confirm the layered decision** (SQLite-as-backbone + Notion-as-view) or elect the simpler pure-Notion path — this is the sign-off this ADR asks for. *(Confirmed 2026-07-28, backfill review.)*
2. [ ] **Model the ticket** on paper. *(Re-scoped 2026-07-28: the ADR is not the place to harden field-level detail — this belongs to the ticket-schema work of ADR-0003 action item 7 / the execution SPEC.)*
3. [x] **Sketch the ticket state machine** (e.g. `issued → scheduled → in-progress → done / dropped / deferred`) — the OS process lifecycle. *(Fulfilled by ADR-0003's execution state machine, accepted 2026-07-28.)*
4. [ ] **Decide the first view.** *(Direction set 2026-07-28: VSCode extensions suffice as the local-dev view for now; CLI acceptable fallback; a richer purpose-built view is deferred until there is state worth viewing.)*
5. [ ] **Device provider** — *(Re-scoped 2026-07-28: do **not** pick a provider. The follow-up ADR defines a generic provider interface implemented per provider (Google, Outlook, …) — no lock-in; providers are drivers behind one interface.)*
6. [ ] Only after 1–5: write the *first* single-responsibility component (most likely: define the SQLite schema + a thin ticket store).

---

## Appendix: Facts that informed this ADR

- **Notion API limits:** ~3 requests/sec average per integration (bursts allowed; HTTP 429 + `Retry-After` on overage), 500KB max payload, 1000 blocks per payload, 2000-char rich-text/URL fields, 100 items per relation/multi-select write. Reads are eventually consistent. Official webhooks shipped in 2025, enabling event-driven triggers.
- **Airtable API:** ~5 requests/sec per base; webhooks available; paid tiers notably pricier than Notion.
- **SQLite:** bundled with Python 3.12 via the standard-library `sqlite3` module — no external dependency, portable single-file database across mac/windows/linux, full ACID transactions and SQL.
- **Google Calendar API:** ~600 requests/min per user, 10,000/min per project; push notifications supported (watch channels expire and must be renewed). **Gmail API:** push via Cloud Pub/Sub; `watch` subscriptions expire (~7 days) and require renewal.

*Sources are listed with the chat message that accompanied this document.*
