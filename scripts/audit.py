"""Audit the document canon: ADR frontmatter vs POLICY.md vs the ID ledger.

Chartered by ADR-0006 §5. Strictly READ-ONLY: this script never writes.
Checks:
  1. Frontmatter parses and matches prose status.
  2. One origin per policy ID across all ADR `proposes` lists.
  3. POLICY.md dictionary origins reconcile with ADR frontmatter, both ways.
  4. ADR reference edges (depends-on / supersedes / defers-to) resolve and
     the depends-on graph is acyclic.
  5. Sequence high-water marks: no ID in use >= the allocator's next value.
  6. Blast radius per ADR: severity-weighted count of proposed policy IDs
     (Law=MAJOR, Limit=MINOR, Lever=PATCH per the ADR-0006 semver coupling).
     Orders review attention; never gates anything.

Usage:
    python scripts/audit.py            # human report; exit 1 on findings
    python scripts/audit.py --json     # machine-readable graph + findings
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "docs" / "adr"
POLICY = ROOT / "docs" / "POLICY.md"
SEQUENCES = ROOT / "docs" / "sequences.json"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
PROSE_STATUS_RE = re.compile(r"^\*\*Status:\*\* (\w+)", re.MULTILINE)
POLICY_ENTRY_RE = re.compile(
    r"^- \*\*([LCK]\d+) — (.+?)\.?\*\* .*?"
    r"\*\((?:(?:value|default): .+? · )?origin: (.+?) · SPEC: (.+?)\)\*\s*$",
    re.MULTILINE,
)
BLAST_WEIGHTS = {"L": 100, "C": 10, "K": 1}  # Law=MAJOR, Limit=MINOR, Lever=PATCH


def load_adrs(findings: list[str]) -> dict[str, dict[str, Any]]:
    adrs: dict[str, dict[str, Any]] = {}
    for path in sorted(ADR_DIR.glob("ADR-*.md")):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            findings.append(f"{path.name}: missing frontmatter block")
            continue
        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            findings.append(f"{path.name}: frontmatter does not parse ({exc})")
            continue
        meta["_file"] = path.name
        prose = PROSE_STATUS_RE.search(text)
        if prose and prose.group(1) != meta.get("status"):
            findings.append(
                f"{meta.get('id', path.name)}: frontmatter status "
                f"{meta.get('status')!r} != prose status {prose.group(1)!r}"
            )
        adrs[meta["id"]] = meta
    return adrs


def load_policies(findings: list[str]) -> dict[str, dict[str, str]]:
    text = POLICY.read_text(encoding="utf-8")
    policies: dict[str, dict[str, str]] = {}
    for pid, name, origin, spec in POLICY_ENTRY_RE.findall(text):
        if pid in policies:
            findings.append(f"POLICY.md: duplicate entry for {pid}")
        policies[pid] = {"name": name, "origin": origin.strip(), "spec": spec.strip()}
    return policies


def check_origins(
    adrs: dict[str, dict[str, Any]],
    policies: dict[str, dict[str, str]],
    findings: list[str],
) -> dict[str, str]:
    proposed_by: dict[str, str] = {}
    for adr_id, meta in adrs.items():
        for pid in meta.get("proposes") or []:
            if pid in proposed_by:
                findings.append(
                    f"{pid}: proposed by both {proposed_by[pid]} and {adr_id} "
                    "(one origin per ID)"
                )
            proposed_by[pid] = adr_id

    for pid, entry in policies.items():
        origin = entry["origin"]
        if origin.startswith("ADR-"):
            if proposed_by.get(pid) != origin:
                findings.append(
                    f"{pid}: POLICY origin {origin} but frontmatter says "
                    f"{proposed_by.get(pid, 'nobody')}"
                )
            elif adrs.get(origin, {}).get("status") != "Accepted":
                findings.append(
                    f"{pid}: origin {origin} is not Accepted "
                    f"({adrs.get(origin, {}).get('status', 'missing')})"
                )
        else:
            findings.append(f"{pid}: origin pending in POLICY.md ({origin})")

    for pid, adr_id in proposed_by.items():
        if adrs[adr_id].get("status") == "Accepted" and pid not in policies:
            findings.append(
                f"{pid}: proposed by Accepted {adr_id} but absent from POLICY.md"
            )
    return proposed_by


def check_graph(adrs: dict[str, dict[str, Any]], findings: list[str]) -> None:
    for adr_id, meta in adrs.items():
        for field in ("depends-on", "supersedes", "defers-to"):
            for ref in meta.get(field) or []:
                if ref not in adrs:
                    findings.append(f"{adr_id}: {field} references missing {ref}")

    state: dict[str, int] = {}  # 0 visiting, 1 done

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 1:
            return
        if state.get(node) == 0:
            cycle = " -> ".join([*trail[trail.index(node) :], node])
            findings.append(f"depends-on cycle: {cycle}")
            return
        state[node] = 0
        for dep in adrs.get(node, {}).get("depends-on") or []:
            visit(dep, [*trail, node])
        state[node] = 1

    for adr_id in adrs:
        visit(adr_id, [])


def check_sequences(
    adrs: dict[str, dict[str, Any]],
    policies: dict[str, dict[str, str]],
    findings: list[str],
) -> None:
    stored = json.loads(SEQUENCES.read_text(encoding="utf-8"))
    used: dict[str, int] = {}
    for pid in set(policies) | {
        p for m in adrs.values() for p in (m.get("proposes") or [])
    }:
        seq, num = pid[0], int(pid[1:])
        used[seq] = max(used.get(seq, 0), num)
    for adr_id in adrs:
        used["ADR"] = max(used.get("ADR", 0), int(adr_id.split("-")[1]))
    for seq, high in used.items():
        if high >= stored.get(seq, 0):
            findings.append(
                f"sequence {seq}: ID {high} in use but allocator next is "
                f"{stored.get(seq)} — allocate via just next-id, never by hand"
            )


def blast_radius(adrs: dict[str, dict[str, Any]]) -> dict[str, int]:
    return {
        adr_id: sum(BLAST_WEIGHTS[p[0]] for p in meta.get("proposes") or [])
        for adr_id, meta in sorted(adrs.items())
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--json", action="store_true", help="machine-readable graph output"
    )
    args = parser.parse_args()

    findings: list[str] = []
    adrs = load_adrs(findings)
    policies = load_policies(findings)
    proposed_by = check_origins(adrs, policies, findings)
    check_graph(adrs, findings)
    check_sequences(adrs, policies, findings)
    blast = blast_radius(adrs)

    if args.json:
        print(
            json.dumps(
                {
                    "adrs": {
                        k: {f: v for f, v in m.items() if not f.startswith("_")}
                        for k, m in adrs.items()
                    },
                    "policies": policies,
                    "proposed_by": proposed_by,
                    "blast_radius": blast,
                    "findings": findings,
                },
                indent=2,
            )
        )
        return 1 if findings else 0

    print(f"ADRs: {len(adrs)} · policy IDs: {len(policies)}")
    print("\nBlast radius (review-attention ordering, not a gate):")
    for adr_id, score in sorted(blast.items(), key=lambda kv: -kv[1]):
        status = adrs[adr_id].get("status", "?")
        print(f"  {adr_id}  {score:>4}  ({status})")
    if findings:
        print(f"\nFINDINGS ({len(findings)}):")
        for finding in findings:
            print(f"  ✗ {finding}")
        return 1
    print("\n✓ canon consistent: origins reconcile, graph acyclic, sequences clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
