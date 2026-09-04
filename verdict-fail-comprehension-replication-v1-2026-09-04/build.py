#!/usr/bin/env python3
"""Build a fresh complete-English comprehension replication carrier."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TARGET = "f68f899dd4a737c36733f3d9aaac2a9558f6727ed0c920280ad23974c7d721ed"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def rotate(answer: str, distractors: list[str], index: int) -> list[str]:
    values = [answer, *distractors]
    offset = index % len(values)
    return values[offset:] + values[:offset]


def scientific() -> list[dict]:
    domains = [
        ("deployment smoke suite", "release candidate", "three contract assertions failed", "runner timed out before assertions"),
        ("archive integrity scan", "archive", "two stored blocks had invalid checksums", "object store was unreachable"),
        ("schema conformance gate", "dataset", "four records violated the required schema", "schema fixture could not be loaded"),
        ("certificate verifier", "certificate", "the signature did not match the public key", "revocation service rate-limited the verifier"),
        ("replica health probe", "replica", "the replica returned corrupted state", "the probe process crashed before connecting"),
        ("policy compliance check", "policy bundle", "a forbidden permission was present", "the evaluator lacked the policy input"),
        ("model safety evaluation", "model build", "the build crossed the declared refusal threshold", "the evaluation host lost power mid-run"),
        ("migration validation job", "migration", "the resulting rows violated the invariant", "the validation database never started"),
    ]
    rows = []
    for case in range(6):
        for domain_index, (check, target, defect, interruption) in enumerate(domains):
            ref = f"case-{case + 41}-{domain_index + 11}"
            answer = f"The {target} is reported as defective"
            rows.append({
                "id": f"verdict-fail-{case + 1:02d}-{domain_index + 1:02d}",
                "english": f"For {ref}, the {check} ran to completion and found the {target} defective: {defect}. Repair or roll back the target.",
                "ainglish": f"{check} {ref}: verdict-fail — {defect}. Repair or roll back the {target}.",
                "question": f"What does the report establish about the {target}?",
                "options": rotate(answer, [
                    f"The check produced no judgment about the {target}",
                    f"The {target} passed the check",
                    "The check was never scheduled",
                ], len(rows)),
                "answer": answer,
                "form": "verdict-fail",
                "probe": "completed adverse judgment versus check-side failure",
            })
            answer = f"The check produced no judgment about the {target}"
            rows.append({
                "id": f"no-verdict-{case + 1:02d}-{domain_index + 1:02d}",
                "english": f"For {ref}, the {check} did not reach a result because {interruption}; the {target}'s condition remains unknown. Rerun the check.",
                "ainglish": f"{check} {ref}: no-verdict — {interruption}; {target} condition unknown. Rerun the check.",
                "question": f"What does the report establish about the {target}?",
                "options": rotate(answer, [
                    f"The {target} is reported as defective",
                    f"The {target} passed the check",
                    "The check was never scheduled",
                ], len(rows)),
                "answer": answer,
                "form": "no-verdict",
                "probe": "check-side failure versus completed adverse judgment",
            })
    assert len(rows) == 96
    return rows


def calibration() -> list[dict]:
    objects = [
        ("amber ticket", "cabinet 17"), ("birch token", "shelf 24"),
        ("cobalt folder", "locker 31"), ("dune key", "cabinet 42"),
        ("elm card", "shelf 53"), ("fern badge", "locker 64"),
        ("gold seal", "cabinet 75"), ("hazel note", "shelf 86"),
        ("indigo disk", "locker 97"), ("jade pass", "cabinet 108"),
        ("kelp label", "shelf 119"), ("linen slip", "locker 120"),
        ("moss token", "cabinet 131"), ("nickel seal", "shelf 142"),
        ("ochre card", "locker 153"), ("pearl key", "cabinet 164"),
    ]
    rows = []
    for index, (thing, place) in enumerate(objects):
        rows.append({
            "id": f"cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The inventory mentions the {thing}, but states no storage location.",
            "ainglish": f"The inventory says the {thing} is stored in {place}.",
            "question": f"Where does the message say the {thing} is stored?",
            "options": rotate(place, ["the intake room", "the dispatch room", "no location is stated"], index),
            "answer": place,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def main() -> None:
    items = scientific() + calibration()
    science = [row for row in items if not row.get("calibration")]
    assert Counter(row["form"] for row in science) == {"verdict-fail": 48, "no-verdict": 48}
    assert len({(row["english"], row["ainglish"]) for row in science}) == 96
    payload = {
        "kind": "dexagon.ainglish.verdict-fail-comprehension-carrier.v1",
        "proposal_public_id": "a-6974j2deetg3rcb5",
        "proposal_revision": "verdict-fail-no-verdict",
        "construct": "verdict-fail / no-verdict",
        "replicates_hash": TARGET,
        "comparator": {"kind": "complete-careful-english-v1"},
        "items": items,
        "reader_calls": 0,
    }
    (ROOT / "items.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.verdict-fail-comprehension-index.v1",
        "model_calls": 0,
        "scientific_items": len(science),
        "calibration_items": len(items) - len(science),
        "forms": dict(sorted(Counter(row["form"] for row in science).items())),
        "items_sha256": sha256(canonical(items)).hexdigest(),
        "source_target": TARGET,
        "comparator": "complete-careful-english-v1",
        "training_asymmetry": "Present readers have ordinary-English training and are not assumed to have seen Ainglish.",
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
