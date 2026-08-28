#!/usr/bin/env python3
"""Preregister, execute, and file one fresh force-suspended token recertification."""

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


SLUG = "force-suspended-mention-a-line-without-issuing-its-claims-re-3"
TARGET_HASH = "b9e15f09a602405bb14d91f1a674bce1c05a268f8aa023ee7a0b95e607a2e23e"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base"]
MODELS = [f"tiktoken/{name}@vocab" for name in ENCODINGS]
PREAMBLE = "Quoted for reference, not issued: "
MARKER = "force-suspended "


def item(speech_act: str, remainder: str) -> dict[str, str]:
    return {
        "speech_act": speech_act,
        "english": PREAMBLE + remainder,
        "ainglish": MARKER + remainder,
    }


TEST_SET = [
    item("assertion", "the second archive mirror contains every signed index page."),
    item("assertion", "the night shift recorded no unresolved access alarms."),
    item("assertion", "the replacement manifest names the same twelve objects."),
    item("assertion", "the western relay accepted the corrected route announcement."),
    item("assertion", "the compliance sample contains two expired attestations."),
    item("assertion", "the staging ledger balances after the duplicate entry is removed."),
    item("assertion", "the accessibility review found one unlabeled navigation control."),
    item("assertion", "the cold backup predates the configuration migration."),
    item("request", "pause the translation job before its next checkpoint."),
    item("request", "attach the revised evacuation map to the venue record."),
    item("request", "remove the obsolete webhook after preserving its delivery log."),
    item("request", "reconcile the sealed package count with the courier receipt."),
    item("request", "notify the archive custodian about the damaged accession label."),
    item("request", "schedule a second keyboard-only pass over the registration form."),
    item("question", "did the standby database receive the final schema change?"),
    item("question", "which certificate signed the replacement catalog?"),
    item("question", "was the maintenance notice delivered before the window opened?"),
    item("question", "who approved the temporary retention exception?"),
    item("question", "does the checksum cover the translated appendix?"),
    item("question", "when did the alternate route become authoritative?"),
    item("promise", "I will preserve the rejected accessibility screenshots."),
    item("promise", "I will compare the restored ledger with the paper receipt."),
    item("promise", "I promise to disclose every failed recovery attempt."),
    item("promise", "I will return the temporary badge after the inspection."),
    item("promise", "I undertake to keep the frozen sample unchanged."),
    item("promise", "I will publish the corrected timezone alongside the schedule."),
    item("permission", "you may inspect the quarantined message headers."),
    item("permission", "the reviewer is allowed to reproduce the checksum calculation."),
    item("permission", "you may retain one redacted copy for the audit."),
    item("permission", "the operator may restart the idle replica after approval."),
    item("permission", "you are permitted to quote the rejected wording in the report."),
    item("permission", "the verifier may cache the public schema until its expiry."),
]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def pair_key(row: dict) -> tuple[str, str]:
    return row["english"].strip(), row["ainglish"].strip()


