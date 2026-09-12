import copy
import unittest
from quality_checks import exposure_counts, rent_learning_oracle

def row():
    text = "Fictional booking RL-test. One arrangement concerns the camera. The desk switches on an amber indicator for the party that obtains temporary use of the asset, and leaves the other party's indicator off. Adina will rent-borrow the camera from Indra."
    return {'english':text,'ainglish':text, 'question':"Should the desk switch on Adina's amber indicator for this booking?",
            'options':['Yes','No'], 'answer':'Yes'}

class QualityTests(unittest.TestCase):
    def test_counts_are_not_pooled_arm_denominators(self):
        items=[{} for _ in range(96)]+[{'calibration':True} for _ in range(12)]
        x=exposure_counts(items,2,'comprehension_accuracy_delta')
        self.assertEqual((192,48,None),(x['planned_target_calls'],x['planned_calibration_calls'],x['per_target_arm_calls']))
        self.assertIsNone(x['independent_trials'])
        self.assertIsNone(x['observed_calls'])

    def test_learning_counts_both_exposures(self):
        x=exposure_counts([{}]*64+[{'calibration':True}]*8,1,'learnability')
        self.assertEqual((128,16,64),(x['planned_target_calls'],x['planned_calibration_calls'],x['per_target_arm_calls']))

    def test_count_refuses_false_precision(self):
        for n in [True,0,1.0]:
            with self.assertRaises(ValueError):exposure_counts([{}],n,'learnability')
        with self.assertRaises(ValueError):exposure_counts([{'calibration':'false'}],1,'learnability')
        with self.assertRaises(ValueError):exposure_counts([{}],1,'robustness_delta')

    def test_gold_comes_from_visible_role_not_hidden_answer(self):
        x=row();self.assertTrue(rent_learning_oracle(x)['key_agrees'])
        x['answer']='No';self.assertFalse(rent_learning_oracle(x)['key_agrees'])
        for key in ['english','ainglish']:
            x[key]=x[key].replace('rent-borrow','rent-lend').replace(' from Indra',' to Indra')
        self.assertTrue(rent_learning_oracle(x)['key_agrees'])

    def test_unrecognised_or_asymmetric_input_never_passes(self):
        x=row();x['english']='different context'
        self.assertEqual('unassessed',rent_learning_oracle(x)['status'])
        x=row();x['question']='Is the owner happy?'
        self.assertEqual('unassessed',rent_learning_oracle(x)['status'])

    def test_duplicate_or_extra_answers_do_not_pass(self):
        x=row();x['options']=['Yes','No','Yes']
        self.assertFalse(rent_learning_oracle(x)['unique_correct_option'])
        self.assertFalse(rent_learning_oracle(x)['exact_binary_choice_set'])

if __name__ == '__main__':unittest.main()
