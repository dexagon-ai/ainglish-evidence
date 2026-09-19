"""CPU-only design tests, not measured comprehension or independent verification."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch
import prepare as p


class DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = p.make_bank()

    def reject(self, mutate):
        bank = copy.deepcopy(self.bank)
        mutate(bank)
        bank['sha256'] = p.digest(bank['items'])
        with self.assertRaises(AssertionError):
            p.audit(bank)

    def test_complete_audit(self):
        report = p.audit(self.bank)
        self.assertEqual(report['reader_calls_performed'], 0)
        self.assertEqual(report['planned_panel_calls_including_controls'], 240)

    def test_sdk_assignment_matches_every_planned_cell(self):
        from ainglish.panel import arm_for
        for item in self.bank['items'][:96]:
            for reader in p.READERS:
                self.assertEqual(p.arm(p.SEED, reader, item['id']), arm_for(p.SEED, reader, item['id']))

    def test_actual_sdk_runner_matches_plan_not_only_helper(self):
        from runner_assignment_audit import runner_assignments, report
        actual = report(self.bank, runner_assignments(self.bank))
        self.assertEqual(actual['actual_plan_disagreements'], 0)
        self.assertEqual(actual['balanced_reader_anchor_frame_blocks'], 32)
        self.assertEqual(actual['opposite_arm_items'], 96)

    def test_historical_name_precision_error_is_detected_by_actual_runner(self):
        from runner_assignment_audit import runner_assignments
        with patch.object(p, 'READERS', p.ROSTER_IDENTIFIERS):
            historical = p.make_bank()
        self.assertEqual(historical['sha256'], 'a1e843a721315ed6f1ff7dd2e43ea0f4ae7d5c3a48387742f5b3c7ae3d8ef7ac')
        actual = [row for row in runner_assignments(historical) if not row['calibration']]
        wrong = sum(row['arm'] != p.arm(p.SEED, row['reader'] + '@q4_k_m', row['item_id']) for row in actual)
        self.assertEqual(wrong, 106)
        with self.assertRaises(AssertionError):
            p.audit(historical)

    def test_precision_is_retained_as_separate_instrument_identity(self):
        self.assertEqual(self.bank['roster_identifiers'], [r + '@q4_k_m' for r in self.bank['readers']])
        self.reject(lambda b: b.update(assignment_key='name@precision'))

    def test_reproducible_bytes(self):
        self.assertEqual(p.make_bank(), self.bank)

    def test_original_artifact_digest_unchanged(self):
        source = json.loads(p.SOURCE.read_text())
        self.assertEqual(p.digest(source['items']), 'caf368bb529fbfee151e584a7f65dcf22c5b36226af34318562bc4016be9352a')

    def test_duplicate_id_rejected(self):
        self.reject(lambda b: b['items'][0].update(id=b['items'][1]['id']))

    def test_wrong_gold_rejected(self):
        self.reject(lambda b: b['items'][0].update(answer='no'))

    def test_wrong_oracle_rejected(self):
        self.reject(lambda b: b['items'][0]['oracle'].update(intended=False))

    def test_comparator_drift_rejected(self):
        self.reject(lambda b: b['items'][0].update(english=b['items'][0]['english'] + ' Extra clue.'))

    def test_bare_arm_drift_rejected(self):
        self.reject(lambda b: b['items'][0].update(bare='An unrelated report.'))

    def test_original_arm_overlap_rejected(self):
        old = json.loads(p.SOURCE.read_text())['items'][0]['english']
        self.reject(lambda b: b['items'][0].update(english=old))

    def test_missing_calibration_rejected(self):
        self.reject(lambda b: b['items'].pop())

    def test_missing_qualification_rejected(self):
        self.reject(lambda b: b['qualification_controls'].pop())

    def test_seed_drift_rejected(self):
        self.reject(lambda b: b.update(seed=p.SEED + 1))

    def test_roster_drift_rejected(self):
        self.reject(lambda b: b['readers'].reverse())

    def test_all_first_gold_rejected(self):
        def mutate(b):
            for i in b['items'][:96]:
                i['options'] = [i['answer']] + [x for x in ('yes', 'no', 'cannot-tell') if x != i['answer']]
        self.reject(mutate)

    def test_assignment_imbalance_rejected(self):
        def mutate(b):
            i = b['items'][0]
            old = p.arm(p.SEED, p.READERS[0], i['id'])
            i['id'] = p.balanced_id('wrong-assignment-test', 'english' if old == 'ainglish' else 'ainglish')
        self.reject(mutate)

    def test_only_preparation_status_allowed(self):
        self.reject(lambda b: b.update(status='approved_to_run'))

    def test_does_not_reuse_original_control_side(self):
        old = json.loads(p.SOURCE.read_text())['qualification_controls'][0]['detectable']
        self.reject(lambda b: b['qualification_controls'][0].update(detectable=old))


if __name__ == '__main__':
    unittest.main()
