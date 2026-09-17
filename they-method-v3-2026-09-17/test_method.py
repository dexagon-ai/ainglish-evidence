from copy import deepcopy
import json
from pathlib import Path
import unittest
import prepare

HERE=Path(__file__).resolve().parent


class MethodCorrectionTest(unittest.TestCase):
    def setUp(self):
        self.v3=json.loads((HERE/'method-choice.json').read_text())
        self.v2=json.loads((HERE.parent/'execution-decisions-2026-09-17/they-method-choice.json').read_text())

    def test_reproducible_exact_artifact(self):
        self.assertEqual(prepare.build(),self.v3)
        self.assertEqual(self.v3['proposed_candidate_sha256'],prepare.digest(self.v3['proposed_candidate']))

    def test_only_method_text_changed(self):
        source=self.v2['proposed_candidate'];candidate=self.v3['proposed_candidate']
        self.assertEqual([k for k in source if source[k]!=candidate[k]],['predicted_measurement'])
        self.assertEqual(candidate['predicted_measurement'],source['predicted_measurement'].replace(self.v3['replace_exact'],self.v3['with_exact'],1))
        restored=self.v3['with_exact'].replace('they-method-policy-v3:','they-method-policy-v2:',1)
        restored=restored.replace('beside every reported interval and bundle decision.','beside every reported bundle decision.',1)
        restored=restored.replace(self.v3['added_controls_clause'],'',1)
        self.assertEqual(restored,self.v3['replace_exact'])

    def test_reviews_are_not_invented_and_holds_remain(self):
        self.assertEqual(self.v3['accepted_v2_candidate_sha256'],'760c177e82c0b623bd7ce0a65ace8808846631a6ab04d22855f8bed9c408f63e')
        self.assertIsNone(self.v3['author_acceptance_of_v3']);self.assertIsNone(self.v3['reviewer_acceptance_of_v3'])
        self.assertFalse(self.v3['target_bank_made']);self.assertFalse(self.v3['amendment_dry_run'])
        self.assertEqual(self.v3['reader_calls'],0)

    def test_safeguards_are_in_candidate_not_just_memo(self):
        text=self.v3['proposed_candidate']['predicted_measurement']
        for phrase in ['every reported interval and bundle decision','All-unknown and fixed-option',
                       'per-dimension control-failure rates','no single shortcut or reused answer',
                       'Before target-bank creation, amendment dry-run or attempt']:
            self.assertIn(phrase,text)


if __name__=='__main__':unittest.main()
