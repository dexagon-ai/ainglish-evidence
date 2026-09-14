"""Validate saved qualification provenance and counts without calling any reader.

Does not mint, submit, or build a launchable target manifest. Failed qualifications remain
failed; this audit checks that the saved observations and SDK receipt agree.
"""
import hashlib
import json
from pathlib import Path
from ainglish.reader_qualification import attach, validate, validate_screen

ROOT = Path(__file__).resolve().parent / "qualification"


def digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def main():
    plans = json.loads((ROOT / "PRE-SPEND.json").read_text())["screens"]
    receipts, summary = [], []
    for plan in plans:
        name = plan["reader"]
        raw = (ROOT / f"{name}-screen.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == plan["raw_screen_sha256"]
        screen = validate_screen(json.loads(raw))
        run = json.loads((ROOT / f"{name}-result.json").read_text())
        receipt = validate(run["receipt"])
        assert receipt["roster_id"] == screen["roster_id"] == plan["roster_id"]
        assert receipt["reader"]["model_digest"] == plan["model_digest"]
        assert run["instrument"]["model_digest"] == plan["model_digest"]
        assert digest(run["instrument"]) == receipt["settings_sha256"]
        assert digest({"kind": screen["kind"], "controls": screen["controls"],
                       "ordering": "control order; detectable then other; one call per cell; no retry"}) == receipt["screen_sha256"]
        expected_cells = [(control, arm) for control in screen["controls"]
                          for arm in ("detectable", "other")]
        assert len(run["observations"]) == len(expected_cells) == plan["planned_cells"]
        counts = {f"{arm}_{suffix}": 0 for arm in ("detectable", "other")
                  for suffix in ("correct", "total")}
        explicit_unknown = 0
        for observed, (control, arm) in zip(run["observations"], expected_cells):
            assert observed["control_id"] == control["id"] and observed["cell"] == arm
            assert observed["expected"] == control["answer"]
            correct = observed["answer"].strip() == control["answer"]
            assert observed["correct"] is correct
            counts[f"{arm}_correct"] += int(correct)
            counts[f"{arm}_total"] += 1
            explicit_unknown += int(arm == "other" and observed["answer"] ==
                                    "The complete assignment is not established.")
        assert all(receipt["result"][key] == value for key, value in counts.items())
        assert run["status"] == ("passed" if receipt["result"]["passed"] else "failed")
        receipts.append(receipt)
        summary.append({"reader": name, "status": run["status"], **counts,
                        "explicit_unknown_in_unresolved_arm": explicit_unknown,
                        "qualified_at": receipt["qualified_at"],
                        "valid_until": receipt["valid_until"],
                        "result_sha256": hashlib.sha256((ROOT / f"{name}-result.json").read_bytes()).hexdigest()})
    scaffold = {"models": [receipt["roster_id"] for receipt in receipts]}
    attached = attach(scaffold, receipts)
    assert len(attached["reader_qualifications"]) == len(receipts)
    assert "reader_qualifications" not in scaffold
    output = {"kind": "qualification-observation-audit", "readers": summary,
              "total_control_cells": sum(row["detectable_total"] + row["other_total"] for row in summary),
              "target_cells": 0, "sdk_receipt_attachment_check": "passed on non-launchable scaffold",
              "boundary": "Provenance and count audit only. Does not establish target comprehension, approve a study, or supply independent replication."}
    (ROOT / "OBSERVATION-AUDIT.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
