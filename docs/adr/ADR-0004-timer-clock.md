---
id: ADR-0004
title: Timer / Clock Device
status: Accepted
date: 2026-07-29
accepted: 2026-07-29
proposes: [C2, C4, C8, K4, K5]
depends-on: [ADR-0002, ADR-0003]
supersedes: []
defers-to: []
---

# ADR-0004: Timer / Clock Device

**Status:** Accepted (2026-07-29)
**Date:** 2026-07-29
**Deciders:** Carlos
**Related:** Builds on ADR-0002 (Device Taxonomy) and ADR-0003 (Execution & Orchestration), which reserved this number; claims the origin-pending flush family per `docs/adr/README.md`.

---

## Context

A day OS is mostly time-triggered: "remind me at 4," "every Monday," "flush the cache every N minutes," "this lease expires in 10 ticks." The accepted execution state machine (ADR-0003) already contains `Ready → Deferred → Ready: timer fires` — an edge with no device behind it. ADR-0003 also introduced the scheduler **tick/quantum** as the single atomic time unit for all timeouts (dispatch-ack, wall-time in the per-worker budget (C6), confirmation timeouts) but deferred its definition. Meanwhile four ratified-in-concept policies sit origin-pending because they are all creatures of time: the flush cadence (K4), batch size (K5), the in-flight write ceiling (C2), and the unconfirmed-action age limit (C4).

## Motivation

Without a clock, the OS cannot wake itself: no deferred tickets, no recurring promises, no lease expiry, no retry backoff pacing, no flush cadence, no urgency aging (which ADR-0005 needs). Every timeout named in accepted canon is currently a promise with no mechanism. This ADR gives time a device, an interrupt, and an owner for the flush family.

---

## Options Considered

### Option A: Wall-clock everywhere (cron model)

Every timed behavior schedules against calendar wall-time directly.

**Pros:** familiar; human-legible schedules. **Cons:** wall-time is non-monotonic (DST, NTP jumps, sleep/resume) — timeouts and backoff built on it misfire exactly when the host misbehaves; every subsystem reinvents its own timing; untestable without waiting.

### Option B: Tick-based virtual clock + timer service (recommended)

A single **Clock device** provides a monotonic **tick** (the quantum from ADR-0003); a **timer service** in ring 0 maintains a queue of timers that fire as **timer interrupt events** through the standard capture path. Wall-time appears only at the edge, translated once ("4:00 PM" → a target tick) by the timer service.

**Pros:** monotonic and testable (a fake clock advances ticks in tests — determinism where determinism is available); one timing authority; timer fires are ordinary captured events — deduped (idempotent capture, L8), recorded before reasoning (L2), audited (L7); sleep/resume handled in one place (the clock reconciles on boot). **Cons:** one wall-time↔tick translation layer to get right (DST, timezones live *only* there).

### Option C: External scheduler dependency (OS cron / cloud scheduler)

**Pros:** zero code. **Cons:** the OS's heartbeat lives outside the OS — invisible to the journal, unauditable (auditability, L7), unavailable to tests, and a second writer of "when things happen." Rejected on principle: the clock is a ring-0 organ, not an outsourced service.

## Trade-off Analysis

Option B is the standard kernel answer for the standard kernel reason: monotonic ticks are the only base that makes timeouts, backoff, and leases *reason-able*, and pushing wall-time to a single translation edge quarantines the messy calendar arithmetic. The cost — one translation layer — is work Option A would have paid in every subsystem separately.

---

## The Clock in the device taxonomy

Per the taxonomy (ADR-0002): the Clock is an **internal device** — the first device that is *part of* the OS rather than external to it. Confirmation class (per the accepted additive delta): `idempotent-keyed` — a timer fire carries its timer ID + scheduled tick as a natural idempotency key, so a duplicate fire dedupes under idempotent capture (L8).

| Property | Value |
| --- | --- |
| Device class | Internal interrupt source (the hardware timer) |
| Emits | Timer interrupt events → standard capture path |
| Owns truth? | No — timer definitions live in the SoR; the clock only fires |
| Confirmation class | `idempotent-keyed` |

**Timer definitions are tickets' property, not the clock's.** A deferred ticket, a recurring promise, a lease expiry, a flush tick — each records its timer in the SoR (single writer of truth, L1); the ring-0 timer service loads them and fires events. On boot, the service rebuilds its queue from the SoR — the run-queue-is-a-view principle applied to time.

## Mechanisms

