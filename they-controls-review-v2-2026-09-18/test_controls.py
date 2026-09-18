from collections import Counter, defaultdict
from copy import deepcopy
import unittest
from controls import BASE, FORMS, LABELS, SPECS, build, score, text_only, witnesses


class CoverageTests(unittest.TestCase):
    def setUp(self): self.f=build()
    def test_actual_units(self):
        self.assertEqual((self.f['semantic_worlds'],self.f['semantic_question_probes'],self.f['prompt_variants']),(55,67,201))
        self.assertEqual(len({r['id'] for r in self.f['items']}),201)
        self.assertEqual(Counter(Counter(r['world_id'] for r in self.f['items']).values()),{3:43,6:12})
    def test_old_ninety_prompts_are_identical(self):
        self.assertEqual(self.f['items'][:90],BASE.build()['items'])
        self.assertEqual(self.f['candidate_sha256'],BASE.build()['candidate_sha256'])
    def test_no_target_markers_or_calibration_claim(self):
        for r in self.f['items']:
            self.assertFalse(any(form in r['text']+' '+r['question'] for form in FORMS))
            self.assertNotIn('calibration',r)
    def test_existing_questions_and_golds_only(self):
        for r in self.f['items']:
            self.assertEqual(r['question'],SPECS[r['dimension']]['question'])
            self.assertIn(r['gold'],LABELS)
    def test_partial_information_covers_five_dimensions(self):
        rows=[r for r in self.f['items'] if r.get('coverage_family')=='partial_information']
        self.assertEqual(len(rows),15)
        self.assertEqual({r['dimension'] for r in rows},set(SPECS))
        self.assertTrue(all(r['gold']==LABELS[2] for r in rows))
    def test_all_named_cue_families_cover_both_forms(self):
        for family in ('name_not_gender','pronoun_not_gender','naming_not_recorder_knowledge','completion_not_coordination'):
            rows=[r for r in self.f['items'] if r.get('coverage_family')==family]
            self.assertEqual(len(rows),6)
            self.assertEqual({r['form_slot'] for r in rows},set(FORMS))
            self.assertTrue(all(r['gold']==LABELS[2] for r in rows))
    def test_same_record_different_questions_and_golds(self):
        groups=defaultdict(list)
        for r in self.f['items']:
            if r.get('coverage_family')=='same_record_distinct_questions': groups[r['world_id']].append(r)
        self.assertEqual(len(groups),12)
        for rows in groups.values():
            self.assertEqual(len(rows),6)
            self.assertEqual(len({r['text'] for r in rows}),1)
            self.assertEqual(len({r['question'] for r in rows}),2)
            self.assertEqual(Counter(r['gold'] for r in rows),{'Yes':3,'No':3})
            for order in range(3):
                pair=[r for r in rows if r['id'].endswith('/order-'+str(order))]
                self.assertEqual(pair[0]['options'],pair[1]['options'])
                self.assertEqual({r['gold'] for r in pair},{'Yes','No'})
    def test_any_shared_record_only_label_at_most_half_on_mixed_world(self):
        groups=defaultdict(list)
        for r in self.f['items']:
            if r.get('coverage_family')=='same_record_distinct_questions': groups[r['world_id']].append(r)
        for rows in groups.values():
            for label in LABELS:
                self.assertLessEqual(sum(r['gold']==label for r in rows)/len(rows),.5)
    def test_question_blind_old_counterexample_reproduces(self):
        f=BASE.build(); result=score(f,BASE.fixture_answers(f,lambda r:text_only(r['text'])))
        self.assertEqual(sum(x['correct'] for x in result['coverage_families'].values()),90)
    def test_question_blind_new_witness_fails_all_ten_explicit_floors(self):
        r=score(self.f,BASE.fixture_answers(self.f,lambda r:text_only(r['text'])))
        mixed=r['coverage_families']['same_record_distinct_questions']
        self.assertEqual((mixed['correct'],mixed['answered']),(36,72))
        self.assertTrue(all(e['explicit_fact']['observed_accuracy']<.9 for e in r['endpoints']))
    def test_each_old_constant_strategy_still_fails(self):
        w=witnesses(self.f)
        for name,result in w.items():
            if name.startswith('constant-'):
                self.assertTrue(all(e['explicit_fact']['observed_accuracy']<.9 for e in result['endpoints']))
    def test_gold_position_balanced_per_endpoint_role(self):
        groups=defaultdict(list)
        for r in self.f['items']: groups[(r['form_slot'],r['dimension'],r['role'])].append(r)
        for rows in groups.values():
            self.assertEqual(len(set(Counter(r['options'].index(r['gold']) for r in rows).values())),1)
    def test_partial_error_witnesses_are_detected_separately(self):
        for label in LABELS[:2]:
            rows=BASE.fixture_answers(self.f,lambda r:label if r.get('coverage_family')=='partial_information' else r['gold'])
            result=score(self.f,rows)
            self.assertEqual(result['coverage_families']['partial_information']['observed_accuracy'],0)
            self.assertEqual(sum(v['incorrect'] for v in result['coverage_families'].values()),15)
    def test_oracle_has_no_certificate(self):
        r=score(self.f,BASE.fixture_answers(self.f))
        self.assertTrue(r['complete'])
        self.assertTrue(r['complete_is_not_passed'])
        self.assertFalse(r['fileable_measurement'])
        self.assertNotIn('bundle_pass',r)
        self.assertTrue(all(x['observed_accuracy']==1 for x in r['coverage_families'].values()))
    def test_shared_world_does_not_allow_reused_observation(self):
        rows=BASE.fixture_answers(self.f)
        mixed=[i for i,r in enumerate(self.f['items']) if r.get('coverage_family')=='same_record_distinct_questions']
        rows[mixed[3]]['observation_id']=rows[mixed[0]]['observation_id']
        with self.assertRaises(ValueError): score(self.f,rows)
    def test_second_read_requires_a_new_contract_not_an_observation_alias(self):
        rows=BASE.fixture_answers(self.f); second=deepcopy(rows[-1]); second['observation_id']='another-read'
        with self.assertRaises(ValueError): score(self.f,rows+[second])
    def test_cross_endpoint_reassignment_refuses(self):
        rows=BASE.fixture_answers(self.f); rows[-1]['dimension']='gender'
        with self.assertRaises(ValueError): score(self.f,rows)
    def test_missing_and_null_remain_absent_not_wrong(self):
        rows=BASE.fixture_answers(self.f); rows[-1]['answer']=None
        r=score(self.f,rows)
        self.assertFalse(r['complete'])
        self.assertEqual(sum(v['incorrect'] for v in r['coverage_families'].values()),0)
        self.assertEqual(sum(v['absent'] for v in r['coverage_families'].values()),1)
    def test_question_counts_are_not_world_counts(self):
        r=score(self.f,BASE.fixture_answers(self.f))
        self.assertEqual((r['semantic_worlds'],r['semantic_question_probes']),(55,67))
        self.assertEqual(r['coverage_families']['same_record_distinct_questions']['semantic_worlds'],12)
    def test_reproducible_and_no_readers(self):
        self.assertEqual(self.f,build())
        self.assertEqual(self.f['reader_calls'],0)
        self.assertEqual(self.f['design_reference_explicit_accuracy_floor'],.9)

if __name__=='__main__': unittest.main()
