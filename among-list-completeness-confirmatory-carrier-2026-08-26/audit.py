#!/usr/bin/env python3
"""Audit the frozen list-completeness carrier without network or model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def triples(value: object) -> set[tuple[str, str, str]]:
    found: set[tuple[str, str, str]] = set()
    if isinstance(value, dict):
        if all(isinstance(value.get(key), str) for key in ("english", "ainglish", "question")):
            found.add((value["english"], value["ainglish"], value["question"]))
        for child in value.values():
            found.update(triples(child))
    elif isinstance(value, list):
        for child in value:
            found.update(triples(child))
    return found


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text())
    sealed = dict(index)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected

    payloads: dict[str, dict[str, object]] = {}
    current_triples: set[tuple[str, str, str]] = set()
    for key, receipt in index["campaigns"].items():
        payload = json.loads((ROOT / receipt["file"]).read_text())
        payloads[key] = payload
        rows = payload["items"]
        scientific = [row for row in rows if not row.get("calibration")]
        controls = [row for row in rows if row.get("calibration")]
        assert len(scientific) == 120 and len(controls) == 8
        assert hashlib.sha256(canonical(rows)).hexdigest() == receipt["items_sha256"]
        assert len({row["id"] for row in rows}) == 128
        assert {position: sum(row["options"].index(row["answer"]) == position for row in scientific)
                for position in range(3)} == {0: 40, 1: 40, 2: 40}
        assert {probe: sum(row["strata"]["probe"] == probe for row in scientific)
                for probe in sorted({row["strata"]["probe"] for row in scientific})} == {
                    "kind_overread": 12,
                    "listed_health_overread": 24,
                    "time_overread": 12,
                    "two_enumeration_attachment": 24,
                    "unlisted_consequence": 48,
                }
        assert {domain: sum(row["strata"]["domain"] == domain for row in scientific)
                for domain in sorted({row["strata"]["domain"] for row in scientific})} == {
                    domain: 15 for domain in sorted({row["strata"]["domain"] for row in scientific})
                }
        current_triples.update(triples(payload))

    for comparator in ("careful", "bare"):
        left = payloads[f"among-others-vs-{comparator}"]["items"][:120]
        right = payloads[f"and-no-others-vs-{comparator}"]["items"][:120]
        assert [row["frame_id"] for row in left] == [row["frame_id"] for row in right]
    left = payloads["among-others-vs-bare"]["items"][:120]
    right = payloads["and-no-others-vs-bare"]["items"][:120]
    assert all(a["english"] == b["english"] and a["question"] == b["question"] for a, b in zip(left, right))
    decisive = [i for i, row in enumerate(left) if row["strata"]["probe"] == "unlisted_consequence"
                or (row["strata"]["probe"] == "two_enumeration_attachment" and row["strata"]["attachment_target"] == "marked-list")]
    assert decisive and all(left[i]["answer"] != right[i]["answer"] for i in decisive)

    overlap = 0
    scanned = 0
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text())
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            continue
        scanned += 1
        overlap += len(current_triples & triples(value))
    assert overlap == 0
    print(json.dumps({
        "status": "passed",
        "campaigns": 4,
        "scientific_rows": 480,
        "calibration_rows": 32,
        "prior_json_files_scanned": scanned,
        "prior_exact_scientific_triple_overlap": overlap,
        "model_calls": 0,
        "network_calls": 0,
        "index_sha256": index["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
