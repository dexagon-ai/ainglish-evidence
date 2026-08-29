#!/usr/bin/env python3
"""No-call tests for the remote qualification decision surfaces."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

import common
import audit_result
import prepare_plan
import run_once


class RemoteQualificationTests(unittest.TestCase):
    def test_choice_parser_matches_panel_contract(self) -> None:
        self.assertEqual(common.decode_code(" b\n"), "B")
        for bad in (None, "", "A because...", '{"answer":"A"}', "D"):
            self.assertIsNone(common.decode_code(bad))

    def test_base_url_boundary(self) -> None:
        for good in (
            "https://inference.example/v1",
            "http://127.0.0.1:8645/v1",
            "http://[::1]:8645/v1",
            "http://localhost:8645/v1",
        ):
            self.assertEqual(common.safe_base_url(good), good)
        for bad in (
            "http://inference.example/v1",
            "ftp://localhost/model",
            "https://user:secret@example.test/v1",
            "https://example.test/v1?token=secret",
            "relative/path",
        ):
            with self.assertRaises(SystemExit):
                common.safe_base_url(bad)

    def test_catalog_binding_is_service_not_weight_identity(self) -> None:
        original = common.request_json
        common.request_json = lambda *_args, **_kwargs: {
            "data": [
                {"id": "vendor/exact", "owned_by": "vendor", "object": "model"},
                {"id": "vendor/other"},
            ]
        }
        try:
            receipt = common.model_catalog_binding(
                "https://reader.example/v1", "vendor/exact", "none"
            )
        finally:
            common.request_json = original
        self.assertEqual(receipt["requested_model"], "vendor/exact")
        self.assertEqual(receipt["weight_identity"], "provider-opaque")
        self.assertTrue(receipt["entry_sha256"].startswith("sha256:"))

    def test_content_digest_fails_closed(self) -> None:
        value = common.add_digest({"kind": "test", "value": 1})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(common.checked(path), value)
            value["value"] = 2
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(SystemExit):
                common.checked(path)

    def test_gates_retain_adverse_and_partial_results(self) -> None:
        format_rows = [
            {
                "valid_choice": True,
                "target_correct": True,
                "fault": None,
                "truncated": False,
                "response_model_mismatch": False,
            }
            for _ in range(12)
        ]
        self.assertTrue(common.format_passed(common.observed_format(format_rows)))
        format_rows[-1]["target_correct"] = False
        self.assertFalse(common.format_passed(common.observed_format(format_rows)))

        packet = common.checked(common.REPO / common.PACKETS["development"]["file"])
        semantic_rows = []
        for item in packet["items"]:
            semantic_rows.append({
                "axis": item["axis"], "expected_label": item["answer"],
                "valid_choice": True, "correct": True, "fault": None,
                "truncated": False, "response_model_mismatch": False,
            })
        observed = common.observed_semantic(packet, semantic_rows)
        self.assertTrue(common.semantic_passed(common.PACKETS["development"]["gate"], observed))
        for row in semantic_rows:
            if row["axis"] == packet["axes"][0]:
                row["correct"] = False
        observed = common.observed_semantic(packet, semantic_rows)
        self.assertFalse(common.semantic_passed(common.PACKETS["development"]["gate"], observed))

    def test_bearer_name_is_fixed_and_secret_is_not_a_receipt(self) -> None:
        old = os.environ.get(common.API_KEY_ENV)
        os.environ[common.API_KEY_ENV] = "sentinel-secret"
        try:
            headers = common.auth_headers("environment-bearer")
            self.assertEqual(headers["Authorization"], "Bearer sentinel-secret")
            self.assertNotIn("sentinel-secret", json.dumps(common.PACKETS))
        finally:
            if old is None:
                os.environ.pop(common.API_KEY_ENV, None)
            else:
                os.environ[common.API_KEY_ENV] = old

    def test_example_configuration_builds_without_catalog_or_inference(self) -> None:
        example = json.loads(
            (common.ROOT / "candidate-nous-portal.example.json").read_text(encoding="utf-8")
        )
        example["model_catalog"] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            path.write_text(json.dumps(example), encoding="utf-8")
            config = prepare_plan.load_candidate(path)
        candidate, transport = prepare_plan.candidate_receipt(config)
        self.assertIsNone(candidate["model_catalog_binding"])
        self.assertEqual(candidate["digest_source"], "provider-opaque")
        self.assertEqual(transport["base_url"], "http://127.0.0.1:8645/v1")

    def test_runner_rows_round_trip_through_offline_auditor(self) -> None:
        packet = common.checked(common.REPO / common.PACKETS["development"]["file"])
        plan = {
            "format_stage": {"controls": common.format_controls()},
            "semantic_stage": {
                "prompt_contract": "Classify the hypothesis and return one code.",
                "gate": common.PACKETS["development"]["gate"],
            },
            "transport": {"model": "vendor/exact"},
        }
        outputs = [control["target"] for control in plan["format_stage"]["controls"]]
        for item in packet["items"]:
            mapping = {common.CODES[index]: label for index, label in enumerate(item["options"])}
            outputs.append(next(code for code, label in mapping.items() if label == item["answer"]))
        iterator = iter(outputs)

        def fake_cell(_plan: dict, _prompt: str) -> dict:
            raw = next(iterator)
            return {
                "raw_output": raw,
                "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "finish_reason": "stop",
                "truncated": False,
                "fault": None,
                "response_model": "vendor/exact",
                "response_model_mismatch": False,
                "system_fingerprint": "test",
                "reasoning_bytes_returned": 0,
                "usage": None,
            }

        original = run_once.request_cell
        run_once.request_cell = fake_cell
        try:
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as journal:
                format_rows, ordinal = run_once.run_format(plan, journal, 0)
                semantic_rows, ordinal = run_once.run_semantic(plan, packet, journal, ordinal)
        finally:
            run_once.request_cell = original
        self.assertEqual(ordinal, 36)
        self.assertTrue(common.format_passed(audit_result.audit_format(plan, format_rows)))
        semantic = audit_result.audit_semantic(plan, packet, semantic_rows, True)
        self.assertTrue(common.semantic_passed(plan["semantic_stage"]["gate"], semantic))

    def test_rehashed_plan_cannot_weaken_frozen_gates(self) -> None:
        example = json.loads(
            (common.ROOT / "candidate-nous-portal.example.json").read_text(encoding="utf-8")
        )
        example["model_catalog"] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            path.write_text(json.dumps(example), encoding="utf-8")
            config = prepare_plan.load_candidate(path)
        candidate, transport = prepare_plan.candidate_receipt(config)
        packet = common.PACKETS["development"]
        plan = {
            "kind": "ainglish.panel.remote-reader-qualification-plan.v1",
            "result_kind": "ainglish.panel.remote-reader-qualification-result.v1",
            "phase": "development",
            "candidate": candidate,
            "transport": transport,
            "development_receipt": None,
            "format_stage": {
                "answer_protocol": "opaque-choice-v1",
                "controls": common.format_controls(),
                "gate": copy.deepcopy(common.FORMAT_GATE),
            },
            "semantic_stage": {
                "packet": {"file": packet["file"], "content_sha256": packet["content_sha256"]},
                "gate": copy.deepcopy(packet["gate"]),
                "pass_meaning": packet["pass_meaning"],
            },
        }
        common.validate_plan_contract(plan)
        plan["format_stage"]["gate"]["target_correct_cells_required"] = 11
        with self.assertRaises(SystemExit):
            common.validate_plan_contract(plan)


if __name__ == "__main__":
    unittest.main()
