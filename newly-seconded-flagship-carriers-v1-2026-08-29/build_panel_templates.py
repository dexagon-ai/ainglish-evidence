#!/usr/bin/env python3
"""Bind the public panel items into receipt-enforcing comprehension templates."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
ITEM_COMMIT = "5eb3824f3e7805cdb8488615a5a8ae3f705ef911"
RAW_BASE = (
    "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
    f"{ITEM_COMMIT}/newly-seconded-flagship-carriers-v1-2026-08-29"
)
SPECS = {
    "average": {
        "slug": "mean-of-population-ref-value-median-of-population-ref-value",
        "seed": 2026082945,
        "construct": "mean-of(<population-ref>) / median-of(<population-ref>)",
        "strata": 60,
        "token_hash": "921e17ac1393b536cad4121697864280922f8d05131abf15e21890d92cf2d485",
        "token_value": -14.5,
        "design": "form x comparator class x preregistered hard cell; all 60 cells are equal-weight and load-bearing",
    },
    "deletion": {
        "slug": "o-removed-from-surface-o-erased-from-inventory-2",
        "seed": 2026082946,
        "construct": "removed-from(<surface>) / erased-from(<inventory>)",
        "strata": 78,
        "token_hash": "3444eac8fd212ae8aeaca7dd53a2c982571bf03df596854a5475fe567d2fcd6b",
        "token_value": -20.125,
        "design": "form x comparator class x preregistered hard cell; all 78 cells are equal-weight and load-bearing",
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def build(name: str) -> dict:
    spec = SPECS[name]
    item_file = f"{name}-panel.items.json"
    packet = json.loads((ROOT / item_file).read_text(encoding="utf-8"))
    items = packet["items"]
    strata = sorted({row["settlement_stratum"] for row in items if not row.get("calibration")})
    counts = Counter(row["settlement_stratum"] for row in items if not row.get("calibration"))
    assert len(strata) == spec["strata"]
    result = {
        "kind": "dexagon.ainglish.manifest-bound-panel-template.v1",
        "proposal_revision": spec["slug"],
        "slug": spec["slug"],
        "metric": "comprehension_accuracy_delta",
        "seed": spec["seed"],
        "comparator": {
            "kind": "three-separate-comparator-classes-v1",
            "description": "Each form is separately compared with bare ambiguous English, its complete careful mapping, and the preregistered short practical alternative; forms and comparator classes never pool.",
        },
        "settlement_strata": [{"id": value, "weight": 1} for value in strata],
        "items": items,
        "panel": [
            {"name": "REPLACE-QUALIFIED-READER-A", "provider": "replace", "model": "replace"},
            {"name": "REPLACE-QUALIFIED-READER-B", "provider": "replace", "model": "replace"},
        ],
        "panel_neff": 2,
        "activation": {
            "runnable": False,
            "reason": "The independently qualified two-lineage roster remains closed at 1/2.",
            "how": "Use the shared receipt-enforcing activate.py with an exact panel after both lineages qualify; commit and push the runspec before the first reader call.",
        },
        "model_calls": 0,
        "governance_writes": 0,
        "construct": spec["construct"],
        "scientific_items": 480,
        "calibration_items": 12,
        "settlement_design": spec["design"],
        "stratum_counts": dict(sorted(counts.items())),
        "prerequisite_receipt": {
            "metric": "token_delta", "measurement_hash": spec["token_hash"],
            "value": spec["token_value"], "registered_at_most": 0, "state": "satisfied",
            "evidentiary_limit": "price-only; never comprehension evidence",
        },
        "source_freeze": {
            "directory": "newly-seconded-flagship-carriers-v1-2026-08-29",
            "items_commit": ITEM_COMMIT,
            "transformation": "exact prompt/answer/position preservation; unused comparator arms and hidden answer-generation values omitted",
        },
        "items_artifact": {
            "file": item_file,
            "published_url": f"{RAW_BASE}/{item_file}",
            "items_sha256": packet["sha256"],
            "activation_rule": "The runnable manifest carries this immutable URL and digest instead of embedding item bytes beyond the 20 KB commitment cap.",
        },
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> None:
    for name in SPECS:
        path = ROOT / f"{name}-panel.template.json"
        if path.exists() and "--refresh-before-freeze" not in sys.argv:
            raise SystemExit(f"REFUSING: {path.name} already exists")
        template = build(name)
        path.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({
            "target": name, "template_sha256": template["content_sha256"],
            "items_sha256": template["items_artifact"]["items_sha256"],
            "strata": len(template["settlement_strata"]), "model_calls": 0,
        }))


if __name__ == "__main__":
    main()
