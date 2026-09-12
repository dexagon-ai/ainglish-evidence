import unittest
from verified_preparation import token_spec,decision,decision_fixtures

class VerifiedPreparationTests(unittest.TestCase):
    def test_distinct_complete_cost_pairs_and_equal_strata(self):
        pairs=token_spec()['manifest']['test_set']
        self.assertEqual(32,len(pairs))
        self.assertEqual(32,len({(x['english'],x['ainglish']) for x in pairs}))
        for form in ['verified','settled','refuted','unverified']:
            self.assertEqual(8,sum(x['stratum']==form for x in pairs))

    def test_policy_is_total_and_prioritised(self):
        self.assertEqual('dispute',decision(True,True,True))
        self.assertEqual('re-verify',decision(False,True,True))
        self.assertEqual('act',decision(False,False,True))
        self.assertEqual('wait',decision(False,False,False))

    def test_six_examples_unique_answers_not_inference(self):
        d=decision_fixtures();self.assertFalse(d['executable_panel'])
        self.assertEqual(6,len(d['items']))
        for row in d['items']:self.assertEqual(1,row['options'].count(row['answer']))

if __name__=='__main__':unittest.main()
