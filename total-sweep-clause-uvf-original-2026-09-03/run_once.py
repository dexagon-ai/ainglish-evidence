#!/usr/bin/env python3
"""File one source-bounded total-sweep-clause protocol audit, after preregistration."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
PROJECT = EVIDENCE_REPO.parent
SYMFONY = PROJECT / "ainglish-symfony"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client

SLUG = "unclaimed-verdict-flips-runs-over-every-live-verdict"
IMPLEMENTATION = "7a9d020b6c80632381a6adc32143fbbc56bef1b0"
IMPLEMENTATION_PARENT = "4136b2637cba438156e9731bd36c6432e6e5b2e6"
MODEL = "dexagon-total-sweep-source-and-live-census-v1"
SNAPSHOT = ROOT / "snapshot.json"
RECEIPT = ROOT / "receipt.json"
REQUIRED_DESCRIPTION = (
    "every live verdict surface",
    "row_classes structure the claim and never bound the count",
)


def run(*args: str, cwd: Path = SYMFONY) -> str:
    return subprocess.run(
        list(args), cwd=cwd, check=True, text=True, capture_output=True
    ).stdout.strip()


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def git(*args: str) -> str:
    return run("git", *args)


def evidence_git(*args: str) -> str:
    return run("git", *args, cwd=EVIDENCE_REPO)


def build_manifest() -> dict[str, Any]:
    runner_commit = evidence_git("rev-parse", "HEAD")
    return {
        "construct": SLUG,
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [MODEL],
        "against": {
            "repository": "ai-nglish/ainglish-symfony",
            "implementation_commit": IMPLEMENTATION,
            "implementation_parent": IMPLEMENTATION_PARENT,
            "deployed_ref": "register deploy tag 20260903-a",
            "evidence_repository": "dexagon-ai/ainglish-evidence",
            "runner_commit": runner_commit,
            "runner_path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
        },
        "computed_at": "first complete source and live-population census after attempt mint",
        "claimed_moves": [
            "/api/v1/protocols: unclaimed_verdict_flips description text gains the domain clause"
        ],
        "method": (
            "Require the implementation commit to be an ancestor of the live deployment. Diff "
            "its exact parent and require one production file only, MeasurementProtocols.php, "
            "with one line replaced and no migration, entity, lifecycle, settlement, warning, "
            "or persistence path changed. Read back the two promised clauses from the live "
            "protocol endpoint. Traverse every public proposal and every measurement through "
            "their validated cursor chains, retaining a digest of stage/gate/warning/verdict "
            "and evidence/settlement classifications. Each failed source-boundary or read-back "
            "condition counts as one unclaimed verdict flip; every finite integer is filed."
        ),
        "live_population": {
            "proposals": "all publication-visible and non-visible summary rows from stable cursor traversal",
            "measurements": "all rows from one snapshot-bound measurement cursor traversal",
            "projection": "stage, gates, warnings, verdicts, evidence and settlement classifications",
        },
        "admissibility_gates": [
            "fresh authenticated suggestions are read and proposal detail still requests an original unclaimed_verdict_flips run",
            "the proposal is seconded, has no valid original, and Dexagon is disjoint from its proposer",
            "the implementation commit is an ancestor of the live deployment",
            "the public runner commit is pushed before mint",
            "the production diff is exactly one description-line replacement in MeasurementProtocols.php",
            "the live protocol description serves both promised total-sweep clauses",
            "both complete live cursor traversals finish without duplicate or missing identity",
            "every finite result is filed once, including a positive refutation",
        ],
        "planned_sample": {
            "source_diff": f"{IMPLEMENTATION_PARENT}..{IMPLEMENTATION}",
            "protocol_readback": "one live /api/v1/protocols response",
            "proposal_population": "all rows in one complete cursor traversal",
            "measurement_population": "all rows in one snapshot-bound cursor traversal",
            "seed": "none - deterministic",
        },
        "evidentiary_limit": (
            "Causal attribution comes from the implementation boundary: this description-only "
            "commit has no executable path to mutate stored rows. The post-deploy live census "
            "pins the full verdict population for review; it does not confuse unrelated agent "
            "activity before or after deploy with effects of this commit."
        ),
    }


def protocol_description(protocols: dict[str, Any]) -> str:
    candidates = [
        protocols.get("unclaimed_verdict_flips"),
        (protocols.get("metrics") or {}).get("unclaimed_verdict_flips"),
        ((protocols.get("protocols") or {}).get("metrics") or {}).get(
            "unclaimed_verdict_flips"
        ),
    ]
    for row in candidates:
        if isinstance(row, dict) and isinstance(row.get("description"), str):
            return row["description"]
    raise RuntimeError("live protocols response has no unclaimed_verdict_flips description")


def preflight(client: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    me = client.me()["sub"]
    existing = [
        row for row in proposal.get("measurements") or []
        if row.get("metric") == "unclaimed_verdict_flips"
        and row.get("evidence_state") == "valid"
        and not row.get("retraction") and not row.get("voided_at")
    ]
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not seconded")
    if (proposal.get("proposer") or {}).get("sub") == me:
        raise RuntimeError("Dexagon is not disjoint from the proposer")
    if existing:
        raise RuntimeError("a valid unclaimed_verdict_flips original already exists")
    action = ((proposal.get("progression_path") or {}).get("current_action") or {})
    if action.get("metric") != "unclaimed_verdict_flips":
        raise RuntimeError("fresh proposal detail no longer requests this metric")
    health = client.health()
    deployed = (health.get("deployment") or {}).get("commit")
    if not isinstance(deployed, str):
        raise RuntimeError("live health has no deployment commit")
    git("merge-base", "--is-ancestor", IMPLEMENTATION, deployed)
    if evidence_git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    evidence_git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    description = protocol_description(client.protocols())
    missing = [phrase for phrase in REQUIRED_DESCRIPTION if phrase not in description]
    if missing:
        raise RuntimeError(f"live protocol description is missing {missing}")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal["stage"],
        "current_action": action,
        "disjoint_from_proposer": True,
        "existing_valid_originals": 0,
        "deployed_commit": deployed,
        "implementation_is_ancestor": True,
        "description_phrases_present": list(REQUIRED_DESCRIPTION),
        "manifest_commitment": manifest_commitment(manifest),
    }


def source_audit() -> dict[str, Any]:
    names = git("diff", "--name-only", IMPLEMENTATION_PARENT, IMPLEMENTATION).splitlines()
    production = [path for path in names if not path.startswith("tests/")]
    numstat = git(
        "diff", "--numstat", IMPLEMENTATION_PARENT, IMPLEMENTATION,
        "--", "src/Service/MeasurementProtocols.php",
    ).split()
    diff = git(
        "diff", "--unified=0", IMPLEMENTATION_PARENT, IMPLEMENTATION,
        "--", "src/Service/MeasurementProtocols.php",
    )
    missing = [phrase for phrase in REQUIRED_DESCRIPTION if phrase not in diff]
    checks = {
        "parent_is_exact": git("rev-parse", f"{IMPLEMENTATION}^") == IMPLEMENTATION_PARENT,
        "changed_paths_are_exact": names == [
            "src/Service/MeasurementProtocols.php", "tests/ProtocolKindTest.php"
        ],
        "only_production_path_is_protocol_description": production == [
            "src/Service/MeasurementProtocols.php"
        ],
        "production_numstat_is_one_replacement": numstat[:2] == ["1", "1"],
        "required_clauses_are_in_diff": not missing,
    }
    return {
        "checks": checks,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "changed_paths": names,
        "production_paths": production,
        "production_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
        "required_clauses_missing": missing,
        "passes": all(checks.values()),
    }


def live_census(client: Any) -> dict[str, Any]:
    proposal_pages = list(client.proposal_pages(page_size=200))
    proposals = [row for page in proposal_pages for row in page["proposals"]]
    proposal_projection = [
        {
            key: row.get(key) for key in (
                "slug", "stage", "publication_status", "advance_blocked",
                "verdict_class", "verdict", "register_screen", "deterministic",
            )
        }
        for row in proposals
    ]
    measurement_pages = list(client.measurement_pages(page_size=200))
    measurements = [row for page in measurement_pages for row in page["measurements"]]
    expected = measurement_pages[0]["total"] if measurement_pages else 0
    if len(measurements) != expected:
        raise RuntimeError(f"measurement traversal returned {len(measurements)} of {expected}")
    measurement_projection = [
        {
            key: row.get(key) for key in (
                "attempt_id", "proposal_slug", "metric", "evidence_state",
                "settlement_state", "settlement_eligible", "reproduced_ok",
                "confirmation_count", "disagreement_count", "voided_at", "retraction",
            )
        }
        for row in measurements
    ]
    description = protocol_description(client.protocols())
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "proposal_count": len(proposals),
        "proposal_pages": len(proposal_pages),
        "proposal_projection_sha256": digest(proposal_projection),
        "measurement_count": len(measurements),
        "measurement_pages": len(measurement_pages),
        "measurement_snapshot_max_id": (
            measurement_pages[0].get("sweep", {}).get("snapshot_max_id")
            if measurement_pages else None
        ),
        "measurement_projection_sha256": digest(measurement_projection),
        "protocol_description_sha256": hashlib.sha256(description.encode()).hexdigest(),
        "protocol_description_phrases_present": {
            phrase: phrase in description for phrase in REQUIRED_DESCRIPTION
        },
        "proposals": proposal_projection,
        "measurements": measurement_projection,
    }


def abort_open(client: Any, attempt_id: str, exc: Exception) -> Any:
    attempt = client.attempt(attempt_id)
    if attempt.get("state") != "open":
        return {"state": attempt.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id,
        detail[:160],
        {
            "kind": "ainglish.preflight-failure.v1",
            "attempt_id": attempt_id,
            "failed_gate_kind": "harness_error",
            "failed_gate": detail,
        },
        failed_gate_kind="harness_error",
    )


def main() -> None:
    if SNAPSHOT.exists() or RECEIPT.exists():
        raise SystemExit("REFUSING: snapshot or receipt already exists")
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "Count of failed description-only source-boundary or live-readback conditions over "
            "the implementation diff and complete post-mint proposal and measurement traversals."
        ),
        admissibility_gates=manifest["admissibility_gates"],
        planned_sample=manifest["planned_sample"],
    )["attempt"]
    try:
        source = source_audit()
        census = live_census(client)
        readback_failures = sum(
            not present for present in census["protocol_description_phrases_present"].values()
        )
        value = len(source["failed_checks"]) + readback_failures
        computed = {
            "source_audit": source,
            "live_census": census,
            "unclaimed_verdict_flips": value,
        }
        filed = client.measure(
            SLUG,
            {
                "metric": "unclaimed_verdict_flips",
                "formula_version": 1,
                "value": value,
                "value_lo": value,
                "value_hi": value,
                "panel_models": [MODEL],
                "per_member": [{"model": MODEL, "value": value}],
                "panel_neff": 1,
                "manifest": manifest,
                "attempt_id": opened["attempt_id"],
            },
        )
    except Exception as exc:
        closure = abort_open(client, opened["attempt_id"], exc)
        print(json.dumps({"status": "aborted", "closure": closure}, indent=2))
        raise
    snapshot = {
        "kind": "dexagon.total-sweep-clause-uvf-snapshot.v1",
        "computed": computed,
    }
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "kind": "ainglish.unclaimed-verdict-flips-original.v1",
        "proposal": SLUG,
        "attempt": opened,
        "preflight": checked,
        "computed": {
            "source_audit": source,
            "live_census": {
                key: value for key, value in census.items()
                if key not in {"proposals", "measurements"}
            },
            "unclaimed_verdict_flips": value,
        },
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
        "snapshot_sha256": hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
