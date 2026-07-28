---
id: ADR-0005
title: Masking & Priority Policy
status: Accepted
date: 2026-07-29
accepted: 2026-07-29
proposes: [C3, K1, K2, K3, K9]
depends-on: [ADR-0002, ADR-0003, ADR-0004]
supersedes: []
defers-to: []
---

# ADR-0005: Masking & Priority Policy

**Status:** Accepted (2026-07-29)
**Date:** 2026-07-29
**Deciders:** Carlos
**Related:** Builds on ADR-0002 (context-switch decision) and ADR-0003 (execution); depends on ADR-0004 (the clock provides the time that urgency aging consumes). Number reserved by accepted ADR-0003.

---

## Context

The attention OS exists because notifications are a denial-of-service attack on a human. Accepted canon already routes every event through a context-switch decision (protocol step 6) governed by three stubbed Levers — the context-switch threshold (K1), masking windows (K2), and triage aggressiveness (K3) — and the completion-decoupling design (GAPS#W10, 2026-07-28) established that *finished work* must also queue for attention rather than interrupt on completion. What no document yet decides: how urgency is computed, what pierces a mask, and what the non-preemptive channel is.

## Motivation

Attention is the currency (Overview); every other subsystem protects it indirectly, but this is the policy that spends it. Without it: the dispatcher can execute flawlessly and still burn the user with interrupts — a perfect kernel serving a notification hell. The masking trio (K1–K3) stays stubbed, the notification feed has no charter, and completed work has no rule for *when* to surface.

---

## Options Considered

### Option A: Interrupt on everything (notification-hell baseline)

Every event and completion prompts immediately. **Pros:** nothing is ever late. **Cons:** it's the disease this OS cures; the human context-switches constantly and the context-switch threshold (K1) is meaningless.

### Option B: Digest-only (never preempt)

All signal arrives in periodic batches; no preemption ever. **Pros:** perfect focus protection. **Cons:** "your 2pm flight moved to noon" waits for the 3pm digest. Some events are genuinely worth an interrupt; a policy that cannot say so is not a policy.

### Option C: Two channels + threshold + mask + break-glass (recommended)

A **preemption channel** (rare, earned: computed urgency must cross the context-switch threshold (K1), subject to masking windows (K2)) and a **feed channel** (constant, non-preemptive, browse-on-your-terms). Urgency **ages with the clock** toward deadlines. A narrow **break-glass tier** pierces masks — the non-maskable interrupt (NMI).

**Pros:** matches how attention actually works — ambient awareness plus rare earned interrupts; every piece maps to accepted machinery. **Cons:** urgency computation is a real function to design and tune.

## Trade-off Analysis

Options A and B are the two failure modes this OS was founded to escape; each is what you get when one channel is missing. Option C is the only shape with both channels, and its cost — designing the urgency curve — is unavoidable work under any competent policy; here it is at least *one* function with *one* owner, tunable as a Lever.

---

## The Model

### Two channels

- **Feed (non-preemptive):** the constant stream — captured events, adjudications, state changes, completed work — rendered to ring-3 views (Web, Notion). Read-only projection of the audit trail and job view; browsing it costs attention only when the human chooses. The feed is *why* the preemption channel can afford to be strict.
- **Preemption (the interrupt):** fires only when computed urgency crosses the context-switch threshold (K1) **and** no masking window (K2) is active (break-glass excepted). Delivered per the confirmation and job-control surfaces of ADR-0001/0003.

### Urgency aging — the priority curve (K9)

Every attention-worthy item carries a computed **urgency** that grows as its deadline (a tick, per ADR-0004) approaches. The curve's shape — base priority, ramp steepness, per-class multipliers — is the proposed urgency-aging curve (K9). Consequences:

- **Completion ≠ notification.** Finished work parks in the feed at its base urgency; it preempts only when its aging urgency crosses the context-switch threshold (K1) — "surfaces when urgency says so, not when finished." The finishing agent's last act (per the retire/revive design): confirm the deadline and curve, journal them (write-ahead, L9), surrender its lease (leased authority, L11), exit.
- **Class-aware ramps.** Work *awaiting review* (five minutes of human attention unlocks a finished thing) ages on a steeper late ramp than work *not yet started*. The curve family is one Lever; its per-class parameters are SPEC-level.
- **Deadline-driven, clock-fed:** "alert at deadline − N" is not a feature — it is just a timer ticket (ADR-0004) whose fire re-evaluates urgency. No second notification mechanism exists.

### Masking windows (K2) and the break-glass tier

During a masking window (K2) — deep work, dinner, sleep — capture never stops (record before reason, L2) but preemption is suppressed; accumulated items surface, pre-triaged, when the mask lifts. **Break-glass:** a narrow, explicitly-defined class of events preempts *through* a mask — the non-maskable interrupt. Two hard properties: membership in the class is defined by explicit rule (never by the mediator's judgment call at delivery time), and every break-glass firing is journaled and reviewable after the fact (auditability, L7). Default class: empty until the human enrolls specific patterns.

### Triage aggressiveness (K3) and admission

Triage aggressiveness (K3) tunes how eagerly the mediator promotes events into tickets. Its ceiling is the **active-ticket WIP cap (C3)**, which this ADR claims from the origin-pending ledger: a hard bound on concurrently active promises, independent of any Lever — the same cap-protecting-attention pattern the governance process applies to Proposed ADRs (ADR-0006 §6). Violation: the ticket store holds more active tickets than the cap.

---

## Decision

Reviewed and **Accepted** 2026-07-29 — see *Review Notes (W12)* below. Adopt Option C — two channels (feed + preemption), urgency computed by an aging curve (K9) over clock-provided deadlines, preemption gated by the context-switch threshold (K1) under masking windows (K2) with an explicit break-glass class, triage bounded by aggressiveness (K3) under the active-ticket WIP cap (C3), and completion decoupled from notification throughout.

---

## Proposed POLICY deltas (ratify into POLICY.md on acceptance)

| ID | Kind | Name | Violation condition | Origin section |
| --- | --- | --- | --- | --- |
| K1 | Lever | Context-switch threshold *(claim)* | — (tunable; default TBD) | §The Model |
| K2 | Lever | Masking / quiet-hours windows *(claim)* | — (tunable; default TBD) | §Masking |
| K3 | Lever | Triage aggressiveness *(claim)* | — (tunable; default TBD; capped by C3) | §Triage |
| K9 | Lever | Urgency-aging curve | — (tunable; default TBD; per-class params SPEC-level) | §Urgency aging |
| C3 | Limit | Active-ticket WIP cap *(claim)* | Active tickets exceed the cap | §Triage |

## Consequences

**Easier:** the notification problem gets one governing policy; completed work stops competing with emergencies; masks are real but not absolute (break-glass); every alert path reduces to timers + urgency + threshold — no second mechanism.

**Harder:** the urgency curve (K9) needs tuning against real usage — expect the defaults to be wrong at first and revised freely (it is a Lever); the break-glass class needs honest curation (everything enrolled = Option A by the back door).

**Revisit:** per-class ramp parameters at SPEC time; whether break-glass needs its own Limit (max class size or max fires per window) once real patterns enroll.

## Deferred to follow-up ADRs

None. With this ADR, every stubbed policy in the dictionary has a formal origin, proposed or ratified.

---

## Review Notes (W12)

**Reviewed:** 2026-07-29 · **Verdict:** Accepted · **Reviewer:** Carlos (human stamp per ADR-0006 §2; draft + checklist self-review conducted by Claude).

- The active-ticket WIP cap (C3) placement here — attention-protection
  territory rather than dispatch mechanics — was flagged as the review's
  judgment call and upheld by the reviewer.
- Checklist: every delta carries kind + violation condition + origin section;
  claims match the origin-pending ledger; break-glass honors auditability
  (L7) and record-before-reason (L2); no conflicts with the Laws (L1–L11).
- With this acceptance the origin-pending ledger empties: every policy ID in
  the dictionary has a ratified origin.

## Action Items (research/planning)

1. [x] Review and accept/amend this ADR. *(Accepted 2026-07-29.)*
2. [x] On acceptance: ratify the deltas — the urgency-aging curve (K9) new; the masking trio (K1–K3) and the active-ticket WIP cap (C3) origin-claimed — into POLICY.md and clear the origin-pending ledger.
3. [ ] SPEC work: urgency function, per-class ramps, break-glass class format, feed rendering rules.
