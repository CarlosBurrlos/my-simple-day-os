# GAPS — depth partner to TODO.md

<!-- Protocol: see CLAUDE.md § Work queue protocol.
     Each entry expands a TODO.md work item (matched by work ID) with the
     detail the one-line queue row can't hold: what the gap actually is,
     why it matters, and what "done" looks like. Entries are deleted when
     their work item pops and completes. Not every queue row needs an
     entry — only the ones with real depth. -->

## W1 — Review ADR-0003

The review has no defined finish line yet (no ADR lifecycle vocabulary — see
W2). For this review, the working definition of done:

- Verdict recorded in ADR-0003 itself (status change + review notes), so the
  outcome never has to be re-derived from memory.
- Each proposed policy ID (L9–L11, C5–C7, K6–K8) checked for: a kind
  (Law/Limit/Lever), a stated violation condition, and an origin section.
- No conflicts with accepted canon (L1–L8); anything deferred is explicitly
  named (ADR-0004 timer/clock, ADR-0005 masking/priority ratifying K1–K3).

## W2 — Meta-ADR (document architecture)

Collects the doctrine agreed in conversation but not yet written down:

- **ADR lifecycle states**: Proposed → Accepted / Rejected → Superseded; who
  moves them; what "opening/closing a review" procedurally means.
- **Amendment story**: IDs are permanent, so changing an accepted ADR means a
  new ADR that supersedes it — currently implied, nowhere written.
- **Ratify/audit doctrine**: pull-based `just ratify` (no watchers; machine
  writes terminate in a human), read-only `just audit`.
- **Blast-radius scoring** + risk-appetite Lever for review ordering.
- **WIP cap**: at most ~2 Proposed ADRs open at a time; soft size cap of
  ~5–6 proposed policy IDs per ADR (ADR-0003's 9 is the ceiling case).
- **Canon location**: stays in `docs/` until a second consumer exists.
- **Freeze gate**: no SPEC may move Draft → Frozen before `just audit` (W7)
  exists and passes — a Frozen version claims immutability, so it must not
  bake in unaudited drift.
- **Phase exit criteria**: one sentence defining when planning ends and
  implementation starts (e.g., ADR-0003 accepted + meta-ADR accepted →
  walking skeleton begins). The WIP cap bounds breadth; this bounds depth.
- **TODO/GAPS vs. audit authority**: TODO.md is *intent* (what was chosen
  and queued); audit output is *state* (what canon says is unresolved).
  Neither overrides the other; the meta-ADR draws the boundary.

## W3 — ADR frontmatter schema

Activation mapping (which policy IDs an ADR proposes) lives only in prose
today. A YAML frontmatter block per ADR — `id`, `status`, `proposes`,
`depends-on`, `supersedes` — is the enabler for `just audit`, blast-radius
scoring, and any future digest: it converts prose into a queryable graph.
Also solves the deferred-decision register gap: ADR-0004/0005 currently exist
only as inline mentions inside ADR-0003, with nothing tracking the IOU.

## W5 — TEMPLATE-ADR.md

Mirrors the SPEC registry shape (proposed policy IDs as a table), pre-normative
language. Two sections mature RFC processes (PEPs, Rust RFCs, IETF) mandate
that ours must too:

- **Motivation** — why this change, what breaks without it.
- **Alternatives considered** — what was rejected and why; the only thing that
  makes "why not X?" answerable months later.

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
