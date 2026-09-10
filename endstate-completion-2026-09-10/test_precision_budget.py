import math
import unittest

from precision_budget import minimum_zero_error_n, report, zero_error_upper


class PrecisionPlanningTests(unittest.TestCase):
    def test_known_zero_error_bound(self):
        self.assertAlmostEqual(zero_error_upper(10),1-0.05**0.1)
        self.assertAlmostEqual(zero_error_upper(20),0.13910834066826516)

    def test_minimum_is_actually_minimum(self):
        for error in [0.01,0.03,0.05,0.10]:
            for claims in [1,2,8,16]:
                n=minimum_zero_error_n(error,simultaneous_claims=claims)
                self.assertLessEqual(zero_error_upper(n,simultaneous_claims=claims),error)
                self.assertGreater(zero_error_upper(n-1,simultaneous_claims=claims),error)
        self.assertEqual(minimum_zero_error_n(0.05),59)

    def test_more_independent_cases_improves_bound(self):
        values=[zero_error_upper(n) for n in [8,16,32,64,128]]
        self.assertEqual(values,sorted(values,reverse=True))

    def test_simultaneous_caution_is_stricter(self):
        self.assertGreater(zero_error_upper(64,simultaneous_claims=8),zero_error_upper(64))
        self.assertEqual(minimum_zero_error_n(0.05,simultaneous_claims=8),99)

    def test_bad_inputs_fail_closed(self):
        for n in [0,-1,1.5,True]:
            with self.assertRaises(ValueError):zero_error_upper(n)
        for conf in [0,1,-1,True,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):zero_error_upper(10,conf)
        for n in [0,-1,1.5,True]:
            with self.assertRaises(ValueError):zero_error_upper(10,simultaneous_claims=n)
        for error in [0,1,-1,True,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):minimum_zero_error_n(error)

    def test_reports_are_not_measurements(self):
        result=report()
        self.assertFalse(result['scientific_measurement'])
        self.assertFalse(result['new_governance_rule'])
        self.assertIn('Not a comprehension-delta',result['warning'])


if __name__=='__main__':unittest.main()
