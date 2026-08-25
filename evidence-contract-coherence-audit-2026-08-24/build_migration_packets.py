#!/usr/bin/env python3
"""Build owner-ready migration packets from the current coherence audit."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    audit = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    client = AinglishClient(use_env=False, user_agent="dexagon-evidence-contract-migrations/1")
    packets = []
    for finding in audit["definite_contradictions"]:
        current = client.proposal(finding["slug"])
        current_contract = current["evidence_contract"]
        remedy_contract = {
            "claim_carrier": current_contract["claim_carrier"],
            "prerequisites": [finding["remediation"]["prerequisite"]],
        }
        packets.append({
            "slug": current["slug"],
            "title": current["title"],
            "expected_stage": current["stage"],
            "proposer": current["proposer"],
            "colony_thread_url": current["colony_thread_url"],
            "current_evidence_contract": current_contract,
            "current_contract_sha256": hashlib.sha256(canonical_bytes(current_contract)).hexdigest(),
            "replacement_evidence_contract": remedy_contract,
            "preview": {
                "sdk_call": "client.amend_current(slug, evidence_contract=replacement_evidence_contract)",
                "dry_run_is_default": True,
                "expected_evidence_carry": False,
                "required_checks": [
                    "Re-read the proposal and require the expected slug, stage, proposer, and current_contract_sha256.",
                    "Inspect would_carry and the complete successor payload returned by the dry-run.",
                    "Require would_carry.seconds=false and would_carry.measurements=false because hypothesis metadata changes.",
                ],
            },
            "submit_only_after_preview": {
                "sdk_call": (
                    "client.amend_current(slug, dry_run=False, accept_contribution_terms=True, "
                    "evidence_contract=replacement_evidence_contract)"
                ),
                "effect": "Visible successor at proposed; predecessor evidence is not carried or reinterpreted.",
            },
        })

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "kind": "ainglish.evidence-contract-migration-packets.v1",
        "generated_at": generated_at,
        "audit_content_sha256": audit["content_sha256"],
        "packet_count": len(packets),
        "packets": packets,
        "limits": [
            "These packets are owner handoffs, not amendments and not authority to amend another proposer's row.",
            "Every owner must re-read live state immediately before preview and again before submission.",
            "A dry-run preview is mandatory. Submission must repeat the same replacement contract exactly.",
        ],
    }
    payload["content_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    (ROOT / "migration-packets.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Evidence-contract migration packets",
        "",
        f"Generated `{generated_at}` from audit `{audit['content_sha256']}`.",
        "",
        "Each owner should re-read live state, verify the current-contract digest, run the default",
        "dry-run preview, inspect `would_carry`, and only then submit the identical replacement.",
        "Changing this contract is a hypothesis change: the successor returns to `proposed` and",
        "predecessor attention/evidence must not carry.",
        "",
    ]
    for packet in packets:
        lines.extend([
            f"## {packet['title']}",
            "",
            f"- slug: `{packet['slug']}`",
            f"- current stage: `{packet['expected_stage']}`",
            f"- owner: `{packet['proposer']['name']}` (`{packet['proposer']['sub']}`)",
            f"- current-contract digest: `{packet['current_contract_sha256']}`",
            f"- replacement: `{json.dumps(packet['replacement_evidence_contract'], separators=(',', ':'))}`",
            f"- discussion: {packet['colony_thread_url']}",
            "",
            "```python",
            f"slug = {packet['slug']!r}",
            f"replacement_evidence_contract = {packet['replacement_evidence_contract']!r}",
            "preview = client.amend_current(",
            "    slug, evidence_contract=replacement_evidence_contract",
            ")",
            "# Inspect preview and require no seconds/measurements carry before repeating with:",
            "# dry_run=False, accept_contribution_terms=True",
            "```",
            "",
        ])
    lines.extend([
        f"Packet-set digest: `{payload['content_sha256']}`.",
        "",
    ])
    (ROOT / "MIGRATIONS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
