"""Numeric unit fixtures only. No inference, API or language evidence."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
from ainglish import panel

WORK=Path(os.environ['AINGLISH_COMPAT_WORK'])
BIN=WORK/'compatibility'
FORMS=['numeric-form-0','numeric-form-1']
READERS=['synthetic-reader-0','synthetic-reader-1']
SEEDS=[16092601,16092602]


def command(case='equal_mid',trials=4,run=0):
    return [str(BIN),str(WORK/f'matrices/matrix-n32-run{run}.bin'),
            str(WORK/f'matrices/matrix-n32-run{1-run}.bin'),str(trials),case]


class CompatibilityTest(unittest.TestCase):
    def test_fixed_numeric_fixtures_match_actual_sdk(self):
        n=32
        items=[{'id':f'numeric-only-f{f}-i{i:05d}','answer':'correct',
                'options':['correct','incorrect'],'settlement_stratum':FORMS[f]}
               for f in range(2) for i in range(n)]
        contract=[{'id':f,'share':.5} for f in FORMS]
        for run in [0,1]:
            rows=[(f'numeric-only-f{f}-i{i:05d}',panel.arm_for(SEEDS[run],reader,f'numeric-only-f{f}-i{i:05d}'),reader,
                   'correct' if (i+2*r+f)%5!=0 else 'incorrect')
                  for f in range(2) for i in range(n) for r,reader in enumerate(READERS)]
            lo,hi,receipt=panel.attested_bootstrap_accuracy(rows,items,[{'name':r} for r in READERS],contract,seed=SEEDS[run])
            native=list(csv.reader(io.StringIO(subprocess.check_output(command('fixture',run=run),text=True))))
            self.assertEqual(int(native[2][4]),receipt['algorithm']['accepted_draws'])
            self.assertAlmostEqual(float(native[2][2]),lo,places=8);self.assertAlmostEqual(float(native[2][3]),hi,places=8)
            value,_,strata=panel._stratified_accuracy(rows,items,contract)
            self.assertAlmostEqual(float(native[2][1]),value,places=4)
            for f in range(2):
                self.assertAlmostEqual(float(native[f][1]),strata[f]['value'],places=4)
                subset=[i for i in items if i['settlement_stratum']==FORMS[f]];ids={x['id'] for x in subset}
                l,h,r=panel.attested_bootstrap_accuracy([x for x in rows if x[0] in ids],subset,[{'name':r} for r in READERS],
                    [{'id':FORMS[f],'share':1}],seed=SEEDS[run])
                self.assertEqual(r['algorithm']['accepted_draws'],2000)
                self.assertAlmostEqual(float(native[f][2]),l,places=8);self.assertAlmostEqual(float(native[f][3]),h,places=8)

    def test_perfect_overlap_does_not_remove_degeneracy_or_generic_guard(self):
        rows=list(csv.reader(io.StringIO(subprocess.check_output(command('perfect_fixture'),text=True))))
        for row in rows:
            self.assertEqual([float(x) for x in row[1:4]],[0.,0.,0.])
            self.assertEqual(row[4:],['2000','1','1'])

    def test_unobservable_arm_refuses_all_pairs(self):
        row=next(csv.DictReader(io.StringIO(subprocess.check_output(command('unobservable_arm_sentinel'),text=True))))
        self.assertEqual(int(row['held_pairs']),4);self.assertEqual(int(row['observable_pairs']),0)
        self.assertEqual(int(row['new_interval_compatible']),0);self.assertEqual(int(row['current_point_strata_compatible']),0)

    def test_all_prespecified_cases_and_count_invariants(self):
        first=subprocess.check_output(command('all'),text=True)
        self.assertEqual(first,subprocess.check_output(command('all'),text=True))
        rows=list(csv.DictReader(io.StringIO(first)))
        plan=list(csv.DictReader(io.StringIO(subprocess.check_output([str(BIN),'--plan'],text=True))))
        self.assertEqual([r['case'] for r in rows],[r['case'] for r in plan]);self.assertEqual(len(rows),12)
        for r in rows:
            self.assertEqual(int(r['observable_pairs'])+int(r['held_pairs']),4)
            for key in ['new_interval_compatible','current_point_strata_compatible']:
                self.assertTrue(0<=int(r[key])<=int(r['observable_pairs']))
            for key in ['original_degenerate_arm','replica_degenerate_arm','original_generic_resolution_guard']:
                self.assertTrue(0<=int(r[key])<=4)

    def test_matrix_identity(self):
        receipt=json.loads((WORK/'matrices/matrix-receipts.json').read_text())
        for row in receipt['matrices']:
            path=WORK/f"matrices/matrix-n{row['n_worlds_per_form']}-run{row['run']}.bin"
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['sha256'])

    def test_bad_parameters_refuse(self):
        for cmd in [command('unknown'),command(trials=0)]:
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)


if __name__=='__main__':unittest.main()
