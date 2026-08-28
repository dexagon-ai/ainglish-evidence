#!/usr/bin/env python3
"""Validate sources/collisions and create a lexical review matrix."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "sources.json"
CANDIDATE_PATH = ROOT / "candidates.json"
SNAPSHOT_PATH = ROOT / "register-snapshot.json"
TARGET = ROOT / "matrix.json"
DISPOSITIONS = {"develop", "compose", "covered", "ordinary", "research_only"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sealed(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = value.get("content_sha256")
    if expected is not None:
        unsigned = dict(value)
        unsigned.pop("content_sha256")
        if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
            raise RuntimeError(f"digest drift: {path.name}")
    return value


def terms(*values: object) -> set[str]:
    return {
        token for value in values if isinstance(value, str)
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "does", "with", "that", "this", "from", "into", "every"}
    }


def similarity(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left | right else 0.0


def main() -> None:
    if TARGET.exists():
        raise SystemExit("REFUSING: matrix already exists")
    source_doc = sealed(SOURCE_PATH)
    candidate_doc = sealed(CANDIDATE_PATH)
    snapshot = sealed(SNAPSHOT_PATH)
    sources = source_doc["sources"]
    cards = candidate_doc["cards"]
    proposals = snapshot["proposals"]
    source_ids = {row["id"] for row in sources}
    if len(sources) != len(source_ids) or len(cards) != 15 or len({row["id"] for row in cards}) != 15:
        raise RuntimeError("source/card population or identity drift")
    by_slug = {row["slug"]: row for row in proposals}
    rows = []
    for card in cards:
        if card["disposition"] not in DISPOSITIONS:
            raise RuntimeError(f"{card['id']}: invalid disposition")
        missing_sources = set(card["source_ids"]) - source_ids
        if missing_sources:
            raise RuntimeError(f"{card['id']}: unknown source IDs {sorted(missing_sources)}")
        missing_collisions = set(card["declared_collision_slugs"]) - by_slug.keys()
        if missing_collisions:
            raise RuntimeError(f"{card['id']}: declared collisions absent from snapshot: {sorted(missing_collisions)}")
        if card["disposition"] == "covered" and not card["declared_collision_slugs"]:
            raise RuntimeError(f"{card['id']}: covered card lacks exact collision")
        if card["disposition"] == "develop" and card["declared_collision_slugs"]:
            raise RuntimeError(f"{card['id']}: develop card already declares collisions")
        needle = terms(card["ambiguity"], card["consequence"], card.get("candidate_form"), card.get("candidate_mapping"))
        neighbors = []
        for proposal in proposals:
            score = similarity(needle, terms(proposal.get("title"), proposal.get("form"), proposal.get("english_mapping")))
            if score:
                neighbors.append({
                    "slug": proposal["slug"], "public_id": proposal.get("public_id"), "stage": proposal.get("stage"),
                    "title": proposal.get("title"), "form": proposal.get("form"), "lexical_jaccard": round(score, 4),
                    "declared_collision": proposal["slug"] in card["declared_collision_slugs"],
                })
        neighbors.sort(key=lambda row: (-row["declared_collision"], -row["lexical_jaccard"], row["slug"]))
        rows.append({**card, "sources": [next(row for row in sources if row["id"] == source_id) for source_id in card["source_ids"]], "lexical_neighbors": neighbors[:8]})

    output = {
        "schema": "ainglish.public-source-ambiguity-matrix.v1",
        "source_snapshot_sha256": snapshot["content_sha256"],
        "source_count": len(sources),
        "card_count": len(rows),
        "disposition_counts": dict(sorted(Counter(row["disposition"] for row in rows).items())),
        "rows": rows,
        "next_development": [row["id"] for row in rows if row["disposition"] == "develop"],
        "method_boundary": [
            "Public source examples establish that an ambiguity has been noticed; they do not validate an Ainglish repair.",
            "Declared collisions are editorial review decisions verified against the snapshot.",
            "Lexical neighbours are triage only and never assert semantic duplication or novelty.",
            "Public accessibility is not treated as a public-domain copyright determination.",
            "A develop disposition is a research lead, not authorization to file a proposal.",
        ],
        "model_calls": 0,
        "gpu_calls": 0,
        "governance_writes": 0,
    }
    output["content_sha256"] = hashlib.sha256(canonical(output)).hexdigest()
    TARGET.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True, "sources": len(sources), "cards": len(rows), "dispositions": output["disposition_counts"],
        "next_development": output["next_development"], "content_sha256": output["content_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
