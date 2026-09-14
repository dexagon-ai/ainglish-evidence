import unittest
from report import analyse
from build import gold

class ReportTests(unittest.TestCase):
 def test_counts_and_cluster_identity(self):
  rows=[{'reader':'r','strata':{'branch':'b','family':str(family)},'arm':arm,
   'answer':'a','expected':'a','correct':True} for family in range(3) for arm in ['english','ainglish']]
  report=analyse(rows)
  self.assertEqual(report['target_cells'],6)
  self.assertEqual(report['frames'],3)
  self.assertEqual(report['per_reader_stratum'][0]['delta_pp'],0)
  self.assertEqual(report['per_reader_stratum'][0]['cluster_interval_pp'],[0,0])
 def test_false_flags_are_rejected(self):
  with self.assertRaises(AssertionError):
   analyse([{'reader':'r','strata':{'branch':'b','family':'1'},'arm':'english','answer':'x','expected':'y','correct':True}])
 def test_expiry_precedes_discharge_but_not_counterproof(self):
  self.assertEqual(gold({'non_discharge':False,'expired':True,'discharge':True}),'re-verify')
  self.assertEqual(gold({'non_discharge':True,'expired':True,'discharge':True}),'dispute')

if __name__=='__main__':unittest.main()
