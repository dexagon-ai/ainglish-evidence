"""Excluded design-review witnesses, not a target study or measurement.

No model, tokenizer, credential, network or Ainglish write is used. The rejected
generator is imported only for its reviewed world semantics and English wording.
Its response menu is NOT reused as the menu of a single-form item.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "build_bank.py"
spec = importlib.util.spec_from_file_location("retained_draft", SOURCE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def display_without_request(item):
    # These are all intended reader-visible fields, excluding the treatment.
    return {"context": item["english"].split("\nRequest:")[0],
            "question": item["question"], "options": item["options"]}


def blind_upper_bound(items, view):
    """Best deterministic accuracy with access ONLY to view(item), on this bank.

    Gold is used to score indistinguishability classes, not supplied to a reader.
    This is a structural bound, not a model prediction or a population estimate.
    """
    groups = defaultdict(Counter)
    for item in items:
        groups[canonical(view(item))][item["answer"]] += 1
    return {"correct_at_most": sum(max(v.values()) for v in groups.values()),
            "total": len(items), "distinct_views": len(groups),
            "ambiguous_views": sum(len(v) > 1 for v in groups.values())}


def old_shortcut(options):
    counts = [(len(re.findall(r"\bP\d+\b", s)), len(re.findall(r"\bG\d+\b", s)))
              for s in options]
    want = (4, 1) if max(p for p, g in counts) >= 3 else (1, 2)
    hits = [s for s, count in zip(options, counts) if count == want]
    return hits[0] if len(hits) == 1 else None


def make_pair(index):
    domain_index, local_index = index % 6, index // 6
    ref = f"review-set-{index + 301}@r2"
    neutral_id = f"excluded-world-{index + 1:02d}"
    worlds = []
    # Both forms get EXACTLY the same world, labels, question and reference.
    original = base.make_world(index, "choose-any", domain_index, local_index)
    original_ref = original["set_ref"]
    for form in base.FORMS:
        w = deepcopy(original)
        w["id"], w["form"], w["set_ref"] = neutral_id, form, ref
        w["ainglish"] = w["ainglish"].replace(original_ref, ref).replace(
            "\nRequest: choose-any(", f"\nRequest: {form}(")
        common = w["ainglish"].split("\nRequest:")[0]
        # Use the exact retained per-form expansion, with this shared N/ref.
        if form == "choose-any":
            expansion = original["english"].split("\nRequest: ", 1)[1].replace(original_ref, ref)
        else:
            draft = base.make_world(index, form, domain_index, local_index)
            expansion = draft["english"].split("\nRequest: ", 1)[1]
            expansion = expansion.replace(draft["set_ref"], ref).replace(
                f"exactly 1/{draft['n']} ", f"exactly 1/{w['n']} ")
        w["english"] = common + "\nRequest: " + expansion
        worlds.append(w)
    originals = [base.make_item(w, index * 2 + i) for i, w in enumerate(worlds)]
    assert originals[0]["question"] == originals[1]["question"]
    # Union BOTH counterfactual menus BEFORE assigning either gold answer.
    options = list(dict.fromkeys(s for item in originals for s in item["options"]))
    assert len(options) == 8
    random.Random(f"neutral-review-deck:{index}").shuffle(options)
    records = {s: {k: v for k, v in record.items() if k in ("policies", "guarantees")}
               for item in originals for s, record in item["probe_contract"]["option_records"].items()}
    pair = []
    for i, item in enumerate(originals):
        item["id"] = f"excluded-review-{index * 2 + i + 1:03d}"
        item["counterfactual_pair"] = neutral_id
        item["status"] = "EXCLUDED_DESIGN_WITNESS_DO_NOT_RUN"
        item["options"] = options.copy()
        item["probe_contract"]["kind"] = "counterfactual-shared-eight-record-review-v1"
        item["probe_contract"]["option_records"] = deepcopy(records)
        pair.append(item)
    return pair


def audit(items):
    assert len(items) == 24
    assert len({x["id"] for x in items}) == 24
    opportunities = Counter()
    for index in range(0, len(items), 2):
        left, right = items[index:index + 2]
        assert display_without_request(left) == display_without_request(right)
        assert left["answer"] != right["answer"]
        assert set(left["options"]) == set(right["options"])
        for item in (left, right):
            common = display_without_request(item)["context"]
            assert common == item["ainglish"].split("\nRequest:")[0]
            assert not any(form in common for form in base.FORMS)
            assert item["answer"] in item["options"] and len(set(item["options"])) == 8
            world = item["semantic_world"]
            gold = sorted(p["label"] for p in item["probe_contract"]["policies"]
                          if base.admissible(world, p))
            assert gold == item["probe_contract"]["policy_gold"]
            true_keys = {"one-eligible"} | ({"equal-odds"} if world["form"] == "draw-uniform" else set())
            guarantee_gold = sorted(g["label"] for g in item["probe_contract"]["guarantees"]
                                    if g["key"] in true_keys)
            assert guarantee_gold == item["probe_contract"]["guarantee_gold"]
            correct = [s for s, r in item["probe_contract"]["option_records"].items()
                       if r["policies"] == gold and r["guarantees"] == guarantee_gold]
            assert correct == [item["answer"]]
            for field, metadata, key in (("policies", "policies", "kind"),
                                         ("guarantees", "guarantees", "key")):
                for entry in item["probe_contract"][metadata]:
                    # Both inclusion AND exclusion must be offered for an opportunity.
                    values = {entry["label"] in r[field]
                              for r in item["probe_contract"]["option_records"].values()}
                    if values == {True, False}:
                        opportunities[f"{world['form']}/{entry[key]}"] += 1
    option_bound = blind_upper_bound(items, lambda x: x["options"])
    context_bound = blind_upper_bound(items, display_without_request)
    assert option_bound["correct_at_most"] == context_bound["correct_at_most"] == 12
    # A sensitivity check must detect reintroduced form leakage, not just pass good data.
    contaminated = deepcopy(items)
    for item in contaminated:
        item["english"] = item["english"].replace("\nRequest:",
            " " + item["settlement_stratum"] + "\nRequest:", 1)
    assert blind_upper_bound(contaminated, display_without_request)["correct_at_most"] == 24
    shortcut = Counter()
    for item in items:
        predicted = old_shortcut(item["options"])
        assert predicted == old_shortcut(list(reversed(item["options"])))
        shortcut[item["settlement_stratum"]] += int(predicted == item["answer"])
    return {"status": "DESIGN_AUDIT_ONLY_NOT_A_LANGUAGE_MEASUREMENT", "items_sha256": digest(items),
            "items": 24, "distinct_worlds": 12, "forms": {"choose-any": 12, "draw-uniform": 12},
            "domains": 6, "answer_records_per_item": 8,
            "options_only_upper_bound": option_bound, "request_removed_upper_bound": context_bound,
            "old_shortcut_correct_by_form": dict(shortcut),
            "reintroduced_context_leak_detected": True,
            "offered_membership_contrast_denominators": dict(sorted(opportunities.items())),
            "reader_calls": 0, "tokenizer_calls": 0,
            "limits": ["Known shortcut repaired on excluded paired witnesses only; other defects remain possible.",
                       "The 50% bound is for the balanced witness pairs, not chance 1/8 or a target-population claim.",
                       "No runtime payload, final sample, interval method or comparator approval is certified."]}


if __name__ == "__main__":
    items = [item for index in range(12) for item in make_pair(index)]
    report = audit(items)
    (ROOT / "excluded-witnesses.json").write_text(json.dumps(
        {"status": "EXCLUDED_DESIGN_WITNESS_DO_NOT_RUN", "items_sha256": digest(items), "items": items},
        indent=2, ensure_ascii=False) + "\n")
    (ROOT / "STRUCTURAL-AUDIT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
