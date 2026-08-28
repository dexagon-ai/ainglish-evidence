#!/usr/bin/env python3
"""File the deterministic bounded-prerequisite unclaimed-flip original once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
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


SLUG = "bounded-evidence-prerequisites-make-a-proposal-s-declared-me"
POPULATION = EVIDENCE_REPO / "evidence-contract-coherence-audit-2026-08-24" / "snapshot.json"
ACCEPTANCE = EVIDENCE_REPO / "bounded-prerequisites-deployment-acceptance-2026-08-24" / "receipt.json"
RECEIPT = ROOT / "receipt.json"
MODEL = "dexagon-independent-contract-replay-v1"


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs() -> tuple[dict, dict]:
    return json.loads(POPULATION.read_text()), json.loads(ACCEPTANCE.read_text())


def build_manifest(population: dict, acceptance: dict) -> dict:
    source_commit = git_output("rev-parse", "HEAD")
    return {
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [MODEL],
        "against": [
            {
                "kind": "legacy-contract-population",
                "url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{source_commit}/evidence-contract-coherence-audit-2026-08-24/snapshot.json",
                "sha256": digest(POPULATION),
                "generated_at": population["generated_at"],
            },
            {
                "kind": "deployment-acceptance-matrix",
                "url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{source_commit}/bounded-prerequisites-deployment-acceptance-2026-08-24/receipt.json",
                "sha256": digest(ACCEPTANCE),
                "computed_at": acceptance["checked_at"],
            },
            {
                "kind": "implementation",
                "repository": "ai-nglish/ainglish-symfony",
                "commit": "8b0eec0b730083e8a74d40b28c0bc2f4f8c7e038",
                "note": "prospective bounded-object branch; legacy string path retained",
            },
        ],
        "computed_at": acceptance["checked_at"],
        "population": {
            "live_rows": population["summary"]["live_proposals"],
            "declared_contracts": population["summary"]["declared_contracts"],
            "selection": population["source"],
        },
        "claimed_moves": [],
        "method": (
            "Load the two content-addressed public artifacts. For every declared contract in the "
            "population, count each prerequisite that is not a string: such a row would enter the "
            "new bounded branch and could move despite the filing's empty claimed_moves. Then count "
            "each runtime acceptance case whose accepted value differs from expected_accepted and "
            "one additional surface if the OpenAPI object union is not confined to prerequisites. "
            "The sum is unclaimed_verdict_flips. File every finite count."
        ),
        "analysis_plan": {
            "legacy_population": "all existing prerequisites must remain strings and therefore retain their legacy evaluation",
            "runtime_cases": "accepted must equal expected_accepted for every frozen case",
            "openapi": "claim_carrier has no object union; prerequisites has the object union",
            "aggregation": "integer sum of moved or mismatched verdict surfaces; no exclusions after mint",
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": source_commit,
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
        },
    }


def evaluate(population: dict, acceptance: dict) -> tuple[int, dict]:
    nonlegacy = []
    for row in population["contracts"]:
        for index, prerequisite in enumerate(row["contract"].get("prerequisites", [])):
            if not isinstance(prerequisite, str):
                nonlegacy.append({"slug": row["slug"], "index": index, "value": prerequisite})
    runtime_mismatches = [
        row for row in acceptance["cases"]
        if bool(row["accepted"]) != bool(row["expected_accepted"])
    ]
    openapi = acceptance["openapi"]
    openapi_mismatch = not (
        openapi.get("claim_carrier_declares_object") is False
        and openapi.get("prerequisites_declares_object") is True
        and openapi.get("matches_runtime_roles") is True
    )
    value = len(nonlegacy) + len(runtime_mismatches) + int(openapi_mismatch)
    return value, {
        "legacy_contracts": len(population["contracts"]),
        "nonlegacy_prerequisites": nonlegacy,
        "runtime_cases": len(acceptance["cases"]),
        "runtime_mismatches": runtime_mismatches,
        "openapi": openapi,
        "openapi_mismatch": openapi_mismatch,
        "unclaimed_verdict_flips": value,
    }


def preflight(client, manifest: dict, population: dict, acceptance: dict) -> dict:
    client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    me = client.me()["sub"]
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not seconded")
    existing = [
        row for row in proposal.get("measurements", [])
        if row.get("metric") == "unclaimed_verdict_flips" and row.get("evidence_state") == "valid"
    ]
    if existing:
        raise RuntimeError("a valid original already exists; stop instead of adding another")
    if (proposal.get("proposer") or {}).get("sub") == me:
        raise RuntimeError("this carrier is intended for a principal disjoint from the proposer")
    if population.get("content_sha256") is None or not population.get("contracts"):
        raise RuntimeError("population artifact is missing its content digest or contracts")
    if acceptance.get("schema") != "ainglish-bounded-prerequisite-deployment-acceptance/v1":
        raise RuntimeError("acceptance artifact has an unexpected schema")
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
        cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return {
        "proposal_stage": proposal["stage"],
        "existing_valid_originals": 0,
        "disjoint_from_proposer": True,
        "population_sha256": digest(POPULATION),
        "acceptance_sha256": digest(ACCEPTANCE),
        "manifest_commitment": manifest_commitment(manifest),
    }


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    evidence = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": checked,
    }
    return {
        "abort_sent": True,
        "result": client.abort_attempt(
            attempt_id, detail[:160], evidence, failed_gate_kind="harness_error",
        ),
    }


def main() -> None:
    client = ainglish_client()
    population, acceptance = load_inputs()
    manifest = build_manifest(population, acceptance)
    checked = preflight(client, manifest, population, acceptance)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists")

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "Unclaimed verdict surfaces under the bounded-prerequisite deployment, replayed over "
            "the complete frozen legacy-contract population plus the live non-mutating runtime "
            "and OpenAPI acceptance matrix; each legacy row entering the new branch or acceptance "
            "verdict mismatch counts once."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and proposal detail still route an original unclaimed_verdict_flips row on a seconded proposal",
            "no valid original exists and this principal is disjoint from the proposer",
            "both exact public input artifacts and this runner are committed and reachable from origin/main",
            "the population digest, runtime expectations, OpenAPI role assertions, and integer aggregation are frozen before evaluation",
            "every finite count is filed once, including a positive refutation",
        ],
        planned_sample={
            "legacy_contracts": len(population["contracts"]),
            "runtime_cases": len(acceptance["cases"]),
            "openapi_role_surfaces": 1,
            "instrument": MODEL,
        },
    )["attempt"]
    try:
        value, computed = evaluate(population, acceptance)
        filed = client.measure(SLUG, {
            "metric": "unclaimed_verdict_flips",
            "formula_version": 1,
            "value": value,
            "panel_models": [MODEL],
            "per_member": [{"model": MODEL, "value": value}],
            "panel_neff": 1,
            "manifest": manifest,
            "attempt_id": opened["attempt_id"],
        })
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise
    receipt = {
        "kind": "ainglish.unclaimed-verdict-flips-original.v1",
        "proposal": SLUG,
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
