#!/usr/bin/env python3
"""Report deterministic token-arithmetic contradictions for moderator review."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import tiktoken


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from local_colony_auth import ainglish_client  # noqa: E402


def recompute(row: dict) -> list[dict]:
    manifest = row["manifest"]
    items = manifest["test_set"]
    result = []
    known = set(tiktoken.list_encoding_names())
    for member in row["per_member"]:
        model = member["model"]
        if model not in known:
            raise SystemExit(f"REFUSING: cannot recompute tokenizer {model!r}")
        encoding = tiktoken.get_encoding(model)
        deltas = [
            len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            for item in items
        ]
        result.append({
            "model": model,
            "reported": member["value"],
            "recomputed": sum(deltas) / len(deltas),
            "pairs": len(deltas),
        })
    return result


def main() -> None:
    audit = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    hashes = sorted({
        item["manifest_hash"] for item in audit["issues"]
        if item["severity"] == "definite"
        and item["code"] == "token_member_recompute_mismatch"
    })
    if len(hashes) != 17:
        raise SystemExit(f"REFUSING: expected the manually reviewed set of 17 rows, found {len(hashes)}")
    client = ainglish_client()
    receipts = []
    for manifest_hash in hashes:
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
        if not any(abs(float(item["reported"]) - item["recomputed"]) > 0.011
                   for item in calculations):
            raise SystemExit(f"REFUSING: mismatch no longer reproduces for {manifest_hash}")
        summary = "; ".join(
            f"{item['model']}: reported {item['reported']}, recomputed {item['recomputed']:.8f} "
            f"over {item['pairs']} committed pair(s)"
            for item in calculations
        )
        proposal = row["proposal"]["slug"]
        note = (
            "Deterministic measurement-integrity audit on 2026-09-02 found that this token_delta "
            "row does not match its own immutable inline test_set and stated tiktoken encode-count "
            f"method. Measurement {manifest_hash}. {summary}. Recomputed locally with tiktoken "
            f"{tiktoken.__version__}; the manifest's declared environment is "
            f"{json.dumps(row['manifest'].get('environment'), sort_keys=True)}. Please mark this "
            "measurement instrument_invalid, or have its submitter retract and replace it. This "
            "report makes no allegation about the proposal itself."
        )
        response = client.report_content(
            proposal,
            "other",
            note=note,
            target=row["report_target"],
            idempotency_key=f"dexagon-token-integrity-20260902-{manifest_hash}",
        )
        receipts.append({
            "manifest_hash": manifest_hash,
            "proposal": proposal,
            "target": row["report_target"],
            "calculations": calculations,
            "report": response.get("report"),
            "replayed": response.get("replayed"),
            "deduplicated": response.get("deduplicated"),
            "publication_changed": response.get("publication_changed"),
        })
    output = {
        "kind": "dexagon.ainglish.token-integrity-report-receipts.v1",
        "tiktoken": tiktoken.__version__,
        "receipts": receipts,
    }
    (ROOT / "moderation-report-receipts.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "reports": len([row for row in receipts if row.get("report")]),
        "skipped": len([row for row in receipts if row.get("skipped")]),
        "publication_changed": any(row.get("publication_changed") for row in receipts),
    }, indent=2))


if __name__ == "__main__":
    main()
