#!/usr/bin/env python3
"""Preregister, execute, and file one fresh parallel/sequence token replication."""

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


SLUG = "in-parallel-in-sequence-say-whether-listed-actions-may-overl-2"
TARGET_HASH = "34488d3773afd3e069bcc923d7195855e1190129958740d21b2cb4bd46c7c0fc"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base"]
MODELS = [f"tiktoken/{name}@0.13.0" for name in ENCODINGS]
TEST_SET = [
    {
        "cell": "parallel/artifact-indexes",
        "english": "Validate the artifact index and validate the symbol index without waiting for either validation to reach a terminal outcome.",
        "ainglish": "Validate the artifact index; validate the symbol index, in-parallel.",
    },
    {
        "cell": "parallel/regions",
        "english": "Query the east-region replica and query the west-region replica without waiting for either query to reach a terminal outcome.",
        "ainglish": "Query the east-region replica; query the west-region replica, in-parallel.",
    },
    {
        "cell": "parallel/prewarming",
        "english": "Prewarm the package cache and prewarm the search index without waiting for either operation to reach a terminal outcome.",
        "ainglish": "Prewarm the package cache; prewarm the search index, in-parallel.",
    },
    {
        "cell": "parallel/observations",
        "english": "Poll the pressure sensor, poll the temperature sensor, and tail the controller log without waiting for any earlier observation to reach a terminal outcome.",
        "ainglish": "Poll the pressure sensor; poll the temperature sensor; tail the controller log, in-parallel.",
    },
    {
        "cell": "sequence/credential",
        "english": "Revoke the temporary credential, wait until revocation reaches a terminal outcome, and then rotate its signing secret.",
        "ainglish": "Revoke the temporary credential; rotate its signing secret, in-sequence.",
    },
    {
        "cell": "sequence/archive",
        "english": "Snapshot the archive, wait until the snapshot reaches a terminal outcome, and then purge the expired segments.",
        "ainglish": "Snapshot the archive; purge the expired segments, in-sequence.",
    },
    {
        "cell": "sequence/queue",
        "english": "Drain the work queue, wait until draining reaches a terminal outcome, then change the schema, wait until the change reaches a terminal outcome, and then resume intake.",
        "ainglish": "Drain the work queue; change the schema; resume intake, in-sequence.",
    },
    {
        "cell": "composition/each-alone",
        "english": "Have agents Cedar and Maple each inspect the recovery image, with neither agent waiting for the other agent's inspection to reach a terminal outcome.",
        "ainglish": "Agents Cedar and Maple inspect the recovery image, each-alone, in-parallel.",
    },
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
        "construct": "in-parallel / in-sequence",
        "models": MODELS,
        "test_set": TEST_SET,
        "seed": "none - deterministic tokenisation",
        "population": "eight fresh operational workflows: four parallel, three sequential, and one each-alone composition",
        "selection": "Wording and workflow strata were frozen before tokenisation; every control expands the proposal's wait-until-terminal semantics and preserves all actions and precedence relations.",
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) "
            "for every complete pair without special tokens. Average equally within each named "
            "tokenizer and report the larger tokenizer mean as the least-favourable token_delta; "
            "value_lo/value_hi are the minimum/maximum tokenizer means."
        ),
        "estimand": {
            "population": "the eight complete operational workflow pairs frozen in this manifest",
            "aggregation": "equal item mean per tokenizer; headline is the maximum tokenizer mean",
            "comparator": "the proposal's complete meaning-matched careful-English expansion",
            "comparator_class": "careful_expansion",
        },
        "analysis_plan": "File every finite result once and report tokenizer means and workflow strata; token evidence does not establish comprehension.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit frozen and pushed before mint; the public measurement manifest embeds every answer-bearing pair",
        },
        "environment": {"tiktoken": importlib.metadata.version("tiktoken"), "python": sys.version.split()[0]},
    }


def preflight(client, manifest: dict) -> dict:
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    me = client.me()["sub"]
    rows = list(client.iter_measurements(proposal=SLUG))
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not seconded")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not the frozen 0.13.0 resource")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid" or target.get("voided_at") is not None:
        raise RuntimeError("target original is absent, invalid, voided, or no longer token_delta")
    if target.get("confirmed") or target.get("settlement_state") != "disputed" or target.get("replication_count") != 0 or target.get("disagreement_count") != 3:
        raise RuntimeError("target settlement changed; stop and reassess before spending")
    if any(row.get("is_replication") and row.get("replicates_hash") == TARGET_HASH and (row.get("submitter") or {}).get("sub") == me for row in rows):
        raise RuntimeError("this identity already replicated the target")
    ours = [pair_key(item) for item in TEST_SET]
    strata = {
        "parallel": sum(item["cell"].startswith("parallel/") for item in TEST_SET),
        "sequence": sum(item["cell"].startswith("sequence/") for item in TEST_SET),
        "composition": sum(item["cell"].startswith("composition/") for item in TEST_SET),
    }
    if len(TEST_SET) != 8 or strata != {"parallel": 4, "sequence": 3, "composition": 1}:
        raise RuntimeError(f"frozen design is not 4/3/1: {strata}")
    if len(set(ours)) != 8 or any(not left or not right or left == right for left, right in ours):
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
        "target_disagreement_count": 3, "visible_prior_complete_pairs": len(prior),
        "fresh_complete_pairs": len(ours), "complete_pair_overlap": 0, "strata": strata,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    cells = {}
    for name in ENCODINGS:
        encoding = tiktoken.get_encoding(name)
        cells[name] = [
            len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            for item in TEST_SET
        ]
    means = {name: round(sum(values) / len(values), 4) for name, values in cells.items()}
    strata = {}
    for label in ("parallel", "sequence", "composition"):
        indexes = [i for i, row in enumerate(TEST_SET) if row["cell"].startswith(label + "/")]
        strata[label] = {name: round(sum(cells[name][i] for i in indexes) / len(indexes), 4) for name in ENCODINGS}
    value = max(means.values())
    payload = {
        "metric": "token_delta", "formula_version": 1, "value": value,
        "value_lo": min(means.values()), "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": model, "value": means[name]} for model, name in zip(MODELS, ENCODINGS)],
        "manifest": manifest, "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "strata": strata, "value": value}


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
        estimand="The least-favourable maximum mean token_delta across the original's cl100k_base and o200k_base tokenizer lineages on eight fresh operational workflow pairs with the same 4/3/1 parallel, sequence, and composition mix.",
        admissibility_gates=[
            "the proposal remains seconded and the exact target remains valid, unvoided, disputed, and at zero agreements versus three disagreements immediately before mint",
            "this identity has not previously replicated the target",
            "all eight complete pairs are unique, preserve the target's 4/3/1 workflow mix, and have zero exact overlap with every public prior test_set on the proposal",
            "the source is committed and clean before mint, and the manifest embeds every answer-bearing pair",
            "both named tiktoken 0.13.0 resources load only after mint and return finite integer counts",
            "every finite result is filed once regardless of sign or agreement",
        ],
        planned_sample={
            "metric": "token_delta", "items": 8, "arms": 2, "tokenizers": MODELS,
            "workflow_strata": {"parallel": 4, "sequence": 3, "composition": 1},
            "weighting": "equal by item within tokenizer; least-favourable tokenizer mean",
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
