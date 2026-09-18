"""Synthetic test fixtures are exposed software tests, not a future measurement bank."""
import ast
import copy
import json
import unittest

from audit import ARCHIVE, bank_summary, require_position_balance, replay_original


def fixture():
    return [
        {"id": f"test-{form}-{position}", "form": f"form-{form}",
         "options": [f"choice-{i}" for i in range(6)], "answer": f"choice-{position}"}
        for form in range(6) for position in range(6)
    ]


class PositionAuditTests(unittest.TestCase):
    def test_retired_carrier_refuses_before_live_work(self):
        tree = ast.parse((ARCHIVE / "run_comprehension_once.py").read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        self.assertIsInstance(main.body[0], ast.Raise)
        self.assertEqual(main.body[0].exc.func.id, "SystemExit")
        self.assertIn("RETIRED 2026-09-18", main.body[0].exc.args[0].value)

    def test_balanced_exposed_fixture(self):
        result = require_position_balance(fixture())
        self.assertEqual(result["overall"]["gold_position_counts"], [6] * 6)

    def test_global_balance_does_not_hide_form_shortcut(self):
        rows = fixture()
        for row in rows:
            row["answer"] = "choice-" + row["form"].split("-")[-1]
        self.assertTrue(bank_summary(rows)["overall"]["balanced_to_one"])
        with self.assertRaisesRegex(ValueError, "form:"):
            require_position_balance(rows)

    def test_original_all_first_rejected(self):
        rows = json.loads((ARCHIVE / "fidelity-cases.json").read_text())
        self.assertEqual(bank_summary(rows)["overall"]["constant_first_correct"], 96)
        with self.assertRaises(ValueError):
            require_position_balance(rows)

    def test_dormant_carrier_all_first_rejected(self):
        rows = json.loads((ARCHIVE / "comprehension-items.json").read_text())
        self.assertEqual(bank_summary(rows)["overall"]["constant_first_correct"], 120)
        with self.assertRaises(ValueError):
            require_position_balance(rows)

    def test_malformed_golds_options_and_ids_rejected(self):
        for mutation in ("missing", "duplicate_option", "duplicate_id"):
            with self.subTest(mutation=mutation):
                rows = fixture()
                if mutation == "missing":
                    rows[0]["answer"] = "not-an-option"
                elif mutation == "duplicate_option":
                    rows[0]["options"][1] = rows[0]["options"][0]
                else:
                    rows[1]["id"] = rows[0]["id"]
                with self.assertRaises(ValueError):
                    bank_summary(rows)

    def test_original_raw_cells_preserved(self):
        rows = json.loads((ARCHIVE / "fidelity-cases.json").read_text())
        result = json.loads((ARCHIVE / "fidelity-result.json").read_text())
        replay = replay_original(rows, result)
        self.assertEqual(sorted(row["correct"] for row in replay.values()), [73, 83])
        self.assertEqual(sum(row["format_invalid"] for row in replay.values()), 35)
        self.assertEqual(sum(row["valid_wrong"] for row in replay.values()), 1)

    def test_tampered_raw_result_rejected(self):
        rows = json.loads((ARCHIVE / "fidelity-cases.json").read_text())
        result = json.loads((ARCHIVE / "fidelity-result.json").read_text())
        changed = copy.deepcopy(result)
        changed["rows"][0]["raw_output"] = "B"
        with self.assertRaisesRegex(ValueError, "digest"):
            replay_original(rows, changed)


if __name__ == "__main__":
    unittest.main()
