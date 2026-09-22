"""CPU integrity checks; none establishes language performance."""
import json,unittest
from pathlib import Path
from calendar_capacity import paired_power
from calendar_oracle import matrix
from itref_instrument import primary,controls,validate

ROOT=Path(__file__).parent
class ReviewArtifactsTest(unittest.TestCase):
    def test_frozen_itref_rebuilds_exactly(self):
        items=[];keys=[];primary(items,keys);controls(items,keys)
        for name,value in [('itref-inputs.json',items),('itref-keys.json',keys),('itref-review.json',validate(items,keys))]:
            self.assertEqual(json.loads((ROOT/name).read_text()),value)
    def test_audit_conserves_scope_and_admits_limits(self):
        a=json.loads((ROOT/'audit.json').read_text())
        self.assertEqual(96,sum(a['stages'].values()))
        self.assertEqual(47,len(a['bounded_wording_reviews']))
        self.assertEqual(26,a['automatic_reviews'])
        self.assertEqual(22,len(a['suggestion_trace']))
        self.assertFalse(a['readiness_rule_changed'])
        self.assertIn('403',' '.join(a['limits']))
        self.assertEqual({'review_only_not_proven_contradiction'},{x['classification'] for x in a['bounded_wording_reviews']})
    def test_legacy_sign_symmetry_and_retention_limit(self):
        rows=json.loads((ROOT/'legacy-audit.json').read_text())['sources']
        self.assertEqual(6,len(rows))
        self.assertEqual([2,2,2],[sum((x['value']>0)-(x['value']<0)==s for x in rows) for s in (-1,0,1)])
        self.assertTrue(all(len(x['pinned_items_sha256'])==64 for x in rows))
        self.assertTrue(all('not established' in x['raw_response_replay'] for x in rows))
    def test_calendar_sensitivity_has_no_inference_claim(self):
        self.assertEqual(84,len(matrix(12)))
        self.assertLess(paired_power(504,.32,.02)['probability_lower_bound_clears_20pp'],.36)
        self.assertGreater(paired_power(504,.42,.02)['probability_lower_bound_clears_20pp'],.99)
        c=json.loads((ROOT/'calendar-capacity.json').read_text())
        self.assertEqual(0,c['reader_calls']);self.assertIn('HOLD',c['status'])
        self.assertEqual(1008,len(c['allocation']))
if __name__=='__main__':unittest.main()
