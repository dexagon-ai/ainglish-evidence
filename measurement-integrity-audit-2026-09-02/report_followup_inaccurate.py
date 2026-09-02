#!/usr/bin/env python3
"""Report the post-audit deterministic contradictions found after the first review wave."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import tiktoken


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from local_colony_auth import ainglish_client  # noqa: E402


EXPECTED = {
    "15d5d9870eee138e0e01487a01108958b94320fadf075d81097491ca5f844a80",
    "5298f058637fc7ed2118b14917fd22f50c247ca290dddcd1e53508848f5ca939",
    "56d5e336eaffe26301ce32f93e3873dde9e7d472cae5ee8e6927e57b73b73c33",
    "5f99679193608a956be6b1636d2e1a0d28dd11509591505110d23b1dc0cb10ae",
    "de9d54819e71c341c0ebe4109d2df8d7f7131aaef943519cd874041c337f237c",
    "fc30650718c9c51fb4afef33f84c29facd34cc757862a8404a4ab610823b7f73",
}


def recompute(row: dict) -> list[dict]:
    items = row["manifest"]["test_set"]
    known = set(tiktoken.list_encoding_names())
    values = []
    for member in row["per_member"]:
        model = member["model"]
        if model not in known:
            raise SystemExit(f"REFUSING: cannot recompute tokenizer {model!r}")
        encoder = tiktoken.get_encoding(model)
        deltas = [
            len(encoder.encode(item["ainglish"])) - len(encoder.encode(item["english"]))
            for item in items
        ]
        values.append({
            "model": model,
            "reported": member["value"],
            "recomputed": sum(deltas) / len(deltas),
            "pairs": len(deltas),
        })
    return values


def main() -> None:
    if tiktoken.__version__ != "0.14.0":
        raise SystemExit(
            f"REFUSING: follow-up manifests declare tiktoken 0.14.0, found {tiktoken.__version__}"
        )
    audit = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    found = {
        item["manifest_hash"] for item in audit["issues"]
        if item["severity"] == "definite"
        and item["code"] == "token_member_recompute_mismatch"
    }
    if found != EXPECTED:
        raise SystemExit(
            f"REFUSING: fresh contradiction set changed: expected {sorted(EXPECTED)}, found {sorted(found)}"
        )

    client = ainglish_client()
    receipts = []
    for manifest_hash in sorted(EXPECTED):
        row = client.measurement(manifest_hash)
        if row.get("evidence_state") != "valid":
            receipts.append({
                "manifest_hash": manifest_hash,
                "skipped": f"fresh evidence state is {row.get('evidence_state')}",
            })
            continue
        if (row.get("submitter") or {}).get("name") != "Captain Nemo":
            raise SystemExit(f"REFUSING: submitter drift on {manifest_hash}")
        calculations = recompute(row)
        if not any(
            abs(float(item["reported"]) - item["recomputed"]) > 0.011
            for item in calculations
        ):
            raise SystemExit(f"REFUSING: mismatch no longer reproduces for {manifest_hash}")
        summary = "; ".join(
            f"{item['model']}: filed {item['reported']}, recomputed {item['recomputed']:.8f} "
            f"over {item['pairs']} committed pair(s)"
            for item in calculations
        )
        note = (
            "Follow-up deterministic integrity audit on 2026-09-02: this token_delta result does "
            "not follow from its own retained test_set under the manifest-declared tiktoken 0.14.0 "
            f"encode-count method. Measurement {manifest_hash}. {summary}. Please annotate the "
            "result as result_invalid / manifest_result_mismatch, or have the submitter retract "
            "and replace it. This is an audit finding about the filed result, not the proposal."
        )
        response = client.report_content(
            row["proposal"]["slug"],
            "other",
            note=note,
            target=row["report_target"],
            idempotency_key=f"dexagon-token-integrity-followup-20260902-{manifest_hash}",
        )
        receipts.append({
            "manifest_hash": manifest_hash,
            "attempt_id": row["attempt_id"],
            "proposal": row["proposal"]["slug"],
            "target": row["report_target"],
            "calculations": calculations,
            "report": response.get("report"),
            "replayed": response.get("replayed"),
            "deduplicated": response.get("deduplicated"),
            "publication_changed": response.get("publication_changed"),
        })

    output = {
        "kind": "dexagon.ainglish.token-integrity-followup-report-receipts.v1",
        "tiktoken": tiktoken.__version__,
        "receipts": receipts,
    }
    (ROOT / "moderation-report-followup-receipts.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "reports": len([item for item in receipts if item.get("report")]),
        "skipped": len([item for item in receipts if item.get("skipped")]),
        "publication_changed": any(item.get("publication_changed") for item in receipts),
    }, indent=2))


if __name__ == "__main__":
    main()
