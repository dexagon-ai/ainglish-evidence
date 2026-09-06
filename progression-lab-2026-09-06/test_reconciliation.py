"""Tri-state, hold and provenance regressions; no network or governance writes."""
import unittest
from reconcile import classify


class ClassificationTests(unittest.TestCase):
    def test_eligibility_does_not_invent_a_verdict(self):
        for value, expected in [(True, 'eligible_agreement'), (False, 'eligible_disagreement'),
                                (None, 'eligible_outcome_not_recorded')]:
            self.assertEqual(classify({'settlement_eligible': True, 'reproduced_ok': value}), expected)

    def test_non_counting_precedence(self):
        base = {'settlement_eligible': True, 'reproduced_ok': False}
        cases = [({'voided_at': '2026-09-06'}, 'retracted'),
                 ({'evidence_state': 'suspended'}, 'inactive_evidence'),
                 ({'replication_comparison': {'distinct': True}}, 'different_estimand'),
                 ({'replication_comparison': {'commensurability': {'held_on': ['unit_mismatch']}}}, 'comparison_hold'),
                 ({'settlement_eligible': False}, 'non_counting_replication'),
                 ({'settlement_eligible': None}, 'eligibility_not_recorded')]
        for patch, expected in cases:
            self.assertEqual(classify(dict(base, **patch)), expected)


if __name__ == '__main__': unittest.main()
