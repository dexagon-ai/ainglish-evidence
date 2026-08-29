#!/usr/bin/env python3
"""Inference-free paired audit of the completed cross-over exposure study."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
EXPECTED_SHA256 = {
    "eval.jsonl": "5681e43f7f20fdfc3b542716b92bc60342f20d5a65c23027b166882ba59d5a92",
    "results/adapter-a.jsonl": "a6d8ccb8c53c4f71651e5508661260ea7b5ca33c2b4b450485a02ca8338443f1",
    "results/adapter-b.jsonl": "48d599fbaa0cf2892f55a33c8ab8894356caff1457108201a59ad97b147e98ad",
    "results/base.jsonl": "4436d45759c9d39d73a9c5d8a854fcd777b2f6932314f54de3311a65f10353b0",
    "analysis.json": "2e3856f2d0daa71d7fd5c023e068d3baa41770076e89d9a5c79fed7fabd27b76",
    "adapter-receipts.json": "7a7c74228f586ddfbdd9145725753bed1a6f55914a5505038e3df2b2c6784581",
}
CONDITIONS = ("base", "adapter-a", "adapter-b")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def exact_paired_sign_probability(exposed_only: int, unexposed_only: int) -> float:
    """Two-sided exact sign probability over outcome-discordant pairs."""

    n = exposed_only + unexposed_only
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, index) for index in range(min(exposed_only, unexposed_only) + 1))
    return min(1.0, 2 * tail / (2**n))


def correct(result: dict[str, Any], source: dict[str, Any]) -> bool:
    return bool(result["valid"] and result["observed"] == source["expected"])


def fpc(value: float) -> str:
    return f"{100 * value:.1f}%"


def markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Post-hoc paired audit",
        "",
        "Status: **complete**",
        "",
        (
            "This deterministic, inference-free audit checks the frozen 2,592 predictions. It "
            "does not rerun a model or replace the prospective interpretation."
        ),
        "",
        "## Paired cold cross-over",
        "",
        "| Construct | Exposed / 48 | Unexposed / 48 | Difference | Exposed-only / unexposed-only | Exact paired probability | Prospective interpretation |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in audit["paired_cold_cross_over"]:
        lines.append(
            f"| {row['title']} | {row['exposed_correct']} | {row['unexposed_correct']} | "
            f"{row['difference']:+.3f} | {row['exposed_only']} / {row['unexposed_only']} | "
            f"{row['two_sided_exact_paired_probability']:.8g} | `{row['prospective_interpretation']}` |"
        )
    lines += [
        "",
        (
            "The exact paired probabilities are post-hoc descriptive diagnostics over the 48 "
            "synthetic held-out frames. They are unadjusted for six comparisons and are not "
            "population-level inference."
        ),
        "",
        "## Strict-output validity",
        "",
        "| Condition | Valid | Invalid | Validity |",
        "|---|---:|---:|---:|",
    ]
    for condition in CONDITIONS:
        row = audit["strict_output_validity"][condition]
        lines.append(
            f"| `{condition}` | {row['valid']} | {row['invalid']} | {fpc(row['validity'])} |"
        )
    lines += [
        "",
        (
            "All 404 malformed outputs came from the untouched base. The adapters learned the "
            "terse one-key JSON response format while learning their assigned tasks. Therefore "
            "absolute base-versus-adapter accuracy conflates semantic performance with instruction "
            "and length compliance. The adapter-versus-adapter paired comparison is the cleaner "
            "selectivity diagnostic."
        ),
        "",
        "## Interpretation",
        "",
        "- Event-versus-state recurrence and failure contract pass the frozen selective-uptake rule and retain sizeable paired cross-over advantages.",
        "- List completeness and claim source have large exposure-specific cold advantages, but fail frozen safety gates because behavior on bare ambiguity worsened; they remain broad behavior shifts.",
        "- Pronoun number is perfect under both adapters, so this experiment cannot attribute its improvement specifically to pronoun exposure.",
        "- Role cardinality differs by only 3 of 48 paired frames; the post-hoc exact paired probability is 0.25 and its frozen classification remains broad behavior shift.",
        "- Every exposed cold construct scored 48/48, with no pole or opaque-label collapse. That demonstrates held-out task acquisition under this high-dose supervised setup, not future-pretraining performance.",
        "",
        "## Provenance-label note",
        "",
        (
            f"The raw result field named `public_preregistration_commit` contains `{audit['provenance']['runtime_directory_commit']}`: "
            "the latest public commit touching the study directory when evaluation began. The "
            f"actual corpus/protocol freeze is `{audit['provenance']['corpus_protocol_freeze_commit']}`, "
            f"and the adapter-receipt freeze is `{audit['provenance']['adapter_receipt_freeze_commit']}`. "
            "Both stages and every input digest remain independently bound; this is a field-label "
            "ambiguity, not input drift. Raw receipts are retained unchanged."
        ),
        "",
        "## Claim boundary",
        "",
        (
            "This is a project-linked supervised QLoRA development result. It is not foundation-model "
            "pretraining, tokenizer integration, human validation, independent Ainglish evidence, a "
            "ratification recommendation, or proof of future efficiency."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    for relative, expected in EXPECTED_SHA256.items():
        actual = sha256(HERE / relative)
        if actual != expected:
            raise SystemExit(f"REFUSING: source drift for {relative}: {actual} != {expected}")

    evaluation_rows = read_jsonl(HERE / "eval.jsonl")
    evaluation = {row["id"]: row for row in evaluation_rows}
    if len(evaluation_rows) != 864 or len(evaluation) != 864:
        raise SystemExit("REFUSING: evaluation population must contain 864 unique IDs")
    results: dict[str, dict[str, dict[str, Any]]] = {}
    for condition in CONDITIONS:
        rows = read_jsonl(HERE / "results" / f"{condition}.jsonl")
        indexed = {row["id"]: row for row in rows}
        if len(rows) != 864 or set(indexed) != set(evaluation):
            raise SystemExit(f"REFUSING: result population drift for {condition}")
        for row in rows:
            source = evaluation[row["id"]]
            if (row["key"], row["arm"], row["expected"]) != (
                source["key"], source["condition"], source["expected"]
            ):
                raise SystemExit(f"REFUSING: source binding drift for {condition} {row['id']}")
        results[condition] = indexed

    plan = json.loads((HERE / "RUN_PLAN.json").read_text(encoding="utf-8"))
    analysis = json.loads((HERE / "analysis.json").read_text(encoding="utf-8"))
    receipts = json.loads((HERE / "adapter-receipts.json").read_text(encoding="utf-8"))
    titles = {
        row["key"]: row["title"]
        for row in json.loads((HERE / "source-pins.json").read_text(encoding="utf-8"))["constructs"]
    }
    prospective = {row["key"]: row["interpretation"] for row in analysis["construct_results"]}

    paired = []
    pole_checks: dict[str, dict[str, dict[str, int]]] = {}
    label_checks: dict[str, dict[str, dict[str, int]]] = {}
    for key in plan["groups"]["a"] + plan["groups"]["b"]:
        group = "a" if key in plan["groups"]["a"] else "b"
        exposed = f"adapter-{group}"
        unexposed = f"adapter-{'b' if group == 'a' else 'a'}"
        ids = [
            row["id"]
            for row in evaluation_rows
            if row["key"] == key and row["condition"] == "ainglish_cold"
        ]
        exposed_correct = [correct(results[exposed][item], evaluation[item]) for item in ids]
        unexposed_correct = [correct(results[unexposed][item], evaluation[item]) for item in ids]
        exposed_only = sum(left and not right for left, right in zip(exposed_correct, unexposed_correct))
        unexposed_only = sum(right and not left for left, right in zip(exposed_correct, unexposed_correct))
        paired.append(
            {
                "key": key,
                "title": titles[key],
                "exposed_condition": exposed,
                "unexposed_condition": unexposed,
                "n": len(ids),
                "exposed_correct": sum(exposed_correct),
                "unexposed_correct": sum(unexposed_correct),
                "difference": (sum(exposed_correct) - sum(unexposed_correct)) / len(ids),
                "exposed_only": exposed_only,
                "unexposed_only": unexposed_only,
                "two_sided_exact_paired_probability": exact_paired_sign_probability(
                    exposed_only, unexposed_only
                ),
                "prospective_interpretation": prospective[key],
            }
        )
        pole_counts: dict[str, Counter[str]] = {}
        label_counts: dict[str, Counter[str]] = {}
        for item in ids:
            source = evaluation[item]
            pole_counts.setdefault(source["pole"], Counter())["total"] += 1
            label_counts.setdefault(source["expected"], Counter())["total"] += 1
            if correct(results[exposed][item], source):
                pole_counts[source["pole"]]["correct"] += 1
                label_counts[source["expected"]]["correct"] += 1
        pole_checks[key] = {name: dict(counts) for name, counts in sorted(pole_counts.items())}
        label_checks[key] = {name: dict(counts) for name, counts in sorted(label_counts.items())}

    validity = {}
    for condition in CONDITIONS:
        rows = list(results[condition].values())
        valid = sum(bool(row["valid"]) for row in rows)
        validity[condition] = {
            "total": len(rows),
            "valid": valid,
            "invalid": len(rows) - valid,
            "validity": valid / len(rows),
            "invalid_by_arm": dict(sorted(Counter(row["arm"] for row in rows if not row["valid"]).items())),
        }

    runtime_commits = {
        row["public_preregistration_commit"]
        for condition in CONDITIONS
        for row in results[condition].values()
    }
    adapter_commits = {
        row["public_adapter_receipt_commit"]
        for condition in CONDITIONS
        for row in results[condition].values()
    }
    if len(runtime_commits) != 1 or len(adapter_commits) != 1:
        raise SystemExit("REFUSING: evaluation commit fields are not constant")

    audit = {
        "schema": "ainglish.crossover-exposure-posthoc-audit.v1",
        "source_sha256": EXPECTED_SHA256,
        "inference_calls": 0,
        "predictions_reused": 2592,
        "paired_cold_cross_over": paired,
        "strict_output_validity": validity,
        "exposed_cold_by_pole": pole_checks,
        "exposed_cold_by_expected_label": label_checks,
        "provenance": {
            "corpus_protocol_freeze_commit": receipts["public_preregistration_commit"],
            "adapter_receipt_freeze_commit": next(iter(adapter_commits)),
            "runtime_directory_commit": next(iter(runtime_commits)),
            "raw_receipts_modified": False,
        },
        "interpretation_boundary": (
            "Post-hoc deterministic diagnostics over synthetic frames; no multiplicity correction, "
            "population sampling claim, governance evidence, or human validation."
        ),
    }
    rendered = json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (HERE / "POST_HOC_AUDIT.json").write_text(rendered, encoding="utf-8")
    (HERE / "POST_HOC_AUDIT.md").write_text(markdown(audit), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "predictions_reused": audit["predictions_reused"],
                "invalid_by_condition": {
                    name: row["invalid"] for name, row in validity.items()
                },
                "paired": {
                    row["key"]: {
                        "difference": row["difference"],
                        "p": row["two_sided_exact_paired_probability"],
                    }
                    for row in paired
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
