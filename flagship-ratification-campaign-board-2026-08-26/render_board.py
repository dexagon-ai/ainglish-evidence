#!/usr/bin/env python3
"""Render the frozen campaign board without live calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    snapshot = json.loads((ROOT / "campaign-board.json").read_text(encoding="utf-8"))
    sealed = dict(snapshot)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("REFUSING: campaign board digest drift")
    roster = snapshot["reader_roster"]
    lines = [
        "# Flagship ratification campaign board",
        "",
        f"Live snapshot: `{snapshot['captured_at']}`. Snapshot digest: `{snapshot['content_sha256']}`.",
        "",
        f"Reader gate: **{roster['qualified_lineages']}/{roster['required_lineages']} qualified lineages; roster_ready={str(roster['roster_ready']).lower()}**. All comprehension-dependent rows remain sealed.",
        "",
        "This board separates editorial usability from empirical support. A row can be intuitive and ratified while still carrying an evidence warning.",
    ]
    lanes = []
    for row in snapshot["rows"]:
        if row["lane"] not in lanes:
            lanes.append(row["lane"])
    for lane in lanes:
        rows = [row for row in snapshot["rows"] if row["lane"] == lane]
        lines += ["", f"## {lane}", "", "| Construct | Stage | Evidence state | Next action |", "|---|---|---|---|"]
        for row in rows:
            form = (row["form"] or row["title"] or row["slug"]).replace("|", "\\|")
            gaps = list(row["missing_evidence"]) + [f"opposing:{item}" for item in row["opposing_evidence"]]
            evidence = ", ".join(gaps) or row["verdict_assessment"] or "not declared"
            lines.append(f"| `{form}` | {row['stage']} | {evidence} | {row['next_action']} |")
    lines += [
        "",
        "## Operating decision",
        "",
        "The immediate autonomous lane is deterministic price evidence, contract repair, register collision work, and recertification. The semantic carrier lane reopens only after a second distinct reader lineage passes the frozen holdout; lowering that gate would make the campaign faster but its evidence less trustworthy.",
        "",
        "The four `publication-ready-with-guards` rows are appropriate homepage examples now as explanations of distinctions. They must not be captioned as experimentally proven comprehension wins. The five `ratified-evidence-under-review` rows belong in a secondary gallery with an evidence-under-review badge.",
        "",
        "## Invariants",
        "",
    ]
    lines += [f"- {rule}" for rule in snapshot["rules"]]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"lanes": len(lanes), "rows": len(snapshot["rows"]), "snapshot_sha256": expected}, indent=2))


if __name__ == "__main__":
    main()
