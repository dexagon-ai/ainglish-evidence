#!/usr/bin/env python3
"""Attach lexical-neighbour receipts to the manually screened candidate census."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TOKEN = re.compile(r"[a-z0-9]+")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def words(value: str) -> set[str]:
    return set(TOKEN.findall(value.lower()))


def main() -> None:
    source = json.loads((ROOT / "candidates.json").read_text())
    register = json.loads((ROOT / "register-snapshot.json").read_text())
    rows = []
    for candidate in source["candidates"]:
        candidate_words = words(" ".join((candidate["problem"], candidate["proposed_form"], candidate["example"])))
        neighbors = []
        for proposal in register["proposals"]:
            proposal_words = words(" ".join(str(proposal.get(key) or "") for key in ("title", "form")))
            union = candidate_words | proposal_words
            score = len(candidate_words & proposal_words) / len(union) if union else 0
            neighbors.append({
                "score": round(score, 4),
                "slug": proposal["slug"],
                "stage": proposal["stage"],
                "title": proposal["title"],
                "form": proposal["form"],
            })
        row = dict(candidate)
        row["editorial_score"] = sum(candidate["checks"])
        row["top_lexical_neighbors"] = sorted(neighbors, key=lambda item: (-item["score"], item["slug"]))[:5]
        rows.append(row)
    payload = {
        "kind": "dexagon.ainglish.language-gap-census.v1",
        "register_snapshot_sha256": register["content_sha256"],
        "population": register["count"],
        "selected": [row["id"] for row in rows if row["decision"] == "select"],
        "candidates": rows,
        "claim_boundary": "Lexical similarity is a discovery aid. Manual semantic-neighbour review controls the deduplication decision.",
        "model_calls": 0,
        "governance_writes": 0,
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    (ROOT / "census.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"candidates": len(rows), "selected": payload["selected"], "content_sha256": payload["content_sha256"]}))


if __name__ == "__main__":
    main()
