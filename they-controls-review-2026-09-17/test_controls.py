from copy import deepcopy
from collections import Counter
import unittest

from controls import build,fixture_answers,score,LABELS,FORMS,SPECS

class ControlTests(unittest.TestCase):
    def setUp(self): self.f=build()
    def test_counts_and_actual_units(self):
        self.assertEqual(len(self.f['items']),90)
        self.assertEqual(len({x['world_id'] for x in self.f['items']}),30)
        self.assertTrue(all(n==3 for n in Counter(x['world_id'] for x in self.f['items']).values()))
    def test_no_target_marker_or_sdk_calibration_claim(self):
        for item in self.f['items']:
            self.assertFalse(any(form in item['text']+' '+item['question'] for form in FORMS))
            self.assertNotIn('calibration',item)
    def test_all_ten_endpoints_and_roles(self):
        for form in FORMS:
            for dimension in SPECS:
                rows=[x for x in self.f['items'] if x['form_slot']==form and x['dimension']==dimension]
                self.assertEqual(Counter(x['role'] for x in rows),{'explicit_fact':6,'underdetermined':3})
                self.assertEqual(Counter(x['gold'] for x in rows),dict.fromkeys(LABELS,3))
    def test_option_position_balance_per_role(self):
        for form in FORMS:
            for dimension in SPECS:
                for role,n in [('explicit_fact',2),('underdetermined',1)]:
                    rows=[x for x in self.f['items'] if x['form_slot']==form and x['dimension']==dimension and x['role']==role]
                    self.assertEqual(Counter(x['options'].index(x['gold']) for x in rows),{0:n,1:n,2:n})
    def test_all_unknown_fails_every_positive_control_endpoint(self):
        result=score(self.f,fixture_answers(self.f,lambda item:LABELS[2]))
        self.assertTrue(all(x['explicit_fact']['observed_accuracy']==0 for x in result['endpoints']))
        self.assertTrue(all(x['underdetermined']['observed_accuracy']==1 for x in result['endpoints']))
    def test_constant_yes_and_no_fail_control_floor(self):
        for label in LABELS[:2]:
            result=score(self.f,fixture_answers(self.f,lambda item:label))
            self.assertTrue(all(x['explicit_fact']['observed_accuracy']==.5 for x in result['endpoints']))
    def test_every_fixed_option_position_fails(self):
        for position in range(3):
            result=score(self.f,fixture_answers(self.f,lambda item:item['options'][position]))
            for endpoint in result['endpoints']:
                self.assertAlmostEqual(endpoint['explicit_fact']['observed_accuracy'],1/3)
                self.assertAlmostEqual(endpoint['underdetermined']['observed_accuracy'],1/3)
    def test_oracle_is_not_measurement_or_instrument_certificate(self):
        result=score(self.f,fixture_answers(self.f))
        self.assertTrue(result['complete'])
        self.assertFalse(result['fileable_measurement'])
        self.assertNotIn('bundle_pass',result)
    def test_one_observation_cannot_count_twice(self):
        rows=fixture_answers(self.f); rows[1]['observation_id']=rows[0]['observation_id']
        with self.assertRaises(ValueError): score(self.f,rows)
    def test_no_cross_dimension_or_form_reassignment(self):
        for key,value in [('dimension','collective_action'),('form_slot','they-many')]:
            rows=fixture_answers(self.f); rows[0][key]=value
            with self.assertRaises(ValueError): score(self.f,rows)
    def test_missing_observation_holds_endpoint(self):
        result=score(self.f,fixture_answers(self.f)[1:])
        self.assertFalse(result['complete'])
        self.assertEqual(sum(x['explicit_fact']['absent'] for x in result['endpoints']),1)
    def test_absent_cell_is_not_a_wrong_answer(self):
        rows=fixture_answers(self.f); rows[0]['answer']=None
        result=score(self.f,rows)
        self.assertFalse(result['complete'])
        self.assertEqual(result['endpoints'][0]['explicit_fact']['incorrect'],0)
        self.assertEqual(result['endpoints'][0]['explicit_fact']['absent'],1)
    def test_unknown_answer_or_unplanned_item_refused(self):
        for key,value in [('answer','Maybe'),('item_id','unplanned')]:
            rows=fixture_answers(self.f); rows[0][key]=value
            with self.assertRaises(ValueError): score(self.f,rows)
    def test_duplicate_plan_or_response_refused(self):
        fixtures=deepcopy(self.f); fixtures['items'].append(fixtures['items'][0])
        with self.assertRaises(ValueError): score(fixtures,[])
        rows=fixture_answers(self.f); extra=deepcopy(rows[0]); extra['observation_id']='new'
        with self.assertRaises(ValueError): score(self.f,rows+[extra])
    def test_deterministic_reconstruction(self):
        self.assertEqual(self.f,build())
        self.assertEqual(self.f['reader_calls'],0)

if __name__=='__main__': unittest.main()
