---
id: ADR-XXXX
title: <short title>
status: Proposed
date: <YYYY-MM-DD>
proposes: []
depends-on: []
supersedes: []
defers-to: []
---

# ADR-XXXX: <Title>

<!-- Lift-and-shift template implementing ADR-0006 §4. Before drafting:
     - Allocate XXXX via `just next-id ADR` (never guess).
     - WIP cap: at most 2 ADRs in Proposed at once (ADR-0006 §6).
     - Size cap: propose ≤ 6 policy IDs; more is a signal to split.
     - Frontmatter schema: docs/adr/README.md. Keep it in sync with prose.
     - Citation style: policy IDs always appear as name + parenthetical ID,
       e.g. "the WIP cap (C3)" — every mention, never a bare ID.
     - Language is PRE-NORMATIVE: the ADR argues and proposes; POLICY.md
       and SPECs carry the normative text after ratification. -->

**Status:** Proposed
**Date:** <YYYY-MM-DD>
**Deciders:** <who stamps>
**Related:** <ADRs this builds on / supersedes / defers to — mirror the frontmatter>

---

## Context

<What situation makes this decision necessary. Cite prior ADRs and canon.>

## Motivation

<Why this change; what breaks or stays broken without it.>

---

## Options Considered

<!-- Genuinely considered, not strawmen (review checklist item 4). One
     subsection per option; a compact dimension table where it helps. -->

### Option A: <name>

**Pros:** … **Cons:** …

### Option B: <name> (recommended)

**Pros:** … **Cons:** …

## Trade-off Analysis

<Why the recommended option wins; what it costs; honesty notes.>

---

## Decision

**Proposed:** <the decision in one paragraph. On acceptance this line is
updated to record the verdict and point at Review Notes.>

---

## Proposed POLICY deltas (ratify into POLICY.md on acceptance)

<!-- Mirror of the SPEC registry shape. Every ID allocator-issued
     (`just next-id L|C|K`). Laws/Limits MUST state a violation condition —
     if it cannot be violated, it is not a policy (review checklist item 1).
     Delete empty subsections; keep frontmatter `proposes` in sync. -->

| ID | Kind | Name | Violation condition | Origin section |
| --- | --- | --- | --- | --- |
| L<N> | Law | <name> | <observable violation> | §<n> |
| C<N> | Limit | <name> | <bound exceeded> | §<n> |
| K<N> | Lever | <name> | — (tunable; declare default + range) | §<n> |

---

## Consequences

**Easier:** … **Harder:** … **Revisit:** …

## Deferred to follow-up ADRs

<!-- Name each deferred decision. If accepted canon will reference a future
     ADR by number, reserve the number via the allocator (ADR-0006 §3). -->

---

## Action Items (research/planning)

1. [ ] <sign-off / ratification items first, then follow-on work>

<!-- On acceptance, add:

## Review Notes (<work-id or "review">)

**Reviewed:** <date> · **Verdict:** Accepted [with amendments] / Rejected (<reason>) · **Reviewer:** <human who stamped; conductor if different>

- <finding → resolution, one line each>
-->
