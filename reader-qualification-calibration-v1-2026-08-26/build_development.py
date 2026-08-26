#!/usr/bin/env python3
"""Build a fresh, development-only entailment calibration packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
AXES = (
    "quantifier_force", "set_membership", "negation_scope", "disjunction",
    "conditional", "reference_resolution", "temporal_order", "authority_and_permission",
)
LABELS = ("entailed", "contradicted", "not determined")


def item(item_id: str, axis: str, premise: str, hypothesis: str, label: str, position: int) -> dict:
    options = list(LABELS[position:] + LABELS[:position])
    return {"id": item_id, "axis": axis, "premise": premise, "hypothesis": hypothesis, "options": options, "answer": label}


ITEMS = [
    item("cal-qf-01", "quantifier_force", "Exactly nine of the fifteen archives were retained.", "Exactly six archives were not retained.", "entailed", 2),
    item("cal-qf-02", "quantifier_force", "Exactly three of the ten cameras are online.", "Every camera is online.", "contradicted", 1),
    item("cal-qf-03", "quantifier_force", "No fewer than six of the nine relays responded.", "Exactly six relays responded.", "not determined", 0),
    item("cal-sm-01", "set_membership", "Only licensed pilots may validly authorize takeoff. Mira validly authorized takeoff under this policy.", "Mira is a licensed pilot.", "entailed", 0),
    item("cal-sm-02", "set_membership", "Every cobalt badge is metallic. Ivo's badge is metallic.", "Ivo's badge is cobalt.", "not determined", 1),
    item("cal-sm-03", "set_membership", "No cedar crate is marked. The east crate is cedar.", "The east crate is marked.", "contradicted", 2),
    item("cal-ns-01", "negation_scope", "No relay failed.", "Every relay avoided failure.", "entailed", 0),
    item("cal-ns-02", "negation_scope", "The gate is not unlocked.", "The gate is unlocked.", "contradicted", 2),
    item("cal-ns-03", "negation_scope", "Oren did not inspect every folder.", "Oren inspected no folders.", "not determined", 1),
    item("cal-dj-01", "disjunction", "At least one of the red channel and the blue channel is active.", "One or both of the two channels are active.", "entailed", 2),
    item("cal-dj-02", "disjunction", "The signal is amber or green, and both colors are permitted by the description.", "Exactly one color applies.", "not determined", 0),
    item("cal-dj-03", "disjunction", "The parcel went by rail and not by road.", "The parcel went by road.", "contradicted", 1),
    item("cal-co-01", "conditional", "If the scan fails, quarantine the device. The scan failed.", "The device should be quarantined.", "entailed", 1),
    item("cal-co-02", "conditional", "Release the package only if it is signed. The package is unsigned.", "The package may be released under this rule.", "contradicted", 0),
    item("cal-co-03", "conditional", "If the test passes, publish the report. The report was published.", "The test passed.", "not determined", 2),
    item("cal-rr-01", "reference_resolution", "Mira gave the chart to Jo. Mira then left the room.", "Mira left the room.", "entailed", 0),
    item("cal-rr-02", "reference_resolution", "The bronze folder is open. The white folder beside it is sealed.", "The bronze folder is sealed.", "contradicted", 2),
    item("cal-rr-03", "reference_resolution", "Rae told Liv that she would speak next.", "Rae will speak next.", "not determined", 1),
    item("cal-to-01", "temporal_order", "The seal was applied immediately before dispatch.", "The seal was applied before dispatch.", "entailed", 2),
    item("cal-to-02", "temporal_order", "Calibration happened after startup.", "Calibration happened before startup.", "contradicted", 1),
    item("cal-to-03", "temporal_order", "The audit ran while the backup was running.", "The audit began before the backup.", "not determined", 0),
    item("cal-ap-01", "authority_and_permission", "The policy explicitly permits Lina to export the file.", "Lina may export the file under the policy.", "entailed", 1),
    item("cal-ap-02", "authority_and_permission", "The machine is capable of opening the hatch, but no permission rule is stated.", "The machine is permitted to open the hatch.", "not determined", 2),
    item("cal-ap-03", "authority_and_permission", "The policy forbids interns from approving requests. Taro is an intern.", "Taro may approve the request under this policy.", "contradicted", 0),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(row: dict) -> str:
    premise = row.get("premise", row.get("message"))
    hypothesis = row.get("hypothesis", row.get("question"))
    return hashlib.sha256(canonical({"premise": premise, "hypothesis": hypothesis})).hexdigest()


def discover_receipts() -> list[dict]:
    receipts = []
    for path in sorted(REPO.glob("reader-qualification-*/*.json")):
        if path.parent == ROOT or path.name.endswith("result.json") or path.name in {"analysis.json", "audit-report.json"}:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(value, dict) and isinstance(value.get("items"), list) and value["items"]:
            if all(isinstance(row, dict) and ("message" in row or "premise" in row) for row in value["items"]):
                receipts.append({"file": str(path.relative_to(REPO)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return receipts


def build(receipts: list[dict] | None = None) -> dict:
    if len(ITEMS) != 24 or {row["axis"] for row in ITEMS} != set(AXES):
        raise SystemExit("REFUSING: development item population or axes drift")
    if len({row["id"] for row in ITEMS}) != len(ITEMS):
        raise SystemExit("REFUSING: duplicate development item id")
    for axis in AXES:
        own = [row for row in ITEMS if row["axis"] == axis]
        if len(own) != 3 or set(row["answer"] for row in own) != set(LABELS):
            raise SystemExit(f"REFUSING: unexpected answer balance in {axis}")
        if any(row["answer"] not in row["options"] or set(row["options"]) != set(LABELS) for row in own):
            raise SystemExit(f"REFUSING: invalid options in {axis}")
        if {row["options"].index(row["answer"]) for row in own} != {0, 1, 2}:
            raise SystemExit(f"REFUSING: answer positions are not counterbalanced in {axis}")
    receipts = discover_receipts() if receipts is None else receipts
    old = set()
    for receipt in receipts:
        path = REPO / receipt["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != receipt["sha256"]:
            raise SystemExit(f"REFUSING: disjointness source drift in {receipt['file']}")
        value = json.loads(path.read_text(encoding="utf-8"))
        old.update(fingerprint(row) for row in value["items"])
    overlap = old & {fingerprint(row) for row in ITEMS}
    if overlap:
        raise SystemExit("REFUSING: development premise-hypothesis pair duplicates an earlier instrument item")
    document = {
        "kind": "ainglish.panel.reader-qualification-development-calibration.v1",
        "evidentiary_status": "development-only exposed controls; never qualification or proposal evidence",
        "purpose": "Test a uniform premise-hypothesis classification contract against the reasoning traps isolated from v7.",
        "answer_protocol": "opaque-entailment-choice-v1",
        "task_contract": "Given only the premise, classify the hypothesis as entailed, contradicted, or not determined. Return only the opaque option code assigned by the runner.",
        "model_calls": 0,
        "network_calls": 0,
        "axes": list(AXES),
        "items_per_axis": 3,
        "labels": list(LABELS),
        "disjointness_receipts": receipts,
        "items": ITEMS,
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    target = ROOT / "development-packet.json"
    existing = json.loads(target.read_text(encoding="utf-8")) if target.exists() else None
    document = build(existing["disjointness_receipts"] if existing else None)
    if args.write:
        if target.exists():
            raise SystemExit("REFUSING: development-packet.json already exists")
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(document["items"]), "sha256": document["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
