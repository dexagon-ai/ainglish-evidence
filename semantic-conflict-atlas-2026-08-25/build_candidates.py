#!/usr/bin/env python3
"""Freeze review-only semantic relation candidates from the live public register."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
MAX_PAIRS = 180
STOP = {
    "a", "an", "and", "as", "at", "be", "by", "does", "for", "from", "in", "is",
    "it", "of", "on", "or", "say", "state", "that", "the", "this", "to", "whether",
    "which", "with", "mark", "marks", "english", "ainglish",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def words(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)
        if len(token) > 1 and token not in STOP
    }


def trigrams(value: str) -> set[str]:
    normalized = " ".join(re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE))
    return {normalized[i:i + 3] for i in range(max(0, len(normalized) - 2))}


def ratio(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 0.0


def surface(row: dict) -> dict:
    return {
        "slug": row["slug"],
        "public_id": row.get("public_id"),
        "title": row.get("title") or "",
        "form": row.get("form") or "",
        "english_mapping": row.get("english_mapping") or "",
        "constraints": row.get("constraints") or "",
        "stage": row.get("stage"),
        "supersedes": row.get("supersedes"),
        "superseded_by": row.get("superseded_by"),
        "duplicate_of": row.get("duplicate_of"),
    }


def declared(left: dict, right: dict) -> list[str]:
    found = []
    for source, target, label in ((left, right, "left"), (right, left, "right")):
        for field in ("supersedes", "superseded_by", "duplicate_of"):
            if source.get(field) == target["slug"]:
                found.append(f"{label}.{field}")
    return sorted(found)


def main() -> None:
    client = AinglishClient(use_env=False)
    rows = [surface(row) for row in client.iter_proposals(page_size=200) if row.get("kind") != "protocol"]
    rows.sort(key=lambda row: row["slug"])
    candidates = []
    for index, left in enumerate(rows):
        left_title = words(left["title"] + " " + left["form"])
        left_form = trigrams(left["form"] or left["title"])
        for right in rows[index + 1:]:
            right_title = words(right["title"] + " " + right["form"])
            title_score = ratio(left_title, right_title)
            form_score = ratio(left_form, trigrams(right["form"] or right["title"]))
            relations = declared(left, right)
            shared = sorted(left_title & right_title)
            if not relations and title_score < 0.18 and form_score < 0.35:
                continue
            priority = max(title_score, form_score) + (1.0 if relations else 0.0)
            candidates.append({
                "pair_id": hashlib.sha256((left["slug"] + "\n" + right["slug"]).encode()).hexdigest()[:16],
                "left": left,
                "right": right,
                "routing": {
                    "title_jaccard": round(title_score, 6),
                    "form_trigram_jaccard": round(form_score, 6),
                    "shared_title_form_terms": shared,
                    "declared_relations": relations,
                    "priority": round(priority, 6),
                },
                "review_required": True,
                "asserted_relation": None,
            })
    candidates.sort(key=lambda row: (-row["routing"]["priority"], row["pair_id"]))
    candidates = candidates[:MAX_PAIRS]
    payload = {
        "kind": "dexagon.ainglish.semantic-conflict-candidates.v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "https://ainglish.org/api/v1/proposals",
        "population": {"published_language_surfaces": len(rows)},
        "method": {
            "maximum_pairs": MAX_PAIRS,
            "title_form_jaccard_floor": 0.18,
            "form_trigram_jaccard_floor": 0.35,
            "declared_edges_always_included": True,
            "meaning": "Deterministic routing only. Every candidate remains review_required and no relation is asserted.",
        },
        "candidates": candidates,
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    (ROOT / "candidates.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "population": len(rows), "candidates": len(candidates),
        "declared": sum(bool(row["routing"]["declared_relations"]) for row in candidates),
        "content_sha256": payload["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
