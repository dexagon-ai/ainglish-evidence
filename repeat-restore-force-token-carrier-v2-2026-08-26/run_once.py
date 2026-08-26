#!/usr/bin/env python3
"""Mint, score, and file the frozen force-explicit token prerequisite once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


ENCODINGS = ("cl100k_base", "o200k_base", "p50k_base")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def load_packet() -> dict:
    value = json.loads((ROOT / "token-items.json").read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("packet digest drift")
    if hashlib.sha256(canonical(value["test_set"])).hexdigest() != value["items_sha256"]:
        raise RuntimeError("item digest drift")
    return value


def preflight(client, frozen: dict) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not published")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = client.suggestions()
    proposal = client.proposal(frozen["proposal_slug"], authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("current successor is not at an executable initial-evidence stage")
    token_work = next(
        (
            work
            for work in (proposal.get("evidence_readiness") or {}).get("work_items", [])
            if work.get("metric") == "token_delta"
        ),
        None,
    )
    if not token_work or token_work.get("state") != "submit_original":
        raise RuntimeError("token prerequisite no longer requests an original")
    if any(
        row.get("metric") == "token_delta" and not row.get("is_replication")
        for row in proposal.get("measurements", [])
    ):
        raise RuntimeError("a token original already exists")
    if len(frozen["test_set"]) != 64 or frozen["form_counts"] != {
        "repeat-event": 32,
        "restore-state": 32,
    }:
        raise RuntimeError("population or form-balance gate")
    if any(counts != {"repeat-event": 4, "restore-state": 4} for counts in frozen["predicate_family_counts"].values()):
        raise RuntimeError("predicate-family balance gate")
    return {
        "commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "form_counts": frozen["form_counts"],
    }


def make_manifest(frozen: dict, check: dict) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "force-explicit repeat-event / restore-state(<S>)",
        "models": [f"tiktoken/{encoding}" for encoding in ENCODINGS],
        "test_set": {
            "url": (
                "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                f"{check['commit']}/repeat-restore-force-token-carrier-v2-2026-08-26/token-items.json"
            ),
            "path": "test_set",
            "items": 64,
            "sha256": frozen["items_sha256"],
        },
        "test_set_note": frozen["comparison"],
        "estimand": {
            "population": (
                "all 64 frozen affirmative event pairs; 32 per form and four per form "
                "in each of eight fresh predicate families"
            ),
            "aggregation": (
                "mean within form per tokenizer, equal-weight mean over the two forms, "
                "headline maximum across tokenizers"
            ),
            "acceptance": frozen["acceptance"],
        },
        "evidentiary_limit": frozen["evidentiary_limit"],
        "environment": {
            "library": "tiktoken",
            "version": "0.13.0",
            "python": sys.version.split()[0],
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["commit"],
            "path": "repeat-restore-force-token-carrier-v2-2026-08-26/token-items.json",
        },
    }


def score(manifest: dict, frozen: dict) -> tuple[dict, dict]:
    # Deliberately load tokenizers only after the attempt exists.
    import tiktoken

    means: dict[str, float] = {}
    form_means: dict[str, dict[str, float]] = {}
    family_means: dict[str, dict[str, float]] = {}
    cells: dict[str, list[dict]] = {}
    for encoding in ENCODINGS:
        encode = tiktoken.get_encoding(encoding).encode
        cells[encoding] = [
            {
                "item_id": row["item_id"],
                "form": row["form"],
                "predicate_family": row["predicate_family"],
                "ainglish_tokens": len(encode(row["ainglish"])),
                "english_tokens": len(encode(row["english"])),
                "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
            }
            for row in frozen["test_set"]
        ]
        form_means[encoding] = {
            form: sum(cell["delta"] for cell in cells[encoding] if cell["form"] == form)
            / frozen["form_counts"][form]
            for form in frozen["forms"]
        }
        family_means[encoding] = {
            family: sum(
                cell["delta"]
                for cell in cells[encoding]
                if cell["predicate_family"] == family
            )
            / 8
            for family in frozen["predicate_family_counts"]
        }
        means[encoding] = sum(form_means[encoding].values()) / len(form_means[encoding])
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": value,
        "panel_models": manifest["models"],
        "per_member": [
            {"model": model, "value": means[encoding]}
            for model, encoding in zip(manifest["models"], ENCODINGS, strict=True)
        ],
        "manifest": manifest,
    }
    return payload, {
        "value": value,
        "means": means,
        "form_means": form_means,
        "family_means": family_means,
        "cells": cells,
    }


def main() -> None:
    attempt_path = ROOT / "token-attempt.json"
    result_path = ROOT / "token-measurement.json"
    abort_path = ROOT / "token-abort.json"
    if attempt_path.exists() or result_path.exists() or abort_path.exists():
        raise SystemExit("REFUSING: local token attempt artifact already exists")
    frozen = load_packet()
    client = ainglish_client()
    check = preflight(client, frozen)
    manifest = make_manifest(frozen, check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20_000:
        raise RuntimeError("manifest exceeds register limit")
    opened = client.mint_attempt(
        frozen["proposal_slug"],
        manifest=manifest,
        estimand=(
            "The least-favourable maximum across three pinned tiktoken encodings of the "
            "equal-form mean token_delta on 64 fresh affirmative force-matched pairs."
        ),
        admissibility_gates=[
            "the current force-explicit successor is seconded or measured and requests a token original",
            "the clean exact 64-item packet is public before mint",
            "the packet remains balanced 32/32 and 4/4 per fresh predicate family",
            "each restore-state argument names the event's entailed result state",
            "the controls express the successor's complete current affirmative mapping",
            "all pinned tokenizers load only after mint",
            "every finite supportive, null, or adverse result is filed",
            "the result is labelled price-only and never used as force or comprehension evidence",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 64,
            "forms": check["form_counts"],
            "models": manifest["models"],
            "readers": 0,
            "items_sha256": frozen["items_sha256"],
        },
        proposal_revision=frozen["proposal_slug"],
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(
        json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        payload, computed = score(manifest, frozen)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(frozen["proposal_slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "ainglish.repeat-restore-force-token-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": check,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "force-explicit token prerequisite harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(
                json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n",
                encoding="utf-8",
            )
        raise
    result = {
        "kind": "ainglish.repeat-restore-force-token-result.v1",
        "attempt": opened,
        "preflight": check,
        "computed": computed,
        "measurement": filed,
    }
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    row = filed.get("measurement") or filed
    print(
        json.dumps(
            {
                "attempt_id": opened["attempt_id"],
                "manifest_commitment": check["manifest_commitment"],
                "value": computed["value"],
                "means": computed["means"],
                "form_means": computed["form_means"],
                "measurement_hash": row.get("hash") or row.get("manifest_hash"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
