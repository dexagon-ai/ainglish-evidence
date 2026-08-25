#!/usr/bin/env python3
"""Join frozen candidates and classifier readings into a review atlas."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    candidates = json.loads((ROOT / "candidates.json").read_text())
    readings = json.loads((ROOT / "classifier-results.json").read_text())
    by_id = {row["pair_id"]: row for row in readings["results"]}
    rows = []
    for candidate in candidates["candidates"]:
        result = by_id[candidate["pair_id"]]
        rows.append({
            "pair_id": candidate["pair_id"],
            "left": candidate["left"]["slug"],
            "right": candidate["right"]["slug"],
            "routing": candidate["routing"],
            "classifiers": result["readings"],
            "model_agreement": result["model_agreement"],
            "agreed_label": result["agreed_label"],
            "review_required": True,
            "asserted_relation": None,
        })
    counts = Counter(row["agreed_label"] or "disagreement_or_error" for row in rows)
    payload = {
        "kind": "dexagon.ainglish.semantic-conflict-atlas.v1",
        "candidate_packet_sha256": candidates["content_sha256"],
        "classifier_results_sha256": readings["content_sha256"],
        "summary": {"pairs": len(rows), "labels": dict(sorted(counts.items()))},
        "interpretation": "Every row remains review_required. Model agreement is not a register relation or governance decision.",
        "rows": rows,
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    (ROOT / "atlas.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    lines = [
        "# Semantic conflict and duplication atlas", "",
        f"Review-only atlas over `{len(rows)}` deterministically routed pairs from "
        f"`{candidates['population']['published_language_surfaces']}` language surfaces.", "",
        "Two local model families independently labelled each pair. Agreement is a triage signal,",
        "not an asserted duplicate, conflict, or supersession edge. Every row remains", 
        "`review_required: true` and `asserted_relation: null`.", "",
        f"Atlas digest: `{payload['content_sha256']}`.", "", "## Summary", "",
    ]
    for label, count in sorted(counts.items()):
        lines.append(f"- `{label}`: {count}")
    current_agreed = []
    for candidate in candidates["candidates"]:
        result = by_id[candidate["pair_id"]]
        if (
            candidate["left"]["stage"] != "superseded"
            and candidate["right"]["stage"] != "superseded"
            and not candidate["routing"]["declared_relations"]
            and result["model_agreement"]
        ):
            current_agreed.append(
                {
                    "label": result["agreed_label"],
                    "left": candidate["left"]["slug"],
                    "right": candidate["right"]["slug"],
                    "priority": candidate["routing"]["priority"],
                    "min_confidence": min(
                        reading["confidence"] for reading in result["readings"]
                        if reading["status"] == "ok"
                    ),
                }
            )
    current_agreed.sort(key=lambda row: (-row["priority"], row["left"], row["right"]))
    lines += [
        "", "## Current-current undeclared review cards", "",
        "These are the agreed cards most likely to need a human or maintainer decision. They are "
        "still routing suggestions, not asserted relations.", "",
        "| Label | Left | Right | Priority | Min confidence |", "|---|---|---|---:|---:|",
    ]
    for row in current_agreed:
        lines.append(
            f"| `{row['label']}` | `{row['left']}` | `{row['right']}` | "
            f"{row['priority']:.4f} | {row['min_confidence']:.2f} |"
        )
    lines += ["", "## Highest-priority agreed review cards", "",
              "| Label | Left | Right | Lexical/form priority |", "|---|---|---|---:|"]
    agreed = [row for row in rows if row["model_agreement"]]
    agreed.sort(key=lambda row: (-row["routing"]["priority"], row["pair_id"]))
    for row in agreed[:40]:
        lines.append(f"| `{row['agreed_label']}` | `{row['left']}` | `{row['right']}` | {row['routing']['priority']:.4f} |")
    lines += [
        "", "## Reproduce", "", "```bash", "python build_candidates.py",
        "python run_classifiers.py", "python summarize.py", "python verify.py", "```", "",
        "`verify.py` recomputes every content pin and refuses if any review card has become an "
        "asserted semantic edge.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines))
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
