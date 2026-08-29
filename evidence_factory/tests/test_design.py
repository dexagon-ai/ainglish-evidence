from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from evidence_factory.design import EvidenceDesign, EvidenceDesignError, freeze_design


class EvidenceDesignTests(unittest.TestCase):
    def make_items(self, root: Path, name: str, *, answer: str = "A") -> None:
        rows = []
        for index in range(4):
            rows.append({"id": f"{name}-cal-{index}", "calibration": True, "answer": answer})
        for index in range(16):
            rows.append({"id": f"{name}-real-{index}", "answer": answer})
        (root / f"{name}.json").write_text(json.dumps(rows, indent=2) + "\n")

    def make_draft(self, root: Path) -> Path:
        self.make_items(root, "marked")
        self.make_items(root, "bare", answer="B")
        payload = {
            "kind": "ainglish.reader-evidence-design.v1",
            "slug": "example",
            "proposal_revision": "example",
            "population": "fresh held-out operational consequence items",
            "forms": ["mark-one"],
            "quality_gates": {
                "mint_before_reader_spend": True,
                "calibration_both_arms": True,
                "retain_all_admissible_outcomes": True,
                "no_scientific_cell_retry": True,
                "complete_pair_identity": True,
                "qualified_reader_lineages_min": 2,
            },
            "campaigns": {
                "marked-vs-careful": {
                    "role": "claim_carrier",
                    "form": "mark-one",
                    "metric": "comprehension_accuracy_delta",
                    "comparator": {"kind": "complete-careful-english-v1"},
                    "items": "marked.json",
                },
                "marked-vs-bare": {
                    "role": "bare_diagnostic",
                    "form": "mark-one",
                    "metric": "comprehension_accuracy_delta",
                    "comparator": {"kind": "balanced-bare-english-v1"},
                    "items": "bare.json",
                },
            },
        }
        path = root / "draft.json"
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path

    def test_freezes_and_validates_complete_design(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frozen = freeze_design(self.make_draft(root), root / "design.json")
            self.assertIsInstance(frozen, EvidenceDesign)
            self.assertEqual(len(frozen.content_digest), 64)

    def test_refuses_drift_after_freeze(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            frozen = freeze_design(self.make_draft(root), root / "design.json")
            rows = json.loads((root / "marked.json").read_text())
            rows[0]["answer"] = "C"
            (root / "marked.json").write_text(json.dumps(rows))
            with self.assertRaisesRegex(EvidenceDesignError, "item drift"):
                EvidenceDesign.load(frozen.path)

    def test_refuses_bare_arm_as_claim_carrier(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            draft = self.make_draft(root)
            payload = json.loads(draft.read_text())
            payload["campaigns"]["marked-vs-careful"]["comparator"]["kind"] = "balanced-bare-english-v1"
            draft.write_text(json.dumps(payload))
            with self.assertRaisesRegex(EvidenceDesignError, "complete careful-English"):
                freeze_design(draft, root / "design.json")

    def test_refuses_missing_quality_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            draft = self.make_draft(root)
            payload = json.loads(draft.read_text())
            payload["quality_gates"]["retain_all_admissible_outcomes"] = False
            draft.write_text(json.dumps(payload))
            with self.assertRaisesRegex(EvidenceDesignError, "retain_all_admissible_outcomes"):
                freeze_design(draft, root / "design.json")

    def test_refuses_reused_diagnostic_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            draft = self.make_draft(root)
            payload = json.loads(draft.read_text())
            payload["campaigns"]["marked-vs-bare"]["items"] = "marked.json"
            draft.write_text(json.dumps(payload))
            with self.assertRaisesRegex(EvidenceDesignError, "reuses the complete item file"):
                freeze_design(draft, root / "design.json")


if __name__ == "__main__":
    unittest.main()
