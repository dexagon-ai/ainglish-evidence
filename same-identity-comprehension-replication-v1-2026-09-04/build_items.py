#!/usr/bin/env python3
"""Build and freshness-check 48 scientific items plus eight construct-free controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
SLUG = "same-one-same-kind-same-name"

SAME_ONE = [
    "deployment ledger", "incident timeline", "release checklist", "shared calendar",
    "routing table", "review queue", "budget workbook", "inventory record",
    "decision log", "schema document", "risk register", "service catalogue",
    "audit notebook", "maintenance schedule", "contact directory", "change journal",
]
SAME_KIND = [
    ("configuration", "parsed-field comparison", "09:10 UTC"),
    ("policy bundle", "semantic clause comparison", "revision 18"),
    ("database snapshot", "row-and-column digest", "Tuesday noon"),
    ("API schema", "normalized-schema diff", "build 771"),
    ("routing map", "ordered-edge comparison", "15:00 UTC"),
    ("translation table", "key-value digest", "release 22"),
    ("permission set", "effective-rights comparison", "last deployment"),
    ("feature profile", "enabled-flag comparison", "checkpoint 6"),
    ("workflow definition", "normalized-step diff", "commit 4ac"),
    ("price list", "currency-and-value check", "1 September"),
    ("alert catalogue", "identifier-and-severity diff", "08:30 UTC"),
    ("retention schedule", "period-and-scope comparison", "policy review 9"),
    ("parser grammar", "production-rule digest", "release candidate 3"),
    ("access matrix", "principal-permission comparison", "midnight UTC"),
    ("build manifest", "dependency-version diff", "pipeline run 440"),
    ("localization file", "message-key comparison", "translation freeze"),
]
SAME_NAME = [
    "backup archive", "release package", "customer export", "configuration file",
    "runbook", "model checkpoint", "database dump", "policy document",
    "container image", "migration script", "test report", "invoice batch",
    "signature file", "schema bundle", "training shard", "incident attachment",
]


def choices(index: int) -> list[str]:
    return ["yes", "no"] if index % 2 == 0 else ["no", "yes"]


def build() -> list[dict]:
    scientific: list[dict] = []
    for index in range(16):
        one = SAME_ONE[index]
        kind, check, moment = SAME_KIND[index]
        name = SAME_NAME[index]
        scientific.extend([
            {
                "id": f"one-{index + 1:02d}",
                "english": f"Mira and Jo edit one shared {one}; changing it through either person's access changes that single object.",
                "ainglish": f"Mira and Jo edit the same-one {one}.",
                "question": f"After Mira changes the {one}, has the {one} Jo reaches changed too?",
                "options": choices(index),
                "answer": "yes",
            },
            {
                "id": f"kind-{index + 1:02d}",
                "english": f"East has a separate {kind} that was verified equal to West's by {check} at {moment}; later changes do not propagate between them.",
                "ainglish": f"East has a same-kind {kind} to West's ({check}, as of {moment}).",
                "question": f"If East changes its {kind} after {moment}, must West's {kind} change too?",
                "options": choices(index + 1),
                "answer": "no",
            },
            {
                "id": f"name-{index + 1:02d}",
                "english": f"Both stores have distinct {name}s with the same identifier; their contents have not been verified equal.",
                "ainglish": f"Both stores have a same-name {name}.",
                "question": f"Does the shared name alone establish that the two {name}s have equal contents?",
                "options": choices(index),
                "answer": "no",
            },
        ])

    controls = []
    facts = [
        ("Nadia", "Oren", "owns the recovery key"),
        ("the amber worker", "the violet worker", "processed the final batch"),
        ("York", "Bath", "holds the sealed copy"),
        ("port 9443", "port 7443", "serves the admin endpoint"),
        ("Tuesday", "Thursday", "is the maintenance day"),
        ("region north", "region south", "contains the primary"),
        ("queue oak", "queue elm", "received the job"),
        ("reviewer Chen", "reviewer Dara", "approved the amendment"),
    ]
    for index, (answer, rival, predicate) in enumerate(facts):
        options = [answer, rival, "cannot tell"] if index % 2 == 0 else [rival, "cannot tell", answer]
        controls.append({
            "id": f"control-{index + 1:02d}",
            "calibration": True,
            "calibration_scope": "target-independent",
            "english": f"Either {answer} or {rival} {predicate}.",
            "ainglish": f"{answer}, not {rival}, {predicate}.",
            "question": f"Which one {predicate}?",
            "options": options,
            "answer": answer,
        })
    return scientific + controls


def main() -> None:
    items = build()
    if len(items) != 56 or sum(not row.get("calibration", False) for row in items) != 48:
        raise SystemExit("REFUSING: expected 48 scientific and 8 calibration items")
    client = AinglishClient()
    proposal = client.proposal(SLUG)
    fresh_pairs = {(row["english"], row["ainglish"]) for row in items if not row.get("calibration")}
    prior_pairs: set[tuple[str, str]] = set()
    for row in proposal.get("measurements") or []:
        manifest = row.get("manifest")
        if not isinstance(manifest, dict) and row.get("manifest_hash"):
            detail = client.measurement(row["manifest_hash"])
            manifest = detail.get("measurement", detail).get("manifest")
        if not isinstance(manifest, dict):
            continue
        prior_items = manifest.get("items") or manifest.get("test_set") or []
        prior_pairs |= {
            (item.get("english"), item.get("ainglish"))
            for item in prior_items if isinstance(item, dict)
        }
    if fresh_pairs & prior_pairs:
        raise SystemExit("REFUSING: scientific complete-pair overlap with existing evidence")
    encoded = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    output = ROOT / "items.json"
    output.write_bytes(encoded + b"\n")
    print(json.dumps({
        "scientific": 48,
        "calibration": 8,
        "prior_pairs": len(prior_pairs),
        "overlap": 0,
        "items_sha256": hashlib.sha256(encoded).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
