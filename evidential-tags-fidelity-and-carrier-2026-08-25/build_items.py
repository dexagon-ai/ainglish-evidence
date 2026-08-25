#!/usr/bin/env python3
"""Freeze controlled tag-application and matched comprehension populations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ["obs:", "obs(instrument):", "inf:", "inf(premises):", "rep(src):", "rep(self-past):"]
PROPOSITIONS = [
    "the release archive contains seven files",
    "the service returned status green",
    "the queue contains four pending jobs",
    "the checksum matches the signed record",
    "the route is closed at the north gate",
    "the appeal was accepted in cycle three",
    "the invoice total is forty credits",
    "the specimen label reads batch cedar",
]
INSTRUMENTS = ["grep", "panel-7", "sensor-k", "ledger-query", "camera-north", "api-check"]
SOURCES = ["Ava", "Bo", "Cy", "Diya", "Eli", "Fara"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(values: list[str], index: int) -> list[str]:
    shift = index % len(values)
    return values[shift:] + values[:shift]


def fidelity_cases() -> list[dict]:
    rows = []
    for index in range(96):
        slot = index % len(FORMS)
        proposition = PROPOSITIONS[(index // len(FORMS)) % len(PROPOSITIONS)]
        instrument = INSTRUMENTS[(index // 12) % len(INSTRUMENTS)]
        source = SOURCES[(index // 16) % len(SOURCES)]
        premise_a = f"log-{index // 6 + 11}"
        premise_b = f"rule-{index % 9 + 2}"
        if slot == 0:
            event = f"You personally and directly observe that {proposition}; no tool, report, inference, or memory supplies it."
            target = "obs:"
        elif slot == 1:
            event = f"You do not directly witness the fact. The instrument {instrument} outputs that {proposition}."
            target = f"obs({instrument}):"
        elif slot == 2:
            event = f"You neither observe nor receive a report of the fact. Reasoning from available evidence, you infer that {proposition}; no premise list is to be named."
            target = "inf:"
        elif slot == 3:
            event = f"You infer that {proposition} specifically from the named premises {premise_a} and {premise_b}; you did not observe it or receive it as a report."
            target = f"inf({premise_a}, {premise_b}):"
        elif slot == 4:
            event = f"External source {source} tells you that {proposition}. You have not independently observed or inferred it."
            target = f"rep({source}):"
        else:
            event = f"You recall from your own earlier state that {proposition}, but have not verified it now."
            target = "rep(self-past):"
        options = [
            "obs:",
            f"obs({instrument}):",
            "inf:",
            f"inf({premise_a}, {premise_b}):",
            f"rep({source}):",
            "rep(self-past):",
        ]
        rows.append({
            "id": f"tag-fidelity-{index + 1:03d}",
            "source_event": event,
            "proposition": proposition,
            "instruction": "Choose the one exact warranted evidential prefix. Do not upgrade, generalise, or omit named sources.",
            "options": rotate(options, index),
            "answer": target,
            "form": FORMS[slot],
            "strata": {"form_index": slot, "instrument": instrument, "source": source},
        })
    return rows


def comprehension_items() -> list[dict]:
    rows = []
    source_classes = [
        "direct personal observation",
        "an instrument output",
        "an inference without named premises",
        "an inference from named premises",
        "a report from an external source",
        "the writer's unverified memory",
    ]
    for index in range(120):
        slot = index % len(FORMS)
        proposition = PROPOSITIONS[(index // len(FORMS)) % len(PROPOSITIONS)]
        instrument = INSTRUMENTS[(index // 12) % len(INSTRUMENTS)]
        source = SOURCES[(index // 20) % len(SOURCES)]
        premise_a = f"record-{index // 6 + 21}"
        premise_b = f"constraint-{index % 7 + 3}"
        if slot == 0:
            ainglish = f"obs: {proposition}."
            english = f"I directly and personally observed that {proposition}."
        elif slot == 1:
            ainglish = f"obs({instrument}): {proposition}."
            english = f"My instrument {instrument} reported that {proposition}; I did not directly witness it."
        elif slot == 2:
            ainglish = f"inf: {proposition}."
            english = f"I infer that {proposition}, without naming the premises here."
        elif slot == 3:
            ainglish = f"inf({premise_a}, {premise_b}): {proposition}."
            english = f"I infer from the named premises {premise_a} and {premise_b} that {proposition}."
        elif slot == 4:
            ainglish = f"rep({source}): {proposition}."
            english = f"According to external source {source}, {proposition}; I have not independently verified it."
        else:
            ainglish = f"rep(self-past): {proposition}."
            english = f"I recall from my own earlier state, unverified now, that {proposition}."
        rows.append({
            "id": f"tag-comprehension-{index + 1:03d}",
            "scenario_id": f"tag-source-{index + 1:03d}",
            "form": FORMS[slot],
            "english": english,
            "ainglish": ainglish,
            "question": "Which source of evidence does the writer claim to possess for the proposition?",
            "options": rotate(source_classes, index),
            "answer": source_classes[slot],
            "strata": {"source_class": source_classes[slot], "form_index": slot},
        })
    return rows


def calibrations() -> list[dict]:
    rows = []
    for index, obj in enumerate(["amber card", "blue key", "cedar token", "dune seal", "elm badge", "fern pass", "gold tag", "hazel slip"]):
        rows.append({
            "id": f"evidential-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"A note mentions the {obj} but provides no shelf number.",
            "ainglish": f"A note states that the {obj} is on shelf nine.",
            "question": "Does the note state that checking shelf nine would find the named object?",
            "options": rotate(["yes", "no", "cannot tell"], index),
            "answer": "yes",
            "set": "construct-free explicit-location known positive",
        })
    return rows


def main() -> None:
    fidelity = fidelity_cases()
    comprehension = comprehension_items()
    assert len(fidelity) == 96 and len(comprehension) == 120
    assert all(row["answer"] in row["options"] for row in fidelity + comprehension)
    fidelity_blob = canonical(fidelity)
    comprehension_blob = canonical(comprehension)
    (ROOT / "fidelity-cases.json").write_bytes(fidelity_blob + b"\n")
    (ROOT / "comprehension-items.json").write_bytes(comprehension_blob + b"\n")
    panel_rows = comprehension + calibrations()
    panel_blob = canonical(panel_rows)
    (ROOT / "comprehension-panel.json").write_text(json.dumps({
        "kind": "ainglish.evidential-tags-comprehension-items.v1",
        "sha256": hashlib.sha256(panel_blob).hexdigest(),
        "design": "120 scientific pairs plus eight construct-free planted-effect calibration rows",
        "items": panel_rows,
    }, indent=2, ensure_ascii=False) + "\n")
    index = {
        "kind": "ainglish.evidential-tags-fidelity-and-carrier.v1",
        "fidelity": {
            "rows": len(fidelity),
            "sha256": hashlib.sha256(fidelity_blob).hexdigest(),
            "forms": {form: sum(row["form"] == form for row in fidelity) for form in FORMS},
        },
        "comprehension": {
            "rows": len(comprehension),
            "sha256": hashlib.sha256(comprehension_blob).hexdigest(),
            "forms": {form: sum(row["form"] == form for row in comprehension) for form in FORMS},
            "panel_file": "comprehension-panel.json",
            "panel_rows": len(panel_rows),
            "panel_sha256": hashlib.sha256(panel_blob).hexdigest(),
        },
    }
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(json.dumps(index, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
