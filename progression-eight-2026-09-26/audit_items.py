#!/usr/bin/env python3
"""Offline structural audit of two already-filed public banks; no inference or re-scoring."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def audit(name):
    measurement = json.loads((ROOT / f"{name}.json").read_text())
    items = json.loads((ROOT / f"{name}-items.json").read_text())
    assert digest(items) == measurement["manifest"]["items_sha256"]
    assert len({item["id"] for item in items}) == len(items)
    for item in items:
        assert len(item["options"]) == len(set(item["options"]))
        assert item["answer"] in item["options"]
        if "gold_position" in item:
            assert item["options"][item["gold_position"]] == item["answer"]
    real = [i for i in items if not i.get("calibration")]
    transfer = [i for i in real if i["settlement_stratum"] == "transfer"]
    missing = []
    for item in transfer:
        second = next(line for line in item["ainglish"].splitlines() if line.startswith("Request 2:"))
        # Presence only, not a semantic judgement or an inferred default key.
        if "idempotency key" not in second:
            missing.append({"id": item["id"], "class": item.get("transfer", item.get("class")),
                            "request_2": second, "recorded_gold": item["answer"]})
    return {
        "manifest_hash": measurement["manifest_hash"],
        "items_sha256": digest(items), "real_items": len(real),
        "calibration_items": len(items) - len(real),
        "strata": dict(Counter(i["settlement_stratum"] for i in real)),
        "transfer_items": len(transfer),
        "request_2_missing_explicit_key": len(missing),
        "missing_key_by_class": dict(Counter(i["class"] for i in missing)),
        "same_request_items_missing_key": [i for i in missing if i["class"].startswith("same-")],
        "recorded_value": measurement["value"],
        "recorded_interval": [measurement["value_lo"], measurement["value_hi"]],
        "reader_roster": measurement["panel_models"],
        "recorded_resolution": measurement["resolution_bound"],
        "checks": "Canonical item digest, unique IDs/options, valid answer and supplied gold-position metadata verified. No semantic gold repair, new inference or result recomputation.",
    }


if __name__ == "__main__":
    print(json.dumps({name: audit(name) for name in ("original", "replica")}, indent=2))
