#!/usr/bin/env python3
"""Capture the live proxy claim carrier and audit fresh-input independence by hash only."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2"
TARGET = "bcc7b1d1f3cc4c975755a9d2f36d72681a301e6e6584334efd7fa4dcc73dc29f"
ATTEMPT = "fe8156f7-8e2f-43cd-9886-6dc8028e7b28"
SOURCE = REPO / "proxy-comprehension-carrier-2026-08-25" / "careful-items.json"
SOURCE_COMMIT = "889675e897de4465afa90b2d3d0cdb649ec68af2"
PROJECTIONS = {
    "english_message": ("english",),
    "ainglish_message": ("ainglish",),
    "arm_pair": ("english", "ainglish"),
    "complete_item": ("english", "ainglish", "question", "options", "answer"),
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def science(rows: list[dict]) -> list[dict]:
    return [row for row in rows if not row.get("calibration")]


def projected_hashes(rows: list[dict], fields: tuple[str, ...]) -> set[str]:
    return {digest({field: row.get(field) for field in fields}) for row in rows}


def main() -> None:
    source_packet = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_rows = source_packet["items"]
    if digest(source_rows) != source_packet["sha256"]:
        raise SystemExit("REFUSING: prospective source packet digest drift")
    first_public = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:proxy-comprehension-carrier-2026-08-25/careful-items.json"],
        cwd=REPO, check=True, capture_output=True,
    ).stdout
    if first_public != SOURCE.read_bytes():
        raise SystemExit("REFUSING: source differs from its pre-original public commit")
    source_time = subprocess.run(
        ["git", "show", "-s", "--format=%aI", SOURCE_COMMIT],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout.strip()

    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    measurement = client.measurement(TARGET)
    original_manifest = client.attempt_manifest(ATTEMPT)
    work = [
        row for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        if row.get("metric") == "comprehension_accuracy_delta"
        and TARGET in (row.get("target_hashes") or [])
    ]
    if (
        proposal.get("stage") != "measured"
        or proposal.get("superseded_by")
        or measurement.get("manifest_hash") != TARGET
        or measurement.get("attempt_id") != ATTEMPT
        or measurement.get("metric") != "comprehension_accuracy_delta"
        or measurement.get("is_replication") is not False
        or measurement.get("settlement_state") != "awaiting"
        or measurement.get("replication_count") != 0
        or len(work) != 1
        or work[0].get("state") != "replicate_original"
    ):
        raise SystemExit("REFUSING: live proxy settlement target drift")
    if original_manifest.get("items_sha256") != measurement["manifest"]["items_sha256"]:
        raise SystemExit("REFUSING: original manifest digest surfaces disagree")

    with urllib.request.urlopen(original_manifest["items_url"], timeout=30) as response:
        remote = json.load(response)
    original_rows = remote["items"] if isinstance(remote, dict) else remote
    if digest(original_rows) != original_manifest["items_sha256"]:
        raise SystemExit("REFUSING: original public item population digest drift")

    source_science = science(source_rows)
    original_science = science(original_rows)
    overlap = {}
    for label, fields in PROJECTIONS.items():
        source_hashes = projected_hashes(source_science, fields)
        original_hashes = projected_hashes(original_science, fields)
        intersection = source_hashes & original_hashes
        overlap[label] = {
            "fields": list(fields),
            "source_unique": len(source_hashes),
            "original_unique": len(original_hashes),
            "overlap": len(intersection),
            "source_hash_set_sha256": digest(sorted(source_hashes)),
            "original_hash_set_sha256": digest(sorted(original_hashes)),
        }
        if intersection:
            raise SystemExit(f"REFUSING: {label} overlaps the target original")

    original_at = measurement["attempt"]["created_at"]
    if datetime.fromisoformat(source_time) >= datetime.fromisoformat(original_at):
        raise SystemExit("REFUSING: prospective source was not public before the original attempt")
    snapshot = {
        "kind": "dexagon.ainglish.proxy-settlement-target-snapshot.v1",
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal": {
            "slug": proposal["slug"],
            "public_id": proposal["public_id"],
            "stage": proposal["stage"],
            "work_state": work[0]["state"],
        },
        "target": {
            "manifest_hash": TARGET,
            "attempt_id": ATTEMPT,
            "metric": measurement["metric"],
            "value": measurement["value"],
            "arms": measurement["arms"],
            "settlement_state": measurement["settlement_state"],
            "replication_count": measurement["replication_count"],
            "construct": original_manifest["construct"],
            "comparator": original_manifest["comparator"],
            "items_sha256": original_manifest["items_sha256"],
            "items_url": original_manifest["items_url"],
            "scientific_items": len(original_science),
            "calibration_items": len(original_rows) - len(original_science),
            "models": original_manifest["models"],
            "original_panel_family_fragments": ["qwen", "gemma", "ornith"],
            "created_at": original_at,
        },
        "prospective_source": {
            "path": str(SOURCE.relative_to(REPO)),
            "first_public_commit": SOURCE_COMMIT,
            "first_public_at": source_time,
            "items_sha256": source_packet["sha256"],
            "scientific_items": len(source_science),
            "calibration_items": len(source_rows) - len(source_science),
            "public_before_original": True,
        },
        "input_disjointness": overlap,
        "original_answer_bearing_inputs": {
            "opened_by_automated_hash_audit": True,
            "text_printed_or_persisted": False,
        },
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = digest(snapshot)
    (ROOT / "snapshot.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "target": TARGET,
        "source_scientific_items": len(source_science),
        "original_scientific_items": len(original_science),
        "all_overlap_counts": {key: row["overlap"] for key, row in overlap.items()},
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
