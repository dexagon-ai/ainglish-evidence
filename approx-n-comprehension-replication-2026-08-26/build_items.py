#!/usr/bin/env python3
"""Freeze fresh cold-read items for an independent approx(N) comprehension replication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082602
CLASSES = ("approximate", "exact", "unspecified", "cannot tell")
BASE_OPTIONS = [
    "approximate: a small difference can remain compatible",
    "exact: a different final quantity contradicts it",
    "unspecified: the writer deliberately withholds that distinction",
    "cannot tell: the available message does not reveal the commitment",
]
ANSWER = dict(zip(CLASSES, BASE_OPTIONS, strict=True))

# None of these scenario frames or object/domain combinations came from Reticuli's carrier. That
# carrier is intentionally never fetched by this generator or its runner.
SCENARIOS = [
    ("alpine seed vault", "cryogenic capsules", 73),
    ("estuary survey", "tagged sandbars", 28),
    ("lunar archive", "sealed film canisters", 91),
    ("wetland observatory", "active acoustic beacons", 46),
    ("ceramics conservatory", "glazed fragments", 117),
    ("highland nursery", "viable cloud-pine cuttings", 64),
    ("desert relay", "charged telemetry cells", 39),
    ("tidal laboratory", "preserved plankton slides", 82),
    ("polar depot", "insulated ration cases", 55),
    ("cave registry", "mapped mineral chambers", 34),
    ("river restoration site", "anchored reed bundles", 106),
    ("aurora station", "calibrated spectrometer plates", 67),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(values: list[str], amount: int) -> list[str]:
    shift = amount % len(values)
    return values[shift:] + values[:shift]


def texts(commitment: str, domain: str, objects: str, count: int, serial: int) -> tuple[str, str]:
    prefix = f"Inventory note {serial} from the {domain}:"
    if commitment == "approximate":
        return (
            f"{prefix} the reserve contains approximately {count} {objects}.",
            f"{prefix} the reserve contains approx({count}) {objects}.",
        )
    if commitment == "exact":
        text = f"{prefix} the verified reserve contains exactly {count} {objects}."
        return text, text
    if commitment == "unspecified":
        text = (
            f"{prefix} a provisional display reads {count} {objects}, and the writer explicitly "
            "does not say whether that display is exact or approximate."
        )
        return text, text
    text = (
        f"{prefix} the surviving fragment reads '[qualifier missing] {count} {objects}'; "
        "the missing qualifier might have said 'exactly' or 'approximately'."
    )
    return text, text


def main() -> None:
    scientific: list[dict[str, object]] = []
    for class_index, commitment in enumerate(CLASSES):
        for scenario_index, (domain, objects, count) in enumerate(SCENARIOS):
            index = class_index * len(SCENARIOS) + scenario_index
            serial = 840 + index
            english, ainglish = texts(commitment, domain, objects, count, serial)
            final_count = count + 1
            scientific.append({
                "id": f"approx-n-fresh-{commitment.replace(' ', '-')}-{scenario_index + 1:02d}",
                "english": english,
                "ainglish": ainglish,
                "question": (
                    f"A later complete count reports {final_count} {objects}. Which description of "
                    "the note writer's numerical commitment determines whether that finding "
                    "contradicts the note?"
                ),
                "options": rotate(BASE_OPTIONS, index),
                "answer": ANSWER[commitment],
                "scenario_id": f"dexagon-fresh-commitment-{serial}",
                "strata": {"commitment_class": commitment, "domain": domain},
            })

    calibration: list[dict[str, object]] = []
    tokens = ("amber spindle", "birch medallion", "cobalt prism", "dahlia wafer",
              "ebony cylinder", "fennel plaque", "garnet shuttle", "heather tile")
    for index, token in enumerate(tokens):
        calibration.append({
            "id": f"approx-n-fresh-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The routing card mentions the {token}, but gives no cabinet number.",
            "ainglish": f"The routing card explicitly places the {token} in cabinet seventeen.",
            "question": "Does the routing card state that cabinet seventeen is the place to inspect?",
            "options": rotate(["yes", "cannot tell"], index),
            "answer": "yes",
            "set": "construct-free explicit-location positive control",
        })

    rows = scientific + calibration
    assert len(scientific) == 48 and len(calibration) == 8 and len(rows) == 56
    assert len({row["id"] for row in rows}) == len(rows)
    assert len({(row["english"], row["ainglish"]) for row in scientific}) == 48
    assert {c: sum(row["strata"]["commitment_class"] == c for row in scientific)
            for c in CLASSES} == {c: 12 for c in CLASSES}
    assert {position: sum(row["options"].index(row["answer"]) == position for row in scientific)
            for position in range(4)} == {position: 12 for position in range(4)}
    assert all("approximately" in row["english"] and "approx(" in row["ainglish"]
               for row in scientific if row["strata"]["commitment_class"] == "approximate")
    assert all(row["english"] == row["ainglish"]
               for row in scientific if row["strata"]["commitment_class"] != "approximate")

    digest = hashlib.sha256(canonical(rows)).hexdigest()
    payload = {
        "kind": "ainglish.approx-n-fresh-comprehension-replication-items.v1",
        "seed": SEED,
        "sha256": digest,
        "reader_calls": 0,
        "independence": (
            "Generated from new scenario frames without fetching or opening the original "
            "answer-bearing carrier."
        ),
        "design": (
            "48 cold-read consequence-classification pairs, 12 per approximate/exact/unspecified/"
            "cannot-tell commitment class, plus eight construct-free calibration rows."
        ),
        "items": rows,
    }
    (ROOT / "items.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    receipt = {
        "kind": "ainglish.approx-n-fresh-comprehension-replication-freeze.v1",
        "items": "items.json",
        "items_sha256": digest,
        "scientific": 48,
        "per_class": {c: 12 for c in CLASSES},
        "answer_positions": {str(position): 12 for position in range(4)},
        "calibration": 8,
        "original_carrier_fetched": False,
        "reader_calls": 0,
    }
    receipt["content_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    (ROOT / "freeze-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
