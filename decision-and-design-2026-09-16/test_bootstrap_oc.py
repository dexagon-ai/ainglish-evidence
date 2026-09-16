"""Cross-check native numeric replay against the installed SDK; no inference."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import unittest

from ainglish import panel
from prepare_bootstrap import FORMS, READERS, SEEDS

WORK = Path(os.environ['AINGLISH_OC_WORK'])
BIN = WORK / 'bootstrap_oc'
MATRICES = WORK / 'matrices'


def command(run=0, trials=1, scenario='fixture', n=300):
    return [str(BIN), str(MATRICES / f'matrix-n{n}-run{run}.bin'),
            str(MATRICES / f'matrix-n{n}-run{1-run}.bin'), str(trials), scenario]


class NumericReplayTests(unittest.TestCase):
    def test_binary_hashes(self):
        receipts = json.loads((MATRICES / 'matrix-receipts.json').read_text())
        for r in receipts['matrices']:
            p = MATRICES / f"matrix-n{r['n_worlds_per_form']}-run{r['run']}.bin"
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), r['sha256'])

    def test_both_fixed_fixtures_match_sdk(self):
        n = 300
        items = [{'id': f'numeric-only-f{f}-i{i:05d}', 'answer': 'correct',
                  'settlement_stratum': FORMS[f]} for f in range(2) for i in range(n)]
        contract = [{'id': f, 'share': .5} for f in FORMS]
        for run in range(2):
            seed = SEEDS[run]
            rows = [(f'numeric-only-f{f}-i{i:05d}',
                     panel.arm_for(seed, reader, f'numeric-only-f{f}-i{i:05d}'), reader,
                     'correct' if (i+2*r+f) % 5 != 0 else 'incorrect')
                    for f in range(2) for i in range(n) for r, reader in enumerate(READERS)]
            lo, hi, _ = panel.attested_bootstrap_accuracy(
                rows, items, [{'name': r} for r in READERS], contract, seed=seed)
            output = subprocess.run(command(run=run), text=True, capture_output=True, check=True)
            native = list(csv.reader(io.StringIO(output.stdout)))
            self.assertEqual(len(native), 3)
            self.assertAlmostEqual(float(native[2][2]), lo, places=8)
            self.assertAlmostEqual(float(native[2][3]), hi, places=8)
            # In this large, complete fixture no form loses an arm on any draw.
            # Independent per-form SDK replay therefore equals the common mask.
            for f in range(2):
                fi = [item for item in items if item['settlement_stratum'] == FORMS[f]]
                ids = {item['id'] for item in fi}
                fr = [row for row in rows if row[0] in ids]
                fl, fh, receipt = panel.attested_bootstrap_accuracy(
                    fr, fi, [{'name': r} for r in READERS],
                    [{'id': FORMS[f], 'share': 1}], seed=seed)
                self.assertEqual(receipt['algorithm']['accepted_draws'], 2000)
                self.assertAlmostEqual(float(native[f][2]), fl, places=8)
                self.assertAlmostEqual(float(native[f][3]), fh, places=8)

    def test_fixed_seed_reproducibility_and_count_invariants(self):
        cmd = command(trials=4, scenario='equality_independent')
        first = subprocess.run(cmd, text=True, capture_output=True, check=True).stdout
        second = subprocess.run(cmd, text=True, capture_output=True, check=True).stdout
        self.assertEqual(first, second)
        row = next(csv.DictReader(io.StringIO(first)))
        n = int(row['trials'])
        for key in ('support_original', 'support_replica', 'support_both',
                    'support_both_and_overlap', 'support_overlap_and_original_negative',
                    'opposes_original', 'degenerate_original', 'cover_form0', 'cover_form1', 'cover_pooled'):
            self.assertTrue(0 <= int(row[key]) <= n)
        self.assertLessEqual(int(row['support_both_and_overlap']), int(row['support_both']))
        self.assertLessEqual(int(row['support_both']), int(row['support_original']))

    def test_unknown_scenario_and_invalid_size_refuse(self):
        result = subprocess.run(command(scenario='not_a_scenario'), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        result = subprocess.run(command(trials=0), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def test_perfect_equality_has_zero_truth_but_guard_holds(self):
        output = subprocess.run(command(scenario='perfect_guard_fixture'),
                                text=True, capture_output=True, check=True).stdout
        rows = list(csv.reader(io.StringIO(output)))
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual([float(x) for x in row[1:4]], [0, 0, 0])
            self.assertEqual(row[4:], ['1', '0'])

    def test_homogeneous_equal_arms_have_exact_zero_expected_delta(self):
        output = subprocess.run(command(trials=3, scenario='equality_near_ceiling'),
                                text=True, capture_output=True, check=True).stdout
        row = next(csv.DictReader(io.StringIO(output)))
        self.assertEqual(float(row['mean_expected_delta_form0']), 0)
        self.assertEqual(float(row['mean_expected_delta_form1']), 0)

    def test_reader_mixture_uses_actual_assignment_not_assumed_half(self):
        output = subprocess.run(command(trials=3, scenario='opposite_reader_effects'),
                                text=True, capture_output=True, check=True).stdout
        row = next(csv.DictReader(io.StringIO(output)))
        receipts = json.loads((MATRICES / 'matrix-receipts.json').read_text())
        entry = next(r for r in receipts['matrices'] if r['n_worlds_per_form'] == 300 and r['run'] == 0)
        for form in range(2):
            counts = entry['arm_counts_by_form_reader'][form]
            ma = sum(c['ainglish'] * p for c, p in zip(counts, (.99, .91))) / sum(c['ainglish'] for c in counts)
            me = sum(c['english'] * p for c, p in zip(counts, (.91, .99))) / sum(c['english'] for c in counts)
            self.assertAlmostEqual(float(row[f'mean_expected_delta_form{form}']), 100*(ma-me), places=8)


if __name__ == '__main__':
    unittest.main()
