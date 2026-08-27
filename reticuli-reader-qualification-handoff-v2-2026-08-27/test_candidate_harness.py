#!/usr/bin/env python3
"""Adversarial offline tests for the staged fresh-lineage harness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_candidate
import build_candidate_plan
from run_candidate_once import decode


def projected_row(raw: str) -> dict:
    parsed, parse_error, exact = decode(raw)
    return {
        "stage": "format",
        "control_id": "format-01",
        "target": "A",
        "raw_output": raw,
        "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "parsed": parsed,
        "parse_error": parse_error,
        "valid_json": parse_error is None,
        "schema_exact": exact,
        "target_correct": exact and parsed["answer"] == "A",
        "thinking_bytes": 0,
        "fault": None,
        "timing": {},
    }


class DecodeTests(unittest.TestCase):
    def test_only_single_opaque_codes_are_exact(self) -> None:
        self.assertTrue(decode('{"answer":"A"}')[2])
        for raw in ('{"answer":""}', '{"answer":"AA"}', '{"answer":"D"}', '{"answer":"A","extra":1}'):
            self.assertFalse(decode(raw)[2], raw)

    def test_invalid_json_is_not_exact(self) -> None:
        parsed, error, exact = decode("A")
        self.assertIsNone(parsed)
        self.assertIsNotNone(error)
        self.assertFalse(exact)


class AuditProjectionTests(unittest.TestCase):
    def test_raw_projection_is_recomputed(self) -> None:
        row = projected_row('{"answer":"A"}')
        audit_candidate.validate_raw_projection(row)
        row["parsed"] = {"answer": "B"}
        with self.assertRaisesRegex(SystemExit, "raw-output projection drift"):
            audit_candidate.validate_raw_projection(row)

    def test_empty_answer_cannot_be_claimed_as_schema_exact(self) -> None:
        row = projected_row('{"answer":""}')
        self.assertFalse(row["schema_exact"])
        row["schema_exact"] = True
        with self.assertRaisesRegex(SystemExit, "raw-output projection drift"):
            audit_candidate.validate_raw_projection(row)

    def test_journal_rows_are_bound_to_result_rows(self) -> None:
        row = projected_row('{"answer":"A"}')
        plan = {"content_sha256": "plan-digest"}
        format_observed = {
            "valid_json_cells": 1,
            "schema_exact_cells": 1,
            "target_correct_cells": 1,
            "thinking_bytes": 0,
            "fault_cells": 0,
        }
        events = [
            {"event": "run_started", "started_at": "start", "plan_sha256": "plan-digest"},
            {"event": "cell_attempted", "stage": "format", "ordinal": 1, "control_id": "format-01"},
            {"event": "cell_recorded", "stage": "format", "ordinal": 1, "row": row},
            {"event": "format_completed", "observed": format_observed, "passed": True},
            {"event": "run_completed", "format_passed": True, "semantic_cells": 0, "development_passed": False},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = root / "attempt.jsonl"
            journal.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
            result = {
                "started_at": "start",
                "attempt_journal": {"file": journal.name, "sha256": hashlib.sha256(journal.read_bytes()).hexdigest()},
                "format": {"observed": format_observed, "passed": True},
                "semantic": {"passed": False},
            }
            prior_root = audit_candidate.ROOT
            audit_candidate.ROOT = root
            try:
                audit_candidate.validate_journal(plan, result, [row], [])
                altered = dict(row)
                altered["target"] = "B"
                with self.assertRaisesRegex(SystemExit, "journal cell sequence drift"):
                    audit_candidate.validate_journal(plan, result, [altered], [])
            finally:
                audit_candidate.ROOT = prior_root


class ProspectiveSelectionTests(unittest.TestCase):
    SOURCE = "command-r:35b-08-2024-q4_K_M"

    @staticmethod
    def fake_get(path: str) -> dict:
        if path == "/api/version":
            return {"version": "0.32.7"}
        if path == "/api/tags":
            return {"models": [{"name": ProspectiveSelectionTests.SOURCE,
                                 "digest": "376304b5a505" + "0" * 52}]}
        raise AssertionError(path)

    @staticmethod
    def fake_post(path: str, payload: dict) -> dict:
        if path != "/api/show" or payload != {"model": ProspectiveSelectionTests.SOURCE}:
            raise AssertionError((path, payload))
        return {"capabilities": ["completion"], "details": {
            "family": "command-r", "families": ["command-r"],
            "parameter_size": "35B", "quantization_level": "Q4_K_M", "format": "gguf",
        }}

    def test_plan_preserves_prospective_host_gate_and_exact_candidate(self) -> None:
        with mock.patch.object(build_candidate_plan, "get", side_effect=self.fake_get), \
             mock.patch.object(build_candidate_plan, "post", side_effect=self.fake_post):
            plan = build_candidate_plan.build(self.SOURCE, "test-phase")
        self.assertEqual(plan["candidate"]["source_model"], self.SOURCE)
        self.assertEqual(plan["gpu_gate"]["minimum_total_free_mib"], 30000)
        self.assertEqual(plan["gpu_gate"]["maximum_utilization_percent"], 15)
        self.assertEqual(plan["runtime"]["ollama_version"], "0.32.7")

    def test_changed_registry_digest_refuses_before_plan(self) -> None:
        def changed_tags(path: str) -> dict:
            value = self.fake_get(path)
            if path == "/api/tags":
                value["models"][0]["digest"] = "f" * 64
            return value
        with mock.patch.object(build_candidate_plan, "get", side_effect=changed_tags), \
             mock.patch.object(build_candidate_plan, "post", side_effect=self.fake_post):
            with self.assertRaisesRegex(SystemExit, "registry digest prefix"):
                build_candidate_plan.build(self.SOURCE, "test-phase")


if __name__ == "__main__":
    unittest.main()
