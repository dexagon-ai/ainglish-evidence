#!/usr/bin/env python3
"""Price the public training pack under equal and observed-use weighting."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import statistics

import tiktoken


ROOT = Path(__file__).resolve().parent
RELEASE = ROOT.parent.parent / "ainglish-releases" / "ainglish-training-v0.35.0"
ENCODINGS = ("cl100k_base", "o200k_base", "p50k_base")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path.name}")
    return value


def weighted(values: dict[str, float], weights: dict[str, int]) -> float | None:
    denominator = sum(weights.get(key, 0) for key in values)
    if denominator == 0:
        return None
    return sum(values[key] * weights.get(key, 0) for key in values) / denominator


def r6(value: float | None) -> float | None:
    return None if value is None else round(value, 6)


def main() -> None:
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise SystemExit("REFUSING: tiktoken version drift")
    snapshot = checked(ROOT / "adoption-snapshot.json")
    manifest = json.loads((RELEASE / "MANIFEST.json").read_text(encoding="utf-8"))
    parallel_path = RELEASE / "data" / "parallel.jsonl"
    expected_sha = manifest["files"]["data/parallel.jsonl"]["sha256"]
    if hashlib.sha256(parallel_path.read_bytes()).hexdigest() != expected_sha:
        raise SystemExit("REFUSING: release parallel data drift")
    pairs = [json.loads(line) for line in parallel_path.read_text(encoding="utf-8").splitlines() if line]
    if len(pairs) != manifest["counts"]["parallel"]:
        raise SystemExit("REFUSING: release pair count drift")

    adoption = {row["slug"]: row["adoption"] for row in snapshot["constructs"]}
    if {row["slug"] for row in pairs} != set(adoption):
        raise SystemExit("REFUSING: release/adoption population mismatch")
    usage_weights = {
        slug: int(row.get("recent_usage") or 0)
        for slug, row in adoption.items()
        if (row.get("coverage") or {}).get("status") == "current_post_ratification"
    }
    encoders = {name: tiktoken.get_encoding(name) for name in ENCODINGS}
    per_pair = []
    per_slug_deltas: dict[str, dict[str, list[int]]] = {
        name: defaultdict(list) for name in ENCODINGS
    }
    for row in pairs:
        receipt = {
            "id": row["id"], "slug": row["slug"], "normative": row["normative"],
            "english_bytes": len(row["english"].encode()),
            "ainglish_bytes": len(row["ainglish"].encode()), "tokenizers": {},
        }
        for name, encoder in encoders.items():
            english = len(encoder.encode(row["english"]))
            ainglish = len(encoder.encode(row["ainglish"]))
            delta = ainglish - english
            receipt["tokenizers"][name] = {"english": english, "ainglish": ainglish, "delta": delta}
            per_slug_deltas[name][row["slug"]].append(delta)
        per_pair.append(receipt)

    aggregates = {}
    for name in ENCODINGS:
        pair_deltas = [row["tokenizers"][name]["delta"] for row in per_pair]
        slug_means = {slug: statistics.mean(values) for slug, values in per_slug_deltas[name].items()}
        observed = weighted(slug_means, usage_weights)
        aggregates[name] = {
            "pair_equal_mean_delta": r6(statistics.mean(pair_deltas)),
            "construct_equal_mean_delta": r6(statistics.mean(slug_means.values())),
            "observed_use_weighted_mean_delta": r6(observed),
            "projected_delta_over_observed_uses": r6(None if observed is None else observed * sum(usage_weights.values())),
            "supportive_pair_fraction": r6(sum(value < 0 for value in pair_deltas) / len(pair_deltas)),
            "null_pair_fraction": r6(sum(value == 0 for value in pair_deltas) / len(pair_deltas)),
            "adverse_pair_fraction": r6(sum(value > 0 for value in pair_deltas) / len(pair_deltas)),
            "per_construct_mean_delta": {slug: r6(value) for slug, value in sorted(slug_means.items())},
        }
    report = {
        "kind": "dexagon.ainglish.traffic-weighted-token-economics.v1",
        "interpretation": {
            "delta": "tokens(Ainglish) - tokens(careful English); negative is fewer current tokens",
            "traffic_proxy": "live recent_usage counts only where the API reports current_post_ratification coverage",
            "boundary": "This reweights reviewed release examples by observed construct-use counts. It does not tokenize the observed corpus sentences, estimate all future traffic, or show comprehension. Model exposure cannot change these literal counts while the tokenizer is fixed.",
        },
        "inputs": {
            "release_version": manifest["version"],
            "register_digest": manifest["source"]["register_digest"],
            "parallel_sha256": expected_sha,
            "pairs": len(pairs),
            "constructs": len(adoption),
            "adoption_snapshot_sha256": snapshot["content_sha256"],
            "tiktoken_version": importlib.metadata.version("tiktoken"),
            "encodings": list(ENCODINGS),
        },
        "traffic_coverage": {
            "current_post_ratification_constructs": len(usage_weights),
            "positive_weight_constructs": sum(value > 0 for value in usage_weights.values()),
            "released_constructs": len(adoption),
            "observed_uses": sum(usage_weights.values()),
            "weights": dict(sorted(usage_weights.items())),
        },
        "aggregates": aggregates,
        "pairs": per_pair,
        "model_calls": 0,
        "governance_evidence": False,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Traffic-weighted token economics",
        "",
        "This report prices every reviewed pair in the CC0 Ainglish v0.35.0 training pack under",
        "three fixed current tokenizer families, then shows both equal-weight and observed-use-weighted",
        "views. A negative delta means the Ainglish form uses fewer tokens than its complete careful-",
        "English comparator. The observed-use view is a coverage-limited proxy, not a universal traffic",
        "forecast.",
        "",
        "| Tokenizer | Equal pairs | Equal constructs | Observed-use weighted | Supportive pairs |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ENCODINGS:
        row = aggregates[name]
        lines.append(
            f"| `{name}` | {row['pair_equal_mean_delta']:+.3f} | {row['construct_equal_mean_delta']:+.3f} | "
            f"{row['observed_use_weighted_mean_delta']:+.3f} | {100 * row['supportive_pair_fraction']:.1f}% |"
        )
    coverage = report["traffic_coverage"]
    lines += [
        "",
        f"Traffic receipt: **{coverage['observed_uses']}** recent semantic uses across "
        f"**{coverage['positive_weight_constructs']}** positively weighted constructs; "
        f"**{coverage['current_post_ratification_constructs']}/{coverage['released_constructs']}** "
        "released constructs had current post-ratification coverage.",
        "",
        "## What this can and cannot say",
        "",
        "The equal-pair view describes the 57 reviewed examples. The construct-equal view prevents",
        "constructs with more examples from dominating. The traffic proxy asks what those per-construct",
        "means would imply if recent semantic-use counts were representative. It does not claim that the",
        "reviewed example is the sentence actually observed in traffic.",
        "",
        "These are current literal-token receipts. A model trained on Ainglish can reduce definitions,",
        "retries, repairs, and explanation overhead without changing a single token count here. Literal",
        "counts for the same string change only when the tokenizer or the string changes; that is tested",
        "separately in the tokenizer-adaptation lab.",
        "",
        f"Frozen report digest: `{report['content_sha256']}`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "report_sha256": report["content_sha256"], "aggregates": aggregates}, indent=2))


if __name__ == "__main__":
    main()
