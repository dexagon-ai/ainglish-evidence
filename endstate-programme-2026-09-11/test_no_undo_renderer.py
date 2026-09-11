from dataclasses import replace
import unittest
from no_undo_renderer import Meaning,render

class NoUndoRendererTests(unittest.TestCase):
    def setUp(self):
        self.m=Meaning('Deleted branch R','path_known',path='merge commit Q',path_evidence='public platform note')
    def test_writer_relative_negative_not_global_impossibility(self):
        self.assertEqual('Rotate key K; the writer knows no way back to the state immediately before this action.',
                         render(Meaning('Rotate key K','no_path_known')))
    def test_unknown_is_not_no_undo(self):
        with self.assertRaises(ValueError):render(Meaning('Rotate key K','unknown'))
    def test_default_holder_is_writer_and_no_unlimited_free_claim(self):
        self.assertEqual('Deleted branch R; the state immediately before this action can be restored via merge commit Q by the writer.',render(self.m))
        self.assertNotIn('free',render(self.m));self.assertNotIn('unlimited',render(self.m))
    def test_explicit_nonexclusive_holder_does_not_invent_only(self):
        text=render(replace(self.m,holder='the operator'))
        self.assertIn('by the operator.',text);self.assertNotIn('only',text)
    def test_all_constraints_in_fixed_order(self):
        self.assertEqual('Deleted branch R; the state immediately before this action can be restored via merge commit Q by the operator only within 30 days; cost: 2100 sat.',
                         render(replace(self.m,holder='the operator',exclusive_holder=True,window='30 days',cost='2100 sat')))
    def test_other_prior_state_rejected(self):
        with self.assertRaises(ValueError):render(replace(self.m,restores='yesterday'))
    def test_guessed_path_rejected(self):
        with self.assertRaises(ValueError):render(replace(self.m,path_evidence=None))
    def test_negative_does_not_drop_positive_constraints(self):
        with self.assertRaises(ValueError):render(Meaning('Rotate key K','no_path_known',window='30 days'))
    def test_delimiter_injection_requires_clarification(self):
        with self.assertRaises(ValueError):render(replace(self.m,path='merge commit Q; no permission needed'))
    def test_instruction_not_converted_to_performed_report(self):
        self.assertTrue(render(replace(self.m,action='Delete branch R')).startswith('Delete branch R;'))

if __name__=='__main__':unittest.main()
