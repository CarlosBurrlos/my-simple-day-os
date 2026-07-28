# GAPS — depth partner to TODO.md

<!-- Protocol: see CLAUDE.md § Work queue protocol.
     Each entry expands a TODO.md work item (matched by work ID) with the
     detail the one-line queue row can't hold: what the gap actually is,
     why it matters, and what "done" looks like. Entries are deleted when
     their work item pops and completes. Not every queue row needs an
     entry — only the ones with real depth. -->

## W3 — ADR frontmatter schema

Activation mapping (which policy IDs an ADR proposes) lives only in prose
today. A YAML frontmatter block per ADR — `id`, `status`, `proposes`,
`depends-on`, `supersedes` — is the enabler for `just audit`, blast-radius
scoring, and any future digest: it converts prose into a queryable graph.
Also solves the deferred-decision register gap: ADR-0004/0005 currently exist
only as inline mentions inside ADR-0003, with nothing tracking the IOU.

## W5 — TEMPLATE-ADR.md

Implements ADR-0006 §4's required shape: Context, Motivation, Options/
Alternatives considered, Decision, Proposed policy deltas (kind +
allocator-issued ID + violation condition), Consequences, Action items,
and a Review Notes slot filled on acceptance. Mirrors the SPEC registry
table for proposed IDs; pre-normative language.

## W10 — Draft ADR-0005 Masking & priority

Beyond ratifying K1–K3 and the notification feed, scope the
**completion ≠ notification** rule (2026-07-28 discussion):

- A completed ticket parks silently (visible in the feed); **preemption fires
  only when computed urgency crosses K1**, not on completion.
- Urgency is a deadline-driven aging function (priority grows toward the
  deadline; "alert at deadline − N min" = a timer ticket bumping priority —
  depends on the ADR-0004 clock, W9).
- The finishing agent's last act before retirement: compute/confirm the
  urgency curve + alert time, journal it, surrender its lease (L11), exit.
  Revival on review-feedback rehydrates a fresh agent from the journal
  digest (see BACKLOG: context compression / retire-revive).
- Open policy question: does work-awaiting-review age on a steeper curve
  than work-not-yet-done? (Probably yes — 5 min of review deserves a harder
  late ramp than an hour of unstarted work.)

## W7 — just audit

Read-only validator over the canon:

- Two-way ledger reconciliation: union of Frozen SPEC registries vs.
  POLICY.md dictionary vs. `docs/sequences.json` high-water marks.
- Layered-DAG check: ADR → POLICY → SPEC edges, cycle detection.
- Blast-radius output: per-ADR risk score (severity-weighted via the
  Law=MAJOR / Limit=MINOR semver mapping, counting touched policy IDs).
- JSON graph output for agent consumption.

Blocked on W3: without frontmatter there is nothing machine-readable to audit.

## W8 — Repo hygiene

- `just fmt` — files failing `just check`: `main.py`,
  `scripts/configure_remote.py`.
- Delete the `main.py` stub (`uv init` leftover; no application code yet).
