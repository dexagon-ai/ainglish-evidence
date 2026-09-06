import json
import unittest
from design import ROOT,FIELDS
from run import decode,prose_format


class DesignTest(unittest.TestCase):
    def testFullFactorialGoldMatchesTheNeutralSemanticBrief(self):
        cases=json.loads((ROOT/'cases.json').read_text())
        self.assertEqual(32,len(cases));self.assertEqual(32,len({tuple(c['brief'][k] for k in FIELDS) for c in cases}))
        for c in cases:
            b=c['brief'];s=c['semantic_brief']
            self.assertEqual(b['include_recipient'],'Mira' in s['acting_team'])
            self.assertEqual(b['collective'],s['number_of_checks']==1)
            self.assertEqual(b['old_A_active'],'A' in s['active_instructions_after_C'])
            self.assertIn('B',s['active_instructions_after_C']);self.assertIn('C',s['active_instructions_after_C'])
            self.assertEqual(b['both_allowed'],'red and blue' in s['permitted_choices'])
            self.assertEqual(b['finish_deadline'],s['deadline_event']=='successful completion')

    def testNoCoercionRepairOrDuplicateKeysInScorer(self):
        value={k:False for k in FIELDS};raw=json.dumps(value)
        self.assertEqual(value,decode(raw,True));self.assertIsNone(decode(raw,False))
        for bad in ['```json\n'+raw+'\n```',raw+' prose','[]',raw.replace('false','0'),raw[:-1]+',"collective":true}',raw.replace('collective','another')]:
            self.assertIsNone(decode(bad,True))
        value['collective']=None
        self.assertEqual(value,decode(json.dumps(value),True))
        self.assertFalse(prose_format(raw,True));self.assertFalse(prose_format('Do the check.',False))
        self.assertFalse(prose_format('include_recipient: false',True))
        self.assertTrue(prose_format('Mira does not join the acting team.',True))


if __name__=='__main__':unittest.main()
