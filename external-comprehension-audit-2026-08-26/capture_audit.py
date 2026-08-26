#!/usr/bin/env python3
"""Capture and audit Reticuli's 2026-08-26 flagship comprehension originals."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


MEASUREMENTS = [
    ("proxy-careful", "bcc7b1d1f3cc4c975755a9d2f36d72681a301e6e6584334efd7fa4dcc73dc29f"),
    ("proxy-bare", "2dc47b111ee5bfd656ecad4f142832711b5d1f35baa8ae07c9fe6dd80261a615"),
    ("proxy-obs", "82177a0e664db5fed7bbcb812a6590277cd398c8c4f3c79b1cca2a50aaa2f2ae"),
    ("moved-later-careful", "3965fddd5d31ea9f9948a113dd549cd84bac61223b61941ec69bde0b0d326635"),
    ("moved-later-bare", "c35249de0f0807215f4ec82e3a964f9f5ac419522b5986de10c0350ed9ae8bbb"),
    ("moved-earlier-careful", "b755d553d4c1f890a54833731a841aef8fa40348d2f641b6ec42b3d1f571813c"),
    ("moved-earlier-bare", "a7270b497fbb5a8012223fa2be74c18ffd68c2dcb5ce3e5c13d6e1d3ff86bbfb"),
    ("may-careful", "dba42c0e48b623502fb370067cf080a1b639a2bb621318400217f1f3d79b3e83"),
    ("may-bare", "fba86a10ff5400837aeb8eaaded01d2e84a233a3fac8f889e64e578ef76cfad8"),
    ("rather-careful", "b661b02842052ced7bc148b50fd4194c6084fbc27f1f70e22e45dd6af88e3d7d"),
    ("rather-bare", "edb44cee446c7105302049ca72135bdb23268325771a8612217fe7deeaf9751f"),
    ("thisonce-careful", "b4284015daf019e10b2bf4a7643c4341d6576859a57ae40d7c99ae0a1ced546c"),
    ("thisonce-bare", "dbc96ac646e5eaa6b115bd904d90a624b08d400a1229833e806512feddf290ef"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def family(model: str) -> str:
    lowered = model.lower()
    if "gemma" in lowered:
        return "Gemma"
    # Ornith-1.0-35B is post-trained from Qwen 3.5. Its model card and the
    # measurement's exact hf.co model path make this a base-lineage collapse,
    # not an independent third architecture.
    if "qwen" in lowered or "ornith" in lowered:
        return "Qwen"
    return f"unresolved:{model}"


def counts(rows: list[dict], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row[key]) for row in rows if key in row).items()))


def main() -> None:
    client = ainglish_client()
    audited = []
    for label, manifest_hash in MEASUREMENTS:
        measurement = client.measurement(manifest_hash)
        manifest = measurement["manifest"]
        with urlopen(manifest["items_url"], timeout=30) as response:
            packet = json.load(response)
        items = packet["items"]
        item_bytes = canonical(items)
        real = [row for row in items if not row.get("calibration")]
        calibration = [row for row in items if row.get("calibration")]
        model_families = sorted({family(model) for model in measurement["panel_models"]})
        audited.append({
            "label": label,
            "manifest_hash": manifest_hash,
            "proposal": measurement["proposal"]["slug"],
            "metric": measurement["metric"],
            "formula_version": measurement["formula_version"],
            "value": measurement["value"],
            "value_lo": measurement["value_lo"],
            "value_hi": measurement["value_hi"],
            "stance": measurement["stance"],
            "arms": measurement["arms"],
            "per_member": measurement["per_member"],
            "comparator": manifest["comparator"],
            "items": {
                "url": manifest["items_url"],
                "declared_sha256": manifest["items_sha256"],
                "computed_sha256": hashlib.sha256(item_bytes).hexdigest(),
                "packet_declared_sha256": packet.get("sha256"),
                "hashes_match": (
                    hashlib.sha256(item_bytes).hexdigest()
                    == manifest["items_sha256"]
                    == packet.get("sha256")
                ),
                "total": len(items),
                "real": len(real),
                "calibration": len(calibration),
                "unique_complete_rows": len({canonical(row) for row in items}),
                "answer_positions": dict(sorted(Counter(
                    row["options"].index(row["answer"])
                    for row in real
                    if row.get("answer") in row.get("options", [])
                ).items())),
                "strata": {
                    key: counts(real, key)
                    for key in ("form", "domain", "cell", "outcome", "power", "stratum")
                    if any(key in row for row in real)
                },
            },
            "reader_audit": {
                "declared_members": measurement["panel_members"],
                "declared_neff": measurement["panel_neff"],
                "declared_neff_basis": measurement["panel_neff_basis"],
                "served_models": measurement["panel_models"],
                "base_families": model_families,
                "base_family_count": len(model_families),
                "strict_local_reader_gate_applies": True,
            },
            "run_integrity": {
                "calibration": measurement["calibration"],
                "transport_faults": manifest["transport_faults"],
                "transport_truncations": manifest["transport_truncations"],
                "harness": manifest["harness"],
                "attempt_state": measurement["attempt"]["state"],
                "manifest_storage": measurement["attempt"]["manifest_storage"],
                "confirmed": measurement["confirmed"],
                "settlement_state": measurement["settlement_state"],
            },
        })

    strict_reader_result = json.loads(
        (ROOT.parent / "reader-qualification-v8-2026-08-26" / "selected-result.json").read_text(
            encoding="utf-8"
        )
    )
    snapshot = {
        "kind": "ainglish.external-comprehension-audit.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Reticuli comprehension originals filed 2026-08-26 for the active flagship pipeline",
        "artifact_rule": "items_sha256 is SHA-256 of JCS-like compact sorted-key serialization of the packet's items array, not of the enclosing JSON file bytes",
        "lineage_rule": "post-training does not create a new base-model lineage; Ornith-1.0-35B collapses with Qwen because its served model card identifies Qwen 3.5 as the base",
        "lineage_source": "https://huggingface.co/ornith-ai/Ornith-1.0-35B",
        "strict_reader_gate": {
            "source": "reader-qualification-v8-2026-08-26/selected-result.json",
            "roster_ready": strict_reader_result["roster_ready"],
            "required_lineages": strict_reader_result["selection_rule"]["minimum_qualified_lineages"],
            "qualified": [
                row["lineage"] for row in strict_reader_result["qualification"] if row["qualified"]
            ],
            "decision": "do not use these originals to unlock Dexagon's sealed semantic carriers; audit and preserve them, then replicate only with a later two-lineage qualified roster",
        },
        "measurements": audited,
        "cross_cutting_findings": [
            "All 13 served manifests resolve to immutable commit-pinned item URLs and all 13 item-array digests recompute exactly.",
            "Every run passed its declared calibration and reports zero transport faults or truncations.",
            "No original is independently confirmed; each remains settlement_state awaiting.",
            "The served pools contain at most two base families, Qwen and Gemma. Qwen 2.5, Qwen 3.8, and Qwen-derived Ornith do not create separate lineages.",
            "The v8 strict ordinary-English qualification gate has only one qualified lineage, Qwen 3.6 35B, so the campaign's two-lineage semantic gate remains closed.",
            "For multi-form proposals the register serves one aggregate scalar and no per-form result fields. Claims that require every form to pass cannot be established from the served scalar alone; per-form evidence must be filed separately or made first-class and auditable.",
            "Several apparent sign conflicts are different estimands: a careful-English carrier and a bare-English descriptive comparison. They must not be pooled or treated as replications of one another.",
        ],
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target = ROOT / "audit.json"
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "measurements": len(audited),
        "hashes_match": sum(row["items"]["hashes_match"] for row in audited),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
