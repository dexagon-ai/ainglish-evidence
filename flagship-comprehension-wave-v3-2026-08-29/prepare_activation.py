#!/usr/bin/env python3
"""Build immutable, panel-ready item arrays from the frozen per-form campaigns.

This is an offline composition step.  It makes no reader or governance call and
does not open the reader gate.  The generated arrays are the exact single-file
artifacts that a future digest-pinned panel runspec can fetch after two reader
lineages have qualified.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

ACTIVATIONS = {
    "they-number-bare-replication": {
        "design": "they-number.design.json",
        "role": "bare_diagnostic",
        "kind": "replication",
        "replicates_hash": "92b77fdcc4b1529f6446f1c9756b80cc08acad1c4433bf845e0a95c98b9693b0",
    },
    "role-cardinality-claim-original": {
        "design": "role-cardinality.design.json",
        "role": "claim_carrier",
        "kind": "original",
    },
    "test-outcome-claim-original": {
        "design": "test-outcome.design.json",
        "role": "claim_carrier",
        "kind": "original",
    },
    "acknowledgement-force-claim-original": {
        "design": "acknowledgement-force.design.json",
        "role": "claim_carrier",
        "kind": "original",
    },
    "enumeration-closure-claim-original": {
        "design": "enumeration-closure.design.json",
        "role": "claim_carrier",
        "kind": "original",
    },
    "repetition-restoration-claim-original": {
        "design": "repetition-restoration.design.json",
        "role": "claim_carrier",
        "kind": "original",
    },
    "preservation-invariant-claim-recertification": {
        "design": "preservation-invariant.design.json",
        "role": "claim_carrier",
        "kind": "original",
    },
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
        raise SystemExit(f"REFUSING: frozen activation drift: {path.name}")
    if not path.exists():
        path.write_text(rendered, encoding="utf-8")


def write_append_only_index(path: Path, value: dict) -> None:
    """Allow new activation seats without permitting an existing seat to drift."""
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        for key, row in existing.get("outputs", {}).items():
            if value["outputs"].get(key) != row:
                raise SystemExit(f"REFUSING: existing activation drift: {key}")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_campaign(design: dict, form: str, role: str) -> tuple[str, dict, list[dict]]:
    matches = [
        (name, campaign)
        for name, campaign in design["campaigns"].items()
        if campaign.get("form") == form and campaign.get("role") == role
    ]
    assert len(matches) == 1, (form, role, [name for name, _ in matches])
    name, campaign = matches[0]
    path = ROOT / campaign["items"]
    assert file_digest(path) == campaign["items_sha256"]
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(rows, list) and rows
    return name, campaign, rows


def main() -> None:
    outputs = {}
    for key, spec in ACTIVATIONS.items():
        design_path = ROOT / spec["design"]
        design = json.loads(design_path.read_text(encoding="utf-8"))
        material = dict(design)
        expected_design_digest = material.pop("content_sha256")
        assert digest(material) == expected_design_digest

        sources = []
        calibration = []
        science = []
        for form in design["forms"]:
            name, campaign, rows = load_campaign(design, form, spec["role"])
            source_calibration = [row for row in rows if row.get("calibration") is True]
            source_science = [row for row in rows if row.get("calibration") is not True]
            assert len(source_calibration) == campaign["planned_sample"]["calibration_items"]
            assert len(source_science) == campaign["planned_sample"]["real_items"]
            assert all(row.get("form") == form for row in source_science)
            calibration.extend(source_calibration)
            science.extend(source_science)
            sources.append({
                "campaign": name,
                "form": form,
                "file": campaign["items"],
                "file_sha256": campaign["items_sha256"],
                "real_items": len(source_science),
                "calibration_items": len(source_calibration),
            })

        rows = calibration + science
        ids = [row["id"] for row in rows]
        assert len(ids) == len(set(ids))
        assert len(science) == len({row["context_id"] for row in science})
        forms = Counter(row["form"] for row in science)
        seams = Counter(row["semantic_seam"] for row in science)
        output_path = ROOT / f"activation-{key}.items.json"
        write_frozen(output_path, rows)
        outputs[key] = {
            "slug": design["slug"],
            "proposal_revision": design["proposal_revision"],
            "kind": spec["kind"],
            "campaign_role": spec["role"],
            "design": spec["design"],
            "design_sha256": expected_design_digest,
            "sources": sources,
            "items": output_path.name,
            "items_sha256": digest(rows),
            "file_sha256": file_digest(output_path),
            "counts": {
                "real_items": len(science),
                "calibration_items": len(calibration),
                "forms": dict(forms),
                "semantic_seams": dict(sorted(seams.items())),
            },
            "replicates_hash": spec.get("replicates_hash"),
            "reader_gate": "closed_pending_two_distinct_qualified_base_model_lineages",
            "model_calls": 0,
            "governance_writes": 0,
        }

    index = {
        "kind": "dexagon.ainglish.flagship-comprehension-wave-v3.activation-index",
        "purpose": "single-file digest-pinned panel inputs composed from the frozen per-form campaigns",
        "outputs": outputs,
        "reader_gate": "closed_pending_two_distinct_qualified_base_model_lineages",
        "model_calls": 0,
        "network_calls": 0,
        "governance_writes": 0,
        "content_sha256": "",
    }
    index["content_sha256"] = digest({k: v for k, v in index.items() if k != "content_sha256"})
    write_append_only_index(ROOT / "activation-index.json", index)
    print(json.dumps({
        "activations": len(outputs),
        "real_items": sum(row["counts"]["real_items"] for row in outputs.values()),
        "calibration_items": sum(row["counts"]["calibration_items"] for row in outputs.values()),
        "model_calls": 0,
        "governance_writes": 0,
        "content_sha256": index["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
