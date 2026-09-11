import unittest
import numpy as np
from settlement_simulation import draw,compare


class SimulationTests(unittest.TestCase):
    def test_known_positive_difference_not_erased_by_aggregate(self):
        a=np.array([[5.,5.] for _ in range(10)]);b=np.array([[15.,-5.] for _ in range(10)])
        x=compare(a,b,np.zeros(2),np.zeros(2),128)
        self.assertEqual(1,x['numeric_current_aggregate_only']['rate'])
        self.assertEqual(0,x['numeric_current_all_strata']['rate'])
        self.assertEqual(0,x['oracle_equivalence_within_5pp_all_strata']['rate'])

    def test_same_estimate_is_not_equivalence_with_unbounded_uncertainty(self):
        a=np.zeros((10,1));x=compare(a,a,np.array([100.]),np.array([100.]),16)
        self.assertEqual(1,x['oracle_difference_ci_contains_zero_all_strata']['rate'])
        self.assertEqual(0,x['oracle_equivalence_within_5pp_all_strata']['rate'])

    def test_fourfold_dependence_increases_variance_fourfold(self):
        _,one=draw(np.random.default_rng(1),100,128,1,[5])
        _,four=draw(np.random.default_rng(1),100,128,4,[5])
        np.testing.assert_allclose(four,4*one)

    def test_repeatability_and_mean(self):
        a,_=draw(np.random.default_rng(23),20000,128,1,[5])
        b,_=draw(np.random.default_rng(23),20000,128,1,[5])
        np.testing.assert_array_equal(a,b)
        self.assertLess(abs(a.mean()-5),.2)


if __name__=='__main__':unittest.main()
