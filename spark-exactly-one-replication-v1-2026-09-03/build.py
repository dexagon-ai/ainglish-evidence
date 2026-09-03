#!/usr/bin/env python3
"""Freeze a fresh 120-item exactly-one(role) replication carrier."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SOURCE = REPO / "one-or-more-exactly-one-comprehension-carrier-2026-08-26" / "build.py"
ORIGINAL = REPO / "one-or-more-exactly-one-comprehension-carrier-v2-2026-09-03" / "items-exactly-one-careful.json"
SLUG = "one-or-more-role-exactly-one-role-does-a-reviewer-require-at"
TARGET = "31b5db3dc0a4cde2cff904bf96f76894471d5c165aa6eb742e9db7aa27ead10b"
SEED = 2026090317
ROLES = (
    ("assessor", "score the benchmark", "scored the benchmark", "benchmark", "scored"),
    ("inspector", "certify the export", "certified the export", "export", "certified"),
    ("releaser", "unlock the rollout", "unlocked the rollout", "rollout", "unlocked"),
    ("controller", "authorise the transfer", "authorised the transfer", "transfer", "authorised"),
    ("adjudicator", "resolve the objection", "resolved the objection", "objection", "resolved"),
    ("archivist", "seal the record", "sealed the record", "record", "sealed"),
    ("examiner", "validate the checksum", "validated the checksum", "checksum", "validated"),
    ("publisher", "issue the bulletin", "issued the bulletin", "bulletin", "issued"),
    ("mediator", "close the grievance", "closed the grievance", "grievance", "closed"),
    ("curator", "admit the collection", "admitted the collection", "collection", "admitted"),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def source_module():
    spec = importlib.util.spec_from_file_location("role_cardinality_source", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load role-cardinality source builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_key(row: dict) -> bytes:
    return canonical({
        "english": row["english"],
        "ainglish": row["ainglish"],
        "question": row["question"],
        "options": row["options"],
        "answer": row["answer"],
    })


def main() -> None:
    source = source_module()
    source.ROLES = ROLES
    payload, _ = source.build_campaign("exactly-one", "careful")
    payload.update({
        "kind": "dexagon.ainglish.role-cardinality-independent-replication-carrier.v1",
        "proposal_revision": SLUG,
        "replicates_hash": TARGET,
        "seed": SEED,
        "population": (
            "120 fresh operational exactly-one(role) items over ten new roles/actions and the "
            "same twelve preregistered semantic cells, plus eight construct-free calibrations"
        ),
        "aggregation": (
            "fresh-input replication of exactly-one(role) versus its complete careful-English "
            "mapping; retain absolute arms and all semantic cells"
        ),
        "freshness": (
            "No complete scientific row, English arm, Ainglish arm, item id or scenario id is "
            "reused from the target original. Question templates and the declared semantic cells "
            "are intentionally preserved to hold the estimand fixed."
        ),
    })
    for index, row in enumerate(payload["items"]):
        row["id"] = row["id"].replace("role-cardinality-", "spark-fresh-cardinality-")
        if row.get("scenario_id"):
            row["scenario_id"] = row["scenario_id"].replace("role-cardinality-", "spark-fresh-cardinality-")
        for field in ("english", "ainglish"):
            row[field] = row[field].replace("Rowan", "Juniper").replace("Sable", "Kestrel").replace("Tern", "Lumen")
        if row.get("calibration"):
            answer = row["answer"]
            token = f"spark-cardinality-calibration-{index + 1:03d}"
            row["english"] = (
                f"The routing note for {token} exists, but it does not record whether bay "
                "twenty-three is open or closed."
            )
            row["ainglish"] = (
                f"The routing note for {token} says bay twenty-three is "
                + ("open." if answer == "yes" else "closed.")
            )
            row["question"] = "Is bay twenty-three described as open?"

    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))["items"]
    scientific = [row for row in payload["items"] if not row.get("calibration")]
    old_scientific = [row for row in original if not row.get("calibration")]
    assert len(scientific) == 120 and len(payload["items"]) == 128
    assert not ({row["id"] for row in scientific} & {row["id"] for row in old_scientific})
    assert not ({row["scenario_id"] for row in scientific} & {row["scenario_id"] for row in old_scientific})
    for field in ("english", "ainglish"):
        assert not ({row[field] for row in scientific} & {row[field] for row in old_scientific})
    assert not ({row_key(row) for row in scientific} & {row_key(row) for row in old_scientific})
    assert all(row["english"] != row["ainglish"] for row in payload["items"] if row.get("calibration"))
    counts = {answer: sum(row["answer"] == answer for row in scientific) for answer in source.OPTIONS}
    positions = {str(position): sum(row["options"].index(row["answer"]) == position for row in scientific) for position in range(3)}
    assert counts == {"yes": 40, "no": 40, "cannot tell": 40}
    assert positions == {"0": 40, "1": 40, "2": 40}
    items_sha256 = hashlib.sha256(canonical(payload["items"])).hexdigest()
    payload["sha256"] = items_sha256
    (ROOT / "items.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.spark-exactly-one-replication-freeze.v1",
        "proposal_revision": SLUG,
        "replicates_hash": TARGET,
        "seed": SEED,
        "items_file": "items.json",
        "items_sha256": items_sha256,
        "scientific_items": 120,
        "calibration_items": 8,
        "answer_counts": counts,
        "answer_positions": positions,
        "source_target_items_sha256": json.loads(ORIGINAL.read_text(encoding="utf-8"))["sha256"],
        "fresh_text_intersections": {
            "complete_rows": 0,
            "ids": 0,
            "scenario_ids": 0,
            "english": 0,
            "ainglish": 0,
        },
        "preserved_question_templates": True,
        "reader_calls": 0,
        "attempt_mints": 0,
        "execution_gate": (
            "Activate only after SDK PR 152 is canonical and its panel harness preserves the "
            "audited reader_qualifications receipt in the immutable manifest."
        ),
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
