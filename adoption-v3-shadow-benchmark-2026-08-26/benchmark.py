#!/usr/bin/env python3
"""Compare v2 and v3-shadow on the frozen corpus; this script performs no network or writes."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_detector(path):
    spec = importlib.util.spec_from_file_location("adoption_detector_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def label_v2(use, mention):
    if use:
        return "use"
    if mention:
        return "mention"
    return "none"


def label_v3(row):
    for label in ("use", "mention", "abstain"):
        if row[label]:
            return label
    return "none"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("detector", type=Path, help="path to the shadow branch tools/adoption_scan.py")
    args = parser.parse_args()
    detector = load_detector(args.detector.resolve())
    corpus = read_jsonl(ROOT / "corpus.jsonl")
    proposals = json.loads((ROOT / "proposals.json").read_text(encoding="utf-8"))
    fixture = json.loads((args.detector.resolve().parents[1] / "tests/fixtures/adoption-mention-vs-use-v3.json").read_text())

    fixture_pattern = detector.re.compile(fixture["pattern"], detector.re.I)
    fixture_correct = 0
    for case in fixture["cases"]:
        got = detector.classify_matches_v3(fixture_pattern, case["text"])
        fixture_correct += ({key: got[key] for key in ("use", "mention", "abstain")} == case["expected"])

    constructs, disagreements = [], []
    for proposal in proposals:
        if detector.skip_reason(proposal):
            continue
        pattern = detector.PATTERNS.get(proposal["slug"]) or detector.derived_pattern(proposal)
        if pattern is None:
            continue
        proposer = ((proposal.get("proposer") or {}).get("name") or "").lower()
        aggregate = {"v2": {"use": 0, "mention": 0}, "v3": {"use": 0, "mention": 0, "abstain": 0}}
        messages_scanned = 0
        for message in corpus:
            if proposer and message["author"].lower() == proposer:
                continue
            messages_scanned += 1
            v2_use, v2_mention = detector.classify_matches(pattern, message["text"])
            v3 = detector.classify_matches_v3(pattern, message["text"])
            aggregate["v2"]["use"] += v2_use
            aggregate["v2"]["mention"] += v2_mention
            for key in aggregate["v3"]:
                aggregate["v3"][key] += v3[key]
            before, after = label_v2(v2_use, v2_mention), label_v3(v3)
            if before != after or v3["abstain"]:
                disagreements.append({
                    "proposal_slug": proposal["slug"],
                    "ref": message["ref"],
                    "author": message["author"],
                    "created_at": message["created_at"],
                    "v2": {"label": before, "use": v2_use, "mention": v2_mention},
                    "v3": v3,
                    "text": message["text"],
                })
        constructs.append({
            "proposal_slug": proposal["slug"],
            "pattern": pattern.pattern,
            "messages_scanned": messages_scanned,
            **aggregate,
        })

    disagreements.sort(key=lambda row: (row["proposal_slug"], row["created_at"], row["ref"]))
    (ROOT / "disagreements.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in disagreements),
        encoding="utf-8",
    )
    report = {
        "kind": "ainglish.adoption-v3-shadow-benchmark.v1",
        "detector_sha256": hashlib.sha256(args.detector.read_bytes()).hexdigest(),
        "production_detector": detector.DETECTOR_VERSION,
        "shadow_detector": detector.SHADOW_DETECTOR_VERSION,
        "corpus_count": len(corpus),
        "fixture": {"correct": fixture_correct, "total": len(fixture["cases"])},
        "instrumented_constructs": len(constructs),
        "disagreement_rows": len(disagreements),
        "constructs": constructs,
    }
    (ROOT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "corpus_count", "fixture", "instrumented_constructs", "disagreement_rows"
    )}, indent=2))


if __name__ == "__main__":
    main()

