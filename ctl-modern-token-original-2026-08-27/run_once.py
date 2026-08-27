#!/usr/bin/env python3
"""Mint before tokenizer access, score the frozen ctl carrier, and file every result."""

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

ENCODINGS = ("cl100k_base", "o200k_base")


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
        raise RuntimeError("frozen source is not published")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = client.suggestions()
    proposal = client.proposal(packet["proposal_slug"], authenticated=True)
    if proposal.get("stage") != "ratified" or proposal.get("superseded_by"):
        raise RuntimeError("proposal lifecycle changed")
    pairs = packet["test_set"]
    if len(pairs) != 32 or len(pairs) & (len(pairs) - 1):
        raise RuntimeError("pair-count gate")
    if len({row["item_id"] for row in pairs}) != len(pairs):
        raise RuntimeError("duplicate item id")
    counts = {form: sum(row["form"] == form for row in pairs) for form in packet["forms"]}
    if counts != {"ctl(named)": 16, "ctl(none)": 16}:
        raise RuntimeError("form-balance gate")
    return {
        "commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "existing_measurements": len(proposal.get("measurements", [])),
        "pairs": len(pairs),
        "form_counts": counts,
    }


def make_manifest(packet: dict, check: dict) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "X ctl(<named control>) | X ctl(none)",
        "models": [f"tiktoken/{encoding}" for encoding in ENCODINGS],
        "test_set": packet["test_set"],
        "items_sha256": packet["items_sha256"],
        "test_set_note": packet["comparison"] + "; forms receive equal weight",
        "estimand": {
            "population": "all 32 frozen complete minimal disclosure pairs, 16 per form",
            "aggregation": "mean per tokenizer across all 32 pairs; headline is the least-favourable maximum tokenizer mean",
            "acceptance": packet["acceptance"],
        },
        "evidentiary_limit": packet["evidentiary_limit"],
        "environment": {"library": "tiktoken", "version": "0.13.0", "python": sys.version.split()[0]},
        "source": {"repository": "dexagon-ai/ainglish-evidence", "commit": check["commit"], "path": "ctl-modern-token-original-2026-08-27/token-items.json"},
    }


def score(manifest: dict, forms: list[str]) -> tuple[dict, dict]:
    import tiktoken

    means, form_means, cells = {}, {}, {}
    for encoding in ENCODINGS:
        encode = tiktoken.get_encoding(encoding).encode
        cells[encoding] = [{
            "item_id": row["item_id"],
            "form": row["form"],
            "ainglish_tokens": len(encode(row["ainglish"])),
            "english_tokens": len(encode(row["english"])),
            "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
        } for row in manifest["test_set"]]
        form_means[encoding] = {
            form: sum(cell["delta"] for cell in cells[encoding] if cell["form"] == form) / 16
            for form in forms
        }
        means[encoding] = sum(cell["delta"] for cell in cells[encoding]) / len(cells[encoding])
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": value,
        "panel_models": manifest["models"],
        "per_member": [{"model": model, "value": means[encoding]} for model, encoding in zip(manifest["models"], ENCODINGS, strict=True)],
        "manifest": manifest,
    }
    return payload, {"value": value, "accepts": value <= -10, "means": means, "form_means": form_means, "cells": cells}


def main() -> None:
    run_number = 2 if any((ROOT / name).exists() for name in ("attempt.json", "measurement.json", "abort.json")) else 1
    while any((ROOT / f"{stem}-{run_number}.json").exists() for stem in ("attempt", "measurement", "abort")):
        run_number += 1
    attempt_path = ROOT / f"attempt-{run_number}.json"
    result_path = ROOT / f"measurement-{run_number}.json"
    abort_path = ROOT / f"abort-{run_number}.json"
    packet = load()
    client = ainglish_client()
    check = preflight(client, packet)
    manifest = make_manifest(packet, check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20_000:
        raise RuntimeError("manifest exceeds register limit")
    opened = client.mint_attempt(
        packet["proposal_slug"],
        manifest=manifest,
        estimand="The least-favourable maximum across cl100k_base and o200k_base of mean token_delta on 32 fresh complete-disclosure pairs, equally balanced by ctl form.",
        admissibility_gates=[
            "fresh authenticated suggestions and proposal state are read before mint",
            "the clean exact 32-pair packet is public before mint",
            "the test set contains exactly 32 unique pairs balanced 16 per form",
            "the comparator carries the full same-run positive-control disclosure and never uses silence",
            "tiktoken 0.13.0 and both pinned encodings load only after mint",
            "every finite supportive, null, or adverse result is filed",
            "the result is labelled as price evidence only and as a new original, never an independent confirmation",
        ],
        planned_sample={"metric": "token_delta", "pairs": 32, "forms": check["form_counts"], "models": manifest["models"], "readers": 0, "items_sha256": packet["items_sha256"]},
        proposal_revision=packet["proposal_slug"],
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n", encoding="utf-8")
    try:
        payload, computed = score(manifest, packet["forms"])
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(packet["proposal_slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {"kind": "dexagon.ainglish.ctl-token-abort.v1", "at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}", "preflight": check}
            aborted = client.abort_attempt(opened["attempt_id"], "token harness failed before measurement emission", receipt, failed_gate_kind="harness_error")
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n", encoding="utf-8")
        raise
    result = {"kind": "dexagon.ainglish.ctl-modern-token-result.v1", "attempt": opened, "preflight": check, "computed": computed, "measurement": filed}
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    row = filed.get("measurement") or filed
    print(json.dumps({"attempt_id": opened["attempt_id"], "value": computed["value"], "accepts": computed["accepts"], "means": computed["means"], "form_means": computed["form_means"], "measurement_hash": row.get("hash") or row.get("manifest_hash")}, indent=2))


if __name__ == "__main__":
    main()
