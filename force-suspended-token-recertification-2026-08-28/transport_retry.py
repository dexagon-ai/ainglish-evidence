#!/usr/bin/env python3
"""File the retained force-suspended result under corrected tokenizer identities."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
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
FAILED_ATTEMPT_ID = "88689bfe-29c5-408e-a0da-6ce72229c7ca"
FAILED_COMMITMENT = "d3de33dc8a955b222ec644e9a5bd8d9a643341f4874e3aab8b2d6032690a4eb9"
SOURCE_PATH = ROOT / "transport-source.json"
RECEIPT_PATH = ROOT / "receipt.json"
MODELS = ["tiktoken/cl100k_base", "tiktoken/o200k_base"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def load_original_module():
    spec = importlib.util.spec_from_file_location("force_suspended_initial", ROOT / "run_once.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the frozen initial runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_source() -> tuple[dict, object]:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    initial = load_original_module()
    if source.get("kind") != "ainglish.token-delta-transport-source.v1":
        raise RuntimeError("transport source kind drift")
    if source.get("failed_manifest_commitment") != FAILED_COMMITMENT:
        raise RuntimeError("failed manifest commitment drift")
    attempt = source.get("failed_attempt") or {}
    if attempt.get("attempt_id") != FAILED_ATTEMPT_ID or attempt.get("state") != "aborted":
        raise RuntimeError("retained failed attempt is not the declared aborted attempt")
    if source.get("corrected_models") != MODELS:
        raise RuntimeError("corrected roster drift")
    if source.get("scientific_change") != "none; same 32 pairs, encodings, counts, estimand, weights and target":
        raise RuntimeError("scientific-change disclosure drift")
    items_sha = hashlib.sha256(canonical(initial.TEST_SET)).hexdigest()
    if source.get("test_set_sha256") != items_sha:
        raise RuntimeError("retained test-set digest drift")
    computed = source.get("computed") or {}
    invalid = source.get("invalid_models") or []
    if invalid != ["tiktoken/cl100k_base@vocab", "tiktoken/o200k_base@vocab"]:
        raise RuntimeError("failed roster drift")
    cells = computed.get("cells") or {}
    if any(len(cells.get(model, [])) != 32 for model in invalid):
        raise RuntimeError("retained cell count drift")
    if any(any(not isinstance(value, int) for value in cells[model]) for model in invalid):
        raise RuntimeError("retained cells are not integer token deltas")
    means = {model: sum(cells[old]) / len(cells[old]) for model, old in zip(MODELS, invalid)}
    if means != {"tiktoken/cl100k_base": -5.0, "tiktoken/o200k_base": -4.0}:
        raise RuntimeError(f"retained means drift: {means}")
    if max(means.values()) != computed.get("value"):
        raise RuntimeError("retained headline drift")
    return source, initial


def build_manifest(source: dict, initial: object) -> dict:
    source_bytes = SOURCE_PATH.read_bytes()
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "force-suspended",
        "models": MODELS,
        "test_set": initial.TEST_SET,
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
                "all pairs were public before the failed attempt minted and every count was "
                "computed only after that mint"
            ),
        },
        "method": (
            "Retain the exact first-attempt tiktoken 0.13.0 cl100k_base and o200k_base cells; "
            "rename only their roster identities from invalid @vocab-suffixed names to the "
            "server-required bare encoding names; perform no second tokenizer run."
        ),
        "analysis_plan": (
            "File the retained finite direction once. This prices the fixed comparison only and "
            "makes no comprehension, speech-act safety, or adoption claim."
        ),
        "transport_successor": {
            "failed_attempt_id": FAILED_ATTEMPT_ID,
            "failed_manifest_commitment": FAILED_COMMITMENT,
            "failed_preflight_receipt_sha256": (
                (source.get("failed_attempt") or {}).get("preflight_receipt_hash")
            ),
            "failure_class": source["failure_class"],
            "only_scientific_field_correction": {
                "from": source["invalid_models"],
                "to": MODELS,
                "reason": "tokenizer @suffix incorrectly created disjoint roster identities",
            },
            "retained_result_sha256": hashlib.sha256(canonical(source["computed"])).hexdigest(),
            "transport_source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "tokenizers_rerun": False,
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "transport_source_path": str(SOURCE_PATH.relative_to(EVIDENCE_REPO)),
            "publication": "successor source and retained result pushed before successor mint",
        },
        "environment": {
            "library": "tiktoken",
            "version": importlib.metadata.version("tiktoken"),
            "python": sys.version.split()[0],
        },
    }


def preflight(client, manifest: dict, source: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    failed = client.attempt(FAILED_ATTEMPT_ID)
    me = client.me()["sub"]

    if not any(
        row.get("slug") == SLUG and row.get("tier") == "recertification" and row.get("executable_now")
        for row in suggestions.get("suggestions", [])
    ):
        raise RuntimeError("fresh suggestions no longer route this recertification")
    if proposal.get("stage") != "ratified" or proposal.get("superseded_by"):
        raise RuntimeError("force-suspended is no longer the current ratified surface")
    if target.get("metric") != "token_delta" or not target.get("confirmed") or target.get("voided_at") is not None:
        raise RuntimeError("standing target is no longer a valid confirmed token_delta original")
    if failed.get("state") != "aborted" or (failed.get("pin") or {}).get("manifest_commitment") != FAILED_COMMITMENT:
        raise RuntimeError("live failed-attempt receipt drift")
    if failed.get("preflight_receipt_hash") != (source.get("failed_attempt") or {}).get("preflight_receipt_hash"):
        raise RuntimeError("live failed-attempt receipt hash drift")
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == TARGET_HASH
        and (row.get("submitter") or {}).get("sub") == me
        and row.get("evidence_state") == "valid"
        for row in proposal.get("measurements", [])
    ):
        raise RuntimeError("Dexagon already has a valid replication of this target")
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
        "failed_attempt_id": FAILED_ATTEMPT_ID,
        "failed_attempt_state": failed["state"],
        "failed_preflight_receipt_sha256": failed["preflight_receipt_hash"],
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
        "tokenizers_rerun": False,
    }


def retained_payload(source: dict, manifest: dict) -> tuple[dict, dict]:
    invalid = source["invalid_models"]
    old_cells = source["computed"]["cells"]
    cells = {model: old_cells[old] for model, old in zip(MODELS, invalid)}
    means = {model: sum(values) / len(values) for model, values in cells.items()}
    value = max(means.values())
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": model, "value": means[model]} for model in MODELS],
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }, {"cells": cells, "means": means, "value": value, "tokenizers_rerun": False}


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt = {
        "kind": "ainglish.transport-successor-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "transport_failure",
        "failed_gate": detail,
        "preflight": checked,
    }
    result = client.abort_attempt(
        attempt_id, detail[:160], receipt, failed_gate_kind="transport_failure",
    )
    return {"abort_sent": True, "preflight_receipt": receipt, "result": result}


def main() -> None:
    if RECEIPT_PATH.exists():
        raise SystemExit(f"REFUSING: {RECEIPT_PATH.name} already exists; this successor is one-shot")
    source, initial = load_source()
    manifest = build_manifest(source, initial)
    client = ainglish_client()
    checked = preflight(client, manifest, source)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "Transport-only successor for attempt 88689bfe-29c5-408e-a0da-6ce72229c7ca: "
            "submit its retained least-favourable token_delta after correcting only invalid "
            "tokenizer roster identity suffixes; no tokenizer rerun."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions still route recertification and force-suspended remains the current ratified surface",
            "the standing target remains a valid confirmed token_delta original and Dexagon has no valid prior replication",
            "the failed attempt remains aborted at its exact manifest and preflight-receipt hashes",
            "the public transport source contains 32 retained integer cells per tokenizer and recomputes exactly to -5 and -4",
            "the only scientific-field correction is removal of the invalid @vocab identity suffix from both tokenizer names",
            "no tokenizer is rerun; submit the retained finite result once regardless of agreement",
        ],
        planned_sample={
            "metric": "token_delta",
            "retained_items": 32,
            "arms": 2,
            "corrected_tokenizer_identities": MODELS,
            "tokenizers_rerun": False,
            "source_attempt_id": FAILED_ATTEMPT_ID,
        },
        proposal_revision=SLUG,
        store_manifest=True,
    )["attempt"]
    try:
        payload, computed = retained_payload(source, manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise

    receipt = {
        "kind": "ainglish.token-delta-recertification-transport-successor.v1",
        "proposal": SLUG,
        "target_hash": TARGET_HASH,
        "source_attempt_id": FAILED_ATTEMPT_ID,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
