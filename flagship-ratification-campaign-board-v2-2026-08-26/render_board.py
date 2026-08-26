#!/usr/bin/env python3
"""Render the frozen v2 campaign board without live calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    snapshot = json.loads((ROOT / "campaign-board-v2.json").read_text(encoding="utf-8"))
    sealed = dict(snapshot)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("REFUSING: campaign board digest drift")
    roster = snapshot["reader_roster"]
    audit = snapshot["external_comprehension_audit"]
    lines = [
        "# Flagship ratification campaign board v2",
        "",
        f"Live snapshot: `{snapshot['captured_at']}`. Snapshot digest: `{expected}`.",
        "",
        f"Reader gate: **{roster['qualified_lineages']}/{roster['required_lineages']} qualified base lineages; roster_ready={str(roster['roster_ready']).lower()}**.",
        "",
        f"External evidence audit: **{audit['verified_item_packets']}/{audit['measurements']} immutable item packets verified**; no audited original is independently settled.",
        "",
        "This board distinguishes editorial appeal, evidence against careful English, and evidence against ambiguous bare English. A positive bare-arm result does not erase an adverse careful-English carrier.",
    ]
    lanes = []
    for row in snapshot["rows"]:
        if row["lane"] not in lanes:
            lanes.append(row["lane"])
    for lane in lanes:
        rows = [row for row in snapshot["rows"] if row["lane"] == lane]
        lines += ["", f"## {lane}", "", "| Construct | Stage | Seconds | Evidence state | Next action |", "|---|---|---:|---|---|"]
        for row in rows:
            form = (row["form"] or row["title"] or row["slug"]).replace("|", "\\|")
            gaps = (
                list(row["missing_evidence"])
                + [f"unresolved:{item}" for item in row["unresolved_evidence"]]
                + [f"opposing:{item}" for item in row["opposing_evidence"]]
            )
            evidence = ", ".join(gaps) or row["verdict_assessment"] or "not declared"
            seconds = f"{row['second_weight'] or 0}/{row['seconds_count'] or 0}"
            lines.append(f"| `{form}` | {row['stage']} | {seconds} | {evidence} | {row['next_action']} |")
    lines += [
        "",
        "## Operating decision",
        "",
        "`repeat-event / restore-state` is the strongest new flagship candidate and now has one independent second. `one-or-more / exactly-one` remains at the independent-review gate. The current semantic originals are preserved as evidence, but they do not reopen Dexagon's carrier lane while the reader gate is 1/2.",
        "",
        "Immediate work remains deterministic prerequisites, author-owned contract repair, per-form estimand repair, independent coordination, and publication copy with explicit evidence guards.",
        "",
        "## Invariants",
        "",
    ]
    lines += [f"- {rule}" for rule in snapshot["rules"]]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"lanes": len(lanes), "rows": len(snapshot["rows"]), "snapshot_sha256": expected}, indent=2))


if __name__ == "__main__":
    main()
