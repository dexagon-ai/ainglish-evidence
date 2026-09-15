import math
import unittest
import planning as p


class PlanningTests(unittest.TestCase):
    def test_cdf_against_direct_small_binomial(self):
        for n in range(1, 31):
            for probability in (.01,.1,.3,.5,.8,.99):
                for k in range(n):
                    direct = sum(math.comb(n,j)*probability**j*(1-probability)**(n-j)
                                 for j in range(k+1))
                    self.assertAlmostEqual(p.binom_cdf(k,n,probability), direct, places=11)

    def test_nist_published_example(self):
        self.assertAlmostEqual(p.cp_lower(4,20,.05), .071354, places=5)
        self.assertAlmostEqual(p.cp_upper(4,20,.05), .401029, places=5)

    def test_zero_errors_closed_form(self):
        for n in (36,72,900,1024,1400):
            self.assertAlmostEqual(p.cp_lower(n,n), .025**(1/n), places=11)
            self.assertAlmostEqual(p.cp_upper(0,n), 1-.025**(1/n), places=11)

    def test_ceiling_not_automatically_a_failure_or_success(self):
        self.assertFalse(p.preservation_pass(36,36,36,36))
        self.assertTrue(p.preservation_pass(900,900,900,900))

    def test_equal_bad_accuracy_is_not_a_pass(self):
        self.assertFalse(p.preservation_pass(500,1000,500,1000))

    def test_mean_alone_does_not_prove_margin(self):
        self.assertFalse(p.preservation_pass(35,36,35,36))

    def test_invalid_sample_rejected(self):
        for k,n in ((0,0),(-1,20),(21,20)):
            with self.assertRaises(ValueError): p.cp_upper(k,n)

    def test_power_stays_in_probability_domain(self):
        result = p.conditional_power(900, .99, .99)
        self.assertLessEqual(result['single_reader_form_power_lower'], 1)
        self.assertGreaterEqual(result['single_reader_form_power_lower'], 0)

    def test_inversion_and_monotonicity(self):
        for n in (20,100,900):
            last = -1
            for k in sorted({0,1,n//2,n-1,n}):
                upper = p.cp_upper(k,n)
                self.assertGreaterEqual(upper,last)
                if k<n: self.assertAlmostEqual(p.binom_cdf(k,n,upper), .025, places=10)
                last = upper


if __name__ == '__main__': unittest.main()
