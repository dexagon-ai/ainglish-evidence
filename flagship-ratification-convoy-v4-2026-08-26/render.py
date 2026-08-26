#!/usr/bin/env python3
"""Render the captured convoy as a concise human-readable board."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    data = json.loads((ROOT / "convoy.json").read_text(encoding="utf-8"))
    lines = [
        "# Flagship ratification convoy v4",
        "",
        f"Captured `{data['captured_at']}`. Digest: `{data['content_sha256']}`.",
        "",
        f"Reader gate: **{data['reader_gate']['qualified_lineages']}/{data['reader_gate']['required_lineages']} lineages**; next prospect: **{data['reader_gate']['next_candidate']}**.",
        f"Production: **{data['production']['catalogue_entries']} catalogue entries**; `/road-to-register` HTTP **{data['production']['road_to_register_http_status']}**.",
        "",
        "This is a dependency ledger, not a lifecycle or measurement substitute. Re-read every live row before a write.",
        "",
    ]
    for lane in dict.fromkeys(row["lane"] for row in data["rows"]):
        lines += [f"## {lane}", "", "| Construct | Stage | Evidence | Owner | Next action |", "|---|---|---|---|---|"]
        for row in [item for item in data["rows"] if item["lane"] == lane]:
            evidence = ", ".join(row["missing_evidence"] + [f"unresolved:{value}" for value in row["unresolved_evidence"]] + [f"opposing:{value}" for value in row["opposing_evidence"]]) or "declared work complete"
            title = (row["title"] or row["slug"]).replace("|", "\\|")
            lines.append(f"| `{title}` | {row['stage']} | {evidence} | {row['owner_class']} | {row['next_action']} |")
        lines.append("")
    lines += ["## Invariants", ""] + [f"- {rule}" for rule in data["rules"]] + [""]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"rendered {len(data['rows'])} rows")


if __name__ == "__main__":
    main()

