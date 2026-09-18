import unittest
import csv
import json
from pathlib import Path
from feasibility import cdf, plan


class FeasibilityTests(unittest.TestCase):
    def test_known_binomial_cases(self):
        self.assertAlmostEqual(.5, cdf(1, 3, .5))
        self.assertAlmostEqual(.95**128, cdf(0, 128, .05), places=12)
        self.assertEqual(1, cdf(128, 128, .2))
        self.assertEqual(0, cdf(-1, 128, .2))

    def test_monotone_cdf(self):
        xs = [cdf(k, 128, .05) for k in range(20)]
        self.assertEqual(sorted(xs), xs)

    def test_budget_and_holds(self):
        p = plan()
        self.assertEqual(31808, p['maximum_per_study'])
        self.assertEqual(63616, p['original_and_replica_maximum'])
        self.assertEqual(0, p['model_calls'])
        self.assertFalse(p['target_bank_created'])
        self.assertFalse(p['reader_seats_accepted'])
        self.assertFalse(p['protocol_operative'])

    def test_retained_campaign_is_complete(self):
        root = Path(__file__).resolve().parent
        with (root / 'cad-n1024.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(12, len(rows))
        self.assertEqual(12, len({r['scenario'] for r in rows}))
        for row in rows:
            self.assertEqual('1024', row['n_worlds_per_form'])
            self.assertEqual('1000', row['trials'])
            self.assertLessEqual(int(row['support_both_and_overlap']), int(row['support_both']))
        execution = json.loads((root / 'execution.json').read_text())
        self.assertEqual(0, execution['model_calls'])
        self.assertEqual(2, len(execution['matrix_receipts']['matrices']))


if __name__ == '__main__': unittest.main()
