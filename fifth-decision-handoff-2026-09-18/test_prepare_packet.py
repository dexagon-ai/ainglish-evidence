import copy
import json
from pathlib import Path
import unittest

from prepare_packet import APPROX, CONSTRUCTION, SAME, candidate, passing_tally, public_view, repair_mapping


ROOT = Path(__file__).resolve().parent


class PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "public-snapshot.json").read_text())
        cls.source = cls.snapshot["proposals"][SAME]
        cls.edits = json.loads((ROOT / "same-identity-proposed-edits.json").read_text())

    def test_three_two_not_passing(self):
        self.assertFalse(passing_tally(3, 2))

    def test_four_two_exact_two_thirds(self):
        self.assertTrue(passing_tally(4, 2))
        self.assertFalse(passing_tally(4, 3))

    def test_quorum_is_separate(self):
        self.assertFalse(passing_tally(4, 0))
        self.assertTrue(passing_tally(5, 0))

    def test_bad_weights_fail_closed(self):
        for pair in ((-1, 0), (True, 2), (3.0, 2)):
            with self.assertRaises(ValueError):
                passing_tally(*pair)

    def test_mapping_repair_reproduces(self):
        self.assertEqual(candidate(self.source), self.edits)

    def test_source_is_not_modified(self):
        before = copy.deepcopy(self.source)
        repair_mapping(self.source["english_mapping"])
        self.assertEqual(self.source, before)

    def test_changed_source_does_not_silently_apply(self):
        with self.assertRaises(ValueError):
            repair_mapping(self.source["english_mapping"].replace("no check and no moment", "no check or moment"))

    def test_duplicate_source_phrase_fails(self):
        with self.assertRaises(ValueError):
            repair_mapping(self.source["english_mapping"] * 2)

    def test_strengthened_scope_and_either_missing(self):
        mapping = self.edits["proposed_fields"]["english_mapping"]
        self.assertIn("a distinct X matching", mapping)
        self.assertIn("no link that propagates changes between them", mapping)
        self.assertIn("missing either the named check or the named moment", mapping)
        self.assertIn("whether their contents are equal is not claimed", mapping)

    def test_not_a_fileable_payload(self):
        self.assertFalse(self.edits["ready_to_file"])
        self.assertEqual(self.edits["unfinished_fields"], ["predicted_measurement", "evidence_contract"])
        self.assertNotIn("evidence_contract", self.edits["proposed_fields"])
        self.assertNotIn("predicted_measurement", self.edits["proposed_fields"])

    def test_no_name_claim_manufactured_by_staleness(self):
        mapping = self.edits["proposed_fields"]["english_mapping"]
        self.assertNotIn("same-name plus testimony", mapping)
        self.assertNotIn("decays toward same-name", mapping)
        self.assertIn("Neither an incomplete check/time claim nor an old check establishes matching identifiers.", mapping)

    def test_new_review_point_not_misrepresented_as_accepted(self):
        point = self.edits["new_review_point_not_previously_accepted"]
        self.assertIn("alpha.json and beta.json", point["witness"])
        self.assertTrue(any("not part of the earlier author acceptance" in stop
                            for stop in self.edits["stop_conditions"]))

    def test_caller_metadata_is_not_published(self):
        source = copy.deepcopy(self.source)
        source["author_work_notices"] = {"active": source.pop("author_notice")}
        source["private_dm"] = "must not be published"
        source["ratification"]["my_vote"] = {"private": True}
        public = public_view(source)
        self.assertNotIn("private_dm", public)
        self.assertNotIn("my_vote", public["ratification"])

    def test_snapshot_is_named_and_non_experimental(self):
        self.assertEqual(set(self.snapshot["proposals"]), {SAME, APPROX, CONSTRUCTION})
        self.assertEqual(len(self.snapshot["ballots"]), 3)
        self.assertIn("not a measurement", self.snapshot["scope"])


if __name__ == "__main__":
    unittest.main()
