import csv
import hashlib
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent


class ReportTest(unittest.TestCase):
    def test_complete_prespecified_grid_and_counts(self):
        design=json.loads((HERE/'results/design.json').read_text())
        rows=json.loads((HERE/'results/all-cases.json').read_text())
        self.assertEqual(len(rows),36)
        self.assertEqual({(r['case'],int(r['n_per_form'])) for r in rows},
                         {(c['case'],n) for c in design['cases'] for n in design['sizes']})
        for r in rows:
            self.assertEqual(int(r['trials']),500)
            self.assertEqual(int(r['held_pairs'])+int(r['observable_pairs']),500)
            self.assertLessEqual(int(r['new_interval_compatible']),int(r['observable_pairs']))
            self.assertLessEqual(int(r['current_point_strata_compatible']),int(r['observable_pairs']))
        self.assertEqual(design['reader_calls'],0)
        self.assertFalse(design['formal_governance_measurement'])

    def test_published_csv_hashes_and_readable_rows_match(self):
        receipt=json.loads((HERE/'results/completion.json').read_text());all_rows=[]
        for name,expected in receipt['csv_sha256'].items():
            p=HERE/'results'/name
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),expected)
            with p.open() as stream:
                all_rows.extend(csv.DictReader(stream))
        self.assertEqual(all_rows,json.loads((HERE/'results/all-cases.json').read_text()))
        self.assertEqual(receipt['simulated_pairs'],18000)

    def test_headline_counts_and_scope_guards(self):
        rows=json.loads((HERE/'results/all-cases.json').read_text())
        values={(r['case'],int(r['n_per_form'])):r for r in rows}
        self.assertEqual([int(values[('equal_mid',n)]['new_interval_compatible']) for n in [32,128,512]],[489,497,490])
        self.assertEqual([int(values[('equal_mid',n)]['current_point_strata_compatible']) for n in [32,128,512]],[0,0,1])
        self.assertEqual([int(values[('both_forms_separated_10pp',n)]['new_interval_compatible']) for n in [32,128,512]],[458,341,35])
        for n in [32,128,512]:self.assertEqual(int(values[('unobservable_arm_sentinel',n)]['held_pairs']),500)
        text=(HERE/'REPORT.md').read_text()
        for term in ['not Ainglish comprehension evidence','not a calibrated','does not establish unchanged historical verdicts']:
            self.assertIn(term,text)


if __name__=='__main__':unittest.main()
