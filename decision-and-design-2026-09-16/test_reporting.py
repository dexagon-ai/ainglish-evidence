import math
import unittest

from summarize_oc import wilson


class ReportingTests(unittest.TestCase):
    def test_wilson_symmetry_and_boundaries(self):
        for n in (10, 1000):
            for k in (0, 1, n//2, n-1, n):
                lo, hi = wilson(k, n)
                rlo, rhi = wilson(n-k, n)
                self.assertTrue(0 <= lo <= hi <= 1)
                self.assertLessEqual(lo, k/n+1e-15)
                self.assertLessEqual(k/n, hi+1e-15)
                self.assertAlmostEqual(lo, 1-rhi)
                self.assertAlmostEqual(hi, 1-rlo)

    def test_zero_out_of_1000_is_not_zero_risk(self):
        lo, hi = wilson(0, 1000)
        self.assertTrue(math.isclose(lo, 0, abs_tol=1e-15))
        self.assertTrue(.003 < hi < .004)

    def test_invalid_count_rejected(self):
        for k, n in ((0, 0), (-1, 10), (11, 10)):
            with self.assertRaises(ValueError):
                wilson(k, n)


if __name__ == '__main__':
    unittest.main()
