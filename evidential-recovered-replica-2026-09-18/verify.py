"""Recount the restored historical replica; no network, SDK or model calls."""
import hashlib
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
AUDIT = runpy.run_path(str(HERE.parent / "evidential-position-audit-2026-09-18/audit.py"))
RESULT_SHA = "c90049abdab2f59a4025ce4841cd446ee1388305ed67c01675340a23b753002d"
CONTENT_SHA = "3f1db6ead192b474b1ec3dfb58f7e81d5ce8065ba223e00232078df74c9405d5"
MANIFEST = "ec89dbe3b0a4a8fbb55d6f2c387d1df72d04b008b4fa89baedd5d14848dd8a50"


def verify():
    inputs = AUDIT["pinned_bank"](HERE / "replica-cases.json", AUDIT["REPLICA_SHA"])
    raw = (HERE / "replica-result.json").read_bytes()
    result = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == RESULT_SHA
    assert AUDIT["digest"](result) == RESULT_SHA
    assert result["content_sha256"] == CONTENT_SHA
    assert result["manifest_commitment"] == MANIFEST
    assert result["attempt_id"] == "91cdd964-0794-4267-8b30-db3f100edc88"
    counts = AUDIT["replay_original"](inputs, result)
    cases = {row["id"]: row for row in inputs}
    for cell in result["rows"]:
        assert cell["form"] == cases[cell["case_id"]]["form"]
    assert len(result["rows"]) == 192
    assert result["exact_code_cells"] == sum(row["cells"] - row["format_invalid"] for row in counts.values())
    return {
        "kind": "ainglish.historical-replica-recovery-audit.v1",
        "measurement_filed": False,
        "retraction_reversed": False,
        "raw_artifact_sha256": RESULT_SHA,
        "internal_content_sha256": CONTENT_SHA,
        "input_sha256": AUDIT["REPLICA_SHA"],
        "measurement": MANIFEST,
        "per_reader": counts,
        "total_cells": len(result["rows"]),
        "format_invalid_retained": sum(row["format_invalid"] for row in counts.values()),
        "value": result["value"],
        "gold_positions": AUDIT["bank_summary"](inputs),
        "boundary": "Historical arithmetic and raw-response grading reproduce; the all-first instrument remains invalid for establishing semantic fidelity. No claim about shortcut use or execution authentication.",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
