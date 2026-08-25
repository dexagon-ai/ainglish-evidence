#!/usr/bin/env python3
"""Run one fresh minimal-pair replication of the moved-* hyphen price."""

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


SLUG = "moved-earlier-moved-later-which-way-did-the-meeting-move"
TARGET_HASH = "b3b5cb796964bfd4b39db682d8d727d13d223833b96d6721e09c357c9e913cc8"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base"]
MODELS = [f"{name}@tiktoken-0.13.0" for name in ENCODINGS]
EVENTS = [
    "archive review", "harbour inspection", "orchard survey", "museum audit",
    "foundry shutdown", "courier collection", "theatre rehearsal", "aquarium census",
    "library handover", "observatory calibration", "bakery cleaning", "studio booking",
    "fleet briefing", "grant interview", "inventory recount", "habitat sampling",
]
TEST_SET = [
    {
        "cell": f"{event.replace(' ', '-')}/{'earlier' if index < 8 else 'later'}",
        "english": f"The {event} is moved {'earlier' if index < 8 else 'later'}.",
        "ainglish": f"The {event} is moved-{'earlier' if index < 8 else 'later'}.",
    }
    for index, event in enumerate(EVENTS)
]


def git_output(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=EVIDENCE_REPO, check=True, capture_output=True, text=True).stdout.strip()


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def build_manifest() -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "moved-earlier / moved-later minimal hyphen price replication",
        "models": MODELS,
        "test_set": TEST_SET,
        "estimand": {
            "population": "minimal schedule-direction statements whose careful control differs only by replacing the marker hyphen with one space",
            "aggregation": "equal-form balanced mean per tokenizer; report the larger tokenizer mean as least favourable",
        },
        "design": {
            "earlier_items": 8, "later_items": 8,
            "pair_difference": "each complete pair differs by exactly one space-to-hyphen substitution",
            "selection": "event nouns fixed before tokenizer import and absent from visible prior complete pairs",
        },
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) for every pair without special tokens. "
            "Average equally within each tokenizer and report the larger mean; value_lo/value_hi are the tokenizer minimum/maximum."
        ),
        "seed": "none - deterministic tokenisation",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence", "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit pushed before mint; every complete pair is embedded in the manifest",
        },
        "tokenizer_package": f"tiktoken-{importlib.metadata.version('tiktoken')}",
    }


def suggested_target(row: dict) -> bool:
    if row.get("replicates_hash") == TARGET_HASH and row.get("executable_now"):
        return True
    readiness = row.get("evidence_readiness") or {}
    return any(TARGET_HASH in (item.get("target_hashes") or []) for item in readiness.get("work_items") or [])


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    cards = [row for row in suggestions.get("suggestions", []) if row.get("slug") == SLUG and suggested_target(row)]
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("proposal is no longer a current measurement-stage surface")
    if not cards:
        raise RuntimeError("fresh authenticated suggestions no longer route work against this target")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not frozen 0.13.0")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid" or target.get("voided_at") is not None:
        raise RuntimeError("target is absent, invalid, voided, or no longer token_delta")
    if target.get("replication_count") != 0:
        raise RuntimeError("target acquired a replication while this carrier was prepared")
    if len(TEST_SET) != 16 or len(TEST_SET) & 15:
        raise RuntimeError("test_set must remain a power-of-two count of 16")
    ours = [pair_key(row) for row in TEST_SET]
    if len(set(ours)) != 16:
        raise RuntimeError("test_set contains duplicate complete pairs")
    for english, ainglish in ours:
        if english.replace(" moved ", " moved-") != ainglish:
            raise RuntimeError("a pair differs by more than the frozen space-to-hyphen edit")
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
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} pair(s)")
    source_path = str(Path(__file__).resolve().relative_to(EVIDENCE_REPO))
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", source_path], cwd=EVIDENCE_REPO).returncode:
        raise RuntimeError("committed source file differs from HEAD")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal["stage"], "target_hash": TARGET_HASH,
        "target_value": target.get("value"), "target_replication_count": 0,
        "fresh_complete_pairs": 16, "visible_prior_pairs": len(prior), "complete_pair_overlap": 0,
        "strata": {"earlier": 8, "later": 8},
        "source_commit": manifest["source"]["commit"], "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken  # deliberately after attempt mint

    cells = {}
    for name in ENCODINGS:
        encoding = tiktoken.get_encoding(name)
        cells[name] = [len(encoding.encode(row["ainglish"])) - len(encoding.encode(row["english"])) for row in TEST_SET]
    means = {name: round(sum(values) / len(values), 4) for name, values in cells.items()}
    value = max(means.values())
    payload = {
        "metric": "token_delta", "formula_version": 1,
        "value": value, "value_lo": min(means.values()), "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": model, "value": means[name]} for model, name in zip(MODELS, ENCODINGS)],
        "manifest": manifest, "replicates_hash": TARGET_HASH,
    }
    strata = {}
    for label, indexes in (("earlier", range(8)), ("later", range(8, 16))):
        strata[label] = {name: round(sum(cells[name][i] for i in indexes) / 8, 4) for name in ENCODINGS}
    return payload, {"cells": cells, "means": means, "strata": strata, "value": value}


def main() -> None:
    if RECEIPT.exists():
        raise SystemExit("REFUSING: receipt already exists; this run is one-shot")
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    opened = client.mint_attempt(
        SLUG, manifest=manifest,
        estimand="The least-favourable maximum, across cl100k_base and o200k_base, of equal-form balanced mean token_delta on sixteen fresh minimal pairs whose careful controls differ only by replacing the marker hyphen with a space.",
        admissibility_gates=[
            "fresh authenticated suggestions still route work against the valid unreplicated target",
            "all sixteen unique complete pairs are absent from every visible prior test_set and balance eight earlier/eight later",
            "every pair differs by exactly one space-to-hyphen substitution",
            "the source file is publicly committed before mint and the manifest embeds every pair",
            "both frozen tiktoken resources return finite integer counts",
            "every finite agreement or disagreement is filed once",
        ],
        planned_sample={"metric": "token_delta", "items": 16, "arms": 2, "earlier": 8, "later": 8, "tokenizers": MODELS},
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            abort = {"kind": "ainglish.token-replication-abort.v1", "at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}"}
            client.abort_attempt(opened["attempt_id"], "token replication raised after mint", abort, failed_gate_kind="harness_error")
        raise
    receipt = {
        "kind": "ainglish.moved-direction-token-replication.v1", "proposal": SLUG,
        "target_hash": TARGET_HASH, "attempt": opened, "preflight": checked,
        "computed": computed, "measurement": filed, "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
