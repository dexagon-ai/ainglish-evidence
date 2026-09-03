#!/usr/bin/env python3
"""Freeze a fresh, target-matched verdict-fail/no-verdict token replication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ainglish import estimand
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
SLUG = "verdict-fail-no-verdict"
TARGET_HASH = "c60e889aeed88f665a8ed99bed2906998550af5d4a7ca8b3a210b5d9144a742b"
MODELS = ["cl100k_base", "o200k_base", "p50k_base"]

TARGET_MANIFEST = {
    "metric": "token_delta",
    "models": MODELS,
    "test_set": [
        {
            "english": "The smoke test failed.",
            "ainglish": "smoke suite: verdict-fail — three assertions; rolling back.",
        },
        {
            "english": "The smoke test failed.",
            "ainglish": "smoke suite: no-verdict — runner timed out at 600s; not rolling back, re-running.",
        },
        {
            "english": "The nightly integrity check failed.",
            "ainglish": "nightly integrity check: no-verdict — runner lost its database connection; row state unchanged from yesterday pass.",
        },
        {
            "english": "The replication run failed.",
            "ainglish": "replication run: no-verdict — tokenizer roster failed to download; original stands unconfirmed, not refuted.",
        },
        {
            "english": "The sanity check failed.",
            "ainglish": "sanity check: verdict-fail — two assertions; holding release.",
        },
        {
            "english": "The build check failed.",
            "ainglish": "build check: no-verdict — runner lost network connection; build state unchanged.",
        },
        {
            "english": "The validation step failed.",
            "ainglish": "validation step: verdict-fail — one assertion; blocking merge.",
        },
        {
            "english": "The integration test failed.",
            "ainglish": "integration test: no-verdict — fixture unavailable; test state unchanged.",
        },
        {
            "english": "The deploy check failed.",
            "ainglish": "deploy check: no-verdict — timeout at 120s; deploy status unknown.",
        },
        {
            "english": "The lint check failed.",
            "ainglish": "lint check: verdict-fail — three warnings; blocking commit.",
        },
    ],
    "seed": "none",
    "method": "tiktoken encode count difference between Ainglish form and English gloss",
    "environment": {"library": "tiktoken", "version": "0.14.0"},
}

VERDICT_FAIL = [
    ("dependency licence audit", "a forbidden licence was found; blocking distribution"),
    ("package checksum audit", "the archive digest differs; rejecting the package"),
    ("migration invariant check", "two account totals changed; stopping migration"),
    ("request budget check", "the endpoint exceeded its quota; halting the batch"),
    ("translation coverage check", "four interface labels are absent; holding publication"),
    ("webhook signature check", "the signature is invalid; discarding the event"),
    ("cursor continuity check", "page forty-two skips a record; blocking export"),
    ("replica quorum check", "only one replica agreed; refusing promotion"),
    ("memory ceiling check", "the worker exceeded eight gigabytes; stopping rollout"),
    ("schema nullability check", "a required field accepted null; rejecting the migration"),
    ("cache coherence check", "two regions returned different versions; disabling writes"),
    ("archive digest check", "one stored object has changed; quarantining the archive"),
    ("dependency cycle check", "the build graph contains a cycle; refusing the release"),
]

NO_VERDICT = [
    ("domain resolution check", "the resolver did not answer; service status remains unknown"),
    ("secret availability check", "the vault could not be reached; credential status remains unknown"),
    ("worker capacity check", "the runner was killed before sampling; capacity remains unknown"),
    ("artifact retrieval check", "the download timed out; artifact integrity remains unknown"),
    ("fixture decoding check", "the fixture parser crashed; target validity remains unknown"),
    ("quota compliance check", "the provider rate-limited the probe; compliance remains unknown"),
    ("audit logging check", "the probe lacked permission to read logs; logging status remains unknown"),
    ("clock agreement check", "the reference clock was unavailable; clock drift remains unknown"),
    ("consumer progress check", "the queue observer disconnected; progress remains unknown"),
    ("temperature sensor check", "the sensor feed was unavailable; temperature remains unknown"),
    ("dataset presence check", "the dataset mount was missing; dataset state remains unknown"),
    ("compiler compatibility check", "the compiler crashed before analysis; compatibility remains unknown"),
    ("database health check", "failover began during the probe; database health remains unknown"),
    ("certificate status check", "the status responder was unreachable; revocation state remains unknown"),
    ("sandbox isolation check", "the sandbox did not start; isolation remains unknown"),
    ("invoice balance check", "the billing endpoint throttled the request; balance remains unknown"),
    ("model availability check", "the inference server did not respond; model status remains unknown"),
    ("telemetry completeness check", "the trace payload was corrupt; completeness remains unknown"),
    ("storage ownership check", "the lease expired before inspection; ownership remains unknown"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    if manifest_commitment(TARGET_MANIFEST) != TARGET_HASH:
        raise SystemExit("embedded target manifest no longer matches its public commitment")

    rows = []
    for check, detail in VERDICT_FAIL:
        rows.append({
            "form": "verdict-fail",
            "english": f"The {check} failed.",
            "ainglish": f"{check}: verdict-fail — {detail}.",
        })
    for check, detail in NO_VERDICT:
        rows.append({
            "form": "no-verdict",
            "english": f"The {check} failed.",
            "ainglish": f"{check}: no-verdict — {detail}.",
        })

    assert len(rows) == 32
    assert len({(row["english"], row["ainglish"]) for row in rows}) == 32
    target_pairs = {(row["english"], row["ainglish"]) for row in TARGET_MANIFEST["test_set"]}
    assert not target_pairs.intersection((row["english"], row["ainglish"]) for row in rows)
    assert sum(row["form"] == "verdict-fail" for row in rows) == 13
    assert sum(row["form"] == "no-verdict" for row in rows) == 19

    declaration = estimand.declaration(
        unit_span="complete check report",
        contrast=(
            "a marked check report carrying its explicit outcome explanation versus a terse "
            "bare-'failed' sentence that omits that explanation"
        ),
        population=(
            "32 fresh operational check reports: 13 completed adverse verdicts and 19 "
            "instrument-side no-result cases, approximating the target's 4:6 class mix"
        ),
        reducer="least_favourable",
        aggregation_rule="equal-item mean per tokenizer, then maximum tokenizer mean (least-favourable)",
    )
    manifest = {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "verdict-fail / no-verdict",
        "models": MODELS,
        "test_set": rows,
        "test_set_note": (
            "Target-matched bare-failed genre. The Ainglish arm also carries an explicit outcome "
            "explanation absent from the English arm, as in the routed original; this run therefore "
            "tests that complete-report contrast, not the isolated token cost of either tag."
        ),
        "comparison_identity": {
            "comparator_genre": "marked-complete-report-versus-terse-bare-failed-v1",
            "class_mix": "13 verdict-fail / 19 no-verdict; nearest 32-item approximation to target 4:6",
            "truth_boundary": "does not estimate a lossless tag-only substitution",
        },
        "estimand_contract": declaration,
        "replicates_hash": TARGET_HASH,
        "selection": (
            "Thirty-two complete pairs fixed before tokenizer loading or counting; zero exact "
            "pair overlap with the target; all finite outcomes will be filed once."
        ),
        "method": (
            "Compute tokens(ainglish)-tokens(english) for every pair and tokenizer; take the "
            "equal-item mean per tokenizer and the maximum lineage mean as headline."
        ),
    }
    spec = {"manifest": manifest, "replication_target_manifest": TARGET_MANIFEST}
    index = {
        "kind": "dexagon.ainglish.verdict-fail-token-settlement-freeze.v1",
        "proposal_revision": SLUG,
        "replicates_hash": TARGET_HASH,
        "pair_count": 32,
        "class_counts": {"verdict-fail": 13, "no-verdict": 19},
        "target_pair_intersection": 0,
        "spec_sha256": hashlib.sha256(canonical(spec)).hexdigest(),
        "reader_calls": 0,
        "tokenizer_calls": 0,
        "attempt_mints": 0,
    }
    (ROOT / "target-manifest.json").write_text(
        json.dumps(TARGET_MANIFEST, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (ROOT / "run-spec.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
