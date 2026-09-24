import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest

import acceptance_matrix as matrix
import build_candidates as banks
from corpus import recover


class PreparationTest(unittest.TestCase):
    def setUp(self):
        self.all={'latest':banks.latest_bank(),'stat':banks.statistical_bank(),'assignment':banks.assignment_bank()}

    def test_all_keys_and_declared_counts(self): banks.verify(self.all)

    def test_each_domain_family_contains_every_statistical_state(self):
        groups={}
        for r in self.all['stat']:
            groups.setdefault((r['domain'],r['template_id']),set()).add(r['answer'])
        self.assertEqual(40,len(groups))
        self.assertTrue(all(v==set(banks.STATES[:4]) for v in groups.values()))

    def test_hidden_statistical_world_cannot_change_bare_gold(self):
        groups={}
        for r in self.all['stat']:
            key=(r['bare'],r['question'],tuple(sorted(r['options'])))
            groups.setdefault(key,set()).add(r['bare_answer'])
        self.assertTrue(all(v=={banks.STATES[4]} for v in groups.values()))

    def test_known_false_closure_and_unresolved_order_differ(self):
        self.assertEqual('No',self.all['latest'][12]['answer'])
        self.assertEqual(banks.YESNO[2],self.all['latest'][11]['answer'])

    def test_default_materialisation_does_not_change_provenance(self):
        r=copy.deepcopy(self.all['assignment'][1]['record'])
        before=banks.resolve(r);r['materialised']=not r['materialised']
        self.assertEqual(before,banks.resolve(r))

    def test_precedence_is_not_list_order(self):
        r=copy.deepcopy(self.all['assignment'][7]['record']);expected=banks.resolve(r)
        r['assignments'].reverse();self.assertEqual(expected,banks.resolve(r))

    def test_null_three_ways(self):
        actual=[banks.resolve(self.all['assignment'][i]['record'])[0] for i in (3,4,5)]
        self.assertEqual([banks.ORIGINS[i] for i in (1,0,2)],actual)

    def test_policy_preserves_global_loss_veto(self):
        for route in ('current_superiority','comparator_v5','preservation_discussion'):
            self.assertIn('confirmed_loss_veto',matrix.interpret(matrix.BASE|{'confirmed_loss':True,'actual_separate_benefit':True,'careful_superiority':True},route))

    def test_cost_allowance_cannot_be_separate_benefit(self):
        self.assertIn('no_separate_demonstrated_benefit',matrix.interpret(matrix.BASE,'preservation_discussion'))

    def test_prior_and_new_review_fixtures(self):
        r=matrix.check();self.assertEqual(40,r['prior_fixture_count']);self.assertEqual(11,r['new_case_count'])

    def test_corpus_parser_exact_lines_and_exclusions(self):
        prose='This paragraph has enough ordinary English words to satisfy the fixed lexical selection rule without any markup.'
        text=prose+'\n\n    '+prose+'\n\nTitle\n=====\n\n'+prose.replace('paragraph','`paragraph`')+'\n'
        self.assertEqual([{'source':'test.rst','first_line':1,'last_line':1,'text':prose}],recover.extract('test.rst',text))

    def test_corpus_offline_recovery(self):
        with redirect_stdout(io.StringIO()):recover.build()

    def test_rebuilt_artifact_identity(self):
        root=Path(__file__).resolve().parent
        manifest=json.loads((root/'candidate-manifest.json').read_text())
        for name,rows in self.all.items():
            self.assertEqual(manifest['cases'][name]['review_bank_sha256'],banks.sha(rows))


if __name__=='__main__':unittest.main()
