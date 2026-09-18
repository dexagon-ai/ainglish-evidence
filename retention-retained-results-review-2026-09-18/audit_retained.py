#!/usr/bin/env python3
"""Offline audit of an existing public journal, not a new measurement or replication."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

EXPECTED_ITEMS = "4adb16219ab03ecf04c0c633394966c15ab007e68d000533778b9bb23ad10428"
EXPECTED_MEASUREMENT = "9fc36a6792d1d69be1ac066d71164d09039c79f8759d7468974cbc67d8693b9e"
EXPECTED_JOURNAL = "9691ec154f6091a321e69ec9de147bdf981dc9358dba35b2749ea27fc7b3407d"

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()

def counts(rows):
    return {arm: {"correct": sum(c["correct"] for c in rows if c["arm"] == arm),
                  "total": sum(c["arm"] == arm for c in rows)}
            for arm in ("english", "ainglish")}

def delta(rows):
    n = counts(rows)
    if any(not x["total"] for x in n.values()):
        return None
    return 100 * (n["ainglish"]["correct"] / n["ainglish"]["total"]
                  - n["english"]["correct"] / n["english"]["total"])

def audit(root):
    bank = json.loads((root / "items.json").read_text())
    m = json.loads((root / "measurement.json").read_text())
    assert m["manifest_hash"] == EXPECTED_MEASUREMENT
    items = bank["items"]
    assert digest(items) == EXPECTED_ITEMS == m["manifest"]["items_sha256"]
    att = m["interval_provenance_attestation"]
    assert att["content_sha256"] == EXPECTED_JOURNAL
    assert digest({k: v for k, v in att.items() if k != "content_sha256"}) == EXPECTED_JOURNAL
    real = [i for i in items if not i.get("calibration")]
    controls = [i for i in items if i.get("calibration")]
    assert len(real) == 64 and len(controls) == 16
    by_id = {i["id"]: i for i in real}
    assert len(by_id) == 64
    assert att["items"] == [{"id": i["id"], "stratum": i["settlement_stratum"]}
                            for i in sorted(real, key=lambda i: i["id"])]
    cells = att["cells"]
    expected = {(i, r) for i in by_id for r in att["readers"]}
    assert len(cells) == len(expected) == 128
    assert {(c["item_id"], c["reader"]) for c in cells} == expected
    for c in cells:
        assert type(c["correct"]) is bool
        word = hashlib.sha256(f'{att["seed"]}|{c["reader"]}|{c["item_id"]}'.encode()).digest()[0]
        assert c["arm"] == ("ainglish" if word % 2 else "english")

    expected_answers = {
        "all-or-nothing": "none of the successful effects may remain authoritative",
        "keep-successes": "the successful effects remain authoritative",
    }
    core_clauses = {
        "all-or-nothing": "If any member fails, leave none of the other member effects committed or safe to rely on as the terminal result.",
        "keep-successes": "If one member fails, keep every other member effect that succeeded and report the failed member separately.",
    }
    gold_bank = defaultdict(Counter)
    domains = defaultdict(set)
    normalized_pairs = defaultdict(list)
    for item in real:
        form = item["settlement_stratum"]
        assert item["answer"] == expected_answers[form]
        assert item["options"].count(item["answer"]) == 1 and len(set(item["options"])) == 4
        assert item["english"].endswith(core_clauses[form])
        assert item["ainglish"].endswith(", " + form + ".")
        # The only answer-bearing instruction difference is the marker versus its core expansion.
        assert item["english"].split(". If", 1)[0] == item["ainglish"][:-(len(form) + 3)]
        assert item["question"].endswith("What may remain authoritative at the terminal outcome?")
        gold_bank[form][item["options"].index(item["answer"]) + 1] += 1
        stem = re.sub(r"^For batch \d+, ", "", item["ainglish"])
        domains[form].add(stem)
        key = tuple(re.sub(r"^For batch \d+, ", "For batch N, ", item[k])
                    for k in ("english", "ainglish", "question"))
        normalized_pairs[key].append(item["id"])
    assert all(dict(v) == {1: 8, 4: 8, 3: 8, 2: 8} for v in gold_bank.values())
    for item in controls:
        assert "all-or-nothing" not in item["ainglish"] + item["english"]
        assert "keep-successes" not in item["ainglish"] + item["english"]

    strata = {}
    gold_exposure = defaultdict(Counter)
    for form in expected_answers:
        part = [c for c in cells if by_id[c["item_id"]]["settlement_stratum"] == form]
        strata[form] = {"counts": counts(part), "delta_pp": delta(part), "by_reader": {}}
        for reader in att["readers"]:
            subset = [c for c in part if c["reader"] == reader]
            detail = counts(subset)
            assert all(x["total"] == 16 for x in detail.values())
            strata[form]["by_reader"][reader] = detail
        for c in part:
            item = by_id[c["item_id"]]
            gold_exposure["/".join((form, c["reader"], c["arm"]))][item["options"].index(item["answer"]) + 1] += 1

    # Recompute the published pooled interval directly from boolean journal cells.
    # These are not reconstructed raw answers and cannot audit their parsing.
    contract = m["manifest"]["settlement_strata"]
    total_weight = sum(row["weight"] for row in contract)
    by_item = {i: [c for c in cells if c["item_id"] == i] for i in by_id}
    estimates = []
    assert att["algorithm"]["draws"] == 2000
    for draw in range(2000):
        parts = []
        for row in contract:
            source = sorted(i for i in by_id if by_id[i]["settlement_stratum"] == row["id"])
            sampled = []
            for position in range(len(source)):
                preimage = "\0".join((att["kind"], str(att["seed"]), row["id"], str(draw), str(position)))
                index = int.from_bytes(hashlib.sha256(preimage.encode()).digest()[:8], "big") % len(source)
                sampled.extend(by_item[source[index]])
            value = delta(sampled)
            if value is None:
                break
            parts.append(row["weight"] / total_weight * value)
        if len(parts) == len(contract):
            estimates.append(sum(parts))
    estimates.sort()
    bounds = [estimates[25 * len(estimates) // 1000], estimates[975 * len(estimates) // 1000]]
    assert len(estimates) == att["algorithm"]["accepted_draws"] == 2000
    assert all(abs(a - b) < 0.000051 for a, b in zip(bounds, [m["value_lo"], m["value_hi"]]))
    assert abs(delta(cells) - m["value"]) < 0.00501
    failures = []
    for cell in cells:
        if cell["correct"]:
            continue
        item = by_id[cell["item_id"]]
        failures.append({**cell, "form": item["settlement_stratum"],
                         "gold_position": item["options"].index(item["answer"]) + 1,
                         "item": item, "observed_response": "not present in the public attestation"})
    assert len(failures) == 5 and all(c["arm"] == "ainglish" for c in failures)
    result = {
        "kind": "dexagon.retention-retained-journal-audit.v1",
        "scope": "Offline arithmetic and item audit, not a measurement or confirmation",
        "measurement_hash": EXPECTED_MEASUREMENT,
        "items_sha256": EXPECTED_ITEMS, "attestation_sha256": EXPECTED_JOURNAL,
        "items_bytes_sha256": hashlib.sha256((root / "items.json").read_bytes()).hexdigest(),
        "scientific_items": len(real), "calibration_items": len(controls),
        "public_journal_cells": len(cells), "counts": counts(cells),
        "delta_pp": delta(cells), "replayed_pooled_bounds": bounds,
        "accepted_bootstrap_draws": len(estimates), "strata": strata,
        "failures": failures, "gold_positions_in_bank": dict(gold_bank),
        "gold_positions_by_actual_exposure": dict(gold_exposure),
        "domain_action_sets_per_form": {k: len(v) for k, v in domains.items()},
        "distinct_pairs_ignoring_batch_number": len(normalized_pairs),
        "repeated_pairs_ignoring_batch_number": [v for v in normalized_pairs.values() if len(v) > 1],
        "raw_response_audit_complete": False,
        "reader_calls": 0, "new_attempts": 0, "submitted_measurements": 0,
    }
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: result[k] for k in ("counts", "delta_pp", "replayed_pooled_bounds",
                                           "distinct_pairs_ignoring_batch_number", "raw_response_audit_complete")}))
