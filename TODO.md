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
W2,Meta-ADR (document architecture),Ratify/audit doctrine + ADR lifecycle + amendment story + WIP cap,,GAPS#W2
W3,ADR frontmatter schema,Machine-readable YAML block per ADR (id/status/proposes/depends-on/supersedes),W2,GAPS#W3
W4,POLICY.md dictionary migration,Restructure POLICY.md into the dictionary form agreed in the governance design,W2,
W5,TEMPLATE-ADR.md,Mirrors SPEC registry shape; pre-normative; pairs with meta-ADR,W2,GAPS#W5
W6,just ratify,Pull-based ADR -> dictionary step; no watchers; human-triggered,W2 W3,
W7,just audit,Read-only ledger reconciliation + DAG/cycle checks + blast-radius scoring,W3,GAPS#W7
W8,Repo hygiene,just fmt (unformatted files); delete main.py stub,,GAPS#W8
W9,Draft ADR-0004 Timer/Clock,Time-triggered + recurring promises; Deferred state; tick/quantum home; K4/K5 default ownership,W5,
W10,Draft ADR-0005 Masking & priority,Ratifies K1-K3 + preemption rules; ALSO notification feed + completion-vs-notification decoupling (urgency-aged alerts),W5,GAPS#W10
```
