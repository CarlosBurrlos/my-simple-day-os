# TODO — FIFO work queue

<!-- Protocol: see CLAUDE.md § Work queue protocol.
     - FIFO: pop from the TOP. New work appends to the BOTTOM.
     - One row per work item, CSV-shaped. Done items are DELETED (git history
       is the archive), not checked off.
     - `id` is an informal work ID (W<n>): monotonically increasing, never
       reused, NOT part of the formal ID system (docs/sequences.json).
     - `depth` points at the matching GAPS.md entry when one exists.
     - next id: W13 -->

```csv
id,name,context,blocked_by,depth
W6,just ratify,Pull-based ADR -> dictionary step; no watchers; human-triggered (ADR-0006 §5),,
W7,just audit,Read-only ledger reconciliation + DAG/cycle checks + blast-radius scoring; needs PyYAML (ask first per AGENTS.md); origin-pending ledger is a pre-seeded finding,,GAPS#W7
W11,Review ADR-0004 Timer/Clock,ADR-0006 §4 checklist; verdict in the ADR; ratify C8 + flush-family claims on acceptance,,
W12,Review ADR-0005 Masking & priority,ADR-0006 §4 checklist; verdict in the ADR; ratify K9 + K1-K3/C3 claims on acceptance; note ADR-0005 depends on ADR-0004 acceptance for clock substrate,W11,
```
