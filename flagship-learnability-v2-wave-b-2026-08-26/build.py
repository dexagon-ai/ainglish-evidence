#!/usr/bin/env python3
"""Build fresh form-separated wave-B learnability carriers offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
N = 48
SEED = 2026082631
CAMPAIGNS = {
    "we-including-you": ("clusivity", "we-including-you", "clusivity"),
    "we-excluding-you": ("clusivity", "we-excluding-you", "clusivity"),
    "fact-not-known": ("fact-choice", "fact-not-known", "fact-choice"),
    "choice-not-made": ("fact-choice", "choice-not-made", "fact-choice"),
}
TEAM_CASES = [
    ("Ari", "Bea", "Cy", "inspect bundle"), ("Dara", "Emil", "Faye", "sign receipt"),
    ("Gus", "Hana", "Ivo", "review alert"), ("Jia", "Kofi", "Luz", "verify archive"),
    ("Mara", "Noel", "Oren", "approve ticket"), ("Pia", "Quin", "Ravi", "close incident"),
    ("Sara", "Tao", "Uma", "publish digest"), ("Vik", "Wren", "Xia", "rotate key"),
]
FACT_CASES = [
    ("whether mirror B already contains build", "query the mirror index", "deployment board"),
    ("which checksum the stored archive has", "read the archive metadata", "release steward"),
    ("whether the worker finished before noon", "inspect the timestamped log", "operations lead"),
    ("which region the board selected yesterday", "retrieve the signed minutes", "regional board"),
    ("whether the invoice was paid last week", "check the settled ledger", "finance desk"),
    ("which key signed the existing receipt", "verify the signature block", "security owner"),
    ("whether the package currently includes tests", "inspect the frozen package", "maintainer"),
    ("which host served the recorded request", "read the access record", "network operator"),
]
CHOICE_CASES = [
    ("which mirror to deploy", "deployment board"), ("whether to retain the archive", "release steward"),
    ("which maintenance window to choose", "operations lead"), ("which region to open next", "regional board"),
    ("whether to waive the late fee", "finance desk"), ("which key to rotate first", "security owner"),
    ("whether to merge the optional tests", "maintainer"), ("which host to promote", "network operator"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def options(answer: str, alternatives: list[str], position: int) -> list[str]:
    values = list(alternatives)
    values.insert(position % 3, answer)
    assert len(values) == 3 and len(set(values)) == 3
    return values


def row(campaign: str, index: int, message: str, question: str, answer: str,
        alternatives: list[str], probe: str) -> dict:
    return {
        "id": f"learn-b-{campaign}-{index + 1:03d}",
        "english": message,
        "ainglish": message,
        "question": question,
        "options": options(answer, alternatives, index % 3),
        "answer": answer,
        "marker": campaign,
        "probe": probe,
        "scenario_id": f"learnability-wave-b-{campaign}-{index + 1:03d}",
    }


def clusivity(marker: str) -> list[dict]:
    includes = marker == "we-including-you"
    rows = []
    for index in range(N):
        one, two, reader, action = TEAM_CASES[index % len(TEAM_CASES)]
        case = 810 + index
        message = f"Message from {one} and {two} to {reader}: {marker} will {action} {case}."
        probe = index % 6
        if probe == 0:
            question, answer, alternatives = "Is the addressed reader part of the stated acting group?", "yes" if includes else "no", ["no" if includes else "yes", "not stated"]
        elif probe == 1:
            question, answer, alternatives = f"Is {reader} expected by this sentence to take part in the action?", "yes" if includes else "no", ["no" if includes else "yes", "not stated"]
        elif probe == 2:
            question, answer, alternatives = f"Are {one} and {two} part of the stated acting group?", "yes", ["no", "not stated"]
        elif probe == 3:
            question, answer, alternatives = "Does the marker say how the acting members divide the work?", "not stated", ["equally", "one member does all of it"]
        elif probe == 4:
            question, answer, alternatives = "Does the marker itself grant authority to perform the action?", "not stated", ["yes", "no"]
        else:
            question, answer, alternatives = "Does the marker say that the reader is merely informed rather than tasked?", "no" if includes else "yes", ["yes" if includes else "no", "not stated"]
        rows.append(row(marker, index, message, question, answer, alternatives, f"clusivity-{probe}"))
    return rows


def fact_choice(marker: str) -> list[dict]:
    is_fact = marker == "fact-not-known"
    rows = []
    for index in range(N):
        if is_fact:
            issue, method, authority = FACT_CASES[index % len(FACT_CASES)]
            message = f"Authenticated note {920 + index}: {marker} — {issue}; {method} could recover the answer."
        else:
            issue, authority = CHOICE_CASES[index % len(CHOICE_CASES)]
            method = "reviewing available evidence"
            message = f"Authenticated note {920 + index}: {marker} — {issue}; the {authority} has not selected an option."
        probe = index % 6
        if probe == 0:
            question, answer, alternatives = "Does an operative answer already exist independently of a new selection?", "yes" if is_fact else "no", ["no" if is_fact else "yes", "not stated"]
        elif probe == 1:
            question, answer, alternatives = "Can observation or retrieval reveal the answer without an authority making a new choice?", "yes" if is_fact else "no", ["no" if is_fact else "yes", "not stated"]
        elif probe == 2:
            question, answer, alternatives = f"Must the {authority} make an operative selection to close this gap?", "no" if is_fact else "yes", ["yes" if is_fact else "no", "not stated"]
        elif probe == 3:
            question, answer, alternatives = "Does the marker assert that nobody else knows anything relevant?", "no", ["yes", "not stated"]
        elif probe == 4:
            question, answer, alternatives = "Does the marker request that the reader investigate or decide?", "no", ["yes", "not stated"]
        else:
            question = "Which event closes the stated gap?"
            answer = method if is_fact else f"an operative selection by the {authority}"
            alternatives = ([f"an operative selection by the {authority}", "the marker does not distinguish them"] if is_fact
                            else [method, "the marker does not distinguish them"])
        rows.append(row(marker, index, message, question, answer, alternatives, f"fact-choice-{probe}"))
    return rows


def calibrations(campaign: str) -> list[dict]:
    objects = ("agate pass", "birch token", "copper seal", "dune card", "elm key", "frost disk", "glass badge", "hemp tag")
    rows = []
    for index, obj in enumerate(objects):
        rack = 31 + index
        answer = f"rack {rack}"
        rows.append({
            "id": f"learn-b-{campaign}-cal-{index + 1:02d}",
            "calibration": True,
            "calibration_scope": "target-independent",
            "calibration_construct": "ziv-location-control-v1",
            "english": f"The note labels the {obj} ziv({rack}), but gives no definition of ziv.",
            "ainglish": f"Control entry: ziv(<N>) means the labelled object is stored in rack N.\n\nThe note labels the {obj} ziv({rack}).",
            "question": f"Where does the control place the {obj}?",
            "options": options(answer, [f"rack {rack + 1}", "not inferable"], index % 3),
            "answer": answer,
        })
    return rows


def entry_text(surface: dict) -> str:
    return (
        "Ainglish register entry\n"
        f"Title: {surface['title']}\n"
        f"Form: {surface['form']}\n\n"
        f"Standard-English mapping:\n{surface['english_mapping']}\n\n"
        f"Registered Ainglish examples:\n{surface['example_ainglish']}\n\n"
        f"Registered standard-English examples:\n{surface['example_english']}\n"
    )


def main() -> None:
    snapshots = json.loads((ROOT / "proposal-snapshots.json").read_text(encoding="utf-8"))
    builders = {"clusivity": clusivity, "fact-choice": fact_choice}
    entries = {}
    for proposal_key, record in snapshots["proposals"].items():
        text = entry_text(record["surface"])
        path = ROOT / f"entry-{proposal_key}.txt"
        path.write_text(text, encoding="utf-8")
        entries[proposal_key] = {"path": path.name, "sha256": hashlib.sha256(text.encode()).hexdigest(), "proposal_slug": record["surface"]["slug"], "surface_sha256": record["surface_sha256"]}
    index = {"kind": "dexagon.ainglish.flagship-learnability-wave-b-freeze.v1", "seed": SEED, "model_calls": 0, "governance_writes": 0, "campaigns": {}}
    seen = set()
    for campaign, (proposal_key, marker, builder_name) in CAMPAIGNS.items():
        scientific = builders[builder_name](marker)
        calibration = calibrations(campaign)
        rows = scientific + calibration
        triples = {(item["english"], item["ainglish"], item["question"]) for item in scientific}
        assert len(scientific) == N and len(calibration) == 8 and len(triples) == N and not triples & seen
        seen |= triples
        assert all(item["english"] == item["ainglish"] and marker in item["english"] for item in scientific)
        assert [sum(item["options"].index(item["answer"]) == position for item in scientific) for position in range(3)] == [16, 16, 16]
        digest = hashlib.sha256(canonical(rows)).hexdigest()
        payload = {"kind": "dexagon.ainglish.flagship-learnability-items.v2", "campaign": campaign, "proposal_key": proposal_key, "marker": marker, "seed": SEED, "sha256": digest, "items": rows}
        path = ROOT / f"items-{campaign}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index["campaigns"][campaign] = {"proposal_key": proposal_key, "marker": marker, "items_path": path.name, "items_sha256": digest, "scientific_items": N, "calibration_items": 8, "entry": entries[proposal_key]}
    index["proposal_snapshot_sha256"] = snapshots["content_sha256"]
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"campaigns": len(CAMPAIGNS), "content_sha256": index["content_sha256"]}))


if __name__ == "__main__":
    main()
