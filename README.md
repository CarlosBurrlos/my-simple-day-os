# my-day-os

An operating system for a personal day: instead of scheduling CPU and managing memory/devices, it schedules **attention** and manages calendar, email, and tasks. Work is modeled as a **deli ticket** — a future promise of completion.

Currently in the planning phase — see `AGENTS.md` for the entry point, then `Overview.md` and `docs/adr/`.

## Architecture at a glance

### The rings

Privilege is concentric, like an OS ring diagram: the innermost ring owns truth; everything outside it acts only through messages and leases.

```mermaid
flowchart TB
    subgraph world["🌍 Real world — devices: email · calendar · Notion HID"]
        subgraph ring3["Ring 3 — sandboxed user space"]
            views["Views — Web · Obsidian · Notion<br/>read + submit intents, never write truth"]
            workers["Workers — agent · automation · human<br/>act only within a capability lease"]
            subgraph ring0["Ring 0 — privileged core"]
                cap["Capture layer (mechanism)<br/>record before reason"]
                med["Mediator (policy)<br/>adjudicate · sole writer of truth"]
                disp["Dispatcher<br/>run queue · gates · leases"]
                sor[("SQLite<br/>SoR · WAL journal · audit log")]
            end
        end
    end
    views -- "intents (messages)" --> med
    disp -- "capability lease" --> workers
    workers -- "step results (messages)" --> med
    med -- "sole writer" --> sor
    med -. "confirmed, leased actions only" .-> world
```

The firewall rules are Laws (see `docs/POLICY.md`): only ring 0 writes the system of record (L1), everything is recorded before any judgment runs on it (L2), all edits travel as messages rather than shared writes (L4), and nothing irreversible happens without an explicit capability plus confirmation (L5).

### Life of a promise

```mermaid
flowchart LR
    ev["Event arrives<br/>(interrupt)"] --> capt["Capture<br/>dedupe · record · audit"]
    capt --> adj["Mediator adjudicates<br/>ticket issued"]
    adj --> q["Run queue<br/>priority · admission"]
    q --> w["Worker executes<br/>agent / automation / human"]
    w --> j["Journal<br/>intent → attempted → confirmed"]
    j --> done["Done — surfaces when<br/>urgency says so, not when finished"]
```

Deeper dives: `docs/adr/ADR-0001` (backbone), `ADR-0002` (devices & latency), `ADR-0003` (execution & orchestration), and `docs/POLICY.md` (the kernel contract: Laws, Limits, Levers).

## AI co-authoring

This project is developed with AI assistance (Anthropic's Claude).
