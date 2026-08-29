#!/usr/bin/env python3
"""Mint, score, and file the group-scope token prerequisite exactly once."""

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
SCRIPTS = REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

ENCODINGS = ("cl100k_base", "o200k_base", "p50k_base")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def load() -> dict:
    packet = json.loads((ROOT / "token-items.json").read_text(encoding="utf-8"))
    sealed = dict(packet)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("packet digest drift")
    if hashlib.sha256(canonical(packet["test_set"])).hexdigest() != packet["items_sha256"]:
        raise RuntimeError("item digest drift")
    return packet


def preflight(client, packet: dict) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not public at origin/main")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = client.suggestions()
    proposal = client.proposal(packet["proposal_slug"], authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("proposal is not yet seconded/current")
    work = next(
        (
            row
            for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
            if row.get("metric") == "token_delta"
        ),
        None,
    )
    if not work or work.get("state") != "submit_original":
        raise RuntimeError("token prerequisite no longer requests an original")
    if any(
        row.get("metric") == "token_delta" and not row.get("is_replication")
        for row in proposal.get("measurements", [])
    ):
        raise RuntimeError("token original already exists")
    pairs = packet["test_set"]
    counts = {form: sum(row["form"] == form for row in pairs) for form in packet["forms"]}
    if len(pairs) != 32 or counts != {"each-group": 16, "groups-combined": 16}:
        raise RuntimeError("pair count or form balance drift")
    return {
        "commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "pairs": len(pairs),
        "form_counts": counts,
    }


def make_manifest(packet: dict, check: dict) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "each-group / groups-combined assertion scope",
        "models": [f"tiktoken/{encoding}" for encoding in ENCODINGS],
        "test_set": packet["test_set"],
        "items_sha256": packet["items_sha256"],
        "test_set_note": packet["comparison"] + "; forms receive equal weight",
        "estimand": {
            "population": "all 32 frozen complete pairs, 16 per form",
            "aggregation": (
                "mean per tokenizer over the form-balanced population; headline is the "
                "least-favourable maximum mean"
            ),
            "acceptance": packet["acceptance"],
        },
        "evidentiary_limit": packet["evidentiary_limit"],
        "environment": {
            "library": "tiktoken",
            "version": "0.13.0",
            "python": sys.version.split()[0],
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["commit"],
            "path": "group-aggregation-scope-token-carrier-2026-08-29/token-items.json",
        },
    }


def score(manifest: dict, forms: list[str]) -> tuple[dict, dict]:
    import tiktoken

    means = {}
    form_means = {}
    cells = {}
    for encoding in ENCODINGS:
        encode = tiktoken.get_encoding(encoding).encode
        cells[encoding] = [
            {
                "item_id": row["item_id"],
                "form": row["form"],
                "ainglish_tokens": len(encode(row["ainglish"])),
                "english_tokens": len(encode(row["english"])),
                "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
            }
            for row in manifest["test_set"]
        ]
        form_means[encoding] = {
            form: sum(cell["delta"] for cell in cells[encoding] if cell["form"] == form)
            / sum(cell["form"] == form for cell in cells[encoding])
            for form in forms
        }
        means[encoding] = sum(form_means[encoding].values()) / len(forms)
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
    return payload, {"value": value, "means": means, "form_means": form_means, "cells": cells}


def main() -> None:
    attempt_path = ROOT / "token-attempt.json"
    result_path = ROOT / "token-measurement.json"
    abort_path = ROOT / "token-abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit("REFUSING: local token attempt artifact already exists")
    packet = load()
    client = ainglish_client()
    check = preflight(client, packet)
    manifest = make_manifest(packet, check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20000:
        raise RuntimeError("manifest exceeds register limit")
    opened = client.mint_attempt(
        packet["proposal_slug"],
        manifest=manifest,
        estimand=(
            "The least-favourable maximum across three pinned tiktoken encodings of mean "
            "token_delta on 32 fresh pairs, with equal form weight."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and current proposal read precede mint",
            "the current lifecycle requests a token_delta original",
            "the exact pair packet and runner are public before mint or tokenizer load",
            "the population contains 32 unique complete pairs balanced 16 per form",
            "both arms preserve the exact group-set reference and assertion scope",
            "all pinned tokenizers load only after mint",
            "every finite supportive, null, or adverse result is filed",
            "the result is price-only and never used as comprehension evidence",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 32,
            "forms": check["form_counts"],
            "models": manifest["models"],
            "readers": 0,
            "items_sha256": packet["items_sha256"],
        },
        proposal_revision=packet["proposal_slug"],
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(
        json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n", encoding="utf-8"
    )
    try:
        payload, computed = score(manifest, packet["forms"])
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(packet["proposal_slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "ainglish.group-aggregation-scope-token-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": check,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "token prerequisite harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(
                json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n",
                encoding="utf-8",
            )
        raise
    result = {
        "kind": "ainglish.group-aggregation-scope-token-result.v1",
        "attempt": opened,
        "preflight": check,
        "computed": computed,
        "measurement": filed,
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
