#!/usr/bin/env python3
"""Preregister, run, and file the biweekly pair's token prerequisite exactly once."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc"
TOKENIZER_VERSION = "0.13.0"
ENCODINGS = ("cl100k_base", "o200k_base")
MODELS = tuple(f"tiktoken/{name}@{TOKENIZER_VERSION}" for name in ENCODINGS)
RECEIPT = ROOT / "token-delta-receipt.json"
ABORT_RECEIPT = ROOT / "token-delta-abort-receipt.json"


SUBJECTS = [
    "the dependency audit", "the access-log review", "the permission scan",
    "the checksum sweep", "the vulnerability scan", "the invoice reconciliation",
    "the policy audit", "the retention review", "the backup verification",
    "the inventory count", "the incident digest", "the usage report",
    "the billing summary", "the deployment bulletin", "the research update",
    "the compliance memo", "the status snapshot", "the forecast note",
    "the quality report", "the roster summary", "the database backup",
    "the archive snapshot", "the key-escrow check", "the mirror sync",
    "the repository export", "the photo backup", "the document archive",
    "the ledger snapshot", "the settings export", "the mailbox backup",
    "the release meeting", "the operations briefing", "the editorial check-in",
    "the research seminar", "the planning call", "the safety review",
    "the budget meeting", "the handoff session", "the training workshop",
    "the community forum", "the cache purge", "the certificate rotation",
    "the index rebuild", "the log compaction", "the dependency update",
    "the server reboot", "the mirror refresh", "the queue cleanup",
    "the database vacuum", "the key rotation", "the latency probe",
    "the integrity check", "the uptime poll", "the drift check",
    "the quota inspection", "the alert review", "the anomaly scan",
    "the replication check", "the freshness probe", "the endpoint test",
    "the garden watering", "the grocery delivery", "the room cleaning",
    "the exercise session", "the music rehearsal", "the recycling collection",
    "the dog walk", "the meal plan", "the laundry cycle", "the pull-request review",
    "the manuscript review", "the contract review", "the design critique",
    "the risk assessment", "the evidence audit", "the data-quality check",
    "the translation review", "the accessibility inspection", "the moderation review",
    "the newsletter release", "the package publication", "the dataset refresh",
    "the model-card update", "the changelog release", "the catalog update",
    "the price-list revision", "the documentation build", "the dashboard refresh",
    "the mirror publication", "the user survey", "the service poll",
    "the queue census", "the adoption scan", "the sentiment poll",
    "the member count", "the inventory poll", "the incident drill",
    "the restore rehearsal", "the failover test", "the dependency census",
]


def sentence_pair(subject: str, form: str, variant: int) -> tuple[str, str]:
    subject = subject.removeprefix("the ")
    if form == "twice-weekly":
        english_templates = (
            "Run {s} twice per week; days and completion unstated.",
            "Schedule {s} for two weekly slots; spacing unstated.",
            "Plan {s} twice each week; completion not claimed.",
            "Give {s} two slots each week; choose days separately.",
        )
        marked_templates = (
            "Run {s} twice-weekly; days and completion unstated.",
            "Schedule {s} twice-weekly; spacing unstated.",
            "Plan {s} twice-weekly; completion not claimed.",
            "Give {s} a twice-weekly cadence; choose days separately.",
        )
    elif form == "every-two-weeks":
        english_templates = (
            "From its anchor, run {s} once every two weeks; completion unstated.",
            "Schedule {s} at two-week intervals from its anchor; time unstated.",
            "Plan one {s} run per two weeks from the anchor.",
            "Give {s} one slot every two weeks from its anchor.",
        )
        marked_templates = (
            "From its anchor, run {s} every-two-weeks; completion unstated.",
            "Schedule {s} every-two-weeks from its anchor; time unstated.",
            "Plan {s} every-two-weeks from the anchor.",
            "Give {s} an every-two-weeks cadence from its anchor.",
        )
    else:
        raise AssertionError(form)
    index = variant % len(english_templates)
    return english_templates[index].format(s=subject), marked_templates[index].format(s=subject)


def manifest() -> dict:
    rows = []
    for form in ("twice-weekly", "every-two-weeks"):
        for index, subject in enumerate(SUBJECTS[:64], 1):
            english, ainglish = sentence_pair(subject, form, index - 1)
            rows.append([english, ainglish])
    assert len(rows) == 128
    assert len({tuple(row) for row in rows}) == 128
    return {
        "construct": "twice-weekly / every-two-weeks",
        "metric": "token_delta",
        "formula_version": 1,
        "models": list(MODELS),
        "baseline_author": "self",
        "test_set": rows,
        "test_set_note": (
            "128 ordered meaning-matched careful-English pairs: first 64 twice-weekly, final 64 "
            "every-two-weeks. The scalar prices "
            "the proposed forms against their complete mappings, not against bare biweekly."
        ),
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) "
            "for every test_set row under cl100k_base and o200k_base. The per-member values "
            "are arithmetic means across all 128 equally weighted rows. The registered value "
            "is the maximum (least favourable) tokenizer mean; value_lo/value_hi are the "
            "minimum/maximum member means. Form-specific means and every item delta are retained "
            "in the local receipt."
        ),
        "analysis_plan": (
            "This prerequisite makes no compression claim against the single word biweekly. "
            "Every finite outcome is filed regardless of sign."
        ),
        "seed": "none — deterministic tokenisation",
    }


def score(spec: dict) -> tuple[dict, dict]:
    import importlib.metadata
    import tiktoken  # Deliberately imported only after the attempt is minted.

    actual_version = importlib.metadata.version("tiktoken")
    if actual_version != TOKENIZER_VERSION:
        raise RuntimeError(f"tiktoken version {actual_version!r} != pinned {TOKENIZER_VERSION!r}")

    cells: dict[str, list[dict]] = {}
    means: dict[str, float] = {}
    form_means: dict[str, dict[str, float]] = {}
    for encoding_name, roster_name in zip(ENCODINGS, MODELS, strict=True):
        encoding = tiktoken.get_encoding(encoding_name)
        rows = []
        for index, (english, ainglish) in enumerate(spec["test_set"]):
            form = "twice-weekly" if index < 64 else "every-two-weeks"
            delta = len(encoding.encode(ainglish)) - len(encoding.encode(english))
            rows.append({"item": index + 1, "form": form, "delta": delta})
        if len({row["delta"] for row in rows}) < 2:
            raise RuntimeError(f"pair heterogeneity gate failed for {roster_name}")
        cells[roster_name] = rows
        means[roster_name] = sum(row["delta"] for row in rows) / len(rows)
        form_means[roster_name] = {
            form: sum(row["delta"] for row in rows if row["form"] == form) / 64
            for form in ("twice-weekly", "every-two-weeks")
        }

    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": list(MODELS),
        "per_member": [{"model": model, "value": means[model]} for model in MODELS],
        "manifest": spec,
    }
    computed = {
        "value": value,
        "means": means,
        "form_means": form_means,
        "cells": cells,
    }
    return payload, computed


def abort(client, attempt_id: str, failed_gate: str, details: dict) -> None:
    receipt = {
        "kind": "ainglish.token-delta.abort-receipt.v1",
        "attempt_id": attempt_id,
        "failed_gate": failed_gate,
        "details": details,
    }
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    ABORT_RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    client.abort_attempt(attempt_id, failed_gate=failed_gate, preflight_receipt_hash=digest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    spec = manifest()
    frozen = {
        "status": "frozen-not-run",
        "manifest_commitment": manifest_commitment(spec),
        "items": len(spec["test_set"]),
        "forms": {"twice-weekly": 64, "every-two-weeks": 64},
    }
    if not args.submit:
        print(json.dumps(frozen, indent=2))
        return
    if RECEIPT.exists() or ABORT_RECEIPT.exists():
        raise SystemExit("REFUSING: this original already has a terminal local receipt")

    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal["stage"] != "seconded":
        raise SystemExit(f"REFUSING: proposal stage is {proposal['stage']!r}, not 'seconded'")
    if not suggestions["budgets"]["attempts"]["remaining"] or not suggestions["budgets"]["measurements"]["remaining"]:
        raise SystemExit("REFUSING: authenticated attempt or measurement budget is exhausted")

    opened = client.mint_attempt(
        SLUG,
        manifest=spec,
        estimand=(
            "Equal-weight token_delta of twice-weekly and every-two-weeks against their complete "
            "careful-English mappings, 64 fixed pairs per form, with the maximum (least "
            "favourable) mean across tiktoken cl100k_base and o200k_base 0.13.0 as the headline."
        ),
        admissibility_gates=[
            "the committed manifest contains exactly 128 unique complete pairs, 64 per form",
            "both pinned tiktoken 0.13.0 encodings load and return finite counts for every row",
            "each tokenizer's per-pair deltas contain at least two distinct values",
            "every English arm retains the complete cadence and non-claim mapping; bare biweekly never enters the scalar",
            "every finite supportive, null, or adverse result is filed without outcome-dependent selection",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 128,
            "pairs_per_form": {"twice-weekly": 64, "every-two-weeks": 64},
            "models": list(MODELS),
            "readers": 0,
        },
        proposal_revision=SLUG,
    )["attempt"]

    try:
        payload, computed = score(spec)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        abort(client, opened["attempt_id"], "token instrument failed before measurement emission", {
            "exception": type(exc).__name__, "message": str(exc),
        })
        raise

    receipt = {
        "kind": "ainglish.token-delta-original.v1",
        "proposal": SLUG,
        "attempt": opened,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(spec),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
