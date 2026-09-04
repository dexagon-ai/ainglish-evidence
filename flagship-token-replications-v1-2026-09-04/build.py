#!/usr/bin/env python3
"""Freeze fresh token carriers for two live-routed flagship candidates."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODELS = ["cl100k_base", "o200k_base", "p50k_base"]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def on_purpose_pairs() -> list[dict]:
    return [
        {"id": "on-purpose-01", "english": "I rotated the signing key deliberately.", "ainglish": "I rotated the signing key on-purpose."},
        {"id": "by-accident-01", "english": "I invalidated the cache by accident; I did not foresee that outcome.", "ainglish": "I invalidated the cache by-accident."},
        {"id": "on-purpose-02", "english": "I paused the import deliberately.", "ainglish": "I paused the import on-purpose."},
        {"id": "by-accident-02", "english": "I removed the label by accident; I did not foresee that outcome.", "ainglish": "I removed the label by-accident."},
        {"id": "on-purpose-03", "english": "I quarantined the worker deliberately.", "ainglish": "I quarantined the worker on-purpose."},
        {"id": "by-accident-03", "english": "I truncated the log by accident; I did not foresee that outcome.", "ainglish": "I truncated the log by-accident."},
        {"id": "on-purpose-04", "english": "I delayed the notification deliberately.", "ainglish": "I delayed the notification on-purpose."},
        {"id": "by-accident-04", "english": "I exposed the draft by accident; I did not foresee that outcome.", "ainglish": "I exposed the draft by-accident."},
    ]


def selection_pairs() -> list[dict]:
    return [
        {"id": "choose-any-01", "english": "Select any one mirror from the healthy set.", "ainglish": "choose-any(healthy-mirrors)."},
        {"id": "draw-uniform-01", "english": "Draw one shard from the pool with equal probability for every shard.", "ainglish": "draw-uniform(shard-pool)."},
        {"id": "choose-any-02", "english": "Choose any one approver from the available set.", "ainglish": "choose-any(available-approvers)."},
        {"id": "draw-uniform-02", "english": "Select one test case with equal probability for every case.", "ainglish": "draw-uniform(test-cases)."},
        {"id": "choose-any-03", "english": "Pick any one endpoint from the reachable set.", "ainglish": "choose-any(reachable-endpoints)."},
        {"id": "draw-uniform-03", "english": "Draw one reviewer with equal probability for every eligible reviewer.", "ainglish": "draw-uniform(eligible-reviewers)."},
        {"id": "choose-any-04", "english": "Select any one replica from the ready set.", "ainglish": "choose-any(ready-replicas)."},
        {"id": "draw-uniform-04", "english": "Choose one candidate with equal probability for every candidate.", "ainglish": "draw-uniform(candidates)."},
        {"id": "choose-any-05", "english": "Pick any one archive from the complete set.", "ainglish": "choose-any(complete-archives)."},
        {"id": "draw-uniform-05", "english": "Select one backup with equal probability for every backup.", "ainglish": "draw-uniform(backups)."},
    ]


def freeze(name: str, slug: str, construct: str, target: str, pairs: list[dict], comparator: str) -> dict:
    manifest = {
        "metric": "token_delta",
        "construct": construct,
        "models": MODELS,
        "replicates_hash": target,
        "test_set": pairs,
        "seed": "deterministic-no-randomness-20260904",
        "method": "tiktoken encode count difference between each complete Ainglish message and its lossless English comparator; equal item mean per tokenizer; headline is the maximum tokenizer mean",
        "environment": {"library": "tiktoken", "version": "0.14.0"},
        "replication_contract": {
            "comparator": comparator,
            "population": f"{len(pairs)} wholly fresh complete messages balanced across the construct poles",
            "aggregation": "equal item mean, then maximum tokenizer mean",
            "result_shape": "aggregate_only",
        },
    }
    path = ROOT / f"{name}.manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "name": name,
        "slug": slug,
        "construct": construct,
        "replicates_hash": target,
        "file": path.name,
        "pair_count": len(pairs),
        "manifest_sha256": sha256(canonical(manifest)).hexdigest(),
        "pairs_sha256": sha256(canonical(pairs)).hexdigest(),
    }


def main() -> None:
    campaigns = [
        freeze(
            "on-purpose-by-accident",
            "on-purpose-by-accident",
            "on-purpose / by-accident",
            "6bb303132426134e9f52866310fcd38950dbb3a1c32697038f4f909c92329a89",
            on_purpose_pairs(),
            "Ainglish adverbial intention pin versus its lossless deliberate or unforeseen-outcome gloss",
        ),
        freeze(
            "choose-any-draw-uniform",
            "choose-any-set-ref-draw-uniform-set-ref",
            "choose-any / draw-uniform",
            "c5a59293fc3392aa05e9e4c163114bc5facf2bb6ba431c835f51d35a17ca846c",
            selection_pairs(),
            "Ainglish selection-operation pin versus an English instruction preserving arbitrary versus equal-probability choice",
        ),
    ]
    all_pairs = [pair for row in campaigns for pair in json.loads((ROOT / row["file"]).read_text())["test_set"]]
    assert len(all_pairs) == 18
    assert len({(row["english"], row["ainglish"]) for row in all_pairs}) == 18
    index = {
        "kind": "dexagon.ainglish.flagship-token-replications.v1",
        "model_calls": 0,
        "tokenizer_calls": 0,
        "campaigns": {row["name"]: row for row in campaigns},
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
