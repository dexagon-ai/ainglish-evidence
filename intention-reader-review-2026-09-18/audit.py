#!/usr/bin/env python3
"""Offline audit of retained public evidence; never runs inference or submits a result."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


MEASUREMENT = "cd045604bc95ddc33befcdeb1185ea4f73fb2f5af192767b735fb6824254950c"
ITEMS = "caf368bb529fbfee151e584a7f65dcf22c5b36226af34318562bc4016be9352a"
JOURNAL = "aa3bc439b935a04352d096ec52214980ecdc9e5536c78201ea1ecec7a7d9ab7a"
SCREEN = "c9362d0347f91f9a87c7eb80b42a6fc74d8fca89eb4802d63827193e25818c91"
ARMS = ("english", "ainglish")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def counts(rows):
    return {arm: {"correct": sum(row["correct"] for row in rows if row["arm"] == arm),
                  "total": sum(row["arm"] == arm for row in rows)} for arm in ARMS}


def delta(rows):
    n = counts(rows)
    if any(not x["total"] for x in n.values()):
        return None
    return 100 * (n["ainglish"]["correct"] / n["ainglish"]["total"]
                  - n["english"]["correct"] / n["english"]["total"])


def audit(root):
    bank = json.loads((root / "items.json").read_text())
    measurement = json.loads((root / "measurement.json").read_text())
    manifest = measurement["manifest"]
    att = measurement["interval_provenance_attestation"]
    assert measurement["manifest_hash"] == MEASUREMENT
    assert digest(bank["items"]) == ITEMS == manifest["items_sha256"] == bank["sha256"]
    assert digest({k: v for k, v in att.items() if k != "content_sha256"}) == JOURNAL
    assert att["content_sha256"] == JOURNAL
    # The qualification-screen digest binds a wrapper, not the controls array alone.
    screen = {"kind": "ainglish.reader-qualification-screen.v1",
              "controls": bank["qualification_controls"],
              "ordering": "control order; detectable then other; one call per cell; no retry"}
    assert digest(screen) == SCREEN
    assert all(q["screen_sha256"] == SCREEN for q in manifest["reader_qualifications"])
    assert len(bank["qualification_controls"]) == 24

    real = [i for i in bank["items"] if not i.get("calibration")]
    controls = [i for i in bank["items"] if i.get("calibration")]
    assert len(real) == 96 and len(controls) == 12
    by_id = {i["id"]: i for i in real}
    assert len(by_id) == 96
    expected_index = [{"id": i["id"], "stratum": i["settlement_stratum"]}
                      for i in sorted(real, key=lambda i: i["id"])]
    assert att["items"] == expected_index
    assert digest(expected_index) == manifest["interval_estimator"]["items_index_sha256"]
    assert att["seed"] == manifest["seed"]
    assert len(att["readers"]) == len(set(att["readers"])) == 2
    cells = att["cells"]
    expected = {(i, r) for i in by_id for r in att["readers"]}
    assert len(cells) == len(expected) == 192
    assert {(c["item_id"], c["reader"]) for c in cells} == expected
    by_item = defaultdict(list)
    for c in cells:
        assert type(c["correct"]) is bool
        first = hashlib.sha256(f'{att["seed"]}|{c["reader"]}|{c["item_id"]}'.encode()).digest()[0]
        assert c["arm"] == ("ainglish" if first % 2 else "english")
        by_item[c["item_id"]].append(c)
    assert all({c["arm"] for c in row} == set(ARMS) for row in by_item.values())

    expected_strata = {"on-purpose-plan-match": 48, "by-accident-unforeseen-slip": 24,
                       "by-accident-accepted-risk": 24}
    assert Counter(i["settlement_stratum"] for i in real) == expected_strata
    assert Counter(i["anchor_class"] for i in real) == {
        "plan-a": 24, "plan-b": 24, "unforeseen": 24, "accepted-risk": 24}
    assert Counter(i["frame"] for i in real) == {
        "first-active": 24, "first-passive": 24, "third-active": 24, "third-passive": 24}
    assert len({i["domain"] for i in real}) == 6
    gold = defaultdict(Counter)
    report_cores = set()
    for i in real:
        positive = i["settlement_stratum"] == "on-purpose-plan-match"
        assert i["answer"] == ("yes" if positive else "no")
        assert i["oracle"]["intended"] is positive
        assert set(i["options"]) == {"yes", "no", "cannot-tell"} and len(i["options"]) == 3
        assert i["question"] == "Was this outcome something the doer meant to bring about?"
        assert i["form"] == ("on-purpose" if positive else "by-accident")
        assert i["anchor_class"] in (("plan-a", "plan-b") if positive else ("unforeseen", "accepted-risk"))
        english_suffix = " deliberately." if positive else " by mistake, without intending that outcome."
        marked_suffix = " " + i["form"] + "."
        assert i["english"].endswith(english_suffix) and i["ainglish"].endswith(marked_suffix)
        # Frozen arm texts differ only in the declared marker/English expansion.
        core = i["english"][:-len(english_suffix)]
        assert core == i["ainglish"][:-len(marked_suffix)] == i["bare"][:-1]
        report_cores.add(core.split(" Report: ", 1)[1])
        if i["anchor_class"] == "accepted-risk":
            assert "as an unwanted possible side effect, accepted that risk, and did not seek that result." in core
        gold[i["settlement_stratum"]][i["options"].index(i["answer"]) + 1] += 1
    assert len(report_cores) == 96

    strata = {}
    for name, total in expected_strata.items():
        rows = [c for c in cells if by_id[c["item_id"]]["settlement_stratum"] == name]
        strata[name] = {"counts": counts(rows), "delta_pp": delta(rows), "by_reader": {}}
        for reader in att["readers"]:
            part = [c for c in rows if c["reader"] == reader]
            strata[name]["by_reader"][reader] = counts(part)
            assert all(x["total"] == total // 2 for x in counts(part).values())

    def grouped(fields):
        groups = defaultdict(list)
        for cell in cells:
            item = by_id[cell["item_id"]]
            key = [cell["reader"]] + [item[f] for f in fields]
            groups["/".join(key)].append(cell)
        return {k: counts(v) for k, v in sorted(groups.items())}

    # Replay the exact published interval from the boolean journal, with no rescoring.
    estimates = []
    contract = manifest["settlement_strata"]
    assert [(s["id"], s["weight"]) for s in contract] == list(zip(expected_strata, (2, 1, 1)))
    assert att["algorithm"]["name"] == "sha256-counter-modulo-v1"
    assert att["algorithm"]["draws"] == 2000
    for draw in range(2000):
        parts = []
        for stratum in contract:
            source = sorted(i for i in by_id if by_id[i]["settlement_stratum"] == stratum["id"])
            sample = []
            for position in range(len(source)):
                preimage = "\0".join((att["kind"], str(att["seed"]), stratum["id"], str(draw), str(position)))
                ix = int.from_bytes(hashlib.sha256(preimage.encode()).digest()[:8], "big") % len(source)
                sample.extend(by_item[source[ix]])
            effect = delta(sample)
            if effect is None:
                break
            parts.append(stratum["weight"] / 4 * effect)
        if len(parts) == len(contract):
            estimates.append(sum(parts))
    estimates.sort()
    bounds = [estimates[25 * len(estimates) // 1000], estimates[975 * len(estimates) // 1000]]
    assert len(estimates) == att["algorithm"]["accepted_draws"] == 2000
    assert all(abs(x - y) < 0.000051 for x, y in zip(bounds, [measurement["value_lo"], measurement["value_hi"]]))
    assert abs(delta(cells) - measurement["value"]) < 0.00501
    incorrect = [c for c in cells if not c["correct"]]
    assert len(incorrect) == 42
    assert all(c["reader"].startswith("gemma3") and
               by_id[c["item_id"]]["settlement_stratum"] == "on-purpose-plan-match" for c in incorrect)
    option_exposure = defaultdict(Counter)
    for c in cells:
        i = by_id[c["item_id"]]
        key = "/".join((c["reader"], i["settlement_stratum"], c["arm"]))
        option_exposure[key][i["options"].index(i["answer"]) + 1] += 1

    return {
        "kind": "dexagon.intention-retained-journal-audit.v1",
        "scope": "Offline audit; not a new measurement, replication, confirmation, or regrading",
        "measurement_hash": MEASUREMENT, "items_sha256": ITEMS,
        "items_bytes_sha256": hashlib.sha256((root / "items.json").read_bytes()).hexdigest(),
        "attestation_sha256": JOURNAL, "qualification_screen_sha256": SCREEN,
        "scientific_items": len(real), "calibration_items": len(controls),
        "public_journal_cells": len(cells), "distinct_report_cores": len(report_cores),
        "counts": counts(cells), "delta_pp": delta(cells),
        "replayed_pooled_bounds": bounds, "accepted_bootstrap_draws": len(estimates),
        "strata": strata,
        "reader_anchor_arm_counts": grouped(["anchor_class"]),
        "reader_stratum_frame_arm_counts": grouped(["settlement_stratum", "frame"]),
        "reader_anchor_frame_arm_counts": grouped(["anchor_class", "frame"]),
        "gold_positions_in_bank": dict(gold), "gold_positions_by_exposure": dict(option_exposure),
        "incorrect_cells": incorrect,
        "raw_response_audit_complete": False,
        "reader_calls": 0, "new_attempts": 0, "submitted_measurements": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).parent)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: result[k] for k in ("counts", "delta_pp", "replayed_pooled_bounds",
                                           "qualification_screen_sha256", "raw_response_audit_complete")}))
