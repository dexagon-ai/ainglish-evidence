import unittest
from collections import Counter
from fractions import Fraction
from build_bank import FORMS, admissible, digest, generate, probe_scores
from prospective_power import ni_reference_power, zero_error_upper, worlds_for_reference_power

class DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = generate()

    def test_exact_declared_shape(self):
        self.assertEqual(len(self.items), 144)
        cells = Counter((i["settlement_stratum"], i["domain"]) for i in self.items)
        self.assertEqual(len(cells), 12)
        self.assertEqual(set(cells.values()), {12})

    def test_unique_complete_worlds_and_surfaces(self):
        for field in ("id", "english", "ainglish"):
            self.assertEqual(len({i[field] for i in self.items}), 144)
        for i in self.items:
            w = i["semantic_world"]
            self.assertEqual(len(w["members"]), len(set(w["members"])))
            self.assertNotIn(w["outsider"], w["members"])
            self.assertTrue(2 <= w["n"] <= 8)

    def test_gold_policy_sets_from_probability_distributions(self):
        for i in self.items:
            w, p = i["semantic_world"], i["probe_contract"]
            allowed = []
            for policy in p["policies"]:
                self.assertEqual(sum(Fraction(v) for v in policy["distribution"].values()), 1)
                if admissible(w, policy):
                    allowed.append(policy["label"])
            self.assertEqual(sorted(allowed), p["policy_gold"])
            permitted_kinds = {r["kind"] for r in p["policies"] if r["label"] in allowed}
            self.assertEqual(permitted_kinds, {"equal-probability"} if w["form"] == "draw-uniform"
                             else {"constant-first", "criterion-based", "unequal-weight", "equal-probability"})

    def test_mutation_changes_admissibility(self):
        for i in self.items[:2]:
            w = i["semantic_world"]
            fake = {"distribution": {w["outsider"]: "1"}}
            self.assertFalse(admissible(w, fake))
            with self.assertRaises(ValueError):
                admissible(w, {"distribution": {w["members"][0]: "2"}})

    def test_no_extra_guarantees(self):
        for i in self.items:
            p = i["probe_contract"]
            keys = {r["key"] for r in p["guarantees"] if r["label"] in p["guarantee_gold"]}
            self.assertEqual(keys, {"one-eligible", "equal-odds"} if i["settlement_stratum"] == "draw-uniform" else {"one-eligible"})

    def test_two_probes_are_independently_recoverable(self):
        for i in self.items:
            scores = [probe_scores(i, option) for option in i["options"]]
            self.assertEqual({(s["implementation"], s["guarantees"]) for s in scores},
                             {(True,True),(True,False),(False,True),(False,False)})
            self.assertEqual(sum(s["joint"] for s in scores), 1)
            self.assertTrue(probe_scores(i, i["answer"])["joint"])
            self.assertFalse(probe_scores(i, "INVALID-RESPONSE")["joint"])

    def test_correct_option_positions_balanced_within_form(self):
        for form in FORMS:
            counts = Counter(i["options"].index(i["answer"]) for i in self.items if i["settlement_stratum"] == form)
            self.assertEqual(counts, {0:18,1:18,2:18,3:18})

    def test_all_implementation_and_guarantee_contrasts(self):
        for form in FORMS:
            subset = [i for i in self.items if i["settlement_stratum"] == form]
            self.assertEqual(len({i["probe_contract"]["policy_contrast"] for i in subset}), 5)
            self.assertEqual(Counter(i["probe_contract"]["guarantee_contrast"] for i in subset),
                             {"one-eligible":18,"equal-odds":18,"crypto-unpredictable":18,"cross-draw-independent":18})

    def test_guarantee_contrast_does_not_reveal_answer_position(self):
        for form in FORMS:
            for key in ("one-eligible", "equal-odds", "crypto-unpredictable", "cross-draw-independent"):
                positions = {i["options"].index(i["answer"]) for i in self.items
                             if i["settlement_stratum"] == form and i["probe_contract"]["guarantee_contrast"] == key}
                self.assertGreaterEqual(len(positions), 3)

    def test_draft_expansion_is_nested_not_independent_replication(self):
        expanded = generate(660)
        self.assertEqual(self.items, expanded[:144])
        self.assertEqual(len(expanded), 660)
        self.assertEqual(digest(self.items), digest(generate()))
        with self.assertRaises(ValueError):
            generate(145)

    def test_power_examples_and_limits(self):
        self.assertLess(ni_reference_power(72,.95), .4)
        self.assertGreater(ni_reference_power(330,.95), .9)
        self.assertAlmostEqual(zero_error_upper(59), 1-.05**(1/59))
        self.assertGreater(zero_error_upper(18), .1)
        self.assertEqual(worlds_for_reference_power(.95), 660)

if __name__ == "__main__":
    unittest.main()
