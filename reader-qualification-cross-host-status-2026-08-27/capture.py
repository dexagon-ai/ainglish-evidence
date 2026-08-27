#!/usr/bin/env python3
"""Verify and summarize the retained local and cross-host reader status."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
COMMIT = "834f966e9627392053c0651573b2c4738f2f14e1"
BASE = f"https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/{COMMIT}/command-r-35b-reader-development-2026-08-27"
FILES = {
    "plan": "command-r-35b-202408-development-v2-plan.json",
    "result": "command-r-35b-202408-development-v2-result.json",
    "audit": "command-r-35b-202408-development-v2-audit.json",
    "research": "research.json",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verified_local(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: local digest drift in {path}: {actual} != {expected}")
    return value


def verified_remote(name: str) -> dict:
    url = f"{BASE}/{FILES[name]}"
    request = urllib.request.Request(url, headers={"User-Agent": "dexagon-reader-status/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.load(response)
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: remote digest drift in {url}: {actual} != {expected}")
    return value


def main() -> None:
    plan = verified_remote("plan")
    result = verified_remote("result")
    audit = verified_remote("audit")
    research = verified_remote("research")
    local = verified_local(EVIDENCE / "reader-qualification-on-disk-audit-2026-08-27/audit.json")
    if result["plan_sha256"] != plan["content_sha256"] or audit["plan_sha256"] != plan["content_sha256"]:
        raise SystemExit("REFUSING: Command R result/audit lost the frozen plan")
    if audit["result"]["content_sha256"] != result["content_sha256"]:
        raise SystemExit("REFUSING: Command R audit does not bind the served result")
    semantic = result["semantic"]["observed"]
    if not result["format"]["passed"] or result["semantic"]["passed"] or result["v8_holdout_eligible"]:
        raise SystemExit("REFUSING: served Command R gate state differs from the retained terminal failure")
    selected = next(row for row in research["candidates"] if row.get("selected"))
    status = {
        "kind": "dexagon.ainglish.reader-qualification-cross-host-status.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "local_inventory": {
            "source": "reader-qualification-on-disk-audit-2026-08-27/audit.json",
            "source_sha256": local["content_sha256"],
            "installed_tags": len(local["artifacts"]),
            "installed_lineages": len(local["lineages"]),
            "qualification_state": local["qualification_state"],
        },
        "command_r_35b": {
            "repository": "reticuli-labs/panel-artifacts",
            "commit": COMMIT,
            "research_sha256": research["content_sha256"],
            "plan_sha256": plan["content_sha256"],
            "result_sha256": result["content_sha256"],
            "audit_sha256": audit["content_sha256"],
            "lineage": result["candidate"]["lineage"],
            "source_model": result["candidate"]["source_model"],
            "source_manifest_sha256": result["candidate"]["source_manifest_sha256"],
            "prospectively_selected": selected["source_model"] == result["candidate"]["source_model"],
            "format": result["format"]["observed"],
            "format_passed": result["format"]["passed"],
            "semantic": semantic,
            "semantic_required": {"total": 22, "per_axis": 2, "per_label": 6},
            "semantic_passed": result["semantic"]["passed"],
            "v8_holdout_eligible": result["v8_holdout_eligible"],
            "terminal_status": "failed-development-no-retry",
            "failure_shape": "six not-determined cells were answered entailed; one entailed cell was answered contradicted",
        },
        "qualification_state": {
            "qualified_distinct_lineages": 1,
            "required_distinct_lineages": 2,
            "roster_ready": False,
            "newly_qualified_lineages": 0,
        },
        "next_selection": {
            "run_authorised": False,
            "reason": "Aya Expanse shares the failed Command family, and Yi 1.5 34B already failed the retained v9 development gate. The old ranking is exhausted for a distinct second lineage.",
            "required_action": "Freeze a new prospective research ranking under the existing host envelope, excluding every qualified or terminally failed broad lineage and prioritising calibrated underdetermination over format strength; publish the selected artifact digest before any call.",
        },
        "claim_boundaries": [
            "This is reader-development evidence, never proposal evidence.",
            "Format success does not establish semantic qualification.",
            "A larger edition of a failed Command model is not a new independent lineage.",
            "Failed development cells are burned; do not retry or tune them.",
        ],
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    }
    status["content_sha256"] = hashlib.sha256(canonical(status)).hexdigest()
    (ROOT / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": status["captured_at"],
        "command_r_format": "pass",
        "command_r_semantic": f"{semantic['correct_cells']}/24 fail",
        **status["qualification_state"],
        "content_sha256": status["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
