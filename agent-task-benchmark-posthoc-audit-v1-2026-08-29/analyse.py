#!/usr/bin/env python3
"""Deterministic post-hoc audit of the frozen existing-reader benchmark."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "agent-task-benchmark-v0.1-ollama-existing-readers-2026-08-28"
RESULTS_PATH = SOURCE / "RESULTS.json"
ROSTER_PATH = SOURCE / "reader-roster.json"
EXPECTED_SOURCE_HASHES = {
    "RESULTS.json": "78dacc62b827dd053a6e38c894a62b9e36e5d4f347fc8f34d5ec54598e86623d",
    "reader-roster.json": "6ca95092b16bfaf2e7877ddf84a88f29249b12dfeac49321b17b723a13e6ad20",
}
BOOTSTRAP_SEED = 2026082947
BOOTSTRAP_DRAWS = 100_000
EPSILON = 1e-12

LINEAGE_PREFIXES = (
    ("command-r7b:", "command-r"),
    ("deepseek-v2:", "deepseek"),
    ("exaone3.5:", "exaone"),
    ("falcon3:", "falcon"),
    ("gemma3:", "gemma"),
    ("glm4:", "glm"),
    ("granite3.3:", "granite"),
    ("internlm2:", "internlm"),
    ("lfm2:", "liquid"),
    ("llama3.1:", "llama"),
    ("mistral-small3.2:", "mistral"),
    ("olmo2:", "olmo"),
    ("phi4:", "phi"),
    ("qwen", "qwen"),
    ("solar-pro:", "solar"),
    ("yi:", "yi"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values: Iterable[float]) -> float:
    rows = list(values)
    return sum(rows) / len(rows)


def quantile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("quantile requires at least one value")
    location = (len(sorted_values) - 1) * probability
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return sorted_values[lower]
    weight = location - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def sign_probability(values: Iterable[float]) -> dict[str, float | int | None]:
    values = list(values)
    positive = sum(value > EPSILON for value in values)
    negative = sum(value < -EPSILON for value in values)
    zero = len(values) - positive - negative
    n = positive + negative
    if n == 0:
        probability = None
    else:
        tail = sum(math.comb(n, k) for k in range(min(positive, negative) + 1)) / (2**n)
        probability = min(1.0, 2 * tail)
    return {
        "positive": positive,
        "zero": zero,
        "negative": negative,
        "nonzero_n": n,
        "two_sided_exact_sign_probability": probability,
    }


def bootstrap_mean_interval(values: Iterable[float], seed_offset: int) -> dict[str, float | int]:
    values = list(values)
    rng = random.Random(BOOTSTRAP_SEED + seed_offset)
    draws = []
    n = len(values)
    for _ in range(BOOTSTRAP_DRAWS):
        draws.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    draws.sort()
    return {
        "seed": BOOTSTRAP_SEED + seed_offset,
        "draws": BOOTSTRAP_DRAWS,
        "lower_2_5_percent": quantile(draws, 0.025),
        "upper_97_5_percent": quantile(draws, 0.975),
    }


def tag_lineage(tag: str) -> str:
    matches = [lineage for prefix, lineage in LINEAGE_PREFIXES if tag.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"reader tag must map to exactly one lineage: {tag!r} -> {matches!r}")
    return matches[0]


def summarise(values: Iterable[float], *, bootstrap_seed_offset: int | None = None) -> dict:
    values = list(values)
    ordered = sorted(values)
    result = {
        "n": len(values),
        "mean": mean(values),
        "median": statistics.median(values),
        "minimum": ordered[0],
        "maximum": ordered[-1],
        "signs": sign_probability(values),
    }
    if bootstrap_seed_offset is not None:
        result["descriptive_lineage_bootstrap_interval"] = bootstrap_mean_interval(
            values, bootstrap_seed_offset
        )
    return result


def group_lineage_means(reader_values: dict[str, float], reader_lineage: dict[str, str]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for reader_id, value in reader_values.items():
        grouped[reader_lineage[reader_id]].append(value)
    return {lineage: mean(values) for lineage, values in sorted(grouped.items())}


def leave_one_out(values: dict[str, float]) -> dict:
    rows = []
    for omitted in sorted(values):
        retained = [value for lineage, value in values.items() if lineage != omitted]
        rows.append({"omitted_lineage": omitted, "mean": mean(retained)})
    return {
        "rows": rows,
        "minimum_mean": min(row["mean"] for row in rows),
        "maximum_mean": max(row["mean"] for row in rows),
    }


def comparison_analysis(
    rows: list[dict],
    reader_lineage: dict[str, str],
    *,
    seed_offset: int,
) -> dict:
    reader_values = {row["reader_id"]: float(row["mean_difference"]) for row in rows}
    lineage_values = group_lineage_means(reader_values, reader_lineage)
    sensitivity_readers = {
        reader_id: value
        for reader_id, value in reader_values.items()
        if reader_lineage[reader_id] not in {"deepseek", "solar"}
    }
    sensitivity_lineages = group_lineage_means(sensitivity_readers, reader_lineage)
    return {
        "reader_weighted": summarise(reader_values.values()),
        "reader_effects": dict(sorted(reader_values.items())),
        "lineage_equal_weight": summarise(
            lineage_values.values(), bootstrap_seed_offset=seed_offset
        ),
        "lineage_effects": lineage_values,
        "leave_one_lineage_out": leave_one_out(lineage_values),
        "posthoc_excluding_deepseek_and_solar": {
            "reader_weighted": summarise(sensitivity_readers.values()),
            "lineage_equal_weight": summarise(sensitivity_lineages.values()),
            "lineage_effects": sensitivity_lineages,
        },
    }


def exposure_analysis(
    comparison_rows: list[dict], reader_lineage: dict[str, str], *, seed_offset: int
) -> dict:
    by_track = {
        track: {
            row["reader_id"]: float(row["mean_difference"])
            for row in comparison_rows
            if row["track"] == track
        }
        for track in ("cold", "one_exposure")
    }
    if set(by_track["cold"]) != set(by_track["one_exposure"]):
        raise ValueError("cold and one-exposure reader sets differ")
    reader_values = {
        reader_id: by_track["one_exposure"][reader_id] - by_track["cold"][reader_id]
        for reader_id in by_track["cold"]
    }
    lineage_values = group_lineage_means(reader_values, reader_lineage)
    return {
        "definition": "one_exposure effect minus cold effect, in zero-repair success-rate points",
        "reader_weighted": summarise(reader_values.values()),
        "reader_effects": dict(sorted(reader_values.items())),
        "lineage_equal_weight": summarise(
            lineage_values.values(), bootstrap_seed_offset=seed_offset
        ),
        "lineage_effects": lineage_values,
        "leave_one_lineage_out": leave_one_out(lineage_values),
    }


def construct_analysis(
    rows: list[dict], reader_lineage: dict[str, str], *, comparison_arm: str
) -> list[dict]:
    indexed = {
        (row["construct"], row["track"], row["reader_id"], row["arm"]): row
        for row in rows
    }
    constructs = sorted({row["construct"] for row in rows})
    output = []
    for construct in constructs:
        track_values = {}
        for track in ("cold", "one_exposure"):
            reader_values = {}
            for reader_id in sorted(reader_lineage):
                ainglish = indexed[(construct, track, reader_id, "ainglish")]
                comparator = indexed[(construct, track, reader_id, comparison_arm)]
                if ainglish["n"] != comparator["n"]:
                    raise ValueError("construct arm denominators differ")
                reader_values[reader_id] = (
                    float(ainglish["zero_repair_success_rate"])
                    - float(comparator["zero_repair_success_rate"])
                )
            lineage_values = group_lineage_means(reader_values, reader_lineage)
            track_values[track] = {
                "reader_weighted": summarise(reader_values.values()),
                "lineage_equal_weight": summarise(lineage_values.values()),
                "lineage_effects": lineage_values,
            }
        lineage_exposure_change = {
            lineage: track_values["one_exposure"]["lineage_effects"][lineage]
            - track_values["cold"]["lineage_effects"][lineage]
            for lineage in track_values["cold"]["lineage_effects"]
        }
        output.append(
            {
                "construct": construct,
                "comparison": f"ainglish_minus_{comparison_arm}",
                "cold": track_values["cold"],
                "one_exposure": track_values["one_exposure"],
                "exposure_change_lineage_equal_weight": summarise(
                    lineage_exposure_change.values()
                ),
                "exposure_change_lineage_effects": lineage_exposure_change,
            }
        )
    return output


def f6(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:+.6f}"


def markdown(audit: dict) -> str:
    lines = [
        "# Post-hoc benchmark robustness audit",
        "",
        "Status: **complete**",
        "",
        (
            "This deterministic audit reuses the frozen 2,904-cell benchmark. It made no model "
            "calls and treats readers or manually grouped lineages—not individual cells—as the "
            "descriptive units."
        ),
        "",
        "## Main comparison",
        "",
        "| Comparison | Track | Reader mean | Equal-lineage mean | 95% descriptive bootstrap interval | Lineage + / 0 / - | Exact sign probability | Leave-one-lineage-out range |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for comparison in ("ainglish_minus_careful", "ainglish_minus_bare"):
        for track in ("cold", "one_exposure"):
            row = audit["comparisons"][comparison][track]
            lineage = row["lineage_equal_weight"]
            interval = lineage["descriptive_lineage_bootstrap_interval"]
            signs = lineage["signs"]
            loo = row["leave_one_lineage_out"]
            lines.append(
                f"| {comparison} | {track} | {f6(row['reader_weighted']['mean'])} | "
                f"{f6(lineage['mean'])} | [{f6(interval['lower_2_5_percent'])}, "
                f"{f6(interval['upper_97_5_percent'])}] | {signs['positive']} / "
                f"{signs['zero']} / {signs['negative']} | "
                f"{f6(signs['two_sided_exact_sign_probability'])} | [{f6(loo['minimum_mean'])}, "
                f"{f6(loo['maximum_mean'])}] |"
            )
    lines += [
        "",
        (
            "The bootstrap interval and exact sign probability are post-hoc descriptive stability "
            "summaries over 16 manually declared lineages. They are not population-level inference: "
            "the lineages are a convenience roster and may share training data or ancestry."
        ),
        "",
        "## Prompt-local definition effect",
        "",
        "| Comparison | Reader mean change | Equal-lineage mean change | 95% descriptive bootstrap interval | Lineage + / 0 / - |",
        "|---|---:|---:|---:|---:|",
    ]
    for comparison in ("ainglish_minus_careful", "ainglish_minus_bare"):
        row = audit["exposure_effects"][comparison]
        lineage = row["lineage_equal_weight"]
        interval = lineage["descriptive_lineage_bootstrap_interval"]
        signs = lineage["signs"]
        lines.append(
            f"| {comparison} | {f6(row['reader_weighted']['mean'])} | "
            f"{f6(lineage['mean'])} | [{f6(interval['lower_2_5_percent'])}, "
            f"{f6(interval['upper_97_5_percent'])}] | {signs['positive']} / "
            f"{signs['zero']} / {signs['negative']} |"
        )
    lines += [
        "",
        "A positive change means the Ainglish arm improved relative to that comparator after one supplied definition. This is prompt exposure, not pretraining or tokenizer integration.",
        "",
        "## Operational-pathology sensitivity",
        "",
        "| Comparison | Track | Equal-lineage mean, all 16 | Mean excluding DeepSeek and Solar | Remaining lineages |",
        "|---|---|---:|---:|---:|",
    ]
    for comparison in ("ainglish_minus_careful", "ainglish_minus_bare"):
        for track in ("cold", "one_exposure"):
            row = audit["comparisons"][comparison][track]
            sensitivity = row["posthoc_excluding_deepseek_and_solar"]["lineage_equal_weight"]
            lines.append(
                f"| {comparison} | {track} | {f6(row['lineage_equal_weight']['mean'])} | "
                f"{f6(sensitivity['mean'])} | {sensitivity['n']} |"
            )
    lines += [
        "",
        "This exclusion is not a replacement result. Solar's all-HTTP-500 rows and DeepSeek's strict-schema failures remain in the frozen primary result.",
        "",
        "## Construct heterogeneity: Ainglish minus careful English",
        "",
        "| Construct | Cold equal-lineage mean | One-exposure equal-lineage mean | Exposure change |",
        "|---|---:|---:|---:|",
    ]
    constructs = sorted(
        audit["constructs"]["ainglish_minus_careful"],
        key=lambda row: row["cold"]["lineage_equal_weight"]["mean"],
        reverse=True,
    )
    for row in constructs:
        lines.append(
            f"| {row['construct']} | {f6(row['cold']['lineage_equal_weight']['mean'])} | "
            f"{f6(row['one_exposure']['lineage_equal_weight']['mean'])} | "
            f"{f6(row['exposure_change_lineage_equal_weight']['mean'])} |"
        )
    lines += [
        "",
        "Each construct has only two frozen items per reader. The ranking is diagnostic and must not be presented as independent confirmation of any construct.",
        "",
        "## Bottom line",
        "",
        (
            "Equal-lineage weighting and leave-one-lineage-out checks do not change the qualitative "
            "result: prompt-cold Ainglish trails careful explicit English, beats bare ambiguous English, "
            "and one supplied definition narrows the careful-English gap while widening the bare-English "
            "advantage. The construct table shows where that aggregate story is weakest and strongest."
        ),
        "",
        (
            "Nothing here establishes current token efficiency, future-training efficiency, human "
            "intuitiveness, external adoption, model-family independence, or governance eligibility."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    observed_hashes = {
        "RESULTS.json": sha256(RESULTS_PATH),
        "reader-roster.json": sha256(ROSTER_PATH),
    }
    if observed_hashes != EXPECTED_SOURCE_HASHES:
        raise SystemExit(
            "frozen source hash mismatch: "
            + json.dumps({"expected": EXPECTED_SOURCE_HASHES, "observed": observed_hashes}, indent=2)
        )

    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))["readers"]
    tag_by_reader = {row["reader_id"]: row["tag"] for row in roster}
    reader_lineage = {
        reader_id: tag_lineage(tag) for reader_id, tag in tag_by_reader.items()
    }
    if len(reader_lineage) != 22 or len(set(reader_lineage.values())) != 16:
        raise ValueError("expected 22 readers across 16 declared lineages")

    pair_sources = {
        "ainglish_minus_careful": results["primary_paired"],
        "ainglish_minus_bare": results["secondary_paired"],
    }
    comparisons = {}
    seed_offset = 0
    for comparison, rows in pair_sources.items():
        comparisons[comparison] = {}
        for track in ("cold", "one_exposure"):
            comparisons[comparison][track] = comparison_analysis(
                [row for row in rows if row["track"] == track],
                reader_lineage,
                seed_offset=seed_offset,
            )
            seed_offset += 1

    exposure_effects = {}
    for comparison, rows in pair_sources.items():
        exposure_effects[comparison] = exposure_analysis(
            rows, reader_lineage, seed_offset=seed_offset
        )
        seed_offset += 1

    constructs = {
        "ainglish_minus_careful": construct_analysis(
            results["construct_summary"], reader_lineage, comparison_arm="careful"
        ),
        "ainglish_minus_bare": construct_analysis(
            results["construct_summary"], reader_lineage, comparison_arm="bare"
        ),
    }

    audit = {
        "schema": "ainglish.agent_task_benchmark.posthoc_audit.v1",
        "status": "complete",
        "analysis_class": "exploratory_post_hoc_descriptive",
        "generated_by": "analyse.py",
        "source": {
            "directory": SOURCE.name,
            "hashes": observed_hashes,
            "observed_rows": results["observed_rows"],
            "observed_readers": results["observed_readers"],
        },
        "lineage_map": {
            reader_id: {"tag": tag_by_reader[reader_id], "lineage": reader_lineage[reader_id]}
            for reader_id in sorted(reader_lineage)
        },
        "declared_lineages": sorted(set(reader_lineage.values())),
        "limitations": [
            "post-hoc exploratory analysis, not preregistered evidence",
            "convenience roster rather than a random model-population sample",
            "manual lineage labels reduce but cannot eliminate model dependence",
            "bootstrap interval and sign probability are descriptive, not population claims",
            "individual benchmark cells are not treated as independent samples",
            "construct strata contain only two frozen items per reader",
            "prompt-local exposure is not pretraining or tokenizer integration",
        ],
        "comparisons": comparisons,
        "exposure_effects": exposure_effects,
        "constructs": constructs,
    }
    (HERE / "AUDIT.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (HERE / "AUDIT.md").write_text(markdown(audit), encoding="utf-8")
    print(f"wrote AUDIT.json and AUDIT.md for {len(reader_lineage)} readers / {len(set(reader_lineage.values()))} lineages")


if __name__ == "__main__":
    main()