- **Tick/quantum (C8).** All internal timing — dispatch-ack, wall-time in the per-worker budget (C6), confirmation timeouts, lease durations, backoff pacing for the retry policy (K7) — is expressed in ticks. The tick's real-time value is a hard constant: proposed as the scheduler tick quantum (C8), value SPEC-level (human-scale — likely ≥ 1 s; this OS needs no millisecond precision).
- **Tickless implementation (informative).** The tick is a **unit of account, not a heartbeat**: `tick = floor(monotonic_now / quantum)`, derived on demand from the host OS's monotonic clock — the host is our hardware; its clock is our oscillator. No process wakes per quantum (the tickless-kernel lesson): the timer service is a long-lived, mostly-asleep ring-0 component doing sleep-until-next-deadline, waking only when a timer is due or an earlier one is registered. Idle cost is zero. Quantization to tick boundaries also yields timer coalescing for free.
- **Deferred tickets.** `Ready → Deferred: scheduled` records a target tick; the timer fire re-readies the ticket through admission control. This activates the deferred-state edge accepted in ADR-0003.
- **Recurring promises.** A recurrence is a **template ticket** plus a repeating timer: each fire *issues a fresh ticket* from the template (copy-on-write instantiation) rather than resurrecting a completed one — IDs stay permanent, history stays honest, and editing the template changes future instances only.
- **Deadlines.** A ticket may carry a deadline (a tick); the clock makes it real. This is the substrate ADR-0005's urgency aging consumes — the clock *provides* time; masking & priority *decides* what time means.
- **Timer coalescing.** Adjacent fires within a small window may batch into one wakeup (the standard power-saving technique; here it saves attention and poll budget under the rate ceiling (C1)). Window size is SPEC-level.
- **Boot reconciliation.** On start, the timer service compares now-tick against the SoR's timer set: overdue timers fire immediately (once, idempotently); the boot-protocol ordering itself remains future work (see BACKLOG).

## Claiming the flush family

Time is what the flush family was waiting for. This ADR formalizes as its own:

- **Flush cadence (K4)** — how often the write-back flush runs, in ticks; interacts with dirty tracking (a cadence tick with an empty dirty set is a no-op; see the flush-triad BACKLOG entry).
- **Batch size (K5)** — writes grouped per external call, paired with the rate ceiling (C1).
- **In-flight write ceiling (C2)** — backpressure bound on the unflushed queue. Violation: the fast tier accepts a write when the flush queue is at the ceiling.
- **Unconfirmed-action age limit (C4)** — an irreversible action awaiting confirmation expires after N ticks rather than piling up. Violation: an unconfirmed action older than the limit remains eligible to act.

---

## Decision

Reviewed and **Accepted** 2026-07-29 — see *Review Notes (W11)* below. Adopt Option B — a ring-0 Clock device (monotonic tick, C8-governed) with a timer service that fires timer interrupt events through the standard capture path; timer definitions live in the SoR; recurrence is template-plus-timer instantiation; and this ADR becomes the formal origin of the flush family — the flush cadence (K4), batch size (K5), the in-flight write ceiling (C2), and the unconfirmed-action age limit (C4).

---

## Proposed POLICY deltas (ratify into POLICY.md on acceptance)

| ID | Kind | Name | Violation condition | Origin section |
| --- | --- | --- | --- | --- |
| C8 | Limit | Scheduler tick quantum | Any internal timeout expressed in a unit other than ticks | §Mechanisms |
| C2 | Limit | In-flight write ceiling *(claim)* | Write accepted while flush queue at ceiling | §Claiming |
| C4 | Limit | Unconfirmed-action age limit *(claim)* | Unconfirmed action older than limit remains actionable | §Claiming |
| K4 | Lever | Flush cadence *(claim)* | — (tunable; default TBD, in ticks) | §Claiming |
| K5 | Lever | Batch size *(claim)* | — (tunable; default TBD; paired with C1) | §Claiming |

## Consequences

**Easier:** deferred and recurring promises become real; every timeout in canon gains its unit and its mechanism; tests get a fake clock; ADR-0005's urgency aging gets its substrate; the flush family gets one coherent owner.

**Harder:** the wall-time↔tick translation edge (DST, timezones, sleep gaps) must be right and lives in exactly one place; boot reconciliation of overdue timers adds a startup obligation.

**Revisit:** tick value and coalescing window at SPEC time; whether deadline semantics need hard/soft classes once urgency aging (ADR-0005) exercises them.

## Deferred to follow-up ADRs

None — this ADR closes ADR-0003's first IOU. The boot protocol (full startup ordering) remains a BACKLOG item, not a numbered reservation.

---

## Review Notes (W11)

**Reviewed:** 2026-07-29 · **Verdict:** Accepted · **Reviewer:** Carlos (human stamp per ADR-0006 §2; draft + checklist self-review conducted by Claude).

- Review interrogated the tick's technical shape; resolved by the tickless
  amendment: the tick is a unit of account derived on demand from the host
  monotonic clock (the host is our hardware), the timer service is a
  sleep-until-next-deadline component with zero idle cost — nothing ever
  actually ticks.
- Checklist: every delta carries kind + violation condition + origin section;
  claims match the origin-pending ledger; no conflicts with the Laws (L1–L11)
  found — timer fires enter via the standard capture path under idempotent
  capture (L8) and record-before-reason (L2).

## Action Items (research/planning)

1. [x] Review and accept/amend this ADR. *(Accepted 2026-07-29.)*
2. [x] On acceptance: ratify the deltas — the tick quantum (C8) new; the flush family (C2, C4, K4, K5) origin-claimed — into POLICY.md and clear the origin-pending ledger rows.
3. [ ] SPEC work: tick value, coalescing window, timer record schema, wall-time translation rules.

&nbsp;