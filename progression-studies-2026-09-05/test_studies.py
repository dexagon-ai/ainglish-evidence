"""Independent gold, balancing and scope checks; no model or register calls."""
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class StudyTests(unittest.TestCase):
    def data(self, name):
        return json.loads((ROOT / (name + '.items-v2.json')).read_text())

    def test_unique_balanced_and_construct_free_controls(self):
        for name, n, options in [('regime',192,6),('some',256,4)]:
            rows = self.data(name)
            real = [r for r in rows if not r.get('calibration')]
            controls = [r for r in rows if r.get('calibration')]
            self.assertEqual(n,len(real)); self.assertEqual(8,len(controls))
            self.assertEqual(len(rows),len({r['id'] for r in rows}))
            self.assertEqual(len(rows),len({(r['english'],r['ainglish']) for r in rows}))
            self.assertEqual({i:n//options for i in range(options)},dict(Counter(r['options'].index(r['answer']) for r in real)))
            for row in rows:
                self.assertIn(row['answer'],row['options'])
                self.assertEqual(len(row['options']),len(set(row['options'])))
            for row in controls:
                self.assertNotRegex(json.dumps(row), r'by-construction|by-rule|in-practice|some-or-all|some-but-not-all')
                self.assertNotIn((row['english'],row['ainglish']),[(r['english'],r['ainglish']) for r in real])

    def test_some_gold_against_finite_population_logic(self):
        # Enumerate all possible counts rather than using the builder's boolean formula.
        for row in self.data('some'):
            if row.get('calibration'): continue
            n=row['strata']['population']
            possible=set(range(1,n+1))
            if row['settlement_stratum']=='some-but-not-all': possible.remove(n)
            parts=re.split(r' 2\. ',row['question'],maxsplit=1)
            answers=[]
            for part in parts:
                count=0 if f'0 of those' in part else n
                compatible=count in possible
                is_contradiction='Does that contradict' in part
                answers.append((not compatible) if is_contradiction else compatible)
            expected='1: '+('yes' if answers[0] else 'no')+'; 2: '+('yes' if answers[1] else 'no')
            self.assertEqual(expected,row['answer'])
            self.assertNotIn(row['answer'],row['english'])
            self.assertNotIn(row['answer'],row['ainglish'])

    def test_regime_counterexample_consequences(self):
        expected={
            'by-construction': ('1: no;', 'claim about the mechanism was false'),
            'by-rule': ('1: yes;', 'responsible person owes a remedy or explanation'),
            'in-practice': ('1: yes;', 'new observation, with no duty created by this claim'),
        }
        for row in self.data('regime'):
            if row.get('calibration'): continue
            prefix,consequence=expected[row['settlement_stratum']]
            self.assertTrue(row['answer'].startswith(prefix))
            self.assertIn(consequence,row['answer'])
            if row['settlement_stratum']=='by-rule':
                self.assertIn('standing rule requires',row['english'])
                self.assertIn('owes repair or explanation',row['english'])
            self.assertIn('same unchanged system',row['question'])

    def test_individual_calibration_cannot_be_rescued_by_partner(self):
        from run_primary_once import individually_gated_reader
        data=self.data('regime'); readers=[{'name':'good'},{'name':'flat'}]
        controls=[r for r in data if r.get('calibration')]
        lookup={(r[arm],r['question']):(r,arm) for r in controls for arm in ['english','ainglish']}
        spent=[]
        def fake(reader,text,question,options):
            spent.append(text)
            r,arm=lookup[(text,question)]
            return r['answer'] if reader['name']=='flat' or arm=='ainglish' else 'the information does not determine who'
        gate=individually_gated_reader(data,readers,fake)
        for reader in readers:
            for row in controls:
                for arm in ['english','ainglish']:gate(reader,row[arm],row['question'],row['options'])
        self.assertEqual(32,len(spent))
        row=data[0]
        with self.assertRaisesRegex(RuntimeError,'per-reader calibration'):
            gate(readers[0],row['english'],row['question'],row['options'])
        self.assertEqual(32,len(spent),'even a pooled 0.5 pass cannot buy a real call with a flat reader')

    def test_strict_study_gate_refuses_one_off_option_after_clean_calibration(self):
        from run_primary_once import individually_gated_reader
        data=self.data('regime');readers=[{'name':'a'},{'name':'b'}]
        controls=[r for r in data if r.get('calibration')]
        lookup={(r[arm],r['question']):(r,arm) for r in controls for arm in ['english','ainglish']}
        calls=[]
        def fake(reader,text,question,options):
            calls.append(text)
            if (text,question) not in lookup:return 'D: 1: notify when the plan changes; 2: y'
            r,arm=lookup[(text,question)]
            return r['answer'] if arm=='ainglish' else 'the information does not determine who'
        gate=individually_gated_reader(data,readers,fake)
        for reader in readers:
            for r in controls:
                for arm in ['english','ainglish']:gate(reader,r[arm],r['question'],r['options'])
        r=data[0]
        with self.assertRaisesRegex(RuntimeError,'zero-off-option'):
            gate(readers[0],r['english'],r['question'],r['options'])
        self.assertEqual(33,len(calls),'one offending call, not a retry or a completed panel')

if __name__=='__main__': unittest.main()
