#!/usr/bin/env python3
"""Recompute local commitments and structural gates across all five workstreams."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "report.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load(relative: str) -> object:
    return json.loads((ROOT / relative).read_text())


def check_rows(rows: list[dict], *, calibration: int | None = None) -> dict:
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert all(row["answer"] in row["options"] for row in rows)
    actual_calibration = sum(bool(row.get("calibration")) for row in rows)
    if calibration is not None:
        assert actual_calibration == calibration
    return {"rows": len(rows), "unique_ids": len(set(ids)), "calibration": actual_calibration}


def modal_tokens() -> dict:
    root = "modal-operational-token-prerequisites-2026-08-25"
    packet = load(f"{root}/items.json")
    sealed = dict(packet); expected = sealed.pop("content_sha256")
    assert digest(sealed) == expected
    out = {"packet_sha256": expected, "campaigns": {}}
    for name, campaign in packet["campaigns"].items():
        assert digest(campaign["test_set"]) == campaign["items_sha256"]
        assert len(campaign["test_set"]) & (len(campaign["test_set"]) - 1) == 0
        receipt = load(f"{root}/{name}.measurement.json")
        measurement = receipt["measurement"]["measurement"]
        assert measurement["attempt"]["state"] == "completed"
        assert measurement["metric"] == "token_delta"
        out["campaigns"][name] = {
            "pairs": len(campaign["test_set"]), "items_sha256": campaign["items_sha256"],
            "value": measurement["value"], "manifest_hash": measurement["manifest_hash"],
            "attempt_id": measurement["attempt_id"], "attempt_state": measurement["attempt"]["state"],
        }
    return out


def modal_carriers() -> dict:
    root = "modal-operational-comprehension-carriers-2026-08-25"
    index = load(f"{root}/index.json")
    out = {}
    for name, meta in index["campaigns"].items():
        rows = load(f"{root}/{meta['file']}")
        assert digest(rows) == meta["sha256"]
        panel = load(f"{root}/{meta['panel_file']}")
        assert digest(panel["items"]) == meta["panel_sha256"] == panel["sha256"]
        observed = {form: sum(row["form"] == form for row in rows) for form in meta["forms"]}
        assert observed == meta["forms"]
        out[name] = {"scientific": check_rows(rows), "panel": check_rows(panel["items"], calibration=8), "forms": observed}
    return out


def proxy() -> dict:
    root = "proxy-comprehension-carrier-2026-08-25"
    index = load(f"{root}/index.json")
    base = load(f"{root}/items.json")
    assert digest(base) == index["items_sha256"]
    out = {"base": check_rows(base), "packets": {}}
    for name, meta in index["panel_packets"].items():
        packet = load(f"{root}/{meta['file']}")
        assert digest(packet["items"]) == meta["items_sha256"] == packet["sha256"]
        out["packets"][name] = check_rows(packet["items"], calibration=8)
    return out


def evidential() -> dict:
    root = "evidential-tags-fidelity-and-carrier-2026-08-25"
    index = load(f"{root}/index.json")
    fidelity = load(f"{root}/fidelity-cases.json")
    comprehension = load(f"{root}/comprehension-items.json")
    panel = load(f"{root}/comprehension-panel.json")
    assert digest(fidelity) == index["fidelity"]["sha256"]
    assert digest(comprehension) == index["comprehension"]["sha256"]
    assert digest(panel["items"]) == index["comprehension"]["panel_sha256"] == panel["sha256"]
    return {
        "fidelity": check_rows(fidelity), "comprehension": check_rows(comprehension),
        "panel": check_rows(panel["items"], calibration=8),
        "fidelity_forms": index["fidelity"]["forms"], "comprehension_forms": index["comprehension"]["forms"],
    }


def census() -> dict:
    root = "ratified-language-census-2026-08-25"
    index = load(f"{root}/index.json")
    rows = load(f"{root}/items.json")
    assert digest(rows) == index["items_sha256"]
    assert len(rows) == 768 and len(index["form_counts"]) == 24
    for form, count in index["form_counts"].items():
        assert count == 32 == sum(row["proposal_form"] == form for row in rows)
    proposal_packets = {}
    for name, meta in index["proposal_packets"].items():
        packet = load(f"{root}/{meta['file']}")
        assert digest(packet["items"]) == meta["items_sha256"] == packet["sha256"]
        stats = check_rows(packet["items"], calibration=8)
        if meta["condition"] == "reference":
            for row in packet["items"]:
                if row.get("calibration"):
                    continue
                assert row["english"].split("\nMessage:", 1)[0] == row["ainglish"].split("\nMessage:", 1)[0]
        proposal_packets[name] = stats
    return {
        "base": check_rows(rows), "forms": len(index["form_counts"]),
        "proposal_packets": len(proposal_packets), "reference_prefixes_byte_identical": True,
    }


def reader_qualification() -> dict:
    root = "reader-qualification-v5-2026-08-25"
    phases = []
    for name in ("phase-a", "reserve", "phi-reserve"):
        spec = load(f"{root}/{name}-holdout.json")
        sealed = dict(spec); spec_expected = sealed.pop("content_sha256")
        assert digest(sealed) == spec_expected
        result = load(f"{root}/{name}-result.json")
        sealed_result = dict(result); result_expected = sealed_result.pop("content_sha256")
        assert digest(sealed_result) == result_expected
        assert result["spec_sha256"] == spec_expected
        phases.append({
            "phase": name, "spec_sha256": spec_expected, "result_sha256": result_expected,
            "roster_ready": result["roster_ready"], "qualification": result["qualification"],
        })
    selected = load(f"{root}/selected-result.json")
    sealed_selected = dict(selected); selected_expected = sealed_selected.pop("content_sha256")
    assert digest(sealed_selected) == selected_expected
    assert selected["source_results"] == [
        {"file": f"{row['phase']}-result.json", "content_sha256": row["result_sha256"]}
        for row in phases
    ]
    assert not selected["roster_ready"] and not selected["fixed_roster"]
    return {
        "phases": phases, "selection_sha256": selected_expected,
        "roster_ready": selected["roster_ready"], "fixed_roster": selected["fixed_roster"],
    }


def main() -> None:
    report = {
        "kind": "ainglish.five-workstream-integrity-report.v1",
        "network_calls": 0, "model_calls": 0, "governance_calls": 0, "status": "passed",
        "reader_qualification": reader_qualification(), "modal_tokens": modal_tokens(),
        "modal_carriers": modal_carriers(), "proxy": proxy(), "evidential": evidential(), "census": census(),
    }
    report["content_sha256"] = digest(report)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": report["status"], "sha256": report["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
