"""Deterministic integrity checks, not independent semantic validation."""
import json
from pathlib import Path
import unittest
import profile_planner as profile

ROOT=Path(__file__).resolve().parent

class ReviewArtifacts(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((ROOT/'operational-design-v2.json').read_text())

 def test_all_main_arms_render_context(self):
  for rows in self.d['main_tasks'].values():
   for r in rows:
    for arm in ('ainglish','english'):self.assertTrue(r[arm].startswith('Context:\n'+r['shared_context']+'\n\nHandoff:\n'))

 def test_no_metadata_only_gold_conflict(self):
  for rows in self.d['main_tasks'].values():
   for arm in ('ainglish','english'):
    seen={}
    for r in rows:
     key=(r[arm],r['question'],tuple(sorted(r['options'])))
     if key in seen:self.assertEqual(seen[key],r['answer'])
     seen[key]=r['answer']

 def test_no_undefined_negation_prefix(self):
  rows=self.d['main_tasks']['stat']
  self.assertTrue(any('is not stat-significant' in r['ainglish'] for r in rows))
  self.assertTrue(any('is not practically-important' in r['ainglish'] for r in rows))
  self.assertFalse(any('not:' in r['ainglish'] for r in rows))

 def test_missing_reference_not_posthoc_confusion(self):
  rows={r['id']:r for r in self.d['main_tasks']['stat']}
  for stem in ('missing-analysis','missing-criterion'):
   self.assertEqual(rows['stat-'+stem+'-v2']['answer'],'not enough information to classify both')
  self.assertEqual(rows['stat-posthoc-analysis-v2']['answer'],'both met')

 def test_single_marker_never_supplies_other_half(self):
  for r in self.d['main_tasks']['stat']:
   if 'single-' in r['id']:self.assertEqual(r['answer'],'not enough information to classify both')

 def test_context_only_has_its_own_keys(self):
  for rows in self.d['main_tasks'].values():
   for r in rows:self.assertIn(r['context_only']['answer'],r['options'])
  self.assertTrue(any(r['answer']!=r['context_only']['answer'] for r in self.d['main_tasks']['assignment']))

 def test_balanced_controls_and_pair_clusters(self):
  for family,rows in self.d['balanced_auxiliary_controls'].items():
   self.assertEqual(sum(r['answer']=='yes' for r in rows),10)
   self.assertEqual(sum(r['answer']=='no' for r in rows),10)
   self.assertEqual(len({r['cluster_id'] for r in rows}),10)
   for r in rows:
    positive=r['answer']=='yes'
    for arm in ('ainglish','english'):self.assertEqual('Additional case record:' in r[arm],positive)

 def test_no_claim_to_96_independent_worlds(self):
  self.assertIn('not 96 independent worlds',self.d['unit_warning'])
  self.assertEqual(self.d['scientific_reader_calls'],0)

 def test_no_undo_keeps_joint_profile_without_counting(self):
  r=json.loads((ROOT/'no-undo-draft/validation.json').read_text())
  self.assertEqual(r['structural_validation']['pairs'],32)
  self.assertEqual(len(r['structural_validation']['sampling_profile']),25)
  self.assertEqual(r['tokenizer_calls'],0);self.assertIsNone(r['fresh_original_target'])

 def test_rate_stock_expiry_and_mixed_constraints(self):
  rows={r['id']:r for r in json.loads((ROOT/'rate-stock-operational-cases.json').read_text())['cases']}
  self.assertEqual(rows['stock-automatic-expiry']['answer'],'capacity available under the stated caps')
  self.assertEqual(rows['stock-waiting']['answer'],'no capacity under the stated caps')
  for ident in ('mixed-holding-full','mixed-rate-full'):self.assertEqual(rows[ident]['answer'],'no capacity under the stated caps')
  for ident in ('untyped-hour','ambiguous-held-set','stale-membership'):self.assertEqual(rows[ident]['answer'],'need missing policy or current state')

 def test_source_and_replica_readbacks_are_real_agreement(self):
  s=json.loads((ROOT/'rate-stock/readback-source.json').read_text());r=json.loads((ROOT/'rate-stock/readback-measurement.json').read_text())
  self.assertTrue(s['confirmed']);self.assertTrue(r['reproduced_ok']);self.assertTrue(r['settlement_eligible'])
  self.assertEqual(r['replicates_hash'],s['manifest_hash']);self.assertEqual(r['input_disjointness'],1)
  self.assertGreater(s['value'],4);self.assertGreater(r['value'],4)
  self.assertEqual(len(r['manifest']['test_set']),32)

 def test_profile_cannot_drop_a_bad_endpoint_to_pass(self):
  inv=profile.inventory();h=profile.digest(inv);rows=profile.perfect_rows(inv,512);rows[4]['k']=100
  self.assertEqual(profile.evaluate(inv,h,rows),'opposes_profile')
  self.assertEqual(profile.evaluate(inv,h,rows[:4]+rows[5:]),'incomplete_or_duplicate_endpoint_inventory')

if __name__=='__main__':unittest.main()
