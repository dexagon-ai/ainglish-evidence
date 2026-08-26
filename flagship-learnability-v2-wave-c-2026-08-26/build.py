#!/usr/bin/env python3
"""Build fresh form-separated wave-C learnability carriers offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
N = 48
SEED = 2026082637
CAMPAIGNS = {
    "moved-earlier": ("moved", "moved-earlier", "moved"),
    "moved-later": ("moved", "moved-later", "moved"),
    "among-others": ("enumeration", "among-others", "enumeration"),
    "and-no-others": ("enumeration", "and-no-others", "enumeration"),
    "by-construction": ("standing", "by-construction", "standing"),
    "by-rule": ("standing", "by-rule", "standing"),
    "in-practice": ("standing", "in-practice", "standing"),
    "same-one": ("identity", "same-one", "identity"),
    "same-kind": ("identity", "same-kind", "identity"),
    "same-name": ("identity", "same-name", "identity"),
}
EVENTS = ("review", "maintenance window", "ballot close", "standup", "delivery slot", "freeze", "audit", "release call")
ENUMERATIONS = (
    ("accepted formats", "CSV", "Parquet", "YAML"), ("retry codes", "408", "429", "500"),
    ("allowed roles", "reviewer", "operator", "auditor"), ("export targets", "JSON", "CSV", "XML"),
    ("enabled regions", "north", "central", "south"), ("notification channels", "email", "webhook", "SMS"),
    ("archive types", "tar", "zip", "rar"), ("checksum families", "SHA-256", "SHA-512", "BLAKE3"),
)
PROPERTIES = (
    ("responses", "valid JSON"), ("audit records", "append-only"), ("logs", "free of secrets"),
    ("identifiers", "unique"), ("requests", "authenticated"), ("exports", "deterministic"),
    ("receipts", "timestamped"), ("snapshots", "immutable"),
)
OBJECTS = ("draft", "config", "bundle", "schema", "ledger", "archive", "manifest", "report")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def placed(answer: str, alternatives: list[str], position: int) -> list[str]:
    assert answer not in alternatives and len(set(alternatives)) == 2
    values = list(alternatives)
    values.insert(position % 3, answer)
    return values


def item(campaign: str, index: int, message: str, question: str, answer: str,
         alternatives: list[str], probe: str) -> dict:
    return {
        "id": f"learn-c-{campaign}-{index + 1:03d}",
        "english": message,
        "ainglish": message,
        "question": question,
        "options": placed(answer, alternatives, index % 3),
        "answer": answer,
        "marker": campaign,
        "probe": probe,
        "scenario_id": f"learnability-wave-c-{campaign}-{index + 1:03d}",
    }


def moved(marker: str) -> list[dict]:
    earlier = marker == "moved-earlier"
    rows = []
    for index in range(N):
        event = EVENTS[index % len(EVENTS)]
        message = f"Schedule notice {1100 + index}: the {event} is {marker}; its replacement time will follow."
        probe = index % 6
        if probe == 0:
            q, answer, alternatives = "Where is the replacement time relative to the event's previous schedule?", "before it" if earlier else "after it", ["after it" if earlier else "before it", "not stated"]
        elif probe == 1:
            q, answer, alternatives = "Which reference point determines the stated direction?", "the event's current schedule", ["the moment of speaking", "midnight in the reader's timezone"]
        elif probe == 2:
            q, answer, alternatives = "Does the marker state how large the schedule change is?", "no", ["yes", "only if the event is in the future"]
        elif probe == 3:
            q, answer, alternatives = "Does the marker assert that all participants were notified?", "no", ["yes", "only for meetings"]
        elif probe == 4:
            q, answer, alternatives = "Does the marker assert that no later rescheduling is possible?", "no", ["yes", "only after publication"]
        else:
            q, answer, alternatives = "Can the new time still be in the future?", "yes", ["no", "not stated by the direction marker"]
        rows.append(item(marker, index, message, q, answer, alternatives, f"moved-{probe}"))
    return rows


def enumeration(marker: str) -> list[dict]:
    closed = marker == "and-no-others"
    rows = []
    for index in range(N):
        label, first, second, candidate = ENUMERATIONS[index % len(ENUMERATIONS)]
        if index % 6 == 5:
            message = f"Policy {1200 + index}: {label} are {first}, {second}, {marker}; alert levels are amber and red."
        else:
            message = f"Policy {1200 + index}: {label} are {first}, {second}, {marker}."
        probe = index % 6
        if probe == 0:
            q, answer, alternatives = "Is the terminated list claimed complete within its stated kind and scope?", "yes" if closed else "no", ["no" if closed else "yes", "not stated"]
        elif probe == 1:
            q = f"What does the message claim about unlisted same-kind candidate {candidate}?"
            answer = "claimed excluded" if closed else "neither admitted nor excluded"
            alternatives = (["neither admitted nor excluded", "claimed admitted"] if closed else ["claimed excluded", "claimed admitted"])
        elif probe == 2:
            q, answer, alternatives = f"Is {first} claimed to be a listed member?", "yes", ["no", "not stated"]
        elif probe == 3:
            q, answer, alternatives = "Does the marker promise that every listed member works correctly?", "no", ["yes", "only for machine-readable lists"]
        elif probe == 4:
            q, answer, alternatives = "Does the marker itself timestamp or permanently freeze the set?", "no", ["yes", "only for complete lists"]
        else:
            q, answer, alternatives = "Does this marker also claim that the later alert-level list is complete?", "no", ["yes", "only when both lists are in one sentence"]
        rows.append(item(marker, index, message, q, answer, alternatives, f"enumeration-{probe}"))
    return rows


def standing(marker: str) -> list[dict]:
    rows = []
    for index in range(N):
        subject, prop = PROPERTIES[index % len(PROPERTIES)]
        message = f"Service report {1300 + index}: {subject} are {prop} {marker}."
        probe = index % 6
        if probe == 0:
            answer = "no without changing the system" if marker == "by-construction" else "yes"
            q, alternatives = "Can an exception occur while the stated regime remains in force?", (["yes", "not stated"] if marker == "by-construction" else ["no without changing the system", "not stated"])
        elif probe == 1:
            answer = "yes" if marker == "by-rule" else "no"
            q, alternatives = "Would an exception itself be a rule violation?", ["no" if answer == "yes" else "yes", "not stated"]
        elif probe == 2:
            answer = "yes" if marker == "by-rule" else "no"
            q, alternatives = "Does the regime say someone owes repair or explanation after an exception?", ["no" if answer == "yes" else "yes", "not stated"]
        elif probe == 3:
            answer = "yes" if marker == "in-practice" else "no"
            q, alternatives = "Is the claim limited to what has been observed so far?", ["no" if answer == "yes" else "yes", "not stated"]
        elif probe == 4:
            answer = "the claim dies or the system changed" if marker == "by-construction" else ("a rule was violated" if marker == "by-rule" else "a new observation occurred, not a breach")
            alternatives = [value for value in ("the claim dies or the system changed", "a rule was violated", "a new observation occurred, not a breach") if value != answer]
            q = "What is the registered consequence of observing an exception?"
        else:
            answer, alternatives = "no", ["yes", "only if the property was intentional"]
            q = "Does the marker merely assert that someone intended the property?"
        rows.append(item(marker, index, message, q, answer, alternatives, f"standing-{probe}"))
    return rows


def identity(marker: str) -> list[dict]:
    rows = []
    for index in range(N):
        obj = OBJECTS[index % len(OBJECTS)]
        checkpoint = 1400 + index
        if marker == "same-one":
            message = f"At checkpoint {checkpoint}, desks A and B edit the same-one {obj}."
        elif marker == "same-kind":
            message = f"At checkpoint {checkpoint}, desk A has a same-kind {obj} to desk B's, checked by SHA-256 as-of checkpoint {checkpoint}."
        else:
            message = f"At checkpoint {checkpoint}, desks A and B have a same-name {obj}."
        probe = index % 6
        if probe == 0:
            answer = "yes" if marker == "same-one" else "no"
            q, alternatives = "Do both mentions reach one shared entity?", ["no" if answer == "yes" else "yes", "not stated"]
        elif probe == 1:
            answer = "yes" if marker == "same-one" else "no"
            q, alternatives = "Does an edit through desk A necessarily change what desk B reaches?", ["no" if answer == "yes" else "yes", "not stated"]
        elif probe == 2:
            answer = "equal by identity" if marker == "same-one" else ("equal under SHA-256 at the named checkpoint" if marker == "same-kind" else "not claimed equal")
            alternatives = [value for value in ("equal by identity", "equal under SHA-256 at the named checkpoint", "not claimed equal") if value != answer]
            q = "What content-equality claim is made?"
        elif probe == 3:
            answer = "no" if marker == "same-one" else "yes"
            q, alternatives = "Can the two held objects later differ without contradiction?", ["yes" if answer == "no" else "no", "not stated"]
        elif probe == 4:
            answer = "one shared thing" if marker == "same-one" else ("distinct copies verified under a named check and moment" if marker == "same-kind" else "matching identifier only")
            alternatives = [value for value in ("one shared thing", "distinct copies verified under a named check and moment", "matching identifier only") if value != answer]
            q = "Which relation does the marker assert?"
        else:
            answer = "yes" if marker == "same-one" else ("no, they may have drifted" if marker == "same-kind" else "not stated")
            alternatives = [value for value in ("yes", "no, they may have drifted", "not stated") if value != answer]
            q = "Must their bytes be equal now, after the named checkpoint?"
        rows.append(item(marker, index, message, q, answer, alternatives, f"identity-{probe}"))
    return rows


def calibrations(campaign: str) -> list[dict]:
    objects = ("ash token", "blue seal", "clay disk", "drift key", "ember card", "fern badge", "gold pass", "haze tag")
    rows = []
    for index, obj in enumerate(objects):
        vault = 51 + index
        answer = f"vault {vault}"
        rows.append({
            "id": f"learn-c-{campaign}-cal-{index + 1:02d}",
            "calibration": True,
            "calibration_scope": "target-independent",
            "calibration_construct": "pev-location-control-v1",
            "english": f"The routing slip labels the {obj} pev({vault}), but supplies no definition of pev.",
            "ainglish": f"Control entry: pev(<N>) means the labelled object is stored in vault N.\n\nThe routing slip labels the {obj} pev({vault}).",
            "question": f"Where does the control place the {obj}?",
            "options": placed(answer, [f"vault {vault + 1}", "not inferable"], index % 3),
            "answer": answer,
        })
    return rows


def entry_text(surface: dict) -> str:
    sections = [
        "Ainglish register entry",
        f"Title: {surface['title']}",
        f"Form: {surface['form']}",
        "Standard-English mapping:\n" + surface["english_mapping"],
    ]
    if surface.get("example_ainglish"):
        sections.append("Registered Ainglish examples:\n" + surface["example_ainglish"])
    if surface.get("example_english"):
        sections.append("Registered standard-English examples:\n" + surface["example_english"])
    return "\n\n".join(sections) + "\n"


def main() -> None:
    snapshots = json.loads((ROOT / "proposal-snapshots.json").read_text(encoding="utf-8"))
    builders = {"moved": moved, "enumeration": enumeration, "standing": standing, "identity": identity}
    entries = {}
    for proposal_key, record in snapshots["proposals"].items():
        text = entry_text(record["surface"])
        path = ROOT / f"entry-{proposal_key}.txt"
        path.write_text(text, encoding="utf-8")
        entries[proposal_key] = {"path": path.name, "sha256": hashlib.sha256(text.encode()).hexdigest(), "proposal_slug": record["surface"]["slug"], "surface_sha256": record["surface_sha256"]}
    index = {"kind": "dexagon.ainglish.flagship-learnability-wave-c-freeze.v1", "seed": SEED, "model_calls": 0, "governance_writes": 0, "campaigns": {}}
    seen = set()
    for campaign, (proposal_key, marker, builder_name) in CAMPAIGNS.items():
        scientific = builders[builder_name](marker)
        calibration = calibrations(campaign)
        rows = scientific + calibration
        current = {(row["english"], row["ainglish"], row["question"]) for row in scientific}
        assert len(scientific) == N and len(calibration) == 8 and len(current) == N and not current & seen
        seen |= current
        assert all(row["english"] == row["ainglish"] and marker in row["english"] for row in scientific)
        assert [sum(row["options"].index(row["answer"]) == position for row in scientific) for position in range(3)] == [16, 16, 16]
        digest = hashlib.sha256(canonical(rows)).hexdigest()
        payload = {"kind": "dexagon.ainglish.flagship-learnability-items.v2", "campaign": campaign, "proposal_key": proposal_key, "marker": marker, "seed": SEED, "sha256": digest, "items": rows}
        path = ROOT / f"items-{campaign}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index["campaigns"][campaign] = {"proposal_key": proposal_key, "marker": marker, "items_path": path.name, "items_sha256": digest, "scientific_items": N, "calibration_items": 8, "entry": entries[proposal_key]}
    index["proposal_snapshot_sha256"] = snapshots["content_sha256"]
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"campaigns": len(CAMPAIGNS), "scientific_items": len(CAMPAIGNS) * N, "content_sha256": index["content_sha256"]}))


if __name__ == "__main__":
    main()
