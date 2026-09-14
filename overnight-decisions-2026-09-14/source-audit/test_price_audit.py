import unittest
from audit_price import normal

class NormalizationTests(unittest.TestCase):
 def test_only_named_relabelled_identifiers_change(self):
  self.assertEqual(normal('x-item-7302; x-invoice-7302; x-pool-7302'),normal('x-item-8302; x-invoice-8302; x-pool-8302'))
 def test_prices_counts_and_answers_are_preserved(self):
  self.assertNotEqual(normal('Price 7302'),normal('Price 8302'))
  self.assertNotEqual(normal('charge zero'),normal('charge greater than zero'))
  self.assertNotEqual(normal({'answer':'A'}),normal({'answer':'B'}))
  self.assertEqual(normal('N=7; 8308; price £8302'), 'N=7; 8308; price £8302')
 def test_only_two_observation_timestamps_change(self):
  self.assertEqual(normal('2026-09-07 at12:00 UTC'),normal('2026-09-13 at15:00 UTC'))
  self.assertNotEqual(normal('2026-09-07 at12:01 UTC'),normal('2026-09-13 at15:00 UTC'))

if __name__=='__main__':unittest.main()
