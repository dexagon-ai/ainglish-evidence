"""No-network structural/oracle audit. Synthetic answers must NEVER be filed as evidence."""
import contextlib
import copy
import hashlib
import io
import json
import socket
import tempfile
import types
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from ainglish import panel
from ainglish.client import manifest_commitment
from report_diagnostics import summarize
from capture_raw import capture

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text())


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


class Audit(unittest.TestCase):
    def setUp(self):
        self.spec = load("learnability-preparation.json")
        self.worlds = load("worlds.json")
        self.real = [i for i in self.spec["items"] if not i.get("calibration")]
        self.controls = [i for i in self.spec["items"] if i.get("calibration")]

    def test_exact_frozen_bytes(self):
        for name, expected in load("frozen-inputs.json")["files"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(sha(self.spec["items"]), self.spec["items_sha256"])
        entry = self.spec["entry"]
        self.assertEqual(entry["text"].encode(), (ROOT / "entry.txt").read_bytes())
        self.assertEqual(entry["sha256"], hashlib.sha256(entry["text"].encode()).hexdigest())
        self.assertEqual(entry["text"], load("proposal-definition-snapshot.json")["english_mapping"])
        self.assertEqual(entry["proposal_revision"], self.spec["slug"])

    def test_coverage_and_unique_complete_cases(self):
        self.assertEqual(len(self.real), 64)
        self.assertEqual(len(self.controls), 12)
        self.assertEqual(len({i["id"] for i in self.spec["items"]}), 76)
        self.assertEqual(len({i["english"] for i in self.real}), 64)
        self.assertEqual(len({i["world_id"] for i in self.real}), 32)
        self.assertEqual(Counter(i["tested_form"] for i in self.real), {"finish-started": 32, "interrupt-started": 32})
        self.assertEqual(set(Counter((i["tested_form"], i["family"]) for i in self.real).values()), {8})
        self.assertEqual(sum(i["form_changes_answer"] for i in self.real), 20)
        for item in self.real:
            self.assertEqual(item["english"], item["ainglish"])
            self.assertEqual(len(set(item["options"])), 3)
            self.assertIn(item["answer"], item["options"])
            self.assertNotIn(item["answer"], item["ainglish"])
            self.assertNotIn(self.spec["entry"]["text"], item["ainglish"])

    def test_gold_key_matches_author_review(self):
        audited = {r["id"]: r for r in load("gold-audit.json")["rows"]}
        worlds = {w["id"]: w for w in self.worlds}
        for item in self.real:
            world = worlds[item["world_id"]]
            arm = "finish" if item["tested_form"] == "finish-started" else "interrupt"
            self.assertEqual(item["answer"], world["options"][world[arm]])
            self.assertEqual(item["answer"], audited[item["id"]]["answer"])
            self.assertTrue(audited[item["id"]]["entailment"])
        # This is key/receipt consistency. Semantic entailment is the written author
        # audit, not proven by comparing the answer key with itself.

    def test_answer_position_balance_before_exposure(self):
        for form in ("finish-started", "interrupt-started"):
            for critical in (None, True, False):
                selected = [i for i in self.real if i["tested_form"] == form and (critical is None or i["form_changes_answer"] == critical)]
                positions = Counter(i["options"].index(i["answer"]) for i in selected)
                self.assertEqual(len(positions), 3)
                self.assertLessEqual(max(positions.values()) - min(positions.values()), 1)

    def test_target_independent_calibration(self):
        self.assertTrue(panel._validate_learnability_v2(self.spec, self.real, self.controls))
        target = ("finish-started", "interrupt-started", self.spec["slug"])
        for control in self.controls:
            for token in target:
                self.assertNotIn(token, json.dumps(control))
            self.assertNotEqual(control["english"], control["ainglish"])
        for name in ("qualification-mistral-small3.2.json", "qualification-gemma3.json"):
            screen = load(name)
            self.assertEqual(len(screen["controls"]), 12)
            for cell in screen["controls"]:
                self.assertTrue(all(cell["detectable"] != c["ainglish"] for c in self.controls))

    def test_transport_has_no_ignored_seed_or_opaque_digest(self):
        for ep in self.spec["panel"]:
            self.assertEqual(ep["provider"], "ollama")
            self.assertEqual(panel.request_sampling(ep)["seed"], 2026091981)
            self.assertNotIn("request_seed", ep)
            self.assertEqual(panel.resolve(ep)["api"], "openai")
        panel._validate_real_reader_configuration(self.spec, panel.ask)

    def test_actual_runner_oracle_is_synthetic_and_complete(self):
        manifest = copy.deepcopy(self.spec)
        manifest["_dry_run"] = True
        real_rows, calibration_rows, calls = [], [], []
        oracle = panel.dry_reader(manifest["items"], manifest)
        def recorder(ep, text, question, options):
            calls.append((ep["name"], text, question, tuple(options)))
            return oracle(ep, text, question, options)
        output = io.StringIO()
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited in this audit")), contextlib.redirect_stdout(output):
            result = panel.run_panel(manifest, ask_fn=recorder, cell_results=real_rows, calibration_results=calibration_rows)
        self.assertIsNotNone(result, output.getvalue()[-2000:])
        self.assertEqual(len(real_rows), 256)
        self.assertEqual(len(calibration_rows), 48)
        self.assertEqual(len(calls), 304)
        self.assertEqual(result["metric"], "learnability")
        self.assertIn("DRY-RUN", result["manifest"]["protocol"])
        self.assertIsNone(result["arms"])
        self.assertEqual(result["value"], 1)  # Deliberately cheating oracle, NOT a result.
        self.assertTrue(manifest_commitment(result["manifest"]))
        lookup = {i["id"]: i for i in self.real}
        self.assertEqual(len({(r["item_id"], r["reader"], r["arm"]) for r in real_rows}), 256)
        for row in real_rows:
            item = lookup[row["item_id"]]
            text = item["ainglish"] if row["arm"] == "english" else manifest["entry"]["text"] + "\n\nMarked message:\n" + item["ainglish"]
            self.assertIn((row["reader"], text, item["question"], tuple(item["options"])), calls)
            self.assertEqual(row["strata"]["form"], item["tested_form"])
        (ROOT / "oracle-audit.log").write_text(output.getvalue())
        (ROOT / "oracle-audit-summary.json").write_text(json.dumps({
            "kind": "synthetic-plumbing-audit-only.v1", "reader_calls": 0,
            "synthetic_callback_calls": len(calls), "synthetic_scientific_cells": len(real_rows),
            "synthetic_calibration_cells": len(calibration_rows), "not_evidence": True,
        }, indent=2) + "\n")

    def test_real_target_failure_is_not_calibration_failure(self):
        manifest = copy.deepcopy(self.spec)
        manifest["_dry_run"] = True
        oracle = panel.dry_reader(manifest["items"], manifest)
        target_texts = {i["english"] for i in self.real}
        target_texts |= {manifest["entry"]["text"] + "\n\nMarked message:\n" + i["ainglish"] for i in self.real}
        keys = {}
        for item in self.real:
            for text in (item["english"], manifest["entry"]["text"] + "\n\nMarked message:\n" + item["ainglish"]):
                keys[(text, item["question"], tuple(item["options"]))] = item["answer"]
        def failing_target(ep, text, question, options):
            if text in target_texts:
                gold = keys[(text, question, tuple(options))]
                return next(o for o in options if o != gold)
            return oracle(ep, text, question, options)
        with patch.object(socket.socket, "connect", side_effect=AssertionError("Network prohibited in this audit")), contextlib.redirect_stdout(io.StringIO()):
            result = panel.run_panel(manifest, ask_fn=failing_target)
        self.assertIsNotNone(result)
        self.assertEqual(result["value"], 0)

    def test_no_unsupported_learnability_settlement_strata(self):
        # SDK settlement_strata supports CAD, not learnability. Per-form results must
        # therefore be explicitly published and checked; the pooled row is insufficient.
        self.assertNotIn("settlement_strata", self.spec)
        self.assertTrue(all("strata" in i for i in self.real))

    def synthetic_rows(self):
        return [{"item_id": item["id"], "reader": ep["name"], "arm": arm,
                 "answer": item["answer"], "expected": item["answer"], "correct": True}
                for item in self.real for ep in self.spec["panel"] for arm in ("english", "ainglish")]

    def test_easy_boundary_cases_cannot_hide_core_errors(self):
        rows = self.synthetic_rows()
        critical_ids = {i["id"] for i in self.real if i["tested_form"] == "finish-started" and i["form_changes_answer"]}
        flipped = 0
        for row in rows:
            if row["item_id"] in critical_ids and row["arm"] == "ainglish" and flipped < 3:
                item = next(i for i in self.real if i["id"] == row["item_id"])
                row["answer"] = next(o for o in item["options"] if o != item["answer"])
                row["correct"] = False
                flipped += 1
        report = summarize(self.spec["items"], [ep["name"] for ep in self.spec["panel"]], rows)
        self.assertTrue(report["overall"]["entry"]["at_least_95_percent_on_complete_bank"])
        self.assertTrue(report["by_form"]["finish-started"]["entry"]["at_least_95_percent_on_complete_bank"])
        self.assertFalse(report["by_form"]["finish-started"]["policy_changing_entry"]["at_least_95_percent_on_complete_bank"])
        self.assertFalse(report["author_bank_readability_requirement_met"])

    def test_partial_and_tampered_results_are_not_clean_passes(self):
        readers = [ep["name"] for ep in self.spec["panel"]]
        rows = self.synthetic_rows()
        self.assertFalse(summarize(self.spec["items"], readers, rows[:-1])["author_bank_readability_requirement_met"])
        rows[0]["correct"] = False
        with self.assertRaises(ValueError):
            summarize(self.spec["items"], readers, rows)

    def test_raw_capture_preserves_preparser_output_and_excludes_credentials(self):
        returned = ("\nB\n", False)
        calls = []
        def fake_chat(ep, prompt):
            calls.append((ep, prompt))
            return returned
        module = types.SimpleNamespace(chat=fake_chat)
        with tempfile.TemporaryDirectory(prefix="stop-raw-audit-") as temporary:
            dest = Path(temporary) / "raw.jsonl"
            with capture(module, dest):
                actual = module.chat({"name": "synthetic", "model": "synthetic",
                                      "api_key_env": "SHOULD_NOT_BE_LOGGED", "api_key": "NOT_A_REAL_SECRET"}, "Synthetic prompt\nA, B, C")
                self.assertIs(actual, returned)
            self.assertIs(module.chat, fake_chat)
            text = dest.read_text()
            self.assertNotIn("SHOULD_NOT_BE_LOGGED", text)
            self.assertNotIn("NOT_A_REAL_SECRET", text)
            self.assertEqual(len(calls), 1)
            records = [json.loads(line) for line in text.splitlines()]
            self.assertEqual(records[1]["raw_text"], "\nB\n")
            self.assertEqual(dest.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError), capture(module, dest):
                pass

    def test_raw_capture_records_and_reraises_transport_failure_once(self):
        calls = []
        def fail(ep, prompt):
            calls.append(prompt)
            raise TimeoutError("not logged")
        module = types.SimpleNamespace(chat=fail)
        with tempfile.TemporaryDirectory(prefix="stop-raw-error-audit-") as temporary:
            dest = Path(temporary) / "raw.jsonl"
            with capture(module, dest), self.assertRaises(TimeoutError):
                module.chat({"name": "synthetic", "model": "synthetic"}, "Synthetic timeout prompt")
            self.assertEqual(len(calls), 1)
            records = [json.loads(line) for line in dest.read_text().splitlines()]
            self.assertEqual(records[-1]["exception_type"], "TimeoutError")
            self.assertNotIn("not logged", dest.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
