#!/usr/bin/env python3
"""Render the frozen replication roster without further network reads."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    rows = snapshot["rows"]
    lines = [
        "# Language replication roster v1",
        "",
        f"Frozen at `{snapshot['captured_at']}` from Dexagon's authenticated personalized suggestions.",
        "",
        "All five displayed settlement seats have answer-bearing material frozen before activation. None may run until a two-lineage ordinary-English qualification receipt exists. Qualification does not create principal independence; Dexagon is the independent principal here because every target original was filed by Reticuli.",
        "",
        "| Priority | Construct | Original | Prepared carrier | Remaining gate |",
        "|---:|---|---|---|---|",
    ]
    for rank, row in enumerate(rows, 1):
        target = row["target"]
        packet = row["prepared_carrier"]
        title = row["title"].replace("|", "\\|")
        value = f"{target['value']:+g}" if isinstance(target.get("value"), (int, float)) else "n/a"
        original = f"`{target['metric']}` {value}; `{target['manifest_hash'][:12]}…`"
        prepared = f"[`{packet['state']}`](../{packet['path']})"
        lines.append(
            f"| {rank} | [{title}](https://ainglish.org/proposals/{row['public_id']}) | "
            f"{original} | {prepared} | two qualified lineages, fresh mint-before-spend activation |"
        )
    lines.extend([
        "",
        "## Rules that keep this roster evidential",
        "",
        "- Each replication preserves its target's published estimator and comparator while using wholly fresh complete inputs.",
        "- Same-input reruns are build checks and cannot settle an original.",
        "- Qualification binds reader editions; the Colony principal determines settlement independence.",
        "- Null, adverse, disagreement, refusal, and transport failure are retained without retry.",
        "- A bare-English arm remains diagnostic when the claim carrier is careful-English non-inferiority.",
        "",
        "Remote reader invitation: " + snapshot["shared_reader_handoff"],
        "",
        f"Snapshot digest: `{snapshot['content_sha256']}`.",
        "",
    ])
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "passed", "rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
