"""Excluded synthetic analysis tests; no numeric synthetic language result is published."""
import json
import unittest
from instrument import ROOT
from report import analyse, decode, selftest

class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items=[i for i in json.loads((ROOT/'items.json').read_text()) if not i.get('calibration')]
        lookup={i['id']:i for i in cls.items}
        cls.cells=[{'item_id':c['world_id'],'reader':c['reader'],'arm':c['arm'],
            'answer':lookup[c['world_id']]['answer']} for c in json.loads((ROOT/'planned-cells.json').read_text())['cells']]

    def test_boundaries_and_all_menu_scores(self):
        self.assertEqual(selftest()['target_reader_calls'],0)

    def test_zero_bootstrap_not_noninferiority_certificate(self):
        result=analyse(self.items,self.cells,draws=100)
        self.assertEqual(result['joint_contrast_pp'],0)
        self.assertTrue(all(not row['passes_minus_5pp'] for row in result['conditional_ni'].values()))
        self.assertEqual(result['correlation_sensitivity']['world_within_form_domain']['percentile_95'],[0,0])

    def test_unknown_not_imputed_as_membership_error(self):
        cell=dict(self.cells[0],answer='invalid option')
        row=decode(self.items,[cell])[0]
        self.assertFalse(row['joint']);self.assertTrue(row['off_option'])
        self.assertTrue(all(d['error'] is None for d in row['decisions'].values()))

    def test_dead_not_wrong(self):
        row=decode(self.items,[dict(self.cells[0],answer=None,absence_reason='timeout')])[0]
        self.assertTrue(row['absent']);self.assertIsNone(row['joint'])

    def test_duplicate_world_reader_refused(self):
        with self.assertRaisesRegex(ValueError,'Repeated'):
            decode(self.items,[self.cells[0],self.cells[0]])

    def test_adverse_is_not_clipped(self):
        cells=[dict(c,answer='invalid option') if c['arm']=='ainglish' else c for c in self.cells]
        result=analyse(self.items,cells,draws=100)
        self.assertEqual(result['joint_contrast_pp'],-100)
        self.assertTrue(all(row['lower_delta_pp']<=-99 for row in result['conditional_ni'].values()))
        self.assertTrue(all(row['joint_correct']==0 for row in result['pooled_descriptive_counts'] if row['arm']=='ainglish'))

if __name__=='__main__':unittest.main()
