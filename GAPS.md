# GAPS — depth partner to TODO.md

<!-- Protocol: see CLAUDE.md § Work queue protocol.
     Each entry expands a TODO.md work item (matched by work ID) with the
     detail the one-line queue row can't hold: what the gap actually is,
     why it matters, and what "done" looks like. Entries are deleted when
     their work item pops and completes. Not every queue row needs an
     entry — only the ones with real depth. -->

## W7 — just audit

Read-only validator over the canon:

- Two-way ledger reconciliation: union of Frozen SPEC registries vs.
  POLICY.md dictionary vs. `docs/sequences.json` high-water marks.
- Layered-DAG check: ADR → POLICY → SPEC edges, cycle detection.
- Blast-radius output: per-ADR risk score (severity-weighted via the
  Law=MAJOR / Limit=MINOR semver mapping, counting touched policy IDs).
- JSON graph output for agent consumption.

Blocked on W3: without frontmatter there is nothing machine-readable to audit.

