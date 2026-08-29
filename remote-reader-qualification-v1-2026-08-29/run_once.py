#!/usr/bin/env python3
"""Run one frozen remote-reader qualification plan exactly once, without retries."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import urllib.error

from common import (
    CODES,
    REPO,
    ROOT,
    add_digest,
    checked,
    decode_code,
    format_passed,
    model_catalog_binding,
    observed_format,
    observed_semantic,
    request_json,
    semantic_passed,
    validate_plan_contract,
)


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def fault_label(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "url_error"
    if isinstance(exc, (TimeoutError, OSError)) and "timed out" in str(exc).lower():
        return "timeout"
    return type(exc).__name__


def reasoning_bytes(message: dict) -> int:
    value = message.get("reasoning_content", message.get("reasoning", ""))
    if value in (None, ""):
        return 0
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return len(value.encode())


def request_cell(plan: dict, prompt: str) -> dict:
    transport = plan["transport"]
    sampling = {key: value for key, value in transport["sampling"].items() if value is not None}
    body = {
        "model": transport["model"],
        **sampling,
        "max_tokens": transport["max_tokens"],
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = request_json(
            transport["base_url"], "/chat/completions", transport["auth_mode"],
            payload=body, timeout_s=transport["timeout_s"],
        )
        choices = response.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise ValueError("response_choices_shape")
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ValueError("response_message_shape")
        finish_reason = choice.get("finish_reason")
        raw = message["content"]
        reported_model = response.get("model")
        mismatch = bool(reported_model) and reported_model != transport["model"]
        return {
            "raw_output": raw,
            "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "finish_reason": finish_reason,
            "truncated": finish_reason in ("length", "max_tokens"),
            "fault": None,
            "response_model": reported_model,
            "response_model_mismatch": mismatch,
            "system_fingerprint": response.get("system_fingerprint"),
            "reasoning_bytes_returned": reasoning_bytes(message),
            "usage": response.get("usage") if isinstance(response.get("usage"), dict) else None,
        }
    except Exception as exc:
        return {
            "raw_output": "",
            "raw_output_sha256": hashlib.sha256(b"").hexdigest(),
            "finish_reason": None,
            "truncated": False,
            "fault": fault_label(exc),
            "response_model": None,
            "response_model_mismatch": False,
            "system_fingerprint": None,
            "reasoning_bytes_returned": 0,
            "usage": None,
        }


def journal_write(handle, value: dict) -> None:
    handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def run_format(plan: dict, journal, ordinal: int) -> tuple[list[dict], int]:
    rows = []
    for control in plan["format_stage"]["controls"]:
        ordinal += 1
        journal_write(journal, {
            "event": "cell_attempted", "stage": "format", "ordinal": ordinal,
            "control_id": control["id"],
        })
        response = request_cell(
            plan,
            "This is a transport-format control. " + control["instruction"] +
            " Answer with EXACTLY one choice code and nothing else.",
        )
        parsed_code = decode_code(response["raw_output"])
        row = {
            "stage": "format",
            "control_id": control["id"],
            "target": control["target"],
            **response,
            "parsed_code": parsed_code,
            "valid_choice": parsed_code is not None and not response["truncated"],
            "target_correct": parsed_code == control["target"] and not response["truncated"],
        }
        rows.append(row)
        journal_write(journal, {
            "event": "cell_recorded", "stage": "format", "ordinal": ordinal, "row": row,
        })
    return rows, ordinal


def semantic_prompt(plan: dict, item: dict) -> tuple[str, dict[str, str]]:
    mapping = {CODES[index]: label for index, label in enumerate(item["options"])}
    choices = "\n".join(f"{code}: {label}" for code, label in mapping.items())
    prompt = (
        plan["semantic_stage"]["prompt_contract"] +
        "\n\nPremise:\n---\n" + item["premise"] +
        "\n---\n\nHypothesis: " + item["hypothesis"] +
        "\nChoices:\n" + choices +
        "\nAnswer with EXACTLY one choice code and nothing else."
    )
    return prompt, mapping


def run_semantic(plan: dict, packet: dict, journal, ordinal: int) -> tuple[list[dict], int]:
    rows = []
    for item in packet["items"]:
        ordinal += 1
        journal_write(journal, {
            "event": "cell_attempted", "stage": "semantic", "ordinal": ordinal,
            "item_id": item["id"],
        })
        prompt, mapping = semantic_prompt(plan, item)
        response = request_cell(plan, prompt)
        parsed_code = decode_code(response["raw_output"])
        parsed_label = mapping.get(parsed_code)
        expected_code = next(code for code, label in mapping.items() if label == item["answer"])
        row = {
            "stage": "semantic",
            "item_id": item["id"],
            "axis": item["axis"],
            "expected_label": item["answer"],
            "expected_code": expected_code,
            **response,
            "parsed_code": parsed_code,
            "parsed_label": parsed_label,
            "valid_choice": parsed_code is not None and not response["truncated"],
            "correct": parsed_label == item["answer"] and not response["truncated"],
        }
        rows.append(row)
        journal_write(journal, {
            "event": "cell_recorded", "stage": "semantic", "ordinal": ordinal, "row": row,
        })
    return rows, ordinal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()
    plan_path = ROOT / args.plan
    plan = checked(plan_path)
    validate_plan_contract(plan)
    packet = checked(REPO / plan["semantic_stage"]["packet"]["file"])
    if packet["content_sha256"] != plan["semantic_stage"]["packet"]["content_sha256"]:
        raise SystemExit("REFUSING: semantic packet drift")
    if plan["phase"] == "holdout":
        development_file = Path(plan["development_receipt"]["file"])
        if not development_file.is_absolute():
            development_file = REPO / development_file
        development = checked(development_file)
        if development["content_sha256"] != plan["development_receipt"]["content_sha256"] \
                or development.get("phase") != "development" \
                or development.get("passed") is not True \
                or development.get("candidate") != plan["candidate"] \
                or development.get("transport") != plan["transport"]:
            raise SystemExit("REFUSING: holdout development receipt drift")

    stem = plan_path.stem
    journal_path = ROOT / f"{stem}-attempt-journal.jsonl"
    result_path = ROOT / f"{stem}-result.json"
    if journal_path.exists() or result_path.exists():
        raise SystemExit("REFUSING: journal or result already exists; never rerun burned cells")

    expected_binding = plan["candidate"].get("model_catalog_binding")
    live_binding = None
    if expected_binding is not None:
        live_binding = model_catalog_binding(
            plan["transport"]["base_url"], plan["transport"]["model"],
            plan["transport"]["auth_mode"],
        )
        if live_binding != expected_binding:
            raise SystemExit("REFUSING: live model catalog binding changed since plan freeze")

    started = utcnow()
    format_rows = []
    semantic_rows = []
    ordinal = 0
    with journal_path.open("x", encoding="utf-8") as journal:
        journal_write(journal, {
            "event": "run_started", "started_at": started,
            "plan_sha256": plan["content_sha256"], "catalog_binding": live_binding,
        })
        format_rows, ordinal = run_format(plan, journal, ordinal)
        format_observed = observed_format(format_rows)
        format_ok = format_passed(format_observed)
        journal_write(journal, {
            "event": "format_completed", "observed": format_observed, "passed": format_ok,
        })
        if format_ok:
            semantic_rows, ordinal = run_semantic(plan, packet, journal, ordinal)
        semantic_observed = observed_semantic(packet, semantic_rows) if semantic_rows else None
        semantic_ok = semantic_passed(
            plan["semantic_stage"]["gate"], semantic_observed
        ) if semantic_observed else False
        journal_write(journal, {
            "event": "semantic_completed", "exposed": format_ok,
            "observed": semantic_observed, "passed": semantic_ok,
        })

    post_binding = None
    post_catalog_fault = None
    if expected_binding is not None:
        try:
            post_binding = model_catalog_binding(
                plan["transport"]["base_url"], plan["transport"]["model"],
                plan["transport"]["auth_mode"],
            )
        except Exception as exc:
            post_catalog_fault = fault_label(exc)
    catalog_stable = expected_binding is None or (
        post_catalog_fault is None and post_binding == expected_binding
    )
    passed = format_ok and semantic_ok and catalog_stable
    result = {
        "kind": plan["result_kind"],
        "evidentiary_status": plan["evidentiary_status"],
        "phase": plan["phase"],
        "plan_sha256": plan["content_sha256"],
        "candidate": plan["candidate"],
        "transport": plan["transport"],
        "started_at": started,
        "completed_at": utcnow(),
        "model_calls_attempted": len(format_rows) + len(semantic_rows),
        "catalog": {
            "before": live_binding,
            "after": post_binding,
            "after_fault": post_catalog_fault,
            "stable": catalog_stable,
        },
        "attempt_journal": {
            "file": journal_path.name,
            "sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest(),
        },
        "format": {"observed": format_observed, "passed": format_ok, "rows": format_rows},
        "semantic": {
            "exposed": format_ok,
            "observed": semantic_observed,
            "passed": semantic_ok,
            "rows": semantic_rows,
        },
        "passed": passed,
        "pass_meaning": plan["semantic_stage"]["pass_meaning"] if passed else None,
        "no_retries": True,
    }
    add_digest(result)
    with result_path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({
        "result": result_path.name,
        "candidate": result["candidate"]["name"],
        "phase": result["phase"],
        "format": {"observed": format_observed, "passed": format_ok},
        "semantic": {"observed": semantic_observed, "passed": semantic_ok},
        "catalog_stable": catalog_stable,
        "passed": passed,
        "content_sha256": result["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
