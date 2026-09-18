import copy
import unittest

import audit


class SuccessorAuditTests(unittest.TestCase):
    def test_self_comparison_does_not_override_real_legacy_oracle(self):
        fixture = {"reference": [{"rows": [{"hash": "12345678", "before_0_37_0": "supports", "after": "supports"}]}]}
        oracle = {"observations": [{"hash": "12345678abcdef", "legacy_prerequisite_stance": "unresolved"}]}
        result = audit.legacy_mismatches(fixture, oracle)
        self.assertFalse(result[0]["matches_real_legacy"])

    def test_oracle_population_cannot_be_silently_dropped(self):
        with self.assertRaises(AssertionError):
            audit.legacy_mismatches({"reference": [{"rows": []}]}, {"observations": [{"hash": "12345678", "legacy_prerequisite_stance": "unresolved"}]})

    def test_contract_listing_normalisation_keeps_content(self):
        value = {"classes": {"cad_at_least_list": [["z", {"at_least": 0}], ["a", {"at_least": -5}]]}, "other": 1}
        original = copy.deepcopy(value)
        normalized = audit.normalise_census(value)
        self.assertEqual(value, original)
        self.assertEqual(normalized["classes"]["cad_at_least_list"], list(reversed(value["classes"]["cad_at_least_list"])))
        self.assertEqual(normalized["other"], 1)

    def witness_input(self, bounds):
        cf = [{"orig_hash": "o", "rep_hash": "r", "counterfactual": "agree", "strata": {"a": {"orig": [-2, 0], "rep": [0, 0]}}}]
        rows = {"o": {"proposal": {"public_id": "p"}, "value_lo": bounds[0][0], "value_hi": bounds[0][1]},
                "r": {"value_lo": bounds[1][0], "value_hi": bounds[1][1], "replication_comparison": {"commensurability": {"verdict": "commensurable"}}}}
        widths = {"o": {"pooled": bounds[0]}, "r": {"pooled": bounds[1]}}
        return cf, rows, widths

    def test_disjoint_pooled_bounds_are_not_hidden_by_cell_overlap(self):
        result = audit.pooled_witnesses(*self.witness_input(([-2, -1], [0, 0])))
        self.assertEqual(len(result), 1)

    def test_touching_pooled_bounds_intersect(self):
        self.assertEqual(audit.pooled_witnesses(*self.witness_input(([-2, 0], [0, 0]))), [])

    def test_existing_disagreement_is_not_counted_as_new_policy_change(self):
        cf, rows, widths = self.witness_input(([-2, -1], [0, 0]))
        cf[0]["counterfactual"] = "oppose"
        self.assertEqual(audit.pooled_witnesses(cf, rows, widths), [])


if __name__ == "__main__":
    unittest.main()
