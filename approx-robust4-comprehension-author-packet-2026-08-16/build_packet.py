#!/usr/bin/env python3
"""Build Dexagon's frozen real-item packet for the approx(N) robust-4 carrier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OPTIONS = ["approximate", "exact", "unspecified", "cannot tell"]
QUESTION = "How does the writer characterize the stated quantity?"
GLOSS_AINGLISH = (
    "Dialect note: approx(N) means approximately N; the value is an estimate, not an exact "
    "measurement. "
)
GLOSS_ENGLISH = (
    "Reading note: 'approximately N' says the value is an estimate, not an exact measurement. "
)

# Each template is rendered once cold and once with the one-sentence arm-specific gloss. The
# scenarios deliberately avoid about/around/roughly/near/estimate and other answer-bearing cues.
# Position is balanced 8/8/8 before the cold/gloss crossing.
CASES = [
    ("storage", "early", "small_integer", "Capacity reading: {marker} GB remain available.", "7"),
    ("archive", "middle", "large_integer", "The archive contains {marker} files.", "1204"),
    ("latency", "final", "medium_integer", "The measured latency in milliseconds is {marker}.", "240"),
    ("responses", "early", "percentage", "Response rate: {marker} percent of nodes replied.", "38"),
    ("duration", "middle", "small_integer", "The task takes {marker} minutes.", "5"),
    ("bandwidth", "final", "decimal", "The observed bandwidth in gigabits per second is {marker}.", "2.5"),
    ("temperature", "early", "decimal", "Temperature reading: {marker} degrees Celsius.", "18.6"),
    ("retention", "middle", "large_integer", "The retention pass kept {marker} records.", "90000"),
    ("liquid", "final", "decimal", "The liquid reserve in litres is {marker}.", "0.75"),
    ("adoption", "early", "percentage", "Adoption rate: {marker} percent across the fleet.", "99.5"),
    ("replicas", "middle", "small_integer", "The cluster has {marker} replicas online.", "12"),
    ("orbit", "final", "medium_integer", "The orbital period in days is {marker}.", "88"),
    ("transfer", "early", "large_integer", "Transfer volume: {marker} bytes crossed the link.", "4500"),
    ("queue", "middle", "small_integer", "The queue currently holds {marker} jobs.", "16"),
    ("recovery", "final", "decimal", "The recovery duration in hours is {marker}.", "3.2"),
    ("requests", "early", "medium_integer", "Arrival rate: {marker} requests per second.", "250"),
    ("parameters", "middle", "medium_integer", "The model contains {marker} billion parameters.", "27"),
    ("regions", "final", "medium_integer", "The number of covered regions is {marker}.", "64"),
    ("events", "early", "decimal", "Event volume: {marker} million events were logged.", "1.6"),
    ("checksum", "middle", "medium_integer", "The checksum scan finished in {marker} seconds.", "42"),
    ("power", "final", "small_integer", "The device power draw in watts is {marker}.", "18"),
    ("packet_loss", "early", "percentage", "Failure rate: {marker} percent of packets were lost.", "0.03"),
    ("cache", "middle", "medium_integer", "The cache can hold {marker} entries.", "512"),
    ("distance", "final", "medium_integer", "The separation between the relays in metres is {marker}.", "730"),
]


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate_options(answer_position: int) -> list[str]:
    alternatives = [option for option in OPTIONS if option != "approximate"]
    rotated = alternatives[answer_position % len(alternatives):] + alternatives[:answer_position % len(alternatives)]
    rotated.insert(answer_position, "approximate")
    return rotated


def build_items() -> list[dict]:
    items: list[dict] = []
    answer_position = 0
    for case_number, (domain, position, quantity_class, template, value) in enumerate(CASES, 1):
        ainglish_sentence = template.format(marker=f"approx({value})")
        english_sentence = template.format(marker=f"approximately {value}")
        pair_id = f"approx-r4-{case_number:02d}"
        for exposure, ainglish_prefix, english_prefix in (
            ("cold", "", ""),
            ("one_sentence_gloss", GLOSS_AINGLISH, GLOSS_ENGLISH),
        ):
            items.append({
                "id": f"{pair_id}-{exposure}",
                "english": english_prefix + english_sentence,
                "ainglish": ainglish_prefix + ainglish_sentence,
                "question": QUESTION,
                "options": rotate_options(answer_position % 4),
                "answer": "approximate",
                "strata": {
                    "exposure": exposure,
                    "pair_id": pair_id,
                    "domain": domain,
                    "quantity_class": quantity_class,
                    "marker_position": position,
                    "commitment_gold": "approximate",
                },
            })
            answer_position += 1
    return items


def validate(items: list[dict]) -> None:
    if len(items) != 48 or len({item["id"] for item in items}) != 48:
        raise SystemExit("REFUSING: packet must contain 48 uniquely identified real items")
    exposures = {name: sum(item["strata"]["exposure"] == name for item in items)
                 for name in ("cold", "one_sentence_gloss")}
    if exposures != {"cold": 24, "one_sentence_gloss": 24}:
        raise SystemExit(f"REFUSING: exposure balance drifted: {exposures}")
    positions = {name: sum(item["strata"]["marker_position"] == name for item in items)
                 for name in ("early", "middle", "final")}
    if positions != {"early": 16, "middle": 16, "final": 16}:
        raise SystemExit(f"REFUSING: marker-position balance drifted: {positions}")
    option_positions = [item["options"].index(item["answer"]) for item in items]
    if {index: option_positions.count(index) for index in range(4)} != {0: 12, 1: 12, 2: 12, 3: 12}:
        raise SystemExit("REFUSING: correct-option positions are not balanced 12/12/12/12")
    for item in items:
        if item["answer"] != "approximate" or set(item["options"]) != set(OPTIONS):
            raise SystemExit(f"REFUSING: four-way key drifted in {item['id']}")
        if "~" in item["english"] or "~" in item["ainglish"]:
            raise SystemExit(f"REFUSING: superseded ~N surface leaked into {item['id']}")
        if "approx(" not in item["ainglish"] or "approximately " not in item["english"]:
            raise SystemExit(f"REFUSING: arm marker missing in {item['id']}")
        if item["strata"]["exposure"] == "cold":
            lowered = (item["english"] + " " + item["ainglish"]).casefold()
            forbidden = ("about ", "around ", "roughly ", "near ", "estimate")
            if any(word in lowered for word in forbidden):
                raise SystemExit(f"REFUSING: answer-bearing cold cue in {item['id']}")


def main() -> None:
    items = build_items()
    validate(items)
    document = {
        "kind": "ainglish.panel.items.v1",
        "proposal": "approx-n-approximation-marker-parenthesized-d-1-robust-4",
        "scientific_author": {
            "username": "dexagon",
            "sub": "52b1883a-464e-403c-9059-d57afe91a13c",
            "operator": "Jack Parnell",
        },
        "items_sha256": hashlib.sha256(canonical_bytes(items)).hexdigest(),
        "design": {
            "real_items": 48,
            "items_per_exposure": {"cold": 24, "one_sentence_gloss": 24},
            "required_execution": "both arms of every item for every reader",
            "comparison": "approx(N) versus careful English approximately N",
            "excluded_comparator": "~N",
            "classification": OPTIONS,
            "claim": "non-inferiority at a preregistered -5 percentage-point margin",
            "reporting": (
                "cold and one_sentence_gloss are evaluated separately; publish each arm's exact "
                "success/denominator and all four observed answer-class counts"
            ),
        },
        "items": items,
    }
    output = ROOT / "items.json"
    output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    file_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    receipt = {
        "kind": "ainglish.author-packet.freeze.v1",
        "proposal": document["proposal"],
        "scientific_author": document["scientific_author"],
        "items": 48,
        "items_sha256": document["items_sha256"],
        "file_sha256": file_sha,
        "generated_by": "build_packet.py",
        "reader_calls": 0,
        "attempts_minted": 0,
    }
    (ROOT / "freeze-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
