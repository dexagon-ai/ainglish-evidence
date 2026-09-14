"""Run the installed official panel with an explicit in-process oracle, NEVER a real reader.

Only an unmistakably synthetic structural summary is saved. No submission client is imported.
The result object is not persisted as a measurement. Also deny network sockets defensively.
"""
from contextlib import redirect_stdout
import io
import importlib.metadata
import json
from pathlib import Path
from unittest.mock import patch

from ainglish import panel
from build_bank import generate, digest, probe_scores

ROOT = Path(__file__).resolve().parent

def main():
    items = generate()
    controls = []
    for index in range(8):
        yes = f"Mailbox-{index}-West"
        no = f"Mailbox-{index}-East"
        controls.append({"id": f"DRY-RUN-control-{index}", "calibration": True,
                         "english": f"The control record has not established whether {yes} or {no} receives the notice.",
                         "ainglish": f"The control record establishes that {yes}, not {no}, receives the notice.",
                         "question": "Where is the notice routed according to the settled record?",
                         "options": [yes, no, "Both", "Not established"], "answer": yes})
    manifest = {"construct": "DRY-RUN-choose-any-review-instrument-NOT-EVIDENCE",
                "metric": "comprehension_accuracy_delta", "seed": 2026091451,
                "items": items + controls, "items_sha256": digest(items + controls),
                "panel": [{"name": "DRY-RUN-same-oracle-seat-A"}, {"name": "DRY-RUN-same-oracle-seat-B"}],
                "panel_neff": 1, "calibration_min_gap": .5,
                "settlement_strata": [{"id": f, "weight": 1} for f in ("choose-any", "draw-uniform")]}
    journal, calibration = [], []
    transcript = io.StringIO()
    with patch("socket.socket", side_effect=RuntimeError("Network forbidden in structural oracle test")), redirect_stdout(transcript):
        result = panel.run_panel(manifest, ask_fn=panel.dry_reader(manifest["items"], manifest),
                                 cell_results=journal, calibration_results=calibration)
    if not result:
        raise SystemExit("Official harness refused the draft shape:\n" + transcript.getvalue())
    # Every option is separately audited; this tests BOTH partial-error paths, not just the oracle's correct path.
    checked = sum(len(i["options"]) for i in items)
    for item in items:
        for option in item["options"]:
            score = probe_scores(item, option)
            assert score["joint"] == (option == item["answer"])
    report = {"status": "DRY-RUN-STRUCTURAL-ONLY-NOT-EVIDENCE", "sdk_version": importlib.metadata.version("ainglish"),
              "real_reader_calls": 0, "network_connections": 0, "oracle_real_cells": len(journal),
              "oracle_calibration_cells": len(calibration), "scoring_options_checked": checked,
              "official_panel_accepted_structure": True, "draft_items_sha256": digest(items),
              "qualifies_a_reader": False, "independent_confirmation": False,
              "statement": "The oracle consults the answer key. It tests plumbing, not language quality; numeric outcomes are deliberately not retained as a measurement."}
    (ROOT / "OFFLINE-HARNESS-CHECK.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
