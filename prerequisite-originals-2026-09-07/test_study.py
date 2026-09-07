import collections
import unittest
import study

class DesignTest(unittest.TestCase):
    def test_counts_unique_complete_pairs_and_balanced_forms(self):
        for name,n in [('windows',64),('negative-modal',256),('stock-flow',256),('incident',512)]:
            rows,cells=study.GENERATORS[name]()
            self.assertEqual(n,len(rows))
            self.assertEqual(n,len({(r['english'],r['ainglish']) for r in rows}))
            self.assertEqual(n,len({r['id'] for r in rows}))
            self.assertEqual([n//2,n//2],sorted(collections.Counter(r['stratum'] for r in rows).values()))
            for r in rows:
                self.assertTrue(r['ainglish'].endswith('.'))
                self.assertTrue(r['english'].endswith('.'))
                self.assertNotEqual(r['ainglish'],r['english'])

    def test_window_zones_and_mapping(self):
        rows,_=study.windows()
        self.assertEqual(16,sum('day@UTC' in r['ainglish'] or 'week@UTC' in r['ainglish'] for r in rows))
        for r in rows:
            self.assertIn('in each' if r['stratum']=='per-clock' else 'in any',r['english'])

    def test_no_modal_bare_ambiguity_as_control(self):
        rows,_=study.negative_modal()
        for r in rows:
            self.assertNotIn(' may not ',r['english'])
            self.assertIn('is forbidden to' if r['stratum'].endswith('prohibition') else 'might not',r['english'])

    def test_incident_cell_bridge_preserves_references_and_four_worlds(self):
        rows,cells=study.incident()
        self.assertEqual(256,len(cells))
        self.assertEqual([64]*4,sorted(collections.Counter((c['world_impact_absent'],c['world_cause_removed']) for c in cells).values()))
        for c in cells:
            for r in [r for r in rows if r['id'].startswith(c['id']+'-')]:
                for key in ['incident']+(['check','time'] if r['stratum']=='impact-recovered' else ['cause','test']):
                    self.assertIn(c[key],r['english']);self.assertIn(c[key],r['ainglish'])

if __name__=='__main__':unittest.main()
