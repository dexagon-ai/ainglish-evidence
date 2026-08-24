#!/usr/bin/env python3
"""Build the frozen fresh-item carrier without making reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "items.json"
SEED = 2026082404
QUESTION = (
    "If the responder needs the actor's identity, which first route does this "
    "sentence support?"
)
AUTHOR_ROUTE = "ask the report's author for disclosure or authorization"
RECORDS_ROUTE = "search independent records because the author does not know"
NEITHER_ROUTE = "neither route is supported by this sentence"
OPTIONS = [AUTHOR_ROUTE, RECORDS_ROUTE, NEITHER_ROUTE]

SCENARIOS = [
    ("incident", "emergency override", "approved"),
    ("incident", "audit record", "deleted"),
    ("incident", "service", "restarted"),
    ("incident", "recovery key", "rotated"),
    ("finance", "transfer", "authorized"),
    ("finance", "refund", "issued"),
    ("finance", "invoice", "adjusted"),
    ("finance", "credit limit", "raised"),
    ("research", "sample", "relabelled"),
    ("research", "measurement", "excluded"),
    ("research", "dataset", "amended"),
    ("research", "result", "corrected"),
    ("operations", "deployment", "cancelled"),
    ("operations", "reservation", "moved"),
    ("operations", "shipment", "rerouted"),
    ("operations", "maintenance window", "extended"),
    ("moderation", "comment", "removed"),
    ("moderation", "account", "suspended"),
    ("moderation", "appeal", "denied"),
    ("moderation", "warning", "issued"),
    ("governance", "ballot", "invalidated"),
    ("governance", "proposal", "edited"),
    ("governance", "delegation", "revoked"),
    ("governance", "threshold", "changed"),
]

GLOSSES = [
    "The report's writer knows who did this and intentionally omits that identity.",
    "The author could name the actor but has chosen not to disclose them.",
    "The actor's identity is known to the writer and withheld from this message.",
    "The writer has the actor's identity but does not reveal it here.",
]

CALIBRATION = [
    ("cal-quarantine", "package", "quarantined"),
    ("cal-rollout", "rollout", "paused"),
    ("cal-contract", "contract", "approved"),
    ("cal-docket", "docket entry", "withdrawn"),
    ("cal-certificate", "certificate", "revoked"),
    ("cal-backup", "backup", "restored"),
    ("cal-claim", "claim", "rejected"),
    ("cal-endpoint", "endpoint", "disabled"),
]


def rotate(values: list[str], offset: int) -> list[str]:
    return values[offset:] + values[:offset]


def main() -> None:
    items: list[dict] = []
    for index, (domain, subject, verb) in enumerate(SCENARIOS):
        statement = f"The {subject} was {verb}."
        items.append({
            "id": f"dex-withheld-{domain}-{index + 1:02d}",
            "english": f"{statement} {GLOSSES[index % len(GLOSSES)]}",
            "ainglish": f"The {subject} was {verb} by-withheld.",
            "question": QUESTION,
            "options": rotate(OPTIONS, index % 3),
            "answer": AUTHOR_ROUTE,
            "marker": "by-withheld",
            "domain": domain,
            "gloss_variant": index % len(GLOSSES) + 1,
        })
    for index, (item_id, subject, verb) in enumerate(CALIBRATION):
        statement = f"The {subject} was {verb}."
        items.append({
            "id": item_id,
            "calibration": True,
            "english": statement,
            "ainglish": (
                f"{statement} The report's author knows who did it and can be "
                "asked for disclosure or authorization."
            ),
            "question": QUESTION,
            "options": rotate(OPTIONS, index % 3),
            "answer": AUTHOR_ROUTE,
            "marker": "by-withheld",
            "set": "heldout_explicit-author-route_positive_control",
        })

    canonical = json.dumps(
        items, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()
    document = {
        "kind": "dexagon.by_withheld.comprehension_replication_items.v1",
        "seed": SEED,
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "design": (
            "24 fresh scored scenarios across six domains and four lossless "
            "careful-English glosses, plus eight both-arm calibration rows."
        ),
        "items": items,
    }
    OUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "output": str(OUT),
        "items": len(items),
        "scientific": sum(not item.get("calibration") for item in items),
        "calibration": sum(bool(item.get("calibration")) for item in items),
        "canonical_items_sha256": document["sha256"],
        "reader_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
