#!/usr/bin/env python3
"""Regression checks for receipt-bound activation and mint-before-spend metadata."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("manifest_bound_activate", ROOT / "activate.py")
assert SPEC and SPEC.loader
ACTIVATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACTIVATE)


def reader(name: str, lineage: str, digest_char: str = "a") -> dict:
    model = f"model-{name}"
    model_digest = digest_char * 64
    receipt = {
        "kind": "ainglish.panel.reader-qualification-receipt.v1",
        "qualified": True,
        "lineage": lineage,
        "model": model,
        "model_digest": "sha256:" + model_digest,
        "holdout_sha256": "f" * 64,
    }
    receipt["content_sha256"] = hashlib.sha256(ACTIVATE.canonical(receipt)).hexdigest()
    return {
        "name": name,
        "model": model,
        "model_digest": "sha256:" + model_digest,
        "provider": "ollama",
        "lineage": lineage,
        "qualification_receipt": receipt,
    }


class ActivationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads((ROOT / "role-cardinality.template.json").read_text(encoding="utf-8"))
        self.panel = [reader("a", "Lineage A", "a"), reader("b", "Lineage B", "b")]

    def test_panel_requires_two_qualified_lineages(self) -> None:
        with self.assertRaises(AssertionError):
            ACTIVATE.validate_panel([reader("a", "Lineage A"), reader("b", "Lineage A")])
        unqualified = reader("b", "Lineage B")
        unqualified["qualification_receipt"]["qualified"] = False
        with self.assertRaises(AssertionError):
            ACTIVATE.validate_panel([reader("a", "Lineage A"), unqualified])

    def test_receipt_bytes_model_and_common_holdout_are_enforced(self) -> None:
        bad_digest = reader("b", "Lineage B", "b")
        bad_digest["qualification_receipt"]["lineage"] = "Other"
        with self.assertRaises(AssertionError):
            ACTIVATE.validate_panel([reader("a", "Lineage A", "a"), bad_digest])
        different_holdout = reader("b", "Lineage B", "b")
        receipt = different_holdout["qualification_receipt"]
        receipt["holdout_sha256"] = "e" * 64
        unsigned = dict(receipt)
        unsigned.pop("content_sha256")
        receipt["content_sha256"] = hashlib.sha256(ACTIVATE.canonical(unsigned)).hexdigest()
        with self.assertRaisesRegex(AssertionError, "same frozen holdout"):
            ACTIVATE.validate_panel([reader("a", "Lineage A", "a"), different_holdout])

    def test_replication_lineage_exclusions_are_enforced(self) -> None:
        constraints = {"forbidden_lineage_fragments": ["qwen", "gemma", "ornith"]}
        with self.assertRaisesRegex(AssertionError, "forbidden original lineage"):
            ACTIVATE.validate_panel(
                [reader("a", "Qwen 3.6", "a"), reader("b", "Seed OSS", "b")],
                constraints,
            )

    def test_replication_attempt_preserves_target_and_report_only_diagnostics(self) -> None:
        template = dict(self.template)
        template["replicates_hash"] = "c" * 64
        template["report_only_diagnostics"] = ["form", "domain"]
        attempt = ACTIVATE.attempt_block(template, ACTIVATE.validate_panel(self.panel), template["seed"])
        self.assertEqual("c" * 64, attempt["planned_sample"]["replicates_hash"])
        self.assertEqual(["form", "domain"], attempt["planned_sample"]["report_only_diagnostics"])
        self.assertTrue(attempt["estimand"].startswith("Fresh-input replication"))
        self.assertTrue(any("post-hoc settlement gate" in gate for gate in attempt["admissibility_gates"]))

    def test_attempt_block_prices_the_complete_planned_spend(self) -> None:
        panel = ACTIVATE.validate_panel(self.panel)
        attempt = ACTIVATE.attempt_block(self.template, panel, self.template["seed"])
        sample = attempt["planned_sample"]
        self.assertEqual(48, sample["settlement_strata"])
        self.assertEqual(960, sample["real_reader_cells"])
        self.assertEqual(48, sample["calibration_reader_cells"])
        self.assertEqual(2, sample["panel_neff"])
        self.assertEqual("f" * 64, sample["qualification_holdout_sha256"])
        self.assertEqual(2, len(sample["qualification_receipt_sha256s"]))
        self.assertEqual(self.template["proposal_revision"], attempt["proposal_revision"])
        self.assertTrue(any("filed once" in gate for gate in attempt["admissibility_gates"]))


if __name__ == "__main__":
    unittest.main()
