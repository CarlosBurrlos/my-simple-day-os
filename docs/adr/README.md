# ADR index & frontmatter schema

Chartered by ADR-0006 §5: every ADR carries a machine-readable YAML
frontmatter block as the substrate for `just audit`, blast-radius scoring,
and digests. **Prose remains authoritative for humans; frontmatter drift
from prose is an audit finding.**

## Schema

The block is the first thing in the file, delimited by `---`:

```yaml
---
id: ADR-XXXX          # allocator-issued, permanent
title: <short title>
status: Proposed      # Proposed | Accepted | Rejected | Superseded
date: YYYY-MM-DD      # drafted
accepted: YYYY-MM-DD  # present only once stamped (or rejected:)
proposes: [L9, C5]    # policy IDs this ADR originates (empty list if none)
depends-on: [ADR-0001]
supersedes: []        # ADRs this one replaces (each must be named in prose too)
defers-to: []         # ADRs this one explicitly defers work to
---
```

Rules:

- `proposes` lists only IDs this ADR *originates* — one origin per policy ID
  across the whole corpus (audit reconciles this against POLICY.md).
- `depends-on` / `supersedes` / `defers-to` reference ADR IDs only; edges
  must be acyclic (audit checks).
- Lifecycle per ADR-0006 §2; `status` here must match the prose header.

## Index

| ID | Title | Status | Proposes |
| --- | --- | --- | --- |
| ADR-0001 | Backbone (System of Record) | Accepted | L1, L3 |
| ADR-0002 | Device Taxonomy & Latency Hierarchy | Accepted | L2, L4–L8, C1 |
| ADR-0003 | Execution & Orchestration Model | Accepted | L9–L11, C5–C7, K6–K8 |
| ADR-0004 | Timer / Clock device | *reserved* | — |
| ADR-0005 | Masking & priority policy | *reserved* | K1–K3 expected |
| ADR-0006 | Document Architecture & Governance (meta) | Accepted | — |

## Origin-pending policy IDs

POLICY.md stubs whose originating ADR is not yet assigned — a pre-seeded
audit finding, to be claimed by ADR-0004/0005 or a successor:

- **The flush family** — flush cadence (K4), batch size (K5), the in-flight
  write ceiling (C2), and the unconfirmed-action age limit (C4): all arise
  from the ADR-0002 write-back model but were never formally proposed by it.
  Expected owner: ADR-0004 (clock/flush territory), claiming the family in
  one act.
- **The WIP cap on active tickets (C3)** — scheduling territory; owner TBD
  (ADR-0004 or ADR-0005).
- **Context-switch threshold (K1), masking windows (K2), triage
  aggressiveness (K3)** — expected from ADR-0005.
