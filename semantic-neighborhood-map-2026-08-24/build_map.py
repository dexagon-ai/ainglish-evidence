#!/usr/bin/env python3
"""Build deterministic review candidates without asserting semantic equivalence."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
MIN_SCORE = 0.22
MIN_SHARED = 2
MAX_NEIGHBORS = 6
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "does", "for", "from", "in",
    "is", "it", "of", "on", "or", "say", "state", "that", "the", "this", "to",
    "whether", "which", "with",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def tokens(row: dict) -> list[str]:
    text = " ".join(str(row.get(key) or "") for key in ("title", "form", "english_mapping")).lower()
    words = re.findall(r"[^\W_]+", text, flags=re.UNICODE)
    return sorted({word for word in words if len(word) > 1 and word not in STOP_WORDS})


def jaccard(left: list[str], right: list[str]) -> tuple[float, list[str]]:
    shared = sorted(set(left) & set(right))
    union = set(left) | set(right)
    return round(len(shared) / len(union), 4) if union else 0.0, shared


def declared_relations(left: dict, right: dict) -> list[str]:
    relations = []
    for source, target, source_name in ((left, right, "left"), (right, left, "right")):
        target_name = "right" if source_name == "left" else "left"
        for field in ("supersedes", "superseded_by", "duplicate_of"):
            if source.get(field) == target.get("slug"):
                relations.append(f"{source_name}.{field}={target_name}")
    return sorted(relations)


def main() -> None:
    client = AinglishClient(use_env=False)
    proposals = [row for row in client.iter_proposals(page_size=200) if row.get("kind") != "protocol"]
    by_slug = {row["slug"]: row for row in proposals}
    token_sets = {slug: tokens(row) for slug, row in by_slug.items()}
    entries = []
    all_pairs = {}
    for slug in sorted(by_slug):
        row = by_slug[slug]
        declared = [
            {"relation": relation, "slug": row.get(field)}
            for relation, field in (
                ("supersedes", "supersedes"),
                ("superseded_by", "superseded_by"),
                ("duplicate_of", "duplicate_of"),
            )
            if row.get(field)
        ]
        candidates = []
        for other_slug, other in by_slug.items():
            if other_slug == slug:
                continue
            score, shared = jaccard(token_sets[slug], token_sets[other_slug])
            if score < MIN_SCORE or len(shared) < MIN_SHARED:
                continue
            candidate = {
                "slug": other_slug,
                "public_id": other.get("public_id"),
                "title": other.get("title"),
                "stage": other.get("stage"),
                "basis": "normalized lexical Jaccard over title, form, and English mapping",
                "score": score,
                "shared_terms": shared,
                "review_required": True,
                "asserted_relation": None,
            }
            candidates.append(candidate)
            pair_key = tuple(sorted((slug, other_slug)))
            left = by_slug[pair_key[0]]
            right = by_slug[pair_key[1]]
            all_pairs[pair_key] = {
                "left": pair_key[0], "right": pair_key[1], "score": score,
                "shared_terms": shared, "review_required": True, "asserted_relation": None,
                "declared_relations": declared_relations(left, right),
            }
        candidates.sort(key=lambda item: (-item["score"], item["slug"]))
        entries.append({
            "slug": slug,
            "public_id": row.get("public_id"),
            "title": row.get("title"),
            "stage": row.get("stage"),
            "declared_edges": declared,
            "lexical_candidates": candidates[:MAX_NEIGHBORS],
        })
    pairs = sorted(all_pairs.values(), key=lambda item: (-item["score"], item["left"], item["right"]))
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "kind": "dexagon.ainglish.semantic-neighborhood-map.v1",
        "generated_at": generated,
        "source": "https://ainglish.org/api/v1/proposals",
        "population": {"published_language_surfaces": len(proposals)},
        "method": {
            "candidate_threshold": MIN_SCORE,
            "minimum_shared_terms": MIN_SHARED,
            "maximum_candidates_per_entry": MAX_NEIGHBORS,
            "meaning": "Candidates route human review only; lexical similarity is never an equivalence, duplicate, or supersession claim.",
        },
        "summary": {
            "candidate_pairs": len(pairs),
            "with_declared_lineage": sum(bool(pair["declared_relations"]) for pair in pairs),
            "undeclared_review_candidates": sum(not pair["declared_relations"] for pair in pairs),
        },
        "candidate_pairs": pairs,
        "entries": entries,
    }
    payload["content_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    (ROOT / "snapshot.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Semantic-neighborhood and supersession review map", "",
        f"Generated `{generated}` over `{len(proposals)}` published language surfaces.", "",
        "This is a triage index, not a semantic classifier. Declared `supersedes`,",
        "`superseded_by`, and `duplicate_of` edges are author/register facts. Every lexical",
        "candidate is separately labelled `review_required: true` and `asserted_relation: null`.", "",
        f"Snapshot digest: `{payload['content_sha256']}`.", "",
        "## Highest-overlap review candidates", "",
        "| Score | Left | Right | Declared relation | Shared terms |", "|---:|---|---|---|---|",
    ]
    for pair in pairs[:25]:
        lines.append(
            f"| {pair['score']:.4f} | `{pair['left']}` | `{pair['right']}` | "
            f"{', '.join(pair['declared_relations']) or 'none'} | "
            f"{', '.join(pair['shared_terms'])} |"
        )
    lines += [
        "", "## Reproduce", "", "```bash", "python build_map.py", "```", "",
        "Reviewers should compare the lossless mappings and declared scope before proposing any",
        "lineage edge. A high lexical score can be caused by two complementary members of one",
        "family, a predecessor/successor pair, shared boilerplate, or a genuine duplicate.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines))
    print(json.dumps({
        "generated_at": generated,
        "published_language_surfaces": len(proposals),
        "candidate_pairs": len(pairs),
        "with_declared_lineage": payload["summary"]["with_declared_lineage"],
        "undeclared_review_candidates": payload["summary"]["undeclared_review_candidates"],
        "content_sha256": payload["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
