import copy
import json
import unittest
from itref_review_v2 import *

class ItrefReviewTest(unittest.TestCase):
    def setUp(self):
        self.entry=json.loads((ROOT/'snapshot.json').read_text())['itref_entry']['english_mapping']
        self.p,self.pk=primary_v2();self.d,self.dk=diagnostics(self.entry)

    def test_full_bare_inputs_and_opposite_keys(self):
        report=validate(self.p,self.pk,self.d,self.dk,self.entry)
        self.assertEqual(report['complete_bare_pairs_equal'],96)
        self.assertEqual(report['primary_answer_positions'],dict.fromkeys('ABCD',48))

    def test_choice_order_leak_is_rejected(self):
        p=copy.deepcopy(self.p)
        a=p[0]['choices']['A'];p[0]['choices']['A']=p[0]['choices']['B'];p[0]['choices']['B']=a
        with self.assertRaises(AssertionError):validate(p,self.pk,self.d,self.dk,self.entry)

    def test_learning_changes_only_the_entry_prefix(self):
        self.assertEqual(sum(k['family']=='learning' for k in self.dk),96)
        for item,key in zip(self.d,self.dk):
            if key['family']=='learning':
                self.assertNotIn('stages',item)
                for arm in ['marked','careful']:
                    self.assertEqual(item['arms'][arm+'_entry_loaded'],self.entry+'\n\n'+item['arms'][arm+'_cold'])

    def test_transform_keys_are_external_and_no_inference_receipts_exist(self):
        for item,key in zip(self.d,self.dk):
            self.assertNotIn('answer',item)
            self.assertNotIn('intended_target',item)
            if key['family'] in ['summary','translation']:
                self.assertIn('never',item['stages'][-1]['input'])
                self.assertEqual(len(item['stages']),2 if key['family']=='summary' else 3)
            self.assertEqual(item['choices'][key['answer']],key['licensed_action'])

    def test_rebuild_matches_published_review_files(self):
        for name,expected in [('itref-primary-v2-inputs.json',self.p),('itref-primary-v2-keys.json',self.pk),
                              ('itref-diagnostic-inputs.json',self.d),('itref-diagnostic-keys.json',self.dk)]:
            self.assertEqual(json.loads((ROOT/name).read_text()),expected)

if __name__=='__main__':unittest.main()
