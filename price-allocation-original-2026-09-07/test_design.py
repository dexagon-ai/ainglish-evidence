import unittest
from collections import Counter
import build
class GoldTests(unittest.TestCase):
 def test_cross_product_and_all_keys(self):
  cases=build.build_cases();self.assertEqual(len(cases),128)
  self.assertEqual(set(Counter((c['domain'],c['form']) for c in cases).values()),{8})
  for c in cases:
   self.assertEqual(c['choice_meanings'][c['answer']],c['gold'])
   self.assertNotEqual(c['gold'][c['asserted_axis']],'not determined')
   self.assertEqual(c['gold'][1-c['asserted_axis']]=='not determined',not c['other_revealed'])
 def test_bare_uncertainty_is_not_a_hidden_world_key(self):
  self.assertEqual(build.bare_truth(True,{}),['not determined','not determined'])
  self.assertEqual(build.bare_truth(True,{1:False}),['no','no'])
  self.assertEqual(build.bare_truth(False,{0:False}),['no','no'])
 def test_no_gold_leak_in_surfaces(self):
  for c in build.build_cases():
   for arm in ['english','ainglish','bare']:
    self.assertNotIn('world',c[arm]);self.assertNotIn('gold',c[arm])
if __name__=='__main__':unittest.main()
