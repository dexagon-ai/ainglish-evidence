import copy
import unittest
from choice_audit import check

def item(rule='same-for-all',available='A',capacity=3):
    base=f'Q-1 permits only {available}. Q-2 permits only B. Q-3 permits only C. Maximum uses within this assignment: A={capacity}, B={capacity}, C={capacity}. '
    return {'id':'x','english':base+'All must use the same choice.',
            'ainglish':base+rule+'(Q).','question':'Can any complete plan obey all the stated requirements?',
            'options':['yes','no','no feasible assignment exists','unknown'],'answer':'no'}

class ChoiceTest(unittest.TestCase):
    def test_duplicate_negatives_on_impossible_assignment(self):
        r=check(item());self.assertTrue(r['non_unique_correct']);self.assertEqual(0,r['feasible_plans'])
    def test_possible_flexible_assignment(self):
        r=check(dict(item('may-vary-across'),answer='yes'));self.assertEqual(['yes'],r['valid_answers'])
    def test_ignores_false_ledger(self):
        a=item();a['ledger']={'feasible':['lie']};self.assertTrue(check(a)['non_unique_correct'])
    def test_capacities_are_load_bearing(self):
        a=item('may-vary-across',capacity=0);self.assertEqual(0,check(a)['feasible_plans'])
    def test_unknown_frame_not_pass(self):
        self.assertEqual('unassessed',check(dict(item(),ainglish='Unrecognised form.'))['status'])
    def test_visible_fact_drift_not_certified(self):
        a=item();a['english']=a['english'].replace('A=3','A=0');self.assertEqual('unassessed',check(a)['status'])
    def test_incorrect_key_detected_without_mutation(self):
        a=dict(item(),answer='yes');b=copy.deepcopy(a);self.assertFalse(check(a)['key_valid']);self.assertEqual(a,b)
    def test_vacuity_is_not_silently_assumed(self):
        a=item();a['question']='Among plans obeying every requirement, must the first and last listed members use the same choice ID?'
        self.assertEqual('unassessed',check(a)['status'])

if __name__=='__main__':unittest.main()
