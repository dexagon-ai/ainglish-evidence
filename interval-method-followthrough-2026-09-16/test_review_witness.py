import unittest

import review_witness as witness


class ReviewWitnessTests(unittest.TestCase):
    def test_masks_replay_current_pooled_statistic(self):
        result = witness.replay_masks()
        self.assertTrue(result["sdk_pooled_replay_equal"])
        self.assertGreater(result["local_mask"]["alpha"]["accepted_draws"],
                           result["common_pooled_mask"]["alpha"]["accepted_draws"])

    def test_existing_cell_limit_is_real(self):
        self.assertTrue(witness.capacity()["limit_plus_one_refused_before_replay"])

    def test_valid_opposition_is_not_hidden_by_other_held_form(self):
        self.assertEqual(witness.required_form_decision([None, (-12, -7)]), "opposes")

    def test_missing_bound_cannot_support(self):
        self.assertEqual(witness.required_form_decision([None, (-4, 2)]), "unresolved")

    def test_inclusive_floor_and_ambiguous_interval(self):
        self.assertEqual(witness.required_form_decision([(-5, 2), (-4, 1)]), "supports")
        self.assertEqual(witness.required_form_decision([(-6, 2), (-4, 1)]), "unresolved")

    def test_missing_population_is_not_vacuous_support(self):
        with self.assertRaises(ValueError):
            witness.required_form_decision([])

    def test_malformed_interval_is_not_opposition(self):
        for bound in ((-1, -7), (float("nan"), -7), (-1, float("inf"))):
            with self.assertRaises(ValueError):
                witness.required_form_decision([bound])

    def test_legacy_and_mixed_generations_are_distinct(self):
        self.assertEqual(witness.prospective_branch(False, False), "legacy_unchanged")
        self.assertNotEqual(witness.prospective_branch(False, True),
                            witness.prospective_branch(True, True))


if __name__ == "__main__":
    unittest.main()
