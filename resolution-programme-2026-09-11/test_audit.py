import unittest
from audit import comparison_checks, interval_state, measurement_summary


class AuditTests(unittest.TestCase):
    def test_interval_crossing_zero_is_not_an_adverse_conclusion(self):
        self.assertEqual(interval_state(-17.3779, .9722), 'includes_zero')
        self.assertEqual(interval_state(-20, -5), 'negative')
        self.assertEqual(interval_state(0, 0), 'includes_zero')
        self.assertEqual(interval_state(None, None), 'not_reported')

    def test_same_sign_does_not_rewrite_magnitude_disagreement(self):
        row = {'manifest_hash': 'a'*64, 'value': -8.52, 'value_lo': -17.3779,
               'value_hi': .9722, 'reproduced_ok': False,
               'replication_comparison': {'original_value': -15.635}}
        r = measurement_summary(row)
        self.assertTrue(r['source_direction_same'])
        self.assertFalse(r['reproduced_ok'])
        self.assertEqual(r['interval_sign'], 'includes_zero')

    def test_stratum_arithmetic_uses_the_served_tolerance_without_widening(self):
        rows = [{'id': 'fail', 'original_value': -24.21, 'replication_value': -3.12,
                 'tolerance': 2.421, 'reproduced_ok': False},
                {'id': 'edge', 'original_value': 1, 'replication_value': 1.1,
                 'tolerance': .1, 'reproduced_ok': True}]
        r = comparison_checks({'replication_comparison': {'strata': rows}})
        self.assertEqual([c['within_tolerance'] for c in r], [False, True])
        self.assertTrue(all(c['matches_served'] for c in r))

    def test_missing_comparison_is_unknown_not_same_direction(self):
        r = measurement_summary({'manifest_hash': 'b'*64, 'value': 0})
        self.assertIsNone(r['source_direction_same'])
        self.assertEqual(r['stratum_arithmetic'], [])


if __name__ == '__main__':
    unittest.main()
