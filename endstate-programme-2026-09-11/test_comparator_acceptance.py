import unittest
import comparator_acceptance as c

class ComparatorAcceptanceTests(unittest.TestCase):
    def test_all_40_cases(self):self.assertEqual(40,len(c.check()))
    def test_all_promises_fail_independently(self):
        flags=c.interpret(c.BASE|{'cost_confirmed':False,'bare_promised':True,'learnability_promised':True})
        for flag in ['separate_cost_unmet','separate_bare_gain_unmet','promised_learning_not_confirmed']:
            self.assertIn(flag,flags)
    def test_loss_veto_survives_even_a_very_wide_fixture_margin(self):
        self.assertIn('confirmed_loss_veto',c.interpret(c.BASE|{'margin':100,'confirmed_loss':True}))

if __name__=='__main__':unittest.main()
