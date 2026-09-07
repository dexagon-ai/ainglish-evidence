import json
from itertools import product
import unittest
from study import ROOT, code, score, current


class DesignTest(unittest.TestCase):
    def testPositionalDecoderIsStrictAndDoesNotRepairOldJson(self):
        self.assertTrue(score(' YNYNN\n',True,'YNYNN')['correct'])
        for raw in ['Y N Y N N','ynynn','"YNYNN"','YNYNN because','{"x":true}']:
            self.assertFalse(score(raw,True,'YNYNN')['valid'])
        self.assertFalse(score('YNYNN',False,'YNYNN')['correct'])

    def testFreshBalancedControlsAndCases(self):
        controls=json.loads((ROOT/'controls.json').read_text());cases=json.loads((ROOT/'cases.json').read_text())
        all_codes={code(bits) for bits in product([False,True],repeat=5)}
        self.assertEqual({c['gold'] for c in controls},all_codes)
        self.assertEqual(len(cases),96)
        self.assertEqual(len({c['id'] for c in cases}),96)
        for context in {c['context_id'] for c in cases}:
            self.assertEqual({c['gold'] for c in cases if c['context_id']==context},all_codes)
        for c in cases:
            self.assertEqual(c['gold'],code(c['brief'].values()))
            self.assertNotIn(c['gold'],current(c,'ainglish'))
            self.assertNotIn(c['gold'],current(c,'english'))
            self.assertIn('CURRENT independent job',current(c,'ainglish'))
        old=json.loads((ROOT.parent/'dialogue-costs-2026-09-07/cases.json').read_text())
        self.assertFalse({c['context'] for c in cases}&{c['context'] for c in old})


if __name__=='__main__':unittest.main()
