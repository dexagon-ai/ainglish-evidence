#!/usr/bin/env python3
"""Compose the next three panel-ready flagship inputs without reader calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

SOURCES = {
    "acknowledgement-force": REPO / "flagship-comprehension-wave-v3-2026-08-29" / "activation-acknowledgement-force-claim-original.items.json",
    "role-cardinality": REPO / "flagship-comprehension-wave-v3-2026-08-29" / "activation-role-cardinality-claim-original.items.json",
    "will-panel": REPO / "modal-operational-comprehension-carriers-2026-08-25" / "panel" / "will.json",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_frozen(path: Path, value: object) -> None:
    rendered = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise SystemExit(f"REFUSING frozen-output drift: {path.name}")
    if not path.exists():
        path.write_text(rendered, encoding="utf-8")


def describe(slug: str, public_id: str, path: Path, rows: list[dict], source_commit: str, owner: str) -> dict:
    science = [row for row in rows if row.get("calibration") is not True]
    calibration = [row for row in rows if row.get("calibration") is True]
    return {
        "slug": slug,
        "public_id": public_id,
        "metric": "comprehension_accuracy_delta",
        "role": "claim_carrier_original",
        "items": str(path.relative_to(REPO)),
        "items_file_sha256": file_digest(path),
        "items_canonical_sha256": digest(rows),
        "source_commit": source_commit,
        "counts": {
            "scientific": len(science),
            "calibration": len(calibration),
            "forms": dict(sorted(Counter(row.get("form", "control") for row in science).items())),
        },
        "measurement_principal": owner,
        "reader_gate": "closed_pending_two_distinct_qualified_base_model_lineages",
    }


def main() -> None:
    acknowledgement = json.loads(SOURCES["acknowledgement-force"].read_text(encoding="utf-8"))
    role = json.loads(SOURCES["role-cardinality"].read_text(encoding="utf-8"))
    will_wrapper = json.loads(SOURCES["will-panel"].read_text(encoding="utf-8"))
    will_science = [row for row in will_wrapper["items"] if row.get("calibration") is not True]
    # Reuse the current target-independent planted-effect controls, not the older easy location
    # controls bundled with the 2026-08-25 carrier. Their reuse does not expose a proposal item.
    calibration = [row for row in acknowledgement if row.get("calibration") is True]
    assert len(calibration) == 24 and len(will_science) == 120
    will_rows = calibration + will_science
    will_path = ROOT / "activation-will-force-claim-original.items.json"
    write_frozen(will_path, will_rows)

    campaigns = {
        "acknowledgement-force": describe(
            "p-ack-as-receipt-r-p-ack-as-agreement-r",
            "a-ee2xyn4mk8kcanzt",
            SOURCES["acknowledgement-force"],
            acknowledgement,
            "8585535aa398021fc645783e7bd42c08c6869c46",
            "Dexagon or another eligible principal; proposer is Saturnia",
        ),
        "role-cardinality": describe(
            "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
            "a-twt7mcv776hnrz2f",
            SOURCES["role-cardinality"],
            role,
            "8585535aa398021fc645783e7bd42c08c6869c46",
            "an eligible principal independent of proposer Dexagon; Longcat holds the current handoff",
        ),
        "will-force": describe(
            "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2",
            "a-fxfcar77qrd3csq5",
            will_path,
            will_rows,
            "315515370027f7a5e697f279340eaad27041d5c4",
            "Dexagon or another eligible principal; proposer is Reticuli",
        ),
    }
    index = {
        "kind": "dexagon.ainglish.flagship-next-three-handoff.v1",
        "purpose": "three human-readable measured proposals one valid comprehension original away from evidence completion",
        "campaigns": campaigns,
        "qualification_kit": {
            "path": "remote-reader-qualification-v1-2026-08-29",
            "commit": "e66679ba1a347319e7f62c9dce634d32da481a56",
            "required": "two distinct base-model lineages pass one unchanged common holdout",
        },
        "composition": {
            "will_scientific_source": "modal-operational-comprehension-carriers-2026-08-25/panel/will.json",
            "will_calibration_source": "flagship-comprehension-wave-v3-2026-08-29/activation-acknowledgement-force-claim-original.items.json",
            "note": "the generated will file is pinned by raw and canonical digests; its scientific source commit is recorded on the campaign",
        },
        "model_downloads": 0,
        "model_calls": 0,
        "governance_writes": 0,
        "content_sha256": "",
    }
    index["content_sha256"] = digest({k: v for k, v in index.items() if k != "content_sha256"})
    write_frozen(ROOT / "index.json", index)
    print(json.dumps({
        "campaigns": len(campaigns),
        "scientific_items": sum(row["counts"]["scientific"] for row in campaigns.values()),
        "calibration_items": sum(row["counts"]["calibration"] for row in campaigns.values()),
        "content_sha256": index["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
