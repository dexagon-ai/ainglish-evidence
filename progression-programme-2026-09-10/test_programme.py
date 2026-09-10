import unittest
from acceptance_fixtures import check
from resolution_audit import lattice, resolutions


class ProgrammeTests(unittest.TestCase):
    def test_eighteen_acceptance_cases_and_margin_sensitivity(self):
        self.assertEqual(len(check()), 18)

    def test_unequal_arms_are_not_one_over_item_count(self):
        cells = [{'arm': 'english', 'correct': True}] * 3 + [{'arm': 'ainglish', 'correct': True}] * 4
        actual = lattice(cells)
        self.assertAlmostEqual(actual['delta_grid_step_pp'], 100/12)
        self.assertNotEqual(actual['delta_grid_step_pp'], 100/7)
        self.assertEqual(actual['rederived_pooled_value'], 0)

    def test_unknown_is_not_zero_precision(self):
        self.assertIsNone(resolutions({'accuracy_resolution': {'scored_cells': 3}})['aggregate'])
        self.assertIsNone(lattice([{'arm': 'english', 'correct': True}]))

    def test_do_not_apply_lattice_to_a_different_reported_estimator(self):
        row = {'value': 80, 'interval_provenance': {'verified': True},
               'interval_provenance_attestation': {'items': [{'id': 'a', 'stratum': 's'}],
                   'cells': [{'item_id': 'a', 'arm': 'english', 'correct': True},
                             {'item_id': 'a', 'arm': 'ainglish', 'correct': True}]},
               'stratum_results': [{'id': 's', 'value': 0}]}
        actual = resolutions(row)
        self.assertFalse(actual['aggregate']['matches_served_point'])
        self.assertTrue(actual['strata']['s']['matches_served_point'])


if __name__ == '__main__':
    unittest.main()
