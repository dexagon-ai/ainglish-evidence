import unittest
import study
class ContractTests(unittest.TestCase):
 def test_schema_requires_booleans_and_unique_complete_keys(self):
  gold=dict.fromkeys(study.FIELDS,False)
  self.assertTrue(study.score(study.json.dumps(gold),True,gold))
  self.assertFalse(study.score(study.json.dumps(gold),False,gold))
  self.assertFalse(study.score(study.json.dumps({k:0 for k in gold}),True,gold))
  self.assertFalse(study.score('{"include_recipient":false,"include_recipient":true}',True,gold))
 def test_current_job_closes_old_ledgers_without_gold(self):
  c={'context':'New isolated job with fresh clause references.','messages':{'english':'The acting team includes you.'},'brief':{'secret_gold':True}}
  self.assertNotIn('secret_gold',study.current(c,'english'))
  self.assertIn('Earlier jobs are closed history',study.SYSTEM)
 def test_generic_correction_contains_no_answer_bits(self):
  self.assertNotIn('true',study.CORRECTION.lower())
  self.assertNotIn('false',study.CORRECTION.lower())
if __name__=='__main__':unittest.main()