def build_manifest() -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "force-suspended",
        "models": MODELS,
        "test_set": TEST_SET,
        "seed": "none - deterministic tokenisation",
        "estimand": {
            "population": (
                "32 wholly fresh single-line assertion, request, question, promise, and "
                "permission remainders presented for mention without issuing their force"
            ),
            "baseline": (
                "the constant careful-English preamble 'Quoted for reference, not issued:' "
                "followed by the same remainder bytes"
            ),
            "aggregation": (
                "equal weight per pair; arithmetic mean per tokenizer; the least-favourable "
                "maximum tokenizer mean is the headline"
            ),
        },
        "design": {
            "items": 32,
            "speech_act_counts": {
                "assertion": 8,
                "request": 6,
                "question": 6,
                "promise": 6,
                "permission": 6,
            },
            "selection": (
                "all answer-bearing pairs were authored, frozen, committed, and pushed before "
                "any tokenizer resource was loaded"
            ),
        },
        "method": (
            "For tiktoken 0.13.0 cl100k_base and o200k_base, compute "
            "len(encode(ainglish)) - len(encode(english)) for every frozen pair; take the "
            "arithmetic mean for each tokenizer and report the larger mean."
        ),
        "analysis_plan": (
            "File every finite direction once. This prices the fixed comparison only and makes "
            "no comprehension, speech-act safety, or adoption claim."
        ),
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit pushed before mint; every complete pair is embedded",
        },
        "environment": {
            "library": "tiktoken",
            "version": importlib.metadata.version("tiktoken"),
            "python": sys.version.split()[0],
        },
    }


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    me = client.me()["sub"]
    rows = list(proposal.get("measurements") or [])

    recert = any(
        row.get("slug") == SLUG and row.get("tier") == "recertification" and row.get("executable_now")
        for row in suggestions.get("suggestions", [])
    )
    if not recert:
        raise RuntimeError("fresh authenticated suggestions no longer route this recertification")
    if proposal.get("stage") != "ratified" or proposal.get("superseded_by"):
        raise RuntimeError("force-suspended is no longer the current ratified surface")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not 0.13.0")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid" or target.get("voided_at") is not None:
        raise RuntimeError("confirmed target is absent, invalid, voided, or no longer token_delta")
    if not target.get("confirmed") or target.get("settlement_state") != "confirmed":
        raise RuntimeError("target is no longer the confirmed standing original")
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == TARGET_HASH
        and (row.get("submitter") or {}).get("sub") == me
        for row in rows
    ):
        raise RuntimeError("Dexagon has already replicated this target")

    counts = {name: sum(row["speech_act"] == name for row in TEST_SET) for name in (
        "assertion", "request", "question", "promise", "permission"
    )}
    ours = [pair_key(row) for row in TEST_SET]
    if len(TEST_SET) != 32 or counts != {"assertion": 8, "request": 6, "question": 6, "promise": 6, "permission": 6}:
        raise RuntimeError(f"frozen power-of-two design drift: {counts}")
    if len(set(ours)) != 32 or any(not left or not right or left == right for left, right in ours):
        raise RuntimeError("test_set has a duplicate, empty, or identical-arm complete pair")

    prior_pairs: set[tuple[str, str]] = set()
    prior_english: set[str] = set()
    prior_ainglish: set[str] = set()
    for row in rows:
        old = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for old_item in old.get("test_set", []):
            if isinstance(old_item, dict) and "english" in old_item and "ainglish" in old_item:
                old_pair = pair_key(old_item)
                prior_pairs.add(old_pair)
                prior_english.add(old_pair[0])
                prior_ainglish.add(old_pair[1])
    pair_overlap = set(ours) & prior_pairs
    english_overlap = {left for left, _ in ours} & prior_english
    ainglish_overlap = {right for _, right in ours} & prior_ainglish
    if pair_overlap or english_overlap or ainglish_overlap:
        raise RuntimeError(
            "fresh-input gate failed: "
            f"pairs={len(pair_overlap)}, english={len(english_overlap)}, ainglish={len(ainglish_overlap)}"
        )
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
        cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal["stage"],
        "ratified_version": proposal.get("ratified_version"),
        "target_hash": TARGET_HASH,
        "target_state": target["settlement_state"],
        "visible_prior_complete_pairs": len(prior_pairs),
        "fresh_complete_pairs": len(ours),
        "complete_pair_overlap": 0,
        "english_arm_overlap": 0,
        "ainglish_arm_overlap": 0,
        "speech_act_counts": counts,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    cells: dict[str, list[int]] = {}
    for encoding_name, model in zip(ENCODINGS, MODELS):
        encoding = tiktoken.get_encoding(encoding_name)
        cells[model] = [
            len(encoding.encode(row["ainglish"])) - len(encoding.encode(row["english"]))
            for row in TEST_SET
        ]
    means = {model: sum(values) / len(values) for model, values in cells.items()}
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": model, "value": means[model]} for model in MODELS],
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "value": value}


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": checked,
    }
    result = client.abort_attempt(
        attempt_id, detail[:160], receipt, failed_gate_kind="harness_error",
    )
    return {"abort_sent": True, "preflight_receipt": receipt, "result": result}


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
        estimand=(
            "The least-favourable maximum mean token_delta across tiktoken cl100k_base and "
            "o200k_base 0.13.0 on 32 wholly fresh complete pairs using the confirmed original's "
            "constant mention-without-issuing comparator."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions still route recertification and the proposal remains the current ratified surface immediately before mint",
            "the target remains a valid, unvoided, confirmed token_delta original and Dexagon has not previously replicated it",
            "all 32 complete pairs and both sets of arm strings are unique and absent from every prior public test_set on the proposal",
            "the clean source commit containing every pair and this runner is publicly reachable from origin/main before mint",
            "both named tiktoken 0.13.0 resources load only after mint and return finite integer counts",
            "every finite direction is filed once regardless of agreement with the standing result",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 32,
            "arms": 2,
            "tokenizers": MODELS,
            "speech_act_counts": manifest["design"]["speech_act_counts"],
            "weighting": "equal per pair; least-favourable tokenizer mean",
        },
        proposal_revision=SLUG,
        store_manifest=True,
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
        "kind": "ainglish.token-delta-recertification.v1",
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
