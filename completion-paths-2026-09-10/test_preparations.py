"""Deterministic preparation checks; no readers, encoders, governance writes or fake evidence."""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from ainglish.client import manifest_commitment

ROOT=Path(__file__).resolve().parent

def load(path):return json.loads((ROOT/path).read_text())
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

class PreparationTests(unittest.TestCase):
    def testRejectedComparatorCannotSpend(self):
        runner=module('removed_replica_test','removed-replication/run.py')
        with self.assertRaisesRegex(RuntimeError,'Packet held before spend'):
            runner.main('run')

    def testFreshFrameIsPinnedAndActuallyFiledAsReplication(self):
        base='removed-replication/source-frame/'
        plan=load(base+'plan.json');result=load(base+'result.json')
        target='903b67a697f5e000b7c57ab64f491e33a7b05aacc67fd5d05a0a99d7c1a6a670'
        self.assertEqual(manifest_commitment(plan['manifest']),result['measurement_hash'])
        self.assertEqual(plan['manifest']['replicates_hash'],target)
        self.assertEqual(load(base+'run-result.json')['payload']['replicates_hash'],target)
        self.assertTrue(result['settlement_eligible'])
        self.assertFalse(result['reproduced_ok'])
        self.assertEqual(result['value'],0.375)
        self.assertFalse(any('stratum' in r for r in plan['manifest']['test_set']))
        self.assertNotIn('settlement_strata',plan['manifest'])

    def testCausalBoundaryRejectsAdditionalChanges(self):
        pre=module('retirement_precheck_test','retirement_precheck.py')
        before='    public function assess(Proposal $p): void\n    {\n        '+pre.OLD+'\n            return;\n        }\n    }\n    /**'
        after=before.replace(pre.OLD,pre.NEW)
        good=pre.causal_boundary(before,after,after)
        self.assertTrue(good['only_guard_changed'] and good['current_method_unchanged'])
        self.assertFalse(pre.causal_boundary(before,after,after.replace('return;','return false;'))['current_method_unchanged'])
        self.assertFalse(pre.causal_boundary(before,after.replace('return;','return false;'),after)['only_guard_changed'])

    def testLearningPacketsBindEntryNotTrainingClaims(self):
        for name in ['rent-learning','resume-learning']:
            base='reader-packets/'+name+'/'
            plan=load(base+'review-plan.json');items=load(base+'items.json')
            self.assertTrue(plan['not_an_executable_runspec'])
            self.assertEqual(plan['reader_instruments'],[])
            self.assertIsNone(plan['scientific_attempt_id'])
            self.assertEqual(plan['target_reader_calls'],0)
            self.assertEqual(hashlib.sha256(plan['entry']['text'].encode()).hexdigest(),plan['entry']['sha256'])
            self.assertEqual(plan['entry']['proposal_revision'],plan['slug'])
            self.assertTrue(all(r['english']==r['ainglish'] for r in items if not r.get('calibration')))
            self.assertTrue(load(base+'offline-audit.json')['ok'])

    def testSanctionGoldLedgerAndRestrictedClaim(self):
        base='reader-packets/sanction-careful/'
        rows=load(base+'items.json');ledger=load(base+'gold-ledger.json')
        self.assertEqual(len(rows),64)
        self.assertEqual(sum(r['strata']['form']=='allow' for r in rows),32)
        for row,key in zip(rows,ledger):
            gold=key['allow_tray'] if key['polarity']=='allow' else key['penalty_tray']
            if not key['asserted_formal_act']:gold='Neither tray is licensed'
            self.assertEqual(row['answer'],gold)
            self.assertNotIn('sanctioned',row['english'])
        self.assertTrue(load(base+'review-plan.json')['not_an_executable_runspec'])

    def testOutcomeDependenceDoesNotInventIndependentAbilities(self):
        note=load('outcome-dependence.json')
        self.assertFalse(note['items_changed'])
        blocks=note['family_dependence']
        self.assertEqual(blocks['weighted-mean'],blocks['affine-average'])
        self.assertEqual(blocks['possible-value'],blocks['maximal-mass'])
        self.assertEqual(note['target_reader_calls'],0)

if __name__=='__main__':unittest.main()
