import json
from pathlib import Path
import unittest
from ainglish.client import manifest_commitment

ROOT=Path(__file__).resolve().parent

class FrozenTokenTest(unittest.TestCase):
    def testRepliedPlanIsByteForByteScientificCopy(self):
        old=json.loads((ROOT.parent/'overnight-progression-2026-09-06/replied-token/prepared.json').read_text())
        self.assertEqual(old,json.loads((ROOT/'replied.prepared.json').read_text()))

    def testInstanceClaimsAreExactFrozenBridge(self):
        old=json.loads((ROOT.parent/'next-claim-kits-2026-09-07/instance/token-pairs.json').read_text())
        plan=json.loads((ROOT/'instance.prepared.json').read_text())
        for left,right in zip(old,plan['manifest']['test_set']):
            for field in ['english','ainglish','stratum']:
                self.assertEqual(left[field],right[field])
        self.assertEqual(256,len(plan['manifest']['test_set']))
        self.assertEqual(plan['manifest_commitment'],manifest_commitment(plan['manifest']))
        self.assertNotIn('replicates_hash',plan['manifest'])
        self.assertNotIn('transport_limits',plan['manifest'])

if __name__=='__main__':unittest.main()
