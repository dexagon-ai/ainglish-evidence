#!/usr/bin/env python3
"""Derive official and diagnostic panel items from two frozen carrier blocks."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from validate_block import ValidationError, canonical_sha, exact_sha


ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "protocol.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def place_answer(options: list[str], answer: str, target_position: int) -> list[str]:
    target_position %= len(options)
    offset = (options.index(answer) - target_position) % len(options)
    return options[offset:] + options[:offset]


def exposed(context: str, surface: str) -> str:
    return f"{context}\n\nTarget sentence: {surface}"


def calibration_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "calibration": True,
            "english": item["english"],
            "ainglish": item["ainglish"],
            "question": item["question"],
            "options": item["options"],
            "answer": item["answer"],
            "carrier": item["carrier"],
            "set": "construct-free-planted-effect",
        }
        for item in rows
    ]


def primary_rows(
    scenarios: list[dict[str, Any]],
    protocol: dict[str, Any],
    form: str,
    comparator: str,
) -> list[dict[str, Any]]:
    surface_field = "careful_surface" if comparator == "careful" else "short_surface"
    comparison = (
        f"{form}-marked-vs-complete-careful-english"
        if comparator == "careful"
        else f"{form}-marked-vs-natural-short-surface-diagnostic"
    )
    options = protocol["primary_options"]
    answer = protocol["primary_answers"][form]
    rows = []
    selected = sorted((item for item in scenarios if item["form"] == form), key=lambda row: row["id"])
    for position, item in enumerate(selected):
        rows.append({
            "id": f"{item['id']}-primary-{comparator}",
            "english": exposed(item["context"], item[surface_field]),
            "ainglish": exposed(item["context"], item["marked_surface"]),
            "question": protocol["primary_question"],
            "options": place_answer(options, answer, position),
            "answer": answer,
            "scenario_id": item["id"],
            "carrier": item["carrier"],
            "form": form,
            "domain": item["domain"],
            "case": item["case"],
            "short_style": item["short_style"],
            "source_class": item["source_class"],
            "comparison": comparison,
        })
    require(len(rows) == 48, f"{comparison} derived {len(rows)} real rows, expected 48")
    return rows


def warrant_rows(scenarios: list[dict[str, Any]], protocol: dict[str, Any]) -> list[dict[str, Any]]:
    options = protocol["warrant_options"]
    rows = []
    for position, item in enumerate(sorted(scenarios, key=lambda row: row["id"])):
        comparison = "authority-warrant-marked-vs-complete-careful-english-diagnostic"
        rows.append({
            "id": f"{item['id']}-warrant-careful",
            "english": exposed(item["context"], item["careful_surface"]),
            "ainglish": exposed(item["context"], item["marked_surface"]),
            "question": protocol["warrant_question"],
            "options": place_answer(options, item["warrant_answer"], position),
            "answer": item["warrant_answer"],
            "scenario_id": item["id"],
            "carrier": item["carrier"],
            "form": item["form"],
            "domain": item["domain"],
            "case": item["case"],
            "source_class": item["source_class"],
            "comparison": comparison,
        })
    require(len(rows) == 96, f"warrant diagnostic derived {len(rows)} rows, expected 96")
    return rows


def write_items(
    output_dir: Path,
    filename: str,
    kind: str,
    source_sha: str,
    real: list[dict[str, Any]],
    calibrations: list[dict[str, Any]],
) -> dict[str, Any]:
    items = real + calibrations
    document = {
        "kind": kind,
        "source_scenarios_sha256": source_sha,
        "sha256": canonical_sha(items),
        "items": items,
    }
    path = output_dir / filename
    encoded = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path.write_bytes(encoded)
    return {
        "file": filename,
        "real_items": len(real),
        "calibration_items": len(calibrations),
        "items_sha256": document["sha256"],
        "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scenarios", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        merged = json.loads(args.scenarios.read_text(encoding="utf-8"))
        protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
        require(merged.get("kind") == "ainglish.proposal-decision.comprehension-scenarios.v1",
                "input is not the frozen merged-scenario kind")
        require(merged.get("protocol_sha256") == exact_sha(PROTOCOL_PATH),
                "merged scenarios reference different protocol bytes")
        content = {
            "scenarios": merged.get("scenarios"),
            "calibration_items": merged.get("calibration_items"),
        }
        require(merged.get("sha256") == canonical_sha(content), "merged scenario content hash drifted")
        scenarios = merged["scenarios"]
        calibrations = calibration_rows(merged["calibration_items"])
        require(len(scenarios) == 96 and len(calibrations) == 8,
                "expected 96 scenarios and eight calibration items")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        receipts = []
        for form in ("proposal-by", "decision-by"):
            receipts.append(write_items(
                args.output_dir,
                f"{form}-careful-items.json",
                f"ainglish.panel.items.v1:{form}-marked-vs-careful",
                merged["sha256"],
                primary_rows(scenarios, protocol, form, "careful"),
                calibrations,
            ))
            receipts.append(write_items(
                args.output_dir,
                f"{form}-short-diagnostic-items.json",
                f"ainglish.panel.items.v1:{form}-marked-vs-short-diagnostic",
                merged["sha256"],
                primary_rows(scenarios, protocol, form, "short"),
                calibrations,
            ))
        receipts.append(write_items(
            args.output_dir,
            "authority-warrant-diagnostic-items.json",
            "ainglish.panel.items.v1:proposal-decision-authority-warrant-diagnostic",
            merged["sha256"],
            warrant_rows(scenarios, protocol),
            calibrations,
        ))
        receipt_path = args.output_dir / "freeze-receipt.json"
        receipt_doc = {
            "protocol_exact_file_sha256": exact_sha(PROTOCOL_PATH),
            "source_scenarios_sha256": merged["sha256"],
            "reader_calls": 0,
            "files": receipts,
        }
        receipt_path.write_text(json.dumps(receipt_doc, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt_doc, indent=2))
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
