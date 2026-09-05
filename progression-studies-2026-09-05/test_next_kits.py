import itertools
import json
from pathlib import Path
import unittest
from collections import Counter
ROOT=Path(__file__).resolve().parent

class NextKitsTests(unittest.TestCase):
    def rows(self,name):return json.loads((ROOT/(name+'.kit-v1.json')).read_text())
    def test_shapes_and_non_target_controls(self):
        for name,n in [('will',192),('since',288),('quantity',192),('choice',192)]:
            data=self.rows(name);real=[x for x in data if not x.get('calibration')]
            self.assertEqual(n,len(real));self.assertEqual(n,len({(x['english'],x['ainglish']) for x in real}))
            self.assertEqual(8,len(data)-n)
            self.assertEqual(len(data),len({x['id'] for x in data}))
            counts=Counter(x['options'].index(x['answer']) for x in real)
            self.assertEqual(1,len(set(counts.values())))
    def test_quantity_gold_by_symbolic_affine_state(self):
        for r in self.rows('quantity'):
            if r.get('calibration'):continue
            led=r['ledger'];a,b=(1,0) if led['initial'] is None else (0,led['initial'])
            for op,n in led['operations']:
                if op=='set-to':a,b=0,n
                else:b+=n
            self.assertEqual(None if a else b,led['final'])
            if 'is the final numeric' in r['question']:
                self.assertEqual('no' if a else 'yes',r['answer'])
            else:
                import re
                amount=int(re.search(r'requirement for (-?\d+)',r['question'])[1])
                self.assertEqual('the final value is not determined' if a else 'yes' if amount<=b else 'no',r['answer'])
    def test_choice_gold_by_exhaustive_constraint_filter(self):
        for r in self.rows('choice'):
            if r.get('calibration'):continue
            d=r['ledger'];valid=[]
            for plan in itertools.product('ABC',repeat=3):
                if not all(p in e for p,e in zip(plan,d['eligibility'])):continue
                if any(plan.count(p)>d['capacities'][p] for p in 'ABC'):continue
                if d['form']=='same-for-all' and len(set(plan))>1:continue
                valid.append(list(plan))
            self.assertEqual(valid,d['feasible'])
            if d['task']=='admissibility':expected='yes' if d['candidate'] in valid else 'no'
            elif d['task']=='feasibility':expected='yes' if valid else 'no'
            else:expected='no feasible assignment exists' if not valid else 'yes' if all(p[0]==p[2] for p in valid) else 'no'
            self.assertEqual(expected,r['answer'])
    def test_notice_is_not_outcome_promise_and_release_is_narrow(self):
        for r in self.rows('will'):
            if r.get('calibration'):continue
            d=r['ledger']
            if d['form']=='will-as-promise':violation=not d['released']
            elif d['form']=='will-as-plan':violation=d['plan_changed'] and not d['notice']
            else:violation=False
            self.assertTrue(r['answer'].endswith('2: '+('yes' if violation else 'no')))
            if d['released']:self.assertIn('duty to communicate a plan change was not waived',r['english'])
    def test_since_exact_asserted_axes_not_actual_causal_absence(self):
        for r in self.rows('since'):
            if r.get('calibration'):continue
            d=r['ledger'];bits=[d['reason_asserted'],d['interval_asserted']]
            if not d['reason_first']:bits.reverse()
            self.assertEqual('1: '+('yes' if bits[0] else 'no')+'; 2: '+('yes' if bits[1] else 'no'),r['answer'])
            self.assertNotIn('because-clause(',r['ainglish'])
            self.assertNotIn('ever-since(',r['ainglish'])
            self.assertNotIn('did not cause',r['english'])
            self.assertNotIn('did not cause',r['ainglish'])

if __name__=='__main__':unittest.main()
