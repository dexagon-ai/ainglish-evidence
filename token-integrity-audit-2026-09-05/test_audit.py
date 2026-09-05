import copy
import unittest
from unittest.mock import patch
from ainglish.client import manifest_commitment
import audit

class Client:
    def __init__(self, manifest, value=1, members=None):
        self.manifest = manifest
        self.row = {"manifest":manifest, "manifest_hash":manifest_commitment(manifest),
                    "attempt_id":"attempt-a", "value":value, "per_member":members}
    def measurement(self, _): return copy.deepcopy(self.row)
    def attempt(self, _): return {"proposal":"test", "backfilled":False}
    def attempt_manifest(self, _): return copy.deepcopy(self.manifest)

def counter(pairs, models):
    by = {m:{"per_pair":[len(a)-len(e) for e,a in pairs],
             "mean":sum(len(a)-len(e) for e,a in pairs)/len(pairs)} for m in models}
    winner = max(models, key=lambda m:by[m]["mean"])
    return {"by_tokenizer":by,"floor":by[winner]["mean"],"floor_tokenizer":winner}

class AuditTests(unittest.TestCase):
    def run_row(self, c, row=None):
        with patch.object(audit, "token_delta", counter):
            return audit.reproduce(c,c.row["manifest_hash"],row)
    def test_exact_and_wrong_member(self):
        c=Client({"models":["cl100k_base"],"test_set":[["a","ab"]]},1,[{"model":"cl100k_base","value":1}])
        self.assertEqual(self.run_row(c)["status"],"matches")
        c.row["per_member"][0]["value"]=2
        self.assertEqual(self.run_row(c)["status"],"mismatch")
    def test_rounding_is_not_large_mismatch(self):
        c=Client({"models":["cl100k_base"],"test_set":[["a","ab"],["a","a"],["a","a"]]},.333)
        self.assertEqual(self.run_row(c)["status"],"coarse_rounding_only")
        c.row["value"]=.3333
        self.assertEqual(self.run_row(c)["status"],"matches")
        c.row["value"]=.332
        self.assertEqual(self.run_row(c)["status"],"mismatch")
    def test_weights_not_item_mixture(self):
        c=Client({"models":["cl100k_base"],"test_set":[
            {"english":"a","ainglish":"ab","stratum":"a"},
            *[{"english":"ab","ainglish":"a","stratum":"b"}]*3],
            "settlement_strata":[{"id":"a","weight":3},{"id":"b","weight":1}]},.5)
        self.assertEqual(self.run_row(c)["status"],"matches")
        self.assertEqual(self.run_row(c)["exact_means"]["cl100k_base"],"1/2")
    def test_same_hash_is_not_same_submission(self):
        c=Client({"models":["cl100k_base"],"test_set":[["a","ab"]]},99)
        own={**c.row,"value":1,"attempt_id":"another","submitter":{"sub":"other"}}
        r=self.run_row(c,own)
        self.assertEqual(r["status"],"matches")
        self.assertEqual(r["attempt_id"],"another")
        self.assertEqual(r["submitter"],{"sub":"other"})
    def test_conflict_and_projection_are_not_adjudication(self):
        with self.assertRaises(ValueError):
            audit.pairs_from({"test_set":[["a","b"]],"pairs":[["a","c"]]})
        c=Client({"models":["cl100k_base"],"test_set":[["a","ab"]]})
        c.row["manifest_hash"]="0"*64
        self.assertEqual(self.run_row(c)["status"],"not_reproduced")
    def test_version_string_does_not_break_audit(self):
        c=Client({"models":["cl100k_base"],"test_set":[["a","ab"]],"environment":"old prose"})
        self.assertEqual(self.run_row(c)["status"],"matches")
    def test_unsupported_not_guessed(self):
        c=Client({"models":["cl100k_base@some-version"],"test_set":[["a","ab"]]})
        self.assertEqual(self.run_row(c)["status"],"not_reproduced")

if __name__ == "__main__": unittest.main()
