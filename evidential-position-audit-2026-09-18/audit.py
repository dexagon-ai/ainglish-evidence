#!/usr/bin/env python3
"""Read-only design/raw-cell audit; no SDK, identity, mint or inference calls."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT.parent / "evidential-tags-fidelity-and-carrier-2026-08-25"
ORIGINAL_SHA = "f23e87f20cf2b0ca33872857c970425f2a8b6d10cf465507801794a352616946"
REPLICA_SHA = "9c1ffc51e4e57b06f6a25281b293c727f9cec9ff42a808db7e08e4ee2343e021"
COMPREHENSION_SHA = "f7d8152d9cf523f94bddf3b153415f3e6aede02050723319756f5c79220dceb8"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def bank_summary(rows):
    """Position diagnostics, including zero-count positions and each semantic form."""
    if not rows:
        raise ValueError("empty bank")
    counts = defaultdict(Counter)
    seen = set()
    arity = len(rows[0]["options"])
    if arity < 2:
        raise ValueError("at least two options required")
    for row in rows:
        if row["id"] in seen:
            raise ValueError("duplicate case id")
        seen.add(row["id"])
        options = row["options"]
        if len(options) != arity or len(set(options)) != arity:
            raise ValueError("inconsistent arity or duplicate options")
        if options.count(row["answer"]) != 1:
            raise ValueError("gold must occur exactly once")
        position = options.index(row["answer"])
        counts["overall"][position] += 1
        counts["form:" + row["form"]][position] += 1
    output = {}
    for name, values in sorted(counts.items()):
        vector = [values[i] for i in range(arity)]
        total = sum(vector)
        output[name] = {
            "n": total, "gold_position_counts": vector,
            "constant_first_correct": vector[0],
            "best_fixed_position_accuracy": max(vector) / total,
            "balanced_to_one": max(vector) - min(vector) <= 1,
        }
    return output


def require_position_balance(rows):
    """Necessary check for a future design; NOT semantic validation or launch permission."""
    summary = bank_summary(rows)
    failed = [name for name, row in summary.items() if not row["balanced_to_one"]]
    if failed:
        raise ValueError("answer-position imbalance: " + ", ".join(failed))
    return summary


def replay_original(cases, result):
    """Reproduce the frozen strip/uppercase/exact-code rule, including invalid outputs."""
    content = {k: v for k, v in result.items() if k != "content_sha256"}
    if digest(content) != result["content_sha256"]:
        raise ValueError("result content digest mismatch")
    by_id = {row["id"]: row for row in cases}
    counts = defaultdict(Counter)
    observed = defaultdict(set)
    for cell in result["rows"]:
        reader = cell["reader"]
        case = by_id[cell["case_id"]]
        if cell["case_id"] in observed[reader]:
            raise ValueError("duplicate reader/case cell")
        observed[reader].add(cell["case_id"])
        raw = cell["raw_output"]
        if hashlib.sha256(raw.encode()).hexdigest() != cell["raw_output_sha256"]:
            raise ValueError("raw output hash mismatch")
        mapping = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", case["options"]))
        code = raw.strip().upper()
        exact = len(code) == 1 and code in mapping
        parsed = mapping.get(code) if exact else None
        correct = parsed == case["answer"]
        if (exact, parsed, correct, case["answer"]) != (
            cell["exact_code"], cell["parsed"], cell["correct"], cell["expected"]
        ):
            raise ValueError("recorded scoring does not reproduce")
        counts[reader]["cells"] += 1
        counts[reader]["correct"] += int(correct)
        counts[reader]["format_invalid"] += int(not exact)
        counts[reader]["valid_wrong"] += int(exact and not correct)
    expected_readers = {row["model"] for row in result["per_member"]}
    if set(counts) != expected_readers:
        raise ValueError("reader roster mismatch")
    for reader in counts:
        if observed[reader] != set(by_id):
            raise ValueError("incomplete reader/case coverage")
        counts[reader]["accuracy"] = counts[reader]["correct"] / counts[reader]["cells"]
    for member in result["per_member"]:
        if member["value"] != counts[member["model"]]["accuracy"]:
            raise ValueError("member value mismatch")
    if result["value"] != min(row["accuracy"] for row in counts.values()):
        raise ValueError("least-favourable aggregate mismatch")
    return dict(sorted(counts.items()))


def pinned_bank(path, expected):
    rows = json.loads(path.read_text())
    if digest(rows) != expected:
        raise ValueError("bank canonical digest mismatch: " + str(path))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replica-bank", type=Path, required=True,
                        help="Byte-preserved download of https://paste.c-net.org/k8y98nh6a0dn")
    args = parser.parse_args()
    original = pinned_bank(ARCHIVE / "fidelity-cases.json", ORIGINAL_SHA)
    replica = pinned_bank(args.replica_bank, REPLICA_SHA)
    carrier = pinned_bank(ARCHIVE / "comprehension-items.json", COMPREHENSION_SHA)
    result = json.loads((ARCHIVE / "fidelity-result.json").read_text())
    output = {
        "kind": "ainglish.evidential-position-design-audit.v1",
        "is_new_measurement": False,
        "original": {"canonical_sha256": ORIGINAL_SHA, "positions": bank_summary(original)},
        "replica": {"canonical_sha256": REPLICA_SHA, "positions": bank_summary(replica)},
        "dormant_comprehension": {
            "canonical_sha256": COMPREHENSION_SHA, "positions": bank_summary(carrier),
            "scope": "120 scientific input rows only; no comprehension inference replay",
        },
        "original_raw_replay": replay_original(original, result),
        "replica_raw_replay": "not performed: published result URL returned HTTP 404 on 2026-09-18",
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
