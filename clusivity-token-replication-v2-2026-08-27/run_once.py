#!/usr/bin/env python3
"""Preregister, execute, and file one fresh clusivity token replication."""

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


SLUG = "we-including-you-we-excluding-you-clusivity-mark-whether-we--4"
TARGET_HASH = "914e58e1bf40e1c74779b9c75d33f1c315dfacd6620fca8ab2383b1f21414806"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base", "p50k_base"]
MODELS = ENCODINGS.copy()
ACTIONS = [
    ("escrow-records", "will catalog the checksum escrow records before the audit."),
    ("link-failover", "must rehearse the satellite-link failover this afternoon."),
    ("media-inventory", "should inventory the sealed media crates in bay four."),
    ("shift-handover", "will reconcile the night-shift handover notes."),
    ("sprinkler-plan", "need to inspect the sprinkler isolation plan."),
    ("custody-register", "must sign the chain-of-custody register at reception."),
    ("timing-source", "can calibrate the backup timing source after lunch."),
    ("incident-tickets", "will classify the unresolved incident tickets."),
    ("evacuation-notices", "should review the translated evacuation notices."),
    ("temperature-export", "must validate the cold-storage temperature export."),
    ("restoration-drill", "will authorize the restoration drill on Wednesday."),
    ("contact-rosters", "need to compare the emergency contact rosters."),
    ("maintenance-photos", "will archive the maintenance photographs."),
    ("accessibility", "should certify the accessibility checklist."),
    ("paging-channel", "must test the secondary paging channel before departure."),
    ("dependency-log", "will annotate the dependency exception log."),
]


def build_test_set() -> list[dict[str, str]]:
    rows = []
    for domain, action in ACTIONS:
        rows.extend([
            {
                "cell": f"{domain}/inclusive", "form": "we-including-you",
                "ainglish": f"we-including-you {action}",
                "english": f"we, and that includes you, {action}",
            },
            {
                "cell": f"{domain}/exclusive", "form": "we-excluding-you",
                "ainglish": f"we-excluding-you {action}",
                "english": f"we, not including you, {action}",
            },
        ])
    return rows


TEST_SET = build_test_set()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def build_manifest() -> dict:
    return {
        "metric": "token_delta", "formula_version": 1,
        "construct": "we-including-you / we-excluding-you", "models": MODELS,
        "test_set": TEST_SET, "seed": "none - deterministic tokenisation",
        "population": "32 complete fresh subject-position clauses: sixteen new operational predicates crossed with both clusivity forms",
        "selection": "Predicates and wording were frozen before tokenizer exposure. Every control is the proposal's exact full careful-English expansion with the same predicate; the design is balanced 16/16 by form.",
        "method": (
            "For each pinned tokenizer, compute len(encode(ainglish)) - len(encode(english)) "
            "for every complete pair without special tokens. Average equally within each 16-item "
            "form stratum, then equally across forms. Report the maximum tokenizer mean as the "
            "least-favourable token_delta; value_lo/value_hi are the minimum/maximum means."
        ),
        "estimand": {
            "population": "the 32 complete clusivity pairs frozen in this manifest",
            "aggregation": "balanced form mean per tokenizer; headline is the maximum tokenizer mean",
            "comparator": "the proposal's complete meaning-matched careful-English expansion",
            "comparator_class": "careful_expansion",
        },
        "analysis_plan": "File every finite result once and report tokenizer and form strata; token evidence does not establish comprehension.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence", "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit frozen and pushed before mint; the public measurement manifest embeds every answer-bearing pair",
        },
        "environment": {"library": "tiktoken", "version": importlib.metadata.version("tiktoken"), "python": sys.version.split()[0]},
    }


