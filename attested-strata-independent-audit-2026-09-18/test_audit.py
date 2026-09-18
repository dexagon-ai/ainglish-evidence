import json
from pathlib import Path
import unittest


class AuditReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(Path(__file__).with_name('report.json').read_text())

    def test_verified_population_and_not_a_measurement(self):
        self.assertEqual(1370, self.r['population_preimage_verified']['measurements'])
        self.assertFalse(self.r['candidate_code_executed'])
        self.assertFalse(self.r['measurement_filed'])

    def test_all_process_seeds_retained(self):
        runs = self.r['process_seed_replays']
        self.assertEqual(list(range(12)), [r['python_hash_seed'] for r in runs])
        self.assertGreater(self.r['distinct_fixture_outcome_digests'], 1)
        self.assertTrue(any(not r['F3d']['match'] for r in runs))

    def test_counterfactual_mismatch_not_hidden(self):
        self.assertEqual({'oppose': 24, 'agree': 29}, self.r['counterfactual_reference_counts'])
        self.assertEqual(25, len(self.r['counterfactual_disagreements']))
        self.assertTrue(self.r['degenerate_pair_reference'][1]['reproduced_ok'])

    def test_rounding_boundary_is_a_real_difference(self):
        self.assertTrue(self.r['F4']['row_predicts_refusal'])
        self.assertFalse(self.r['F4']['reference_predicts_refusal'])
        self.assertTrue(self.r['F4']['matcher_is_unconditional'])

    def test_missing_or_unexecuted_checks_named(self):
        self.assertFalse(self.r['F10_in_fixture_output'])
        self.assertTrue(self.r['F11_matcher_is_unconditional'])
        self.assertFalse(self.r['raw_frozen_rows_in_packet'])
        self.assertFalse(self.r['raw_frozen_proposals_in_packet'])

    def test_unit_witness_is_not_claimed_as_real_journal(self):
        w = self.r['pooled_bound_unit_witness']
        self.assertEqual('supports', w['reference_result'])
        self.assertEqual('unresolved', w['declared_rule_result'])
        self.assertIn('not an attested execution', w['scope'])


if __name__ == '__main__':
    unittest.main()
