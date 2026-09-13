#!/usr/bin/env python3
"""Structural checks only; neither reader evidence nor semantic certification."""

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def main():
    snapshot = json.loads((ROOT / "public-context.json").read_text())
    assert snapshot["proposal"]["public_id"] == "a-ptwhg57dq4w4fas4"
    assert snapshot["target_calls"] == 0
    assert snapshot["status"] == "design-held-no-attempt-no-target-exposure"
    assert snapshot["qualification_verified_for_new_study"] is False
    warning = snapshot["proposal"]["evidence_readiness"]["success_criteria_review"]
    assert warning["review_only"] is True and warning["changes_readiness"] is False
    assert snapshot["proposal"]["evidence_contract"] == {
        "claim_carrier": ["comprehension_accuracy_delta"], "prerequisites": ["token_delta"]
    }
    models = {model["name"]: model["digest"] for model in snapshot["local_models"]}
    assert models["dexagon-gemma3-12b-pp-task:ctx4k"] == (
        "de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f"
    )
    assert models["dexagon-mistral-small3.2-24b-pp-task:ctx4k"] == (
        "6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de"
    )
    cases = re.findall(r"^\| ([OKN][1-8]) \|", (ROOT / "SEMANTIC-CHECKS.md").read_text(), re.M)
    assert len(cases) == len(set(cases)) == 16
    assert cases == ([f"O{i}" for i in range(1, 5)] +
                     [f"K{i}" for i in range(1, 9)] +
                     [f"N{i}" for i in range(1, 5)])
    raw = (ROOT / "public-context.json").read_text()
    assert not re.search(r"ghp_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9_.-]{20,}", raw)
    assert len(snapshot["measurements"]) == len(snapshot["proposal"]["measurements"])
    print(json.dumps({"status": "structural-checks-pass", "semantic_review_cases": len(cases),
                      "required_models_inventory_matched": 2, "target_calls": 0,
                      "scientific_validity_certified": False}))


if __name__ == "__main__":
    main()
