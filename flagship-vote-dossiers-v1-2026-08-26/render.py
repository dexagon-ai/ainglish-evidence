#!/usr/bin/env python3
"""Render the vote-dossier snapshot."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    data = json.loads((ROOT / "dossiers.json").read_text(encoding="utf-8"))
    lines = [
        "# Flagship vote dossiers v1", "",
        f"Captured `{data['captured_at']}`. Digest: `{data['content_sha256']}`.", "",
        data["claim"], "",
        f"Current outcome: **{data['summary']['dossier_ready_for_independent_ballot']}/{data['summary']['candidates']}** active catalogue candidates are dossier-ready, and **{data['summary']['dexagon_votes_routed']}** Dexagon ballots are freshly routed.", "",
        "| Candidate | Stage | Verdict | Ready | Exact blockers |", "|---|---|---|---:|---|",
    ]
    for row in data["dossiers"]:
        title = (row["title"] or row["slug"]).replace("|", "\\|")
        blockers = "; ".join(row["blockers"]) or "none"
        lines.append(f"| `{title}` | {row['stage']} | {row['verdict_assessment']} | {'yes' if row['dossier_ready_for_independent_ballot'] else 'no'} | {blockers} |")
    lines += ["", "## Ballot boundary", "", "A dossier becomes useful only after the live evidence contract is complete and the API opens a ballot. The eventual voter must reason publicly, preserve adverse evidence, disclose linkage, and abstain after verifying the row. This packet never converts Dexagon's author or measurer role into an independent vote.", ""]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"rendered {len(data['dossiers'])} dossiers")


if __name__ == "__main__":
    main()

