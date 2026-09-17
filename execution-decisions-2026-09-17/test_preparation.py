import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


class PreparationTest(unittest.TestCase):
    def setUp(self):
        self.resume = json.loads((HERE/'resume-phase-one.json').read_text())
        self.they = json.loads((HERE/'they-method-choice.json').read_text())

    def test_no_silent_authorization_or_spend(self):
        self.assertEqual(self.resume['state'],'HELD_NO_MINT_NO_READER_CALLS')
        self.assertIsNone(self.resume['author_design_acceptance'])
        self.assertIsNone(self.resume['accepted_independent_executor'])
        self.assertEqual(self.resume['actual_reader_calls'],0)
        self.assertEqual(self.resume['attempt_ids'],[])
        self.assertIsNone(self.they['author_decision'])
        self.assertFalse(self.they['target_bank_made'])
        self.assertFalse(self.they['amendment_dry_run'])

    def test_exact_accepted_core_and_no_boundary_pooling(self):
        candidate = self.resume['runspec_candidate_not_authorized']
        source = json.loads((HERE.parent/'resume-boundary-correction-2026-09-16/careful-items.json').read_text())
        self.assertEqual(candidate['items'][:64],source[:64])
        self.assertEqual(len(candidate['items']),72)
        self.assertTrue(all(x.get('calibration') for x in candidate['items'][64:]))
        self.assertEqual(candidate['attempt']['planned_sample']['total_calls'],160)

    def test_allocation_and_grouping_are_honest(self):
        self.assertEqual(sum(sum(x.values()) for x in self.resume['allocation'].values()),128)
        groups = self.resume['analysis_groups_not_independent_world_claims']
        self.assertEqual(len(groups),32)
        self.assertTrue(all(len(x)==2 for x in groups.values()))

    def test_bulky_bank_is_pinned_outside_small_manifest(self):
        self.assertLess(self.resume['candidate_manifest_canonical_bytes'],20480)
        candidate = self.resume['runspec_candidate_not_authorized']
        self.assertIn('/5a9f85664b4edf4f84ceb1a878769e0908ddd1b4/',candidate['items_url'])
        self.assertEqual(candidate['items'],json.loads((HERE/'resume-core-items.json').read_text()))

    def test_instruments_preserve_exact_existing_qualifications(self):
        panel = self.resume['runspec_candidate_not_authorized']['panel']
        receipts = self.resume['runspec_candidate_not_authorized']['reader_qualifications']
        self.assertEqual(len({x['lineage']['key'] for x in receipts}),2)
        self.assertEqual({x['model_digest'] for x in panel},
                         {x['reader']['model_digest'] for x in receipts})
        self.assertTrue(all(x['result']['passed'] for x in receipts))

    def test_they_changes_only_method_sentence(self):
        original = json.loads((HERE.parent/'preservation-successor-review-2026-09-16/amendment-changes.json').read_text())
        candidate = self.they['proposed_candidate']
        self.assertEqual([k for k in original if original[k]!=candidate[k]],['predicted_measurement'])
        self.assertEqual(candidate['predicted_measurement'], original['predicted_measurement'].replace(
            self.they['replace_exact'],self.they['with_exact']))

    def test_they_doc_and_proposed_replacement_match(self):
        lines = (HERE/'THEY-METHOD-v2.md').read_text().splitlines()
        replacement = ' '.join(x[2:] for x in lines if x.startswith('> '))
        self.assertEqual(replacement,self.they['with_exact'])


if __name__ == '__main__':
    unittest.main()
