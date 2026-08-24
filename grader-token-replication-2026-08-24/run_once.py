#!/usr/bin/env python3
"""Run and file one preregistered fresh-input grader-is-graded token replication."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "grader-is-graded-robust-word-based-form-of-grader-graded-2"
TARGET_HASH = "dc50f8a3f8b9ccebaf81921fe48a6fcb16f65fbf794d4671b7f6b4a0017f989d"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base"]
MODELS = [f"tiktoken/{name}@0.13.0" for name in ENCODINGS]


TEST_SET = [
    {"cell": "compliance/direct", "english": "The process validating compliance is the same process whose compliance is being validated.", "ainglish": "The compliance validation is grader-is-graded."},
    {"cell": "calibration/direct", "english": "The robot inspecting calibration is the same robot whose calibration is under inspection.", "ainglish": "The calibration inspection is grader-is-graded."},
    {"cell": "database-health/direct", "english": "The database judging database health is the same database whose health is being judged.", "ainglish": "The database-health judgement is grader-is-graded."},
    {"cell": "failover/direct", "english": "The controller rating failover readiness is the same controller whose readiness is being rated.", "ainglish": "The failover-readiness rating is grader-is-graded."},
    {"cell": "review-quality/direct", "english": "The review team assessing review quality is the same team whose reviewing is being assessed.", "ainglish": "The review-quality assessment is grader-is-graded."},
    {"cell": "moderation/direct", "english": "The moderator evaluating moderator neutrality is the same moderator whose neutrality is being evaluated.", "ainglish": "The neutrality evaluation is grader-is-graded."},
    {"cell": "schedule/produced-artifact", "english": "The planner checking the deployment schedule is the same planner that created the schedule.", "ainglish": "The schedule check is grader-is-graded."},
    {"cell": "binary/produced-artifact", "english": "The compiler vetting the executable is the same compiler that built the executable.", "ainglish": "The executable vetting is grader-is-graded."},
    {"cell": "summary/produced-artifact", "english": "The summarizer scoring the summary is the same summarizer that wrote the summary.", "ainglish": "The summary score is grader-is-graded."},
    {"cell": "translation/produced-artifact", "english": "The translator reviewing the translation is the same translator that produced the translation.", "ainglish": "The translation review is grader-is-graded."},
    {"cell": "alerts/produced-artifact", "english": "The monitor validating the alerts is the same monitor that emitted the alerts.", "ainglish": "The alert validation is grader-is-graded."},
    {"cell": "dataset/produced-artifact", "english": "The curator approving the dataset is the same curator that assembled the dataset.", "ainglish": "The dataset approval is grader-is-graded."},
    {"cell": "report/produced-artifact", "english": "The reviewer scoring the report is the same reviewer that authored the report.", "ainglish": "The report score is grader-is-graded."},
    {"cell": "queue/produced-artifact", "english": "The scheduler validating the work queue is the same scheduler that generated the queue.", "ainglish": "The queue validation is grader-is-graded."},
    {"cell": "forecast/produced-artifact", "english": "The simulator checking the forecast is the same simulator that produced the forecast.", "ainglish": "The forecast check is grader-is-graded."},
    {"cell": "policy/produced-artifact", "english": "The policy engine approving the rule set is the same engine that generated the rule set.", "ainglish": "The rule-set approval is grader-is-graded."},
]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def build_manifest() -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "grader-is-graded",
        "models": MODELS,
        "estimand": {
            "population": "operational disclosures where an evaluator is itself evaluated or produced the evaluated artifact",
            "baseline": "honest careful English explicitly naming the evaluator/evaluated identity or artifact provenance coupling",
            "aggregation": "equal weight over 16 fresh domains with the target 3:5 direct-self/provenance-coupled composition preserved as 6:10; registered floor is the larger tokenizer mean",
        },
        "design": {
            "strata": {"direct-self-evaluation": 6, "produced-artifact": 10},
            "balance": "six direct-self and ten produced-artifact disclosures, matching the targets 3:5 composition",
            "selection": "domains and wording fixed before tokenisation; exact complete-pair overlap with every visible prior manifest must be zero",
        },
        "test_set": TEST_SET,
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) "
            "for every complete pair without special tokens. Take the arithmetic mean for each "
            "named tokenizer and report the larger tokenizer mean as the least-favourable "
            "token_delta; value_lo/value_hi are the minimum/maximum tokenizer means."
        ),
        "analysis_plan": "Report the aggregate, both tokenizer means, both relation strata, and reproduction verdict regardless of sign; token evidence does not establish comprehension or correctness.",
        "seed": "none - deterministic tokenisation",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit frozen and pushed before mint; complete test_set is embedded in the public measurement manifest",
        },
        "tokenizer_package": f"tiktoken-{importlib.metadata.version('tiktoken')}",
    }


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    cards = [
        card for card in suggestions.get("suggestions", [])
        if card.get("replicates_hash") == TARGET_HASH
    ]
    if proposal.get("stage") != "ratified":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not ratified")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not the frozen 0.13.0 resource")
    if not cards or not cards[0].get("confirmation_capable") or not cards[0].get("executable_now"):
        raise RuntimeError("fresh authenticated suggestions no longer offer this confirmation-capable replication")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid" or target.get("voided_at") is not None:
        raise RuntimeError("target original is absent, invalid, voided, or no longer token_delta")
    if target.get("settlement_state") != "disputed" or target.get("replication_count") != 0 or target.get("disagreement_count") != 1:
        raise RuntimeError("target settlement is no longer the registered 0-agreement/1-disagreement dispute")
    if len(TEST_SET) != 16 or len(TEST_SET) & (len(TEST_SET) - 1):
        raise RuntimeError("test_set is not the frozen power-of-two count 16")
    ours = [pair_key(item) for item in TEST_SET]
    strata = {
        "direct-self-evaluation": sum(item["cell"].endswith("/direct") for item in TEST_SET),
        "produced-artifact": sum(item["cell"].endswith("/produced-artifact") for item in TEST_SET),
    }
    if strata != {"direct-self-evaluation": 6, "produced-artifact": 10}:
        raise RuntimeError(f"relation strata do not preserve the target composition: {strata}")
    if len(set(ours)) != 16 or any(not left or not right or left == right for left, right in ours):
        raise RuntimeError("test_set contains a duplicate, empty, or identical-arm complete pair")
    prior = set()
    for row in proposal.get("measurements", []):
        old = row.get("manifest") or {}
        if not old.get("test_set") and row.get("manifest_hash"):
            old = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for item in old.get("test_set", []):
            if isinstance(item, dict) and "english" in item and "ainglish" in item:
                prior.add(pair_key(item))
    overlap = sorted(set(ours) & prior)
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; frozen source is ambiguous")
    return {
        "proposal_stage": proposal["stage"],
        "suggestion_confirmation_capable": True,
        "target_hash": TARGET_HASH,
        "target_state": target["settlement_state"],
        "target_replication_count": target["replication_count"],
        "target_disagreement_count": target["disagreement_count"],
        "visible_prior_complete_pairs": len(prior),
        "fresh_complete_pairs": len(ours),
        "complete_pair_overlap": 0,
        "strata": strata,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # The tokenizer is deliberately imported only after attempt minting.
    import tiktoken

    cells = {}
    for encoding_name in ENCODINGS:
        encoding = tiktoken.get_encoding(encoding_name)
        cells[encoding_name] = [
            len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            for item in TEST_SET
        ]
    means = {name: round(sum(values) / len(values), 4) for name, values in cells.items()}
    by_relation = {}
    for label, suffix in (("direct-self-evaluation", "/direct"), ("produced-artifact", "/produced-artifact")):
        indexes = [i for i, row in enumerate(TEST_SET) if row["cell"].endswith(suffix)]
        by_relation[label] = {
            name: round(sum(cells[name][i] for i in indexes) / len(indexes), 4)
            for name in ENCODINGS
        }
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": model, "value": means[name]} for model, name in zip(MODELS, ENCODINGS)],
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "by_relation": by_relation, "value": value}


def abort_if_open(client, attempt_id: str, detail: str, preflight_receipt: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt_obj = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": preflight_receipt,
    }
    result = client.abort_attempt(
        attempt_id,
        detail[:160],
        receipt_obj,
        failed_gate_kind="harness_error",
    )
    return {"abort_sent": True, "preflight_receipt": receipt_obj, "result": result}


def main() -> None:
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists; this run is one-shot")
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand="The least-favourable maximum mean token_delta across cl100k_base and o200k_base on 16 fresh complete grader-is-graded pairs, preserving the targets 3:5 direct-self/provenance composition as 6:10, against honest careful English stating the same evaluator coupling.",
        admissibility_gates=[
            "fresh authenticated suggestions still offer this exact confirmation-capable target",
            "the ratified target remains valid, unvoided, disputed, with zero agreements and one disagreement",
            "all 16 complete pairs are unique, preserve the targets direct-self/provenance composition, and are absent from every visible prior test_set",
            "the source is committed and clean before mint, and the public manifest embeds every answer-bearing pair",
            "both named tiktoken resources load and return finite integer counts",
            "every finite result is filed regardless of sign or agreement with the target",
        ],
        planned_sample={
            "metric": "token_delta", "items": 16, "arms": 2, "tokenizers": MODELS,
            "domains": 16, "relation_strata": {"direct-self-evaluation": 6, "produced-artifact": 10},
            "weights": "equal by item within tokenizer; least-favourable tokenizer mean",
        },
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise
    receipt = {
        "kind": "ainglish.token-delta-replication.v1",
        "proposal": SLUG,
        "target_hash": TARGET_HASH,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
