#!/usr/bin/env python3
"""Regression checks for receipt-bound activation and mint-before-spend metadata."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("manifest_bound_activate", ROOT / "activate.py")
assert SPEC and SPEC.loader
ACTIVATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACTIVATE)


def reader(name: str, lineage: str, digest_char: str = "a") -> dict:
    return {
        "name": name,
        "model": f"model-{name}",
        "provider": "ollama",
        "lineage": lineage,
        "qualification_receipt": {
            "qualified": True,
            "content_sha256": digest_char * 64,
        },
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

    def test_attempt_block_prices_the_complete_planned_spend(self) -> None:
        panel = ACTIVATE.validate_panel(self.panel)
        attempt = ACTIVATE.attempt_block(self.template, panel, self.template["seed"])
        sample = attempt["planned_sample"]
        self.assertEqual(48, sample["settlement_strata"])
        self.assertEqual(960, sample["real_reader_cells"])
        self.assertEqual(48, sample["calibration_reader_cells"])
        self.assertEqual(2, sample["panel_neff"])
        self.assertEqual(self.template["proposal_revision"], attempt["proposal_revision"])
        self.assertTrue(any("filed once" in gate for gate in attempt["admissibility_gates"]))


if __name__ == "__main__":
    unittest.main()
