"""Regression and deliberately corrupted-fixture tests, with no inference."""
from copy import deepcopy
import json
import unittest
import audit_choose as a


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.render=json.loads((a.EVIDENCE/'choose-any-final-package-2026-09-15/rendering-contract.json').read_text())
        cls.banks={label:json.loads((a.ROOT/f'choose-{label}-items.json').read_text())
                   for label in ('original','replication')}

    def test_all_visible_targets(self):
        for label,check in (('original',a.check_source),('replication',a.check_replication)):
            for item in self.banks[label]:
                if not item.get('calibration'):check(item,self.render['spans'][item['settlement_stratum']])

    def test_wrong_answer_rejected(self):
        for label,check in (('original',a.check_source),('replication',a.check_replication)):
            item=deepcopy(self.banks[label][0]);item['answer']=next(x for x in item['options'] if x!=item['answer'])
            with self.assertRaises(AssertionError):check(item,self.render['spans'][item['settlement_stratum']])

    def test_incomplete_comparator_rejected(self):
        for label,check in (('original',a.check_source),('replication',a.check_replication)):
            item=deepcopy(self.banks[label][0]);item['english']=item['english'][:-15]
            with self.assertRaises(AssertionError):check(item,self.render['spans'][item['settlement_stratum']])

    def test_source_wrong_probability_metadata_rejected(self):
        item=deepcopy(self.banks['original'][0])
        policy=next(x for x in item['probe_contract']['policies'] if x['kind']=='unequal-weight')
        for member in policy['distribution']:policy['distribution'][member]='1/2'
        with self.assertRaises(AssertionError):a.check_source(item,self.render['spans'][item['settlement_stratum']])

    def test_replica_disguised_uniform_weight_rejected(self):
        import re
        item=deepcopy(self.banks['replication'][0])
        for arm in ('english','ainglish'):
            item[arm]=re.sub(r'assigning weight \d+ to','assigning weight 1 to',item[arm])
        with self.assertRaises(AssertionError):a.check_replication(item,self.render['spans'][item['settlement_stratum']])

    def test_scored_cell_coverage_and_arm_assignment(self):
        for label in self.banks:
            m=json.loads((a.ROOT/f'choose-{label}-measurement.json').read_text())
            a.scored_stats(m,self.banks[label])
            broken=deepcopy(m);broken['interval_provenance_attestation']['cells'].pop()
            with self.assertRaises(AssertionError):a.scored_stats(broken,self.banks[label])
            broken=deepcopy(m);cell=broken['interval_provenance_attestation']['cells'][0]
            cell['arm']='ainglish' if cell['arm']=='english' else 'english'
            with self.assertRaises(AssertionError):a.scored_stats(broken,self.banks[label])


if __name__=='__main__':unittest.main()
