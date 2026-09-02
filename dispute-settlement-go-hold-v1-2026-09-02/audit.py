#!/usr/bin/env python3
"""Audit balance, held-out consequence wording, and exact-pair disjointness."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
SLUG = "go-unless-no-t-hold-until-yes-say-what-the-addressee-s-silen"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def get_json(url: str):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


def prior_pairs() -> tuple[set[tuple[str, str]], list[dict]]:
    proposal = get_json(f"https://ainglish.org/api/v1/proposals/{SLUG}")
    pairs: set[tuple[str, str]] = set()
    sources = []
    for measurement in proposal.get("measurements", []):
        if measurement.get("metric") != "comprehension_accuracy_delta":
            continue
        manifest_hash = measurement.get("manifest_hash")
        detail = get_json(f"https://ainglish.org/api/v1/measurements/{manifest_hash}")
        manifest = detail.get("manifest") or {}
        rows = manifest.get("items") or manifest.get("test_set")
        url = manifest.get("items_url")
        if rows is None and isinstance(url, str):
            rows = get_json(url)
        if isinstance(rows, dict):
            rows = rows.get("items")
        if not isinstance(rows, list):
            sources.append({"manifest_hash": manifest_hash, "items": "not_dereferenceable"})
            continue
        before = len(pairs)
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("english"), str) and isinstance(row.get("ainglish"), str):
                pairs.add((row["english"], row["ainglish"]))
        sources.append({"manifest_hash": manifest_hash, "items": len(rows), "new_exact_pairs": len(pairs) - before})
    return pairs, sources


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    rows = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    assert sha256(canonical(rows)).hexdigest() == index["items_sha256"]
    scientific = [row for row in rows if not row.get("calibration")]
    calibrations = [row for row in rows if row.get("calibration")]
    exact = [(row["english"], row["ainglish"]) for row in rows]
    assert len(exact) == len(set(exact))
    assert all(row["answer"] not in row["english"] and row["answer"] not in row["ainglish"] for row in scientific)
    assert all("go-unless-no" not in row["english"] and "hold-until-yes" not in row["english"] for row in scientific)
    assert all("go-unless-no" not in row["ainglish"] and "hold-until-yes" not in row["ainglish"] for row in calibrations)
    counts = Counter((row["form"], row["strata"]["response_kind"]) for row in scientific)
    old_pairs, sources = prior_pairs()
    overlaps = sorted(set(exact) & old_pairs)
    assert not overlaps, "fresh carrier overlaps a served prior complete pair"
    output = {
        "kind": "dexagon.ainglish.go-hold-dispute-carrier-audit.v1",
        "items_sha256": index["items_sha256"],
        "scientific_items": len(scientific),
        "calibration_items": len(calibrations),
        "form_response_counts": {f"{form}/{kind}": count for (form, kind), count in sorted(counts.items())},
        "unique_complete_pairs": len(set(exact)),
        "prior_exact_pairs_audited": len(old_pairs),
        "exact_pair_overlaps": len(overlaps),
        "held_out_answer_vocabulary": True,
        "construct_free_calibration": True,
        "prior_sources": sources,
        "model_calls": 0,
    }
    (ROOT / "audit.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
