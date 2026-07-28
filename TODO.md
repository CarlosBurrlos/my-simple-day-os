# TODO — FIFO work queue

<!-- Protocol: see CLAUDE.md § Work queue protocol.
     - FIFO: pop from the TOP. New work appends to the BOTTOM.
     - One row per work item, CSV-shaped. Done items are DELETED (git history
       is the archive), not checked off.
     - `id` is an informal work ID (W<n>): monotonically increasing, never
       reused, NOT part of the formal ID system (docs/sequences.json).
     - `depth` points at the matching GAPS.md entry when one exists.
     - next id: W11 -->

```csv
id,name,context,blocked_by,depth
W6,just ratify,Pull-based ADR -> dictionary step; no watchers; human-triggered (ADR-0006 §5),,
W7,just audit,Read-only ledger reconciliation + DAG/cycle checks + blast-radius scoring; needs PyYAML (ask first per AGENTS.md); origin-pending IDs C2-C4 are a pre-seeded finding,,GAPS#W7
W9,Draft ADR-0004 Timer/Clock,ID reserved 2026-07-28 (named in accepted ADR-0003); time-triggered + recurring promises; tick/quantum home; K4/K5 ownership,,
W10,Draft ADR-0005 Masking & priority,ID reserved 2026-07-28 (named in accepted ADR-0003); K1-K3 + preemption + notification feed + urgency-aged alerts,,GAPS#W10
```
