#!/usr/bin/env python3
"""Build the v2 role-cardinality carrier with valid planted controls."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
V1 = ROOT.parent / "one-or-more-exactly-one-comprehension-carrier-2026-08-26" / "build.py"


def load_v1():
    spec = importlib.util.spec_from_file_location("role_cardinality_v1", V1)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen v1 builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    v1 = load_v1()
    campaigns = {}
    for form in ("one-or-more", "exactly-one"):
        for comparison in ("careful", "bare"):
            payload, receipt = v1.build_campaign(form, comparison)
            payload["kind"] = "dexagon.ainglish.role-cardinality-comprehension-carrier.v2"
            payload["seed"] = 2026090307
            payload["calibration"] = (
                "Eight target-independent literal controls; the English arm withholds bay status "
                "and the Ainglish-labelled experimental arm states it. These controls qualify "
                "the live instrument only and contain no proposal marker."
            )
            controls = [row for row in payload["items"] if row.get("calibration")]
            assert len(controls) == 8
            for index, row in enumerate(controls):
                token = f"calibration-role-cardinality-{comparison}-{index + 1:02d}"
                row["english"] = (
                    f"The routing note for {token} exists, but it does not record whether bay "
                    "fourteen is open or closed."
                )
                row["ainglish"] = (
                    f"The routing note for {token} says bay fourteen is "
                    + ("open." if row["answer"] == "yes" else "closed.")
                )
                assert row["english"] != row["ainglish"]
            payload["sha256"] = hashlib.sha256(v1.canonical(payload["items"])).hexdigest()
            filename = receipt["file"]
            receipt["items_sha256"] = payload["sha256"]
            (ROOT / filename).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            campaigns[f"{form}-vs-{comparison}"] = receipt

    index = {
        "kind": "dexagon.ainglish.role-cardinality-comprehension-freeze.v2",
        "proposal_revision": v1.SLUG,
        "seed": 2026090307,
        "scientific_items_per_campaign": 120,
        "calibrations_per_campaign": 8,
        "scientific_source": (
            "Byte-for-byte scientific rows from v1; only the invalid byte-identical "
            "target-independent calibration arms are replaced."
        ),
        "campaigns": campaigns,
        "reader_calls": 0,
        "governance_writes": 0,
        "execution_gate": (
            "proposal seconded, token prerequisite complete, two distinct readers pass the "
            "same frozen target-independent qualification screen, and panel receipts preserve "
            "those qualifications"
        ),
    }
    index["content_sha256"] = hashlib.sha256(v1.canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
