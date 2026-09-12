import unittest
import numpy as np
from preservation_simulation import PLAN, probabilities, generate, lower_bounds, rate

class SimulationTests(unittest.TestCase):
    def test_known_mean_is_delta_without_clipping(self):
        for scenario in PLAN['scenarios']:
            for delta in PLAN['deltas']:
                effects = [probabilities(scenario,delta,r,i) for r in [-1,1] for i in [-1,1]]
                self.assertAlmostEqual(delta, sum(ai-en for en,ai in effects)/4)

    def test_reproducible_generation(self):
        for scenario in PLAN['scenarios']:
            a = generate(np.random.default_rng(12),scenario,-.02,3,10)
            b = generate(np.random.default_rng(12),scenario,-.02,3,10)
            np.testing.assert_array_equal(a,b)
            self.assertTrue(set(np.unique(a)) <= {-1,0,1})

    def test_degenerate_bootstraps_are_visible_not_equivalence(self):
        self.assertEqual(dict.fromkeys(PLAN['methods'],0.0),
                         lower_bounds(np.zeros((2,16)),np.random.default_rng(1),99))

    def test_mc_interval_does_not_claim_zero_uncertainty(self):
        self.assertGreater(rate(0,400)['mc_wilson95'][1],0)
        self.assertLess(rate(400,400)['mc_wilson95'][0],1)

if __name__ == '__main__': unittest.main()
