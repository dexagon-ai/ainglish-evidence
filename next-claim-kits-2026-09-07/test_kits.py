import hashlib
import json
from pathlib import Path
import unittest
import build

ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text())

class KitTest(unittest.TestCase):
    def test_finite_world_entailment(self):
        self.assertEqual(build.entail([(True,False),(False,False)],0),'not determined')
        self.assertEqual(build.entail([(True,False),(False,False)],1),'no')
        self.assertEqual(build.entail([(True,False),(True,True)],0),'yes')
        with self.assertRaises(AssertionError):build.entail([],0)

    def test_replied_never_uses_hidden_scenario_as_evidence(self):
        rows=read('replied/gold-audit.json');items=read('replied/items.json')
        self.assertEqual(len(rows),256)
        for row,item in zip(rows,items):
            expected=['yes','yes'] if row['form']=='replied-no' else ['not determined','not determined']
            self.assertEqual(row['visible_gold'],expected)
            self.assertFalse(row['hidden_world_used_for_gold'])
            self.assertEqual(row['choice_meanings'][item['answer']],expected)
            self.assertNotIn('does this record establish',item['question'])
            self.assertNotIn('hidden_world',item)

    def test_instance_identity_and_history_are_not_collapsed(self):
        rows=read('instance/gold-audit.json');items=read('instance/items.json')
        self.assertEqual(len(rows),256)
        for row,item in zip(rows,items):
            form=item['settlement_stratum'];scenario=item['strata']['scenario']
            if form=='same-instance-as':
                expected=['yes',{0:'not determined',1:'no',2:'yes',3:'not determined'}[scenario]]
            else:
                expected=['no' if scenario in [2,3] else 'not determined','no' if scenario==1 else 'not determined']
            self.assertEqual(row['visible_gold'],expected)
            self.assertEqual(row['choice_meanings'][item['answer']],expected)
            for w in row['compatible_worlds']:
                self.assertTrue(not w[0] or (w[1] and w[2]))
                self.assertTrue(w[0 if form=='same-instance-as' else 1])

    def test_complete_token_bridge_and_form_balance(self):
        for name in ['replied','instance']:
            items=read(name+'/items.json');counts={}
            for row in items:counts[row['settlement_stratum']]=counts.get(row['settlement_stratum'],0)+1
            self.assertEqual(sorted(counts.values()),[128,128])
        tokens=read('instance/token-pairs.json');items=read('instance/items.json');gold=read('instance/gold-audit.json')
        self.assertEqual(len({(r['english'],r['ainglish']) for r in tokens}),256)
        for token,item,row in zip(tokens,items,gold):
            self.assertEqual(token['id'],item['id'])
            for arm in ['english','ainglish']:
                self.assertEqual(row['shared_context']+token[arm],item[arm])
                self.assertIn('2026-09-07T12:00Z',token[arm])
                if token['stratum']=='value-equal-to':self.assertIn(row['key'],token[arm])

    def test_frozen_file_hashes(self):
        for name,h in read('FROZEN.json').items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),h,name)

if __name__=='__main__':unittest.main()
