import math
import unittest
from report import ALPHA,bounds,cdf,count_rows
from build import primary,consequence_bank,learning_bank

class ReportTest(unittest.TestCase):
 def test_perfect_keeps_uncertainty(self):
  lo,hi=bounds(100,100)
  self.assertAlmostEqual(lo,ALPHA**.01,places=10);self.assertEqual(hi,1.)
  self.assertLess(lo,1.)
 def test_zero_keeps_uncertainty(self):
  lo,hi=bounds(0,100)
  self.assertEqual(lo,0.);self.assertAlmostEqual(hi,1-ALPHA**.01,places=10)
 def test_midpoint_is_symmetric(self):
  lo,hi=bounds(50,100);self.assertAlmostEqual(lo,1-hi,places=10)
  self.assertAlmostEqual(cdf(50,100,hi),ALPHA,places=10)
  self.assertAlmostEqual(cdf(49,100,lo),1-ALPHA,places=10)
 def test_no_empty_cell(self):
  with self.assertRaises(ValueError):bounds(0,0)
 def test_counts_use_response_not_trusted_boolean(self):
  row={'answer':'No','expected':'Yes','correct':True,'reader':'x','arm':'english','strata':{'form':'none-of'}}
  with self.assertRaises(AssertionError):count_rows([row])
 def test_required_counts_and_families(self):
  p=primary();c=consequence_bank();l=learning_bank()
  self.assertEqual((len(p),len(c),len(l)),(448,2240,128))
  self.assertEqual(len({r['strata']['predicate_family'] for r in p}),32)
  self.assertEqual(len({r['strata']['frame'] for r in c}),224)
  self.assertTrue(all(r['english']==r['ainglish'] for r in l))

if __name__=='__main__':unittest.main()
