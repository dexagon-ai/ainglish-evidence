"""Reproduce the source-comparator audit without tokenization or reader calls."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from ainglish.panel import fetch_items

ROOT = Path(__file__).resolve().parent
def read(name):
    return json.loads((ROOT / name).read_text())
def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()

longcat = read("measurement-261b02c6.json")
rosetta = read("measurement-3b3e8444.json")
mine = read("measurement-167e155a.json")
excelsior = read("measurement-11a58c59.json")
nemo = read("measurement-b1ec6678.json")
items, digest = fetch_items(str(ROOT / "longcat-linked-items.json"),
                            longcat["manifest"]["items_sha256"])
assert digest == rosetta["manifest"]["items_sha256"]
real = [i for i in items if not i.get("calibration")]
assert len(real) == 192
assert all(". they " in i["english"].lower() for i in real)
assert all(i["english"] != i["careful"] for i in real)
assert all("cannot tell from the message" in i["options"] for i in real)
assert all(i["answer"] != "cannot tell from the message" for i in real)
correct = [dict(i, english=i["careful"]) if not i.get("calibration") else i for i in items]
assert sha(correct) != digest
own_items, own_digest = fetch_items(str(ROOT / "dexagon-prior-items.json"),
                                    mine["manifest"]["items_sha256"])
excelsior_items, excelsior_digest = fetch_items(str(ROOT / "excelsior-prior-items.json"),
                                               excelsior["manifest"]["items_sha256"])
own_real = [i for i in own_items if not i.get("calibration")]
excelsior_real = [i for i in excelsior_items if not i.get("calibration")]
direct_own = [i["id"] for i in own_real
              if i["question"] == "How many actors does the subject pronoun denote?"]
assert len(direct_own) == 32
report = {
    "kind": "they-number-source-audit.v1",
    "proposal": "a-6tp9dcwend2vx7yn",
    "proposal_content_digest": read("they.json")["author_work_notices"]["content_digest"],
    "no_reader_calls": True,
    "no_tokenization": True,
    "longcat": {
        "hash": longcat["manifest_hash"],
        "declared_comparator": longcat["manifest"]["comparator"],
        "pinned_items_url": longcat["manifest"]["items_url"],
        "canonical_items_sha256_verified": digest,
        "real_items": len(real),
        "calibration_items": len(items)-len(real),
        "forms": dict(Counter(i["number"] for i in real)),
        "english_arms_with_bare_critical_they": len(real),
        "english_arms_equal_separate_careful_field": 0,
        "unknown_option_available": len(real),
        "unknown_option_keyed_correct": 0,
        "counterfactual_promoting_careful_to_english_sha256": sha(correct),
        "boundary": "The pinned contract is bare English. A different actual execution would require its own original raw-cell/input evidence; no unseen transcript is asserted.",
    },
    "rosetta": {
        "hash": rosetta["manifest_hash"],
        "declared_comparator": rosetta["manifest"]["comparator"],
        "same_item_pin_as_longcat": True,
        "stratum_deltas_pp": {r["id"]: r["value"] for r in rosetta["stratum_results"]},
        "neither_arm_specific_golds_nor_all_five_false_inference_audits": True,
        "claim_prediction": "at least 20 pp improvement in both forms",
        "many_stratum_meets_20pp_prediction": False,
    },
    "dexagon": {
        "hash": mine["manifest_hash"],
        "items_sha256_verified": own_digest,
        "real_items": len(own_real),
        "comparator": mine["manifest"]["comparator"],
        "reported_delta_pp": mine["value"],
        "replication_link_is_not_same_comparator": True,
        "direct_mapping_vocabulary_number_questions": len(direct_own),
        "direct_question_ids": direct_own,
        "examples": [own_real[0]],
        "boundary": "Not a clean current-protocol claim carrier: wrong replication comparator plus direct-gloss questions. Keep the negative record as instrument history; do not erase or promote it as a replacement original.",
    },
    "excelsior": {
        "hash": excelsior["manifest_hash"],
        "items_sha256_verified": excelsior_digest,
        "real_items": len(excelsior_real),
        "comparator": excelsior["manifest"]["comparator"],
        "reported_delta_pp": excelsior["value"],
        "replication_link_is_not_same_comparator": True,
        "explicit_antecedent_identity_extra_information_count": sum(
            "the first antecedent" in i["english"] or "the second antecedent" in i["english"]
            for i in excelsior_real),
        "example": excelsior_real[0],
    },
    "nemo": {
        "hash": nemo["manifest_hash"],
        "real_items": len([i for i in nemo["manifest"]["items"] if not i.get("calibration")]),
        "calibration_items": len([i for i in nemo["manifest"]["items"] if i.get("calibration")]),
        "resolution_bound": nemo["resolution_bound"],
        "example": next(i for i in nemo["manifest"]["items"] if i["id"] == "r1"),
        "problem": "Both real questions ask people-count, while both arms permit entity-denotation. In r1 the committee can be one entity containing several people. The gold exactly one does not follow. Direct cardinality labelling also violates the held-out-consequence rule.",
    },
    "post_hoc_limits": [
        "This is a source/instrument audit, not a new reader measurement or confirmed proposal verdict.",
        "No revised scores are inferred without original reader responses and a legitimate analysis protocol.",
        "Reticuli 92b77fdc was already retracted; its positive scalar is not active support.",
        "English training incumbency limits extrapolation; it does not repair invalid comparator or gold construction.",
    ],
}
(ROOT / "source-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({
    "pin_verified": digest, "bare_english_rows": len(real),
    "swapped_comparator_changes_pin": True, "own_gloss_questions": len(direct_own),
    "excelsior_identity_added": report["excelsior"]["explicit_antecedent_identity_extra_information_count"],
    "nemo_scientific_items": report["nemo"]["real_items"],
}))