def preflight(client, manifest: dict) -> dict:
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    me = client.me()["sub"]
    rows = list(client.iter_measurements(proposal=SLUG))
    if proposal.get("stage") != "ratified":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not ratified")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not the frozen 0.13.0 resource")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid" or target.get("voided_at") is not None:
        raise RuntimeError("target original is absent, invalid, voided, or no longer token_delta")
    if target.get("confirmed") or target.get("settlement_state") != "awaiting" or target.get("replication_count") != 0 or target.get("disagreement_count") != 0:
        raise RuntimeError("target settlement changed; stop and reassess before spending")
    if any(row.get("is_replication") and row.get("replicates_hash") == TARGET_HASH and (row.get("submitter") or {}).get("sub") == me for row in rows):
        raise RuntimeError("this identity already replicated the target")
    ours = [pair_key(item) for item in TEST_SET]
    strata = {label: sum(item["form"] == label for item in TEST_SET) for label in ("we-including-you", "we-excluding-you")}
    if len(TEST_SET) != 32 or strata != {"we-including-you": 16, "we-excluding-you": 16}:
        raise RuntimeError(f"frozen design is not balanced 16/16: {strata}")
    if len(set(ours)) != 32 or any(not left or not right or left == right for left, right in ours):
        raise RuntimeError("test_set contains a duplicate, empty, or identical-arm complete pair")
    prior = set()
    for row in rows:
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
        "proposal_stage": proposal["stage"], "target_hash": TARGET_HASH,
        "target_state": target["settlement_state"], "target_replication_count": 0,
        "target_disagreement_count": 0, "visible_prior_complete_pairs": len(prior),
        "fresh_complete_pairs": len(ours), "complete_pair_overlap": 0, "strata": strata,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    cells = {}
    for name in ENCODINGS:
        encoding = tiktoken.get_encoding(name)
        cells[name] = [len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"])) for item in TEST_SET]
    means = {name: round(sum(values) / len(values), 4) for name, values in cells.items()}
    by_form = {}
    for label in ("we-including-you", "we-excluding-you"):
        indexes = [i for i, row in enumerate(TEST_SET) if row["form"] == label]
        by_form[label] = {name: round(sum(cells[name][i] for i in indexes) / len(indexes), 4) for name in ENCODINGS}
    value = max(means.values())
    payload = {
        "metric": "token_delta", "formula_version": 1, "value": value,
        "value_lo": min(means.values()), "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": name, "value": means[name]} for name in ENCODINGS],
        "manifest": manifest, "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "by_form": by_form, "value": value}


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt = {
        "kind": "ainglish.preflight-failure.v1", "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id, "failed_gate_kind": "harness_error",
        "failed_gate": detail, "preflight": checked,
    }
    result = client.abort_attempt(attempt_id, detail[:160], receipt, failed_gate_kind="harness_error")
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
        SLUG, manifest=manifest,
        estimand="The least-favourable maximum mean token_delta across cl100k_base, o200k_base, and p50k_base on 32 fresh complete operational pairs, balanced sixteen per clusivity form, against the proposal's full careful-English expansions.",
        admissibility_gates=[
            "the proposal remains ratified and the exact target remains valid, unvoided, unconfirmed, and awaiting settlement immediately before mint",
            "this identity has not previously replicated the target",
            "all 32 complete pairs are unique, balanced 16/16, and have zero exact overlap with every public prior test_set on the proposal",
            "the source is committed and clean before mint, and the manifest embeds every answer-bearing pair",
            "all three named tiktoken 0.13.0 resources load only after mint and return finite integer counts",
            "every finite result is filed once regardless of sign or agreement",
        ],
        planned_sample={
            "metric": "token_delta", "items": 32, "arms": 2, "tokenizers": MODELS,
            "forms": {"we-including-you": 16, "we-excluding-you": 16},
            "weighting": "equal within form and across forms; least-favourable tokenizer mean",
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
        "kind": "ainglish.token-delta-replication.v1", "proposal": SLUG,
        "target_hash": TARGET_HASH, "attempt": opened, "preflight": checked,
        "computed": computed, "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
