import unittest
from completion_admission import admission,improve_stock_grammar

class CompletionAdmissionTests(unittest.TestCase):
    def fixtures(self,n):
        mapping={str(i):[f'{i}-{k}' for k in range(8)] for i in range(20)}
        rows=[{'review_id':str(i),'binding_prohibition_is_a_plausible_reading':i<n,
               'epistemic_nonoccurrence_is_a_plausible_reading':True,'reason_or_lexical_prior_concern':'Invented test judgement, not review'} for i in range(20)]
        return rows,mapping
    def test_threshold_counts_rows_and_discloses_clauses(self):
        x=admission(*self.fixtures(16),author_count_unit='contextual_primary_rows',prior_answer_exposure=False)
        self.assertTrue(x['minimum_128_rows_met']);self.assertEqual(16,x['independent_bare_clauses'])
        x=admission(*self.fixtures(15),author_count_unit='contextual_primary_rows',prior_answer_exposure=False)
        self.assertFalse(x['minimum_128_rows_met'])
    def test_unresolved_unit_is_not_chosen_by_the_runner(self):
        with self.assertRaises(ValueError):admission(*self.fixtures(20),prior_answer_exposure=False)
    def test_exposed_review_cannot_be_called_blind(self):
        with self.assertRaises(ValueError):admission(*self.fixtures(20),author_count_unit='contextual_primary_rows',prior_answer_exposure=True)
    def test_missing_decision_is_not_an_admission(self):
        rows,mapping=self.fixtures(20);rows[0]['binding_prohibition_is_a_plausible_reading']=None
        with self.assertRaises(ValueError):admission(rows,mapping,author_count_unit='contextual_primary_rows',prior_answer_exposure=False)
    def test_grammar_repair_does_not_change_marker_or_key(self):
        source=[{'id':'invented','english':'Exactly 1 distinct workers are inside S.','ainglish':'Exactly 1 workers remain-in(S).','answer':'key'}]
        rows,changes=improve_stock_grammar(source)
        self.assertEqual('Exactly 1 distinct worker is inside S.',rows[0]['english'])
        self.assertEqual('Exactly 1 worker remain-in(S).',rows[0]['ainglish'])
        self.assertEqual('key',rows[0]['answer']);self.assertEqual(2,len(changes))
        self.assertIn('workers',source[0]['english'])

if __name__=='__main__':unittest.main()
