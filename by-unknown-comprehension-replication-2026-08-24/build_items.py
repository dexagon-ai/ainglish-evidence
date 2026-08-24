#!/usr/bin/env python3
"""Build Dexagon's fresh by-unknown carrier without making reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "items.json"
SEED = 2026082417
QUESTION = (
    "If the responder needs the actor's identity, which first route does this "
    "sentence support?"
)
RECORDS_ROUTE = "check records or traces independently of the report's author"
AUTHOR_ROUTE = "ask the report's author to identify the actor"
NEITHER_ROUTE = "neither route is supported by this sentence"
OPTIONS = [RECORDS_ROUTE, AUTHOR_ROUTE, NEITHER_ROUTE]

SCENARIOS = [
    ("cybersecurity", "administrator session", "terminated"),
    ("cybersecurity", "access token", "revoked"),
    ("cybersecurity", "firewall policy", "modified"),
    ("cybersecurity", "sandbox", "quarantined"),
    ("health-operations", "specimen", "discarded"),
    ("health-operations", "appointment", "reassigned"),
    ("health-operations", "dosage", "changed"),
    ("health-operations", "ward transfer", "approved"),
    ("civic-services", "permit", "reissued"),
    ("civic-services", "registry record", "sealed"),
    ("civic-services", "inspection", "rescheduled"),
    ("civic-services", "public notice", "withdrawn"),
    ("inventory", "pallet", "relabeled"),
    ("inventory", "stock count", "corrected"),
    ("inventory", "purchase order", "split"),
    ("inventory", "crate", "rerouted"),
    ("education", "course result", "amended"),
    ("education", "enrolment", "cancelled"),
    ("education", "room booking", "changed"),
    ("education", "scholarship hold", "released"),
    ("energy", "sensor", "replaced"),
    ("energy", "breaker", "opened"),
    ("energy", "turbine", "stopped"),
    ("energy", "fuel delivery", "delayed"),
]

GLOSSES = [
    (
        "The report's writer does not know who did this; identifying the actor "
        "requires checking records or traces independently of the writer."
    ),
    (
        "The author has no information identifying the actor, so the identity "
        "must be investigated in independent records or traces."
    ),
    (
        "Who did this is unknown to the writer; use records or traces other than "
        "the writer's testimony to find the actor."
    ),
    (
        "The writer cannot identify the actor; the supported first route is an "
        "independent search of records or traces."
    ),
]

CALIBRATION = [
    ("cal-cache", "cache entry", "purged"),
    ("cal-badge", "visitor badge", "deactivated"),
    ("cal-filing", "court filing", "corrected"),
    ("cal-lot", "production lot", "held"),
    ("cal-voucher", "travel voucher", "cancelled"),
    ("cal-feed", "telemetry feed", "disabled"),
    ("cal-roster", "staff roster", "revised"),
    ("cal-route", "delivery route", "closed"),
]


def rotate(values: list[str], offset: int) -> list[str]:
    return values[offset:] + values[:offset]


def main() -> None:
    items: list[dict] = []
    for index, (domain, subject, verb) in enumerate(SCENARIOS):
        statement = f"The {subject} was {verb}."
        items.append({
            "id": f"dex-unknown-{domain}-{index + 1:02d}",
            "english": f"{statement} {GLOSSES[index % len(GLOSSES)]}",
            "ainglish": f"The {subject} was {verb} by-unknown.",
            "question": QUESTION,
            "options": rotate(OPTIONS, index % 3),
            "answer": RECORDS_ROUTE,
            "marker": "by-unknown",
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
                f"{statement} The report's author cannot identify the actor; "
                "check independent records or traces first."
            ),
            "question": QUESTION,
            "options": rotate(OPTIONS, index % 3),
            "answer": RECORDS_ROUTE,
            "marker": "by-unknown",
            "set": "heldout_explicit-independent-route_positive_control",
        })

    canonical = json.dumps(
        items, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()
    document = {
        "kind": "dexagon.by_unknown.comprehension_replication_items.v1",
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
