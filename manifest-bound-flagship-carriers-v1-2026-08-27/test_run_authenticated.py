#!/usr/bin/env python3
"""Zero-network contract tests for the authenticated runspec wrapper."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import run_authenticated as subject


class LiveWorkTest(unittest.TestCase):
    def proposal(self, state: str, target: str | None = None) -> dict:
        row = {"metric": "comprehension_accuracy_delta", "state": state}
        if target:
            row["target_hashes"] = [target]
        return {
            "slug": "example",
            "stage": "measured",
            "superseded_by": None,
            "evidence_readiness": {"work_items": [row]},
        }

    def test_replication_requires_exact_awaiting_target_and_live_work_item(self) -> None:
        target_hash = "a" * 64
        spec = {
            "slug": "example",
            "metric": "comprehension_accuracy_delta",
            "replicates_hash": target_hash,
        }
        target = {
            "manifest_hash": target_hash,
            "metric": "comprehension_accuracy_delta",
            "settlement_state": "awaiting",
        }
        result = subject.validate_live_work(
            spec, self.proposal("replicate_original", target_hash), target
        )
        self.assertEqual(result["action"], "replicate_original")

        with self.assertRaisesRegex(SystemExit, "not awaiting"):
            subject.validate_live_work(
                spec,
                self.proposal("replicate_original", target_hash),
                {**target, "settlement_state": "eligible_agreement"},
            )
        with self.assertRaisesRegex(SystemExit, "no longer requests"):
            subject.validate_live_work(spec, self.proposal("complete"), target)

    def test_original_requires_fresh_submit_original_work(self) -> None:
        spec = {"slug": "example", "metric": "comprehension_accuracy_delta"}
        result = subject.validate_live_work(spec, self.proposal("submit_original"), None)
        self.assertEqual(result["action"], "submit_original")
        with self.assertRaisesRegex(SystemExit, "no longer requests"):
            subject.validate_live_work(spec, self.proposal("complete"), None)

    def test_superseded_surface_refuses(self) -> None:
        proposal = self.proposal("submit_original")
        proposal["superseded_by"] = "successor"
        with self.assertRaisesRegex(SystemExit, "current proposal surface"):
            subject.validate_live_work(
                {"slug": "example", "metric": "comprehension_accuracy_delta"},
                proposal,
                None,
            )


class ReceiptTest(unittest.TestCase):
    def test_existing_attempt_receipt_refuses_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runspec = Path(directory) / "example.runspec.json"
            runspec.write_text("{}\n", encoding="utf-8")
            subject.ensure_unspent(runspec)
            (Path(directory) / "example.runspec.json.attempt-123.abort.json").write_text(
                "{}\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(SystemExit, "already has an attempt receipt"):
                subject.ensure_unspent(runspec)


if __name__ == "__main__":
    unittest.main()
