#!/usr/bin/env python3
"""Offline fail-closed audit for the seven frozen comprehension designs."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from evidence_factory.design import EvidenceDesign  # noqa: E402


EXPECTED = {
    "they-number": {"forms": 2, "roles": 4, "real": 64, "seams": 4, "per_seam": 16},
    "enumeration-closure": {"forms": 2, "roles": 4, "real": 100, "seams": 4, "per_seam": 25},
    "role-cardinality": {"forms": 2, "roles": 4, "real": 64, "seams": 4, "per_seam": 16},
    "repetition-restoration": {"forms": 2, "roles": 5, "real": 64, "seams": 1, "per_seam": 64},
    "test-outcome": {"forms": 2, "roles": 4, "real": 48, "seams": 3, "per_seam": 16},
    "acknowledgement-force": {"forms": 2, "roles": 4, "real": 80, "seams": 4, "per_seam": 20},
    "preservation-invariant": {"forms": 2, "roles": 5, "real": 120, "seams": 1, "per_seam": 120},
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked_hash(value: dict) -> str:
    expected = value["content_sha256"]
    material = dict(value)
    del material["content_sha256"]
    assert hashlib.sha256(canonical(material)).hexdigest() == expected
    return expected


def collect_message_fields(value: object, messages: set[str]) -> None:
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key in ("english", "ainglish", "message"):
                item = current.get(key)
                if isinstance(item, str):
                    messages.add(item)
            arms = current.get("arms")
            if isinstance(arms, dict):
                messages.update(item for item in arms.values() if isinstance(item, str))
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def prior_messages() -> tuple[set[str], int]:
    messages: set[str] = set()
    files = 0
    for path in REPO.rglob("*.json"):
        if ROOT == path.parent or ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        files += 1
        collect_message_fields(value, messages)
    return messages, files


def load_rows(path: Path) -> tuple[list[dict], list[dict]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(rows, list) and rows
    science = [row for row in rows if row.get("calibration") is not True]
    calibration = [row for row in rows if row.get("calibration") is True]
    return science, calibration


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    index_hash = checked_hash(index)
    assert set(index["outputs"]) == set(EXPECTED)
    assert index["summary"] == {
        "designs": 7,
        "item_files": 30,
        "real_items": 2232,
        "model_calls": 0,
        "governance_writes": 0,
    }
    assert index["reader_gate"]["current"] == "closed"

    all_ids: set[str] = set()
    all_contexts: set[str] = set()
    all_calibration_pairs: set[tuple[str, str]] = set()
    new_messages: set[str] = set()
    report: dict[str, dict] = {}
    total_real = 0
    total_calibration = 0

    for key, expected in EXPECTED.items():
        pointer = index["outputs"][key]
        design = EvidenceDesign.load(ROOT / pointer["design"])
        assert design.content_digest == pointer["design_sha256"]
        payload = design.payload
        assert len(payload["forms"]) == expected["forms"]
        assert len(payload["campaigns"]) == expected["roles"]
        training = payload["training_data_interpretation"]
        assert "not assumed to have seen Ainglish" in training["present_zero_shot"]
        assert "prospective benefit is a hypothesis" in training["future_efficiency"]
        assert "cannot establish comprehension" in training["token_boundary"]
        assert payload["model_calls"] == payload["governance_writes"] == 0

        campaign_report = {}
        role_seams: dict[tuple[str, str], Counter] = {}
        for name, campaign in payload["campaigns"].items():
            path = ROOT / campaign["items"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == campaign["items_sha256"]
            science, calibration = load_rows(path)
            is_diagnostic = campaign["role"] == "learnability_diagnostic"
            assert len(science) == (campaign["planned_sample"]["real_items"])
            assert len(calibration) == 12
            if not is_diagnostic:
                assert len(science) == expected["real"]
            assert len({row["context_id"] for row in science}) == len(science)
            assert not ({row["context_id"] for row in science} & all_contexts)
            all_contexts.update(row["context_id"] for row in science)
            assert all(row["english"] != row["ainglish"] for row in science)
            assert all(row["comparator_kind"] == campaign["comparator"]["kind"] for row in science)
            assert all(row["answer"] in row["options"] for row in science + calibration)
            assert all(len(row["options"]) == len(set(row["options"])) for row in science + calibration)
            assert all(row.get("calibration_scope") == "target-independent" for row in calibration)

            ids = {row["id"] for row in science + calibration}
            assert len(ids) == len(science) + len(calibration)
            assert not ids & all_ids
            all_ids |= ids
            for row in science + calibration:
                pair = (row["english"], row["ainglish"])
                assert pair not in all_calibration_pairs if row.get("calibration") else True
                if row.get("calibration"):
                    all_calibration_pairs.add(pair)
                assert row["english"] not in new_messages
                new_messages.add(row["english"])
                assert row["ainglish"] not in new_messages
                new_messages.add(row["ainglish"])

            seams = Counter(row["semantic_seam"] for row in science)
            positions = {}
            for seam, count in seams.items():
                seam_positions = Counter(
                    row["options"].index(row["answer"])
                    for row in science if row["semantic_seam"] == seam
                )
                assert max(seam_positions.values()) - min(seam_positions.values()) <= 1
                assert set(seam_positions) == set(range(len(next(
                    row["options"] for row in science if row["semantic_seam"] == seam
                ))))
                positions[seam] = dict(sorted(seam_positions.items()))
                if not is_diagnostic:
                    assert count == expected["per_seam"]
            if not is_diagnostic:
                assert len(seams) == expected["seams"]
                role_seams[(campaign["form"], campaign["role"])] = seams

            if key == "repetition-restoration" and not is_diagnostic:
                assert Counter(row["metadata"]["force"] for row in science) == {
                    "affirmative": 16, "negated": 16, "question": 16, "directive": 16,
                }
            if key == "acknowledgement-force" and not is_diagnostic:
                downstream = [row for row in science if row["semantic_seam"] == "downstream-nonclaim"]
                assert Counter(row["metadata"]["nonclaim"] for row in downstream) == {
                    "authority": 5,
                    "a promise to comply": 5,
                    "truth of the message": 5,
                    "implementation": 5,
                }
            if key == "preservation-invariant" and not is_diagnostic:
                assert set(Counter(row["metadata"]["variant"] for row in science).values()) == {10}

            total_real += len(science)
            total_calibration += len(calibration)
            campaign_report[name] = {
                "real_items": len(science),
                "calibration_items": len(calibration),
                "unique_contexts": len(science),
                "seams": dict(sorted(seams.items())),
                "answer_positions": positions,
            }

        for form in payload["forms"]:
            assert role_seams[(form, "claim_carrier")] == role_seams[(form, "bare_diagnostic")]
        report[key] = {"design_sha256": design.content_digest, "campaigns": campaign_report}

    assert total_real == 2232
    assert total_calibration == 360
    assert len(all_contexts) == total_real
    assert len(all_calibration_pairs) == total_calibration
    assert len(new_messages) == 2 * (total_real + total_calibration)

    for row in index["ratified_flagship_gaps"].values():
        assert (ROOT / row["carrier"]).resolve().is_file()
        if row.get("secondary"):
            assert (ROOT / row["secondary"]).resolve().is_file()

    receipt = json.loads((ROOT / "live-receipt.json").read_text(encoding="utf-8"))
    receipt_hash = checked_hash(receipt)
    assert set(receipt["progression"]) == {
        index["outputs"][key]["slug"] for key in EXPECTED if key != "preservation-invariant"
    }
    assert all(row["stage"] == "measured" for row in receipt["progression"].values())
    assert len(receipt["ratified_flagships"]) == 5
    assert all(row["stage"] == "ratified" for row in receipt["ratified_flagships"].values())
    assert receipt["model_calls"] == receipt["governance_writes"] == 0

    prior, prior_files = prior_messages()
    overlaps = sorted(new_messages & prior)
    assert not overlaps, f"exact message overlap with earlier evidence: {overlaps[:3]}"

    # The repository-wide file count is useful run diagnostics, but it is
    # intentionally excluded from the frozen result because later, unrelated
    # evidence packages legitimately increase it.
    result = {
        "kind": "dexagon.ainglish.flagship-comprehension-wave-v3.audit",
        "status": "passed_waiting_external_reader_gate",
        "index_sha256": index_hash,
        "live_receipt_sha256": receipt_hash,
        "designs": report,
        "totals": {
            "designs": 7,
            "campaigns": 30,
            "scientific_items": total_real,
            "calibration_items": total_calibration,
            "unique_item_ids": len(all_ids),
            "unique_contexts": len(all_contexts),
            "prior_exact_message_overlap": 0,
        },
        "reader_gate": "closed",
        "model_calls": 0,
        "network_calls": 0,
        "governance_writes": 0,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    target = ROOT / "audit.json"
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != rendered:
        raise SystemExit("REFUSING: frozen audit drift")
    if not target.exists():
        target.write_text(rendered, encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "scientific_items": total_real,
        "calibration_items": total_calibration,
        "prior_json_files_scanned": prior_files,
        "content_sha256": result["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
