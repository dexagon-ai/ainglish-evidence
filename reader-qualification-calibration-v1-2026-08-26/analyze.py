#!/usr/bin/env python3
"""Derive a development-only diagnostic from immutable v7 reader results."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "reader-qualification-v7-2026-08-25"
RESULT_FILES = ("phase-a-result.json", "reserve-b-result.json", "final-reserve-result.json")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def seal(value: dict) -> dict:
    value = dict(value)
    value["content_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    return value


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}: {actual} != {expected}")
    return value


def raw_receipt(path: Path) -> dict:
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def load_source() -> tuple[dict, list[dict], dict, dict]:
    plan = checked(SOURCE / "plan.json")
    selected = checked(SOURCE / "selected-result.json")
    audit = checked(SOURCE / "audit-report.json")
    if selected["plan_sha256"] != plan["content_sha256"]:
        raise SystemExit("REFUSING: selected result belongs to another plan")
    if selected["roster_ready"] or selected["fixed_roster"]:
        raise SystemExit("REFUSING: this diagnostic is bound to the terminal v7 no-roster result")
    if audit["status"] != "passed" or audit["selected"]["content_sha256"] != selected["content_sha256"]:
        raise SystemExit("REFUSING: v7 audit does not validate the terminal selected result")
    declared = {row["file"]: row["content_sha256"] for row in selected["source_results"]}
    if tuple(declared) != RESULT_FILES:
        raise SystemExit("REFUSING: unexpected v7 result sequence")
    results = []
    for name in RESULT_FILES:
        result = checked(SOURCE / name)
        if result["content_sha256"] != declared[name] or result["plan_sha256"] != plan["content_sha256"]:
            raise SystemExit(f"REFUSING: source binding drift in {name}")
        results.append(result)
    return plan, results, selected, audit


def entropy(counts: Counter, total: int) -> float:
    if not total:
        return 0.0
    return round(-sum((count / total) * math.log2(count / total) for count in counts.values()), 6)


def build_outputs() -> tuple[dict, dict]:
    plan, results, selected, audit = load_source()
    items = {row["id"]: row for row in plan["items"]}
    rows = [cell for result in results for cell in result["rows"]]
    readers = sorted({cell["reader"] for cell in rows})
    if len(readers) != 6 or len(rows) != len(readers) * len(items):
        raise SystemExit("REFUSING: v7 response matrix is not six complete 64-cell reader rows")
    identities = {(cell["reader"], cell["item_id"]) for cell in rows}
    if len(identities) != len(rows):
        raise SystemExit("REFUSING: duplicate response cell")
    by_item: dict[str, list[dict]] = defaultdict(list)
    by_reader: dict[str, dict[str, dict]] = defaultdict(dict)
    for cell in rows:
        if cell["item_id"] not in items or cell["expected"] != items[cell["item_id"]]["answer"]:
            raise SystemExit("REFUSING: item or answer binding drift")
        by_item[cell["item_id"]].append(cell)
        by_reader[cell["reader"]][cell["item_id"]] = cell

    review_path = ROOT / "semantic-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review["source_plan_sha256"] != plan["content_sha256"]:
        raise SystemExit("REFUSING: semantic review belongs to another plan")
    review_by_id = {row["item_id"]: row for row in review["items"]}
    if len(review_by_id) != len(review["items"]):
        raise SystemExit("REFUSING: duplicate semantic-review item")

    item_rows = []
    support_histogram = Counter()
    for item in plan["items"]:
        cells = by_item[item["id"]]
        parsed_counts = Counter(cell["parsed_answer"] for cell in cells if cell["parsed_answer"] is not None)
        unparsed = sum(cell["parsed_answer"] is None for cell in cells)
        key_support = parsed_counts[item["answer"]]
        support_histogram[key_support] += 1
        ranked = parsed_counts.most_common()
        majority = ranked[0][0] if ranked and (len(ranked) == 1 or ranked[0][1] > ranked[1][1]) else None
        flags = []
        if key_support == 0:
            flags.append("zero-key-support")
        if majority is not None and majority != item["answer"] and parsed_counts[majority] >= 4:
            flags.append("majority-against-key")
        if key_support <= 3:
            flags.append("low-key-support")
        if unparsed:
            flags.append("malformed-output-present")
        item_rows.append({
            "item_id": item["id"],
            "axis": item["axis"],
            "answer_key": item["answer"],
            "response_counts": {
                "yes": parsed_counts["yes"],
                "no": parsed_counts["no"],
                "cannot tell": parsed_counts["cannot tell"],
                "unparsed": unparsed,
            },
            "key_support": key_support,
            "parsed_responses": len(cells) - unparsed,
            "unique_majority_answer": majority,
            "response_entropy_bits": entropy(parsed_counts, len(cells) - unparsed),
            "flags": flags,
        })

    low_support = {row["item_id"] for row in item_rows if row["key_support"] <= 3}
    if set(review_by_id) != low_support:
        raise SystemExit("REFUSING: semantic review must cover exactly every item with at most 3/6 key support")
    for row in item_rows:
        if row["item_id"] in review_by_id:
            semantic = review_by_id[row["item_id"]]
            row["semantic_review"] = {
                key: semantic[key]
                for key in ("key_status", "failure_mode", "rationale", "development_action", "native_review")
            }

    axes = []
    for axis in plan["axes"]:
        axis_items = [row for row in item_rows if row["axis"] == axis]
        key_support = sum(row["key_support"] for row in axis_items)
        axes.append({
            "axis": axis,
            "items": len(axis_items),
            "response_cells": len(axis_items) * len(readers),
            "key_support_cells": key_support,
            "key_support_fraction": round(key_support / (len(axis_items) * len(readers)), 6),
            "low_support_items": sum(row["key_support"] <= 3 for row in axis_items),
            "zero_support_items": sum(row["key_support"] == 0 for row in axis_items),
        })

    agreement = []
    for left, right in itertools.combinations(readers, 2):
        paired = [
            (by_reader[left][item_id]["parsed_answer"], by_reader[right][item_id]["parsed_answer"])
            for item_id in items
        ]
        parsed = [(a, b) for a, b in paired if a is not None and b is not None]
        same = sum(a == b for a, b in parsed)
        agreement.append({
            "left": left,
            "right": right,
            "jointly_parsed_items": len(parsed),
            "same_answer_items": same,
            "agreement_fraction": round(same / len(parsed), 6),
        })

    native_sources = [row for row in review["items"] if row["native_review"]]
    native_packet = seal({
        "kind": "ainglish.panel.reader-qualification-native-review-packet.v1",
        "evidentiary_status": "optional development-only wording review; cannot alter v7",
        "blinding": "The v7 answer key, model identities, model responses, and consensus counts are omitted.",
        "instructions": "For each item, select the best ordinary-English answer, give high, medium, or low confidence, and optionally note a second reasonable reading. Do not research the source packet.",
        "response_schema": {
            "selected_answer": ["yes", "no", "cannot tell"],
            "confidence": ["high", "medium", "low"],
            "ambiguity_note": "optional string"
        },
        "items": [
            {
                "review_id": f"native-review-{index:02d}",
                "message": items[row["item_id"]]["message"],
                "question": items[row["item_id"]]["question"],
                "options": ["yes", "no", "cannot tell"],
            }
            for index, row in enumerate(native_sources, 1)
        ],
    })

    unanimous_wrong = [
        row["item_id"] for row in item_rows
        if row["key_support"] == 0 and row["parsed_responses"] == len(readers)
    ]
    majority_wrong = [row["item_id"] for row in item_rows if "majority-against-key" in row["flags"]]
    analysis = seal({
        "kind": "ainglish.panel.reader-qualification-calibration-analysis.v1",
        "evidentiary_status": "development-only instrument diagnosis; never proposal evidence",
        "immutability_statement": "This report neither changes nor reinterprets any v7 item, answer, score, qualification decision, or no-roster gate.",
        "methodology": {
            "model_calls": 0,
            "network_calls": 0,
            "consensus_role": "triage only; model agreement is not a truth oracle",
            "semantic_review_rule": review["review_rule"],
            "key_support_denominator": len(readers),
        },
        "source_receipts": {
            "directory": SOURCE.name,
            "plan": {"file": "plan.json", "content_sha256": plan["content_sha256"]},
            "results": selected["source_results"],
            "selected": {"file": "selected-result.json", "content_sha256": selected["content_sha256"]},
            "audit": {"file": "audit-report.json", "content_sha256": audit["content_sha256"]},
            "semantic_review": raw_receipt(review_path),
        },
        "population": {"readers": len(readers), "items": len(items), "response_cells": len(rows)},
        "summary": {
            "key_support_histogram": {str(key): support_histogram[key] for key in range(len(readers) + 1)},
            "perfect_support_items": support_histogram[len(readers)],
            "low_support_items_at_most_three": len(low_support),
            "zero_support_items": support_histogram[0],
            "unanimous_against_key_items": unanimous_wrong,
            "unique_majority_against_key_items": majority_wrong,
            "malformed_output_cells": sum(cell["parsed_answer"] is None for cell in rows),
            "reviewed_keys_defensible": sum(row["key_status"] == "defensible" for row in review["items"]),
            "reviewed_keys_wording_sensitive": sum(row["key_status"] == "defensible-but-wording-sensitive" for row in review["items"]),
            "native_review_items": len(native_sources),
        },
        "diagnosis": [
            "All three zero-support items are classic inference traps: affirming the consequent, denying the antecedent, and forced pronoun resolution.",
            "Several low-support items use polar meta-questions where no means not established, while cannot tell is a tempting answer about the embedded proposition.",
            "The next instrument should use one explicit premise-hypothesis classification contract: entailed, contradicted, or not determined.",
            "The normative only-rule item is defensible under its compliance phrase but is wording-sensitive enough for one optional native review.",
        ],
        "axes": axes,
        "items": item_rows,
        "reader_pair_agreement": agreement,
        "native_review_packet": {"file": "native-review-packet.json", "content_sha256": native_packet["content_sha256"]},
    })
    return analysis, native_packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    analysis, native = build_outputs()
    if args.write:
        for name, value in (("analysis.json", analysis), ("native-review-packet.json", native)):
            path = ROOT / name
            if path.exists():
                raise SystemExit(f"REFUSING: {name} already exists")
            path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "analysis_sha256": analysis["content_sha256"],
        "native_review_packet_sha256": native["content_sha256"],
        "summary": analysis["summary"],
    }, indent=2))


if __name__ == "__main__":
    main()
