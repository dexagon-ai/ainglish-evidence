#!/usr/bin/env python3
"""Offline audit of a remote-reader result and its durable one-shot journal."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from common import (
    CODES,
    REPO,
    ROOT,
    add_digest,
    checked,
    decode_code,
    file_sha256,
    format_passed,
    observed_format,
    observed_semantic,
    semantic_passed,
    validate_plan_contract,
)


def check_transport_projection(row: dict, requested_model: str) -> None:
    raw = row.get("raw_output")
    if not isinstance(raw, str) or row.get("raw_output_sha256") != hashlib.sha256(raw.encode()).hexdigest():
        raise SystemExit("REFUSING: raw output digest projection drift")
    if row.get("parsed_code") != decode_code(raw):
        raise SystemExit("REFUSING: parsed choice projection drift")
    truncated = row.get("finish_reason") in ("length", "max_tokens")
    if row.get("truncated") is not truncated:
        raise SystemExit("REFUSING: truncation projection drift")
    reported = row.get("response_model")
    mismatch = bool(reported) and reported != requested_model
    if row.get("response_model_mismatch") is not mismatch:
        raise SystemExit("REFUSING: response-model mismatch projection drift")


def audit_format(plan: dict, rows: list[dict]) -> dict:
    controls = plan["format_stage"]["controls"]
    if len(rows) != len(controls):
        raise SystemExit("REFUSING: format row count drift")
    for row, control in zip(rows, controls):
        check_transport_projection(row, plan["transport"]["model"])
        if (row.get("stage"), row.get("control_id"), row.get("target")) != \
                ("format", control["id"], control["target"]):
            raise SystemExit("REFUSING: format identity/order drift")
        valid = row["parsed_code"] is not None and not row["truncated"]
        correct = row["parsed_code"] == control["target"] and not row["truncated"]
        if row.get("valid_choice") is not valid or row.get("target_correct") is not correct:
            raise SystemExit("REFUSING: format verdict projection drift")
    return observed_format(rows)


def audit_semantic(plan: dict, packet: dict, rows: list[dict], exposed: bool) -> dict | None:
    if not exposed:
        if rows:
            raise SystemExit("REFUSING: semantic rows exist after a failed format gate")
        return None
    if len(rows) != len(packet["items"]):
        raise SystemExit("REFUSING: semantic row count drift")
    for row, item in zip(rows, packet["items"]):
        check_transport_projection(row, plan["transport"]["model"])
        mapping = {CODES[index]: label for index, label in enumerate(item["options"])}
        expected_code = next(code for code, label in mapping.items() if label == item["answer"])
        parsed_label = mapping.get(row["parsed_code"])
        expected_identity = ("semantic", item["id"], item["axis"], item["answer"], expected_code)
        got_identity = (
            row.get("stage"), row.get("item_id"), row.get("axis"),
            row.get("expected_label"), row.get("expected_code"),
        )
        if got_identity != expected_identity:
            raise SystemExit("REFUSING: semantic identity/key projection drift")
        valid = row["parsed_code"] is not None and not row["truncated"]
        correct = parsed_label == item["answer"] and not row["truncated"]
        if row.get("parsed_label") != parsed_label or row.get("valid_choice") is not valid \
                or row.get("correct") is not correct:
            raise SystemExit("REFUSING: semantic verdict projection drift")
    return observed_semantic(packet, rows)


def journal_rows(path: Path) -> tuple[list[dict], list[dict]]:
    format_rows = []
    semantic_rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("event") != "cell_recorded":
            continue
        if event.get("stage") == "format":
            format_rows.append(event["row"])
        elif event.get("stage") == "semantic":
            semantic_rows.append(event["row"])
        else:
            raise SystemExit("REFUSING: journal contains an unknown recorded-cell stage")
    return format_rows, semantic_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--write")
    args = parser.parse_args()
    plan = checked(ROOT / args.plan)
    validate_plan_contract(plan)
    result_path = ROOT / args.result
    result = checked(result_path)
    packet = checked(REPO / plan["semantic_stage"]["packet"]["file"])
    if result.get("plan_sha256") != plan["content_sha256"]:
        raise SystemExit("REFUSING: result points to a different plan")
    if result.get("candidate") != plan["candidate"] or result.get("transport") != plan["transport"]:
        raise SystemExit("REFUSING: result candidate/transport drift")

    journal_path = ROOT / result["attempt_journal"]["file"]
    if file_sha256(journal_path) != result["attempt_journal"]["sha256"]:
        raise SystemExit("REFUSING: attempt journal digest drift")
    recorded_format, recorded_semantic = journal_rows(journal_path)
    if recorded_format != result["format"]["rows"] or recorded_semantic != result["semantic"]["rows"]:
        raise SystemExit("REFUSING: result rows differ from the durable attempt journal")

    format_observed = audit_format(plan, result["format"]["rows"])
    format_ok = format_passed(format_observed)
    semantic_observed = audit_semantic(
        plan, packet, result["semantic"]["rows"], format_ok,
    )
    semantic_ok = semantic_passed(
        plan["semantic_stage"]["gate"], semantic_observed
    ) if semantic_observed else False
    catalog = result["catalog"]
    expected_binding = plan["candidate"].get("model_catalog_binding")
    catalog_stable = expected_binding is None or (
        catalog.get("before") == expected_binding
        and catalog.get("after") == expected_binding
        and catalog.get("after_fault") is None
    )
    passed = format_ok and semantic_ok and catalog_stable
    if result["format"]["observed"] != format_observed or result["format"]["passed"] is not format_ok:
        raise SystemExit("REFUSING: format aggregate projection drift")
    if result["semantic"]["observed"] != semantic_observed \
            or result["semantic"]["passed"] is not semantic_ok:
        raise SystemExit("REFUSING: semantic aggregate projection drift")
    if catalog.get("stable") is not catalog_stable or result.get("passed") is not passed:
        raise SystemExit("REFUSING: final qualification verdict projection drift")
    if result.get("model_calls_attempted") != len(recorded_format) + len(recorded_semantic):
        raise SystemExit("REFUSING: model-call count drift")

    audit = {
        "kind": "ainglish.panel.remote-reader-qualification-result-audit.v1",
        "plan_sha256": plan["content_sha256"],
        "result": {"file": result_path.name, "content_sha256": result["content_sha256"]},
        "journal": {"file": journal_path.name, "sha256": result["attempt_journal"]["sha256"]},
        "format_observed": format_observed,
        "semantic_observed": semantic_observed,
        "catalog_stable": catalog_stable,
        "passed": passed,
        "model_calls": 0,
        "network_calls": 0,
        "status": "passed-with-result" if passed else "passed-with-adverse-result",
    }
    add_digest(audit)
    if args.write:
        output = ROOT / args.write
        if output.exists():
            raise SystemExit(f"REFUSING: audit output already exists: {output}")
        with output.open("x", encoding="utf-8") as handle:
            json.dump(audit, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
