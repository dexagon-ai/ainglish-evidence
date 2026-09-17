"""All outcomes here are synthetic fixtures, never language evidence."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest
from ainglish import panel
import group_sensitivity as g

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'execution-decisions-2026-09-17'


class GroupSensitivityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((SOURCE/'resume-phase-one.json').read_text())['runspec_candidate_not_authorized']
        cls.core = [x for x in cls.source['items'] if not x.get('calibration')]
        cls.index = g.group_index(cls.source['items'], [x['name'] for x in cls.source['panel']], cls.source['seed'])
        cls.cells = [{**cell, 'correct': n % 7 != 0}
                     for n, cell in enumerate(c for group in cls.index['groups'] for c in group['cells'])]
        cls.result = g.analyse(cls.index, cls.cells)

    def test_exact_accepted_input_identity(self):
        self.assertEqual(g.digest(self.core), 'a735c6e6fe7647cd80365b5ed7a9befa7c65e5f0b9d583cb7406a9832eceec8c')
        self.assertEqual(len(self.index['groups']), 32)
        self.assertTrue(all(len(x['items'])==2 and len(x['cells'])==4 for x in self.index['groups']))

    def test_allocation_matches_official_sdk_for_every_cell(self):
        counts = {}
        for group in self.index['groups']:
            counts.setdefault(group['policy'], Counter())
            for cell in group['cells']:
                self.assertEqual(cell['arm'], panel.arm_for(self.source['seed'], cell['reader'], cell['item_id']))
                counts[group['policy']][cell['arm']] += 1
        self.assertEqual(counts, {'redo-core': {'english':33,'ainglish':31}, 'resume-core': {'english':37,'ainglish':27}})

    def test_draws_preserve_domain_policy_and_group_multiplicity(self):
        by_id = {x['id']:x for x in self.index['groups']}
        for draw in [0,1,123,1999]:
            sample = g.sample_groups(self.index, draw)
            self.assertEqual(len(sample),32)
            self.assertEqual(Counter((by_id[x]['domain'],by_id[x]['policy']) for x in sample),
                             {(d,p):4 for d in g.DOMAINS for p in g.POLICIES})
            self.assertEqual(sum(len(by_id[x]['cells']) for x in sample),128)
        self.assertLess(len(set(g.sample_groups(self.index,0))),32)

    def test_random_index_byte_definition(self):
        sample = g.sample_groups(self.index,0)
        block,members = g.blocks(self.index)[0]
        raw = b'\0'.join([g.ALGORITHM.encode(),b'2026091702',block.encode(),b'0',b'0'])
        self.assertEqual(sample[0], members[int.from_bytes(hashlib.sha256(raw).digest()[:8],'big')%4])

    def test_point_uses_all_cells_equal_policy_weights(self):
        policies={i:group['policy'] for group in self.index['groups'] for i in group['items']}
        expected={}
        for policy in g.POLICIES:
            by_arm={a:[c['correct'] for c in self.cells if policies[c['item_id']]==policy and c['arm']==a] for a in g.ARMS}
            expected[policy]=100*(Fraction(sum(by_arm['ainglish']),len(by_arm['ainglish']))-
                                  Fraction(sum(by_arm['english']),len(by_arm['english'])))
            self.assertAlmostEqual(self.result['point_unrounded_pp'][policy],float(expected[policy]),places=11)
        self.assertAlmostEqual(self.result['point_unrounded_pp']['aggregate'],float(sum(expected.values())/2),places=11)

    def test_result_is_not_fileable_or_governance_evidence(self):
        self.assertFalse(self.result['fileable_measurement'])
        self.assertEqual(self.result['governance_effect'],'none')
        self.assertEqual(self.result['draws'],2000)
        self.assertEqual(self.result['accepted_draws']+self.result['invalid_draws'],2000)

    def test_reordering_cells_and_groups_cannot_change_result(self):
        index=deepcopy(self.index); index['groups'].reverse()
        result=g.analyse(index,list(reversed(self.cells)))
        # Index hash is deliberately sensitive to serialized index ordering.
        for key in self.result:
            if key!='group_index_sha256':self.assertEqual(result[key],self.result[key],key)

    def test_missing_duplicate_extra_and_wrong_arm_refused(self):
        cases=[self.cells[:-1], self.cells+[self.cells[0]]]
        extra=deepcopy(self.cells); extra[0]['item_id']='not-in-plan';cases.append(extra)
        wrong=deepcopy(self.cells);wrong[0]['arm']='english' if wrong[0]['arm']=='ainglish' else 'ainglish';cases.append(wrong)
        for cells in cases:
            with self.assertRaises(ValueError):g.analyse(self.index,cells)

    def test_boolean_not_numeric_correctness(self):
        cells=deepcopy(self.cells);cells[0]['correct']=1
        with self.assertRaises(ValueError):g.analyse(self.index,cells)

    def test_index_cannot_split_or_omit_companion_cells(self):
        index=deepcopy(self.index);index['groups'][0]['cells'].pop()
        with self.assertRaises(ValueError):g.analyse(index,self.cells)
        index=deepcopy(self.index);index['groups'][0]['items'][0]=index['groups'][1]['items'][0]
        with self.assertRaises(ValueError):g.analyse(index,self.cells)

    def test_dead_arm_holds_jointly_without_retries(self):
        policies={i:group['policy'] for group in self.index['groups'] for i in group['items']}
        cells=deepcopy(self.cells)
        for c in cells:
            if policies[c['item_id']]=='resume-core' and c['arm']=='english':c['correct']=None
        result=g.analyse(self.index,cells)
        self.assertEqual(result['accepted_draws'],0)
        self.assertEqual(result['invalid_draw_indices'],list(range(2000)))
        self.assertEqual(result['nominal_95_percentile_intervals_pp'],{})
        self.assertEqual(result['absent_cells_retained'],37)
        self.assertEqual(result['missing_policy_arm_counts'],{'resume-core:english':2000})

    def test_partial_invalid_draws_use_one_common_mask(self):
        group=next(x for x in self.index['groups'] if x['policy']=='resume-core'
                   and {c['arm'] for c in x['cells']}=={'english','ainglish'})
        policies={i:x['policy'] for x in self.index['groups'] for i in x['items']}
        cells=[{**c,'correct':None if policies[c['item_id']]=='resume-core'
               and c['item_id'] not in group['items'] else c['correct']} for c in self.cells]
        result=g.analyse(self.index,cells)
        expected_invalid=[n for n in range(2000) if group['id'] not in g.sample_groups(self.index,n)]
        self.assertEqual(result['invalid_draw_indices'],expected_invalid)
        self.assertGreater(result['accepted_draws'],0)
        self.assertLess(result['accepted_draws'],2000)
        self.assertEqual(set(result['nominal_95_percentile_intervals_pp']),{'aggregate',*g.POLICIES})
        mask=bytes(int(n not in expected_invalid) for n in range(2000))
        self.assertEqual(result['accepted_mask_sha256'],hashlib.sha256(mask).hexdigest())

    def test_perfect_synthetic_scores_flag_degeneracy_not_certainty(self):
        result=g.analyse(self.index,[{**c,'correct':True} for c in self.cells])
        self.assertTrue(all(x['degenerate'] and x['lo']==0 and x['hi']==0
                            for x in result['nominal_95_percentile_intervals_pp'].values()))
        self.assertEqual(result['governance_effect'],'none')

    def test_official_sdk_receipt_and_integrity_checks(self):
        # Artificial answers generate a test-only SDK receipt; no reader function is called.
        lookup={(c['item_id'],c['reader']):c for c in self.cells}
        rows=[]
        for i in self.core:
            for r in self.source['panel']:
                c=lookup[(i['id'],r['name'])]
                answer=i['answer'] if c['correct'] else next(x for x in i['options'] if x!=i['answer'])
                rows.append((i['id'],c['arm'],r['name'],answer))
        contract=panel._settlement_contract(self.source,self.core,self.source['panel'],self.source['seed'])
        _,_,receipt=panel.attested_bootstrap_accuracy(rows,self.core,self.source['panel'],contract,seed=self.source['seed'])
        self.assertEqual(g.analyse(self.index,g.verified_cells(self.index,receipt)),self.result)
        bad=deepcopy(receipt);bad['cells'][0]['correct']=not bad['cells'][0]['correct']
        with self.assertRaises(ValueError):g.verified_cells(self.index,bad)

    def test_prepared_manifest_pins_analysis_and_leaves_science_unchanged(self):
        held=json.loads((HERE/'held-execution.json').read_text());spec=held['runspec_candidate_not_authorized']
        for key in ['items','items_sha256','items_url','seed','metric','panel','reader_qualifications','settlement_strata','comparator']:
            self.assertEqual(spec[key],self.source[key],key)
        self.assertIsNone(held['analysis_revision_acceptance']);self.assertIsNone(held['frozen_replica_bank'])
        self.assertEqual(held['reader_calls'],0);self.assertEqual(held['attempt_ids'],[])
        for value in held['pins'].values():self.assertIn(value,spec['study_scope'])
        self.assertEqual(held['pins']['analysis_code_sha256'],hashlib.sha256((HERE/'group_sensitivity.py').read_bytes()).hexdigest())
        self.assertEqual(held['pins']['analysis_plan_sha256'],g.digest(json.loads((HERE/'analysis-plan.json').read_text())))
        self.assertEqual(held['pins']['group_index_sha256'],g.digest(json.loads((HERE/'group-index.json').read_text())))


if __name__=='__main__':
    unittest.main()
