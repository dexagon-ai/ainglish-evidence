import importlib.util
import json
import math
from pathlib import Path
import unittest

from preservation_design import clearance, exact
from profile_fixtures import evaluate
from task_designs import latest, statistical, assignment

ROOT=Path(__file__).resolve().parent


class BoundTests(unittest.TestCase):
    def test_exact_marginal_implementation(self):exact.verify()

    def test_all_correct_is_not_zero_uncertainty(self):
        self.assertLess(exact.lower(2,2,.05),.9)
        self.assertGreater(exact.upper(0,2,.05),.05)

    def test_zero_failures_formula(self):
        for n in (2,16,64,128,512):
            self.assertAlmostEqual(exact.upper(0,n,.05),1-.05**(1/n))

    def test_larger_sample_reduces_boundary_uncertainty(self):
        self.assertLess(clearance(32,32,32,32,0,32),0)
        self.assertGreater(clearance(128,128,128,128,0,128),0)

    def test_invalid_count_rejected(self):
        for k,n in ((-1,4),(5,4),(True,4),(3,0),(1.5,4)):
            with self.assertRaises(ValueError):evaluate([{'marked':(k,n),'english':(4,4),'errors':[(0,4)]}])

    def test_exact_tail_coverage_small_samples(self):
        for n in (5,16,32):
            for p in (.01,.05,.2,.5,.9,.99):
                false=sum(exact.distribution(n,p)[k] for k in range(n+1) if exact.lower(k,n,.025)>p)
                self.assertLessEqual(false,.025+1e-10)


class OperationalTests(unittest.TestCase):
    def test_each_family_has_twelve_review_cases(self):
        for rows in (latest(),statistical(),assignment()):
            self.assertEqual(len(rows),12);self.assertEqual(len({r['id'] for r in rows}),12)

    def test_invariant_options_no_cardinality_shortcut(self):
        for rows in (latest(),statistical(),assignment()):
            expected=set(rows[0]['options'])
            for r in rows:
                self.assertEqual(set(r['options']),expected)
                self.assertEqual(r['options'],r['context_only']['options'])
                self.assertIn(r['answer'],r['options'])
                self.assertIn(r['context_only']['answer'],r['options'])

    def test_no_linguistic_message_in_context_only(self):
        for r in latest()+statistical()+assignment():
            self.assertEqual(r['context_only']['text'],r['shared_context'])
            self.assertNotIn(r['ainglish_message'],r['context_only']['text'])

    def test_ablations_have_own_golds(self):
        for rows in (latest(),statistical(),assignment()):
            self.assertTrue(any(r['answer']!=r['context_only']['answer'] for r in rows))

    def test_four_statistical_joint_states(self):
        self.assertEqual({r['answer'] for r in statistical()[:4]},
            {'both met','neither met','test threshold met only','practical criterion met only'})

    def test_single_marker_not_scored_against_hidden_other_fact(self):
        for r in statistical()[4:8]:self.assertEqual(r['answer'],'not enough information to classify both')

    def test_missing_criterion_is_not_also_defined(self):
        r=next(r for r in statistical() if r['id'].endswith('missing-criterion'))
        self.assertNotIn('C requires',r['shared_context'])
        self.assertEqual(r['answer'],'not enough information to classify both')

    def test_historical_final_not_retroactively_false(self):
        r=next(r for r in latest() if r['id'].endswith('historical-reopening'))
        self.assertEqual(r['answer'],'record the terminal item at the cited historical closure')

    def test_equal_value_not_origin(self):
        rows=assignment()
        a=next(r for r in rows if r['id'].endswith('explicit-equals-default'))
        d=next(r for r in rows if r['id'].endswith('default-equals-explicit'))
        self.assertNotEqual(a['answer'],d['answer'])

    def test_rejected_resolution_context_already_conclusive(self):
        r=next(r for r in assignment() if r['id'].endswith('rejected-null'))
        self.assertEqual(r['answer'],r['context_only']['answer'])

    def test_required_non_entailments_are_separate_unmeasured_probes(self):
        for r in latest()+statistical()+assignment():self.assertGreaterEqual(len(r['non_entailment_probes']),2)


if __name__=='__main__':unittest.main()
