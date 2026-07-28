# SPEC-XXXX: <Subsystem / Domain Name>

<!-- Allocate XXXX via `just next-id SPEC`. Lift-and-shift template: everything
     here is generic; angle-bracket slots are per-instance. -->

**Version:** 0.1.0 <!-- semver: Law change = MAJOR, new Limit/Lever = MINOR, editorial = PATCH -->
**Status:** Draft <!-- Draft → Frozen; a Frozen version is immutable — changes bump the version -->
**Date:** <YYYY-MM-DD>
**Origin:** <ADR(s) whose accepted policies this SPEC formalizes>

---

## Purpose & boundary

<What this SPEC formalizes, and — per the POLICY/SPEC division — only what the
POLICY dictionary *cannot* capture: strict technical definitions required to
uphold the policies' ability to govern. Abstract intent stays in POLICY.md;
if a rule is fully expressible as a dictionary entry, it does not belong here.>

## Registry

<!-- The manifest of policy segments this SPEC governs. One row per policy ID.
     POLICY.md points down at this SPEC; this table points back up. The union
     of all Frozen SPEC registries is the formal ID ledger (reconcilable
     against docs/sequences.json). IDs are permanent: never renumber/reuse. -->

| Policy ID | Kind  | Name                    | Origin ADR | Formalized in |
| --------- | ----- | ----------------------- | ---------- | ------------- |
| L<N>      | Law   | <short name>            | ADR-XXXX   | §<n>          |
| C<N>      | Limit | <short name>            | ADR-XXXX   | §<n>          |
| K<N>      | Lever | <short name>            | ADR-XXXX   | §<n>          |

## Normative language

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted
as in RFC 2119. Laws formalize as MUST/MUST NOT, Limits as bounded MUSTs with
declared constants, Levers as MAY/SHOULD with declared defaults and ranges.

## Formal definitions

<!-- One section per registry row, in registry order. Each section: the policy's
     technical grounding — data shapes, state machines, invariants, constants,
     protocol steps. Cite the policy ID in the heading. -->

### §1. L<N> — <name>

<normative technical definition>

## Conformance

<What it means for an implementation to conform to this SPEC; how a violation
of each policy is detected/observed.>

## Changelog

| Version | Date         | Change                       |
| ------- | ------------ | ---------------------------- |
| 0.1.0   | <YYYY-MM-DD> | Initial draft from ADR-XXXX. |
