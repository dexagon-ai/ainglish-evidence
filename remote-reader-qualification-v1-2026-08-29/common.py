#!/usr/bin/env python3
"""Shared, model-free contracts for the remote-reader qualification kit."""

from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
API_KEY_ENV = "AINGLISH_READER_API_KEY"
CODES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
CHOICE_CODES = frozenset(CODES[:3])
FORMAT_GATE = {
    "valid_choice_cells_required": 12,
    "target_correct_cells_required": 12,
    "fault_cells_required": 0,
    "truncated_cells_required": 0,
    "response_model_mismatch_cells_required": 0,
}

PACKETS = {
    "development": {
        "file": "reader-qualification-calibration-v1-2026-08-26/development-packet.json",
        "content_sha256": "5e4f755594e88b5bb4aefdff89c93b76f7406ee467ecabfe4c02ecb2beb447a7",
        "items": 24,
        "gate": {
            "valid_choice_cells_required": 24,
            "correct_cells_required": 22,
            "correct_per_axis_required": 2,
            "correct_per_label_required": 7,
            "fault_cells_required": 0,
            "truncated_cells_required": 0,
            "response_model_mismatch_cells_required": 0,
        },
        "pass_meaning": "Eligible only for this kit's frozen holdout; never proposal evidence or reader qualification by itself.",
    },
    "holdout": {
        "file": "reader-qualification-v10-general-2026-08-29/holdout.json",
        "content_sha256": "06c183392234fd4fcedf24bee6dea3804f62e986cb66bad59f46f85c521d2102",
        "items": 64,
        "gate": {
            "valid_choice_cells_required": 64,
            "correct_cells_required": 60,
            "correct_per_axis_required": 7,
            "correct_per_label_required": 0,
            "fault_cells_required": 0,
            "truncated_cells_required": 0,
            "response_model_mismatch_cells_required": 0,
        },
        "pass_meaning": "Qualified ordinary-English remote reader service/model configuration for prospectively frozen general-scope Ainglish comprehension panels.",
    },
}


def canonical(value: dict) -> bytes:
    material = copy.deepcopy(value)
    material.pop("content_sha256", None)
    return json.dumps(
        material, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()


def add_digest(value: dict) -> dict:
    value["content_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    return value


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = value.get("content_sha256")
    actual = hashlib.sha256(canonical(value)).hexdigest()
    if expected != actual:
        raise SystemExit(f"REFUSING: content digest mismatch for {path}: {expected!r} != {actual}")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_loopback_endpoint(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def safe_base_url(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit("REFUSING: candidate.base_url must be a non-empty absolute URL")
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        raise SystemExit("REFUSING: base_url must not contain credentials, a query, or a fragment")
    if parsed.scheme.lower() != "https" and not (
        parsed.scheme.lower() == "http" and is_loopback_endpoint(value)
    ):
        raise SystemExit("REFUSING: remote readers require HTTPS, except for an explicit loopback proxy")
    if not parsed.hostname:
        raise SystemExit("REFUSING: base_url needs an explicit host")
    return value.strip().rstrip("/")


def auth_headers(auth_mode: str) -> dict[str, str]:
    if auth_mode == "none":
        return {}
    if auth_mode != "environment-bearer":
        raise SystemExit(f"REFUSING: unsupported auth_mode {auth_mode!r}")
    key = os.environ.get(API_KEY_ENV, "")
    if not key:
        raise SystemExit(f"REFUSING: auth_mode requires {API_KEY_ENV}, but it is not set")
    return {"Authorization": f"Bearer {key}"}


def request_json(base_url: str, path: str, auth_mode: str, *, payload: dict | None = None,
                 timeout_s: int = 120) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "ainglish-remote-reader-qualification/1"}
    headers.update(auth_headers(auth_mode))
    data = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(base_url.rstrip("/") + path, data=data,
                                     headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("endpoint returned a non-object JSON response")
    return value


def model_catalog_binding(base_url: str, model: str, auth_mode: str) -> dict:
    payload = request_json(base_url, "/models", auth_mode, timeout_s=30)
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise SystemExit("REFUSING: /models returned no data array")
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == model]
    if len(matches) != 1:
        raise SystemExit(f"REFUSING: /models matched {len(matches)} entries for exact id {model!r}")
    entry_bytes = json.dumps(
        matches[0], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode()
    return {
        "source": "openai:/models",
        "requested_model": model,
        "entry_sha256": "sha256:" + hashlib.sha256(entry_bytes).hexdigest(),
        "weight_identity": "provider-opaque",
    }


def format_controls() -> list[dict]:
    phrasings = (
        "Return only target code {target}.",
        "The required one-byte answer is {target}.",
        "Copy {target} and add nothing else.",
        "Select the supplied target, which is {target}.",
    )
    rows = []
    for round_number, wording in enumerate(phrasings, 1):
        for target in "ABC":
            rows.append({
                "id": f"format-{len(rows) + 1:02d}",
                "round": round_number,
                "target": target,
                "instruction": wording.format(target=target),
            })
    return rows


def decode_code(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    code = raw.strip().upper()
    return code if code in CHOICE_CODES else None


def observed_format(rows: list[dict]) -> dict:
    return {
        "valid_choice_cells": sum(row["valid_choice"] for row in rows),
        "target_correct_cells": sum(row["target_correct"] for row in rows),
        "fault_cells": sum(row["fault"] is not None for row in rows),
        "truncated_cells": sum(row["truncated"] for row in rows),
        "response_model_mismatch_cells": sum(row["response_model_mismatch"] for row in rows),
    }


def observed_semantic(packet: dict, rows: list[dict]) -> dict:
    return {
        "valid_choice_cells": sum(row["valid_choice"] for row in rows),
        "correct_cells": sum(row["correct"] for row in rows),
        "correct_by_axis": {
            axis: sum(row["correct"] for row in rows if row["axis"] == axis)
            for axis in packet["axes"]
        },
        "correct_by_label": {
            label: sum(row["correct"] for row in rows if row["expected_label"] == label)
            for label in packet["labels"]
        },
        "fault_cells": sum(row["fault"] is not None for row in rows),
        "truncated_cells": sum(row["truncated"] for row in rows),
        "response_model_mismatch_cells": sum(row["response_model_mismatch"] for row in rows),
    }


def format_passed(observed: dict) -> bool:
    return (
        observed["valid_choice_cells"] == 12
        and observed["target_correct_cells"] == 12
        and observed["fault_cells"] == 0
        and observed["truncated_cells"] == 0
        and observed["response_model_mismatch_cells"] == 0
    )


def semantic_passed(gate: dict, observed: dict) -> bool:
    return (
        observed["valid_choice_cells"] == gate["valid_choice_cells_required"]
        and observed["correct_cells"] >= gate["correct_cells_required"]
        and all(value >= gate["correct_per_axis_required"]
                for value in observed["correct_by_axis"].values())
        and all(value >= gate["correct_per_label_required"]
                for value in observed["correct_by_label"].values())
        and observed["fault_cells"] == gate["fault_cells_required"]
        and observed["truncated_cells"] == gate["truncated_cells_required"]
        and observed["response_model_mismatch_cells"] ==
            gate["response_model_mismatch_cells_required"]
    )


def validate_plan_contract(plan: dict) -> None:
    """Refuse a rehashed plan that weakens or bypasses the kit's frozen decision surface."""
    if plan.get("kind") != "ainglish.panel.remote-reader-qualification-plan.v1" or \
            plan.get("result_kind") != "ainglish.panel.remote-reader-qualification-result.v1":
        raise SystemExit("REFUSING: unsupported remote-reader qualification plan contract")
    phase = plan.get("phase")
    if phase not in PACKETS:
        raise SystemExit("REFUSING: plan phase is not development or holdout")
    packet = PACKETS[phase]
    semantic = plan.get("semantic_stage")
    if not isinstance(semantic, dict) or semantic.get("packet") != {
        "file": packet["file"], "content_sha256": packet["content_sha256"],
    } or semantic.get("gate") != packet["gate"] or semantic.get("pass_meaning") != packet["pass_meaning"]:
        raise SystemExit("REFUSING: semantic packet, gate, or pass meaning drift")
    format_stage = plan.get("format_stage")
    if not isinstance(format_stage, dict) or format_stage.get("answer_protocol") != "opaque-choice-v1" \
            or format_stage.get("controls") != format_controls() \
            or format_stage.get("gate") != FORMAT_GATE:
        raise SystemExit("REFUSING: format controls or gate drift")
    if (phase == "development") != (plan.get("development_receipt") is None):
        raise SystemExit("REFUSING: development receipt is inconsistent with phase")

    candidate = plan.get("candidate")
    transport = plan.get("transport")
    if not isinstance(candidate, dict) or not isinstance(transport, dict):
        raise SystemExit("REFUSING: candidate and transport receipts are required")
    if transport.get("adapter") != "openai-chat-completions-opaque-choice-v1":
        raise SystemExit("REFUSING: transport adapter drift")
    if safe_base_url(transport.get("base_url")) != transport.get("base_url"):
        raise SystemExit("REFUSING: transport base URL normalization drift")
    if transport.get("auth_mode") not in ("none", "environment-bearer") \
            or transport.get("credential_env_name_recorded") is not False:
        raise SystemExit("REFUSING: credential boundary drift")
    if transport.get("model") != candidate.get("model") or not transport.get("model"):
        raise SystemExit("REFUSING: candidate and transport model ids differ")
    for key in ("max_tokens", "timeout_s"):
        value = transport.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise SystemExit(f"REFUSING: transport {key} must be a positive integer")
    sampling = transport.get("sampling")
    if not isinstance(sampling, dict) or set(sampling) - {
        "temperature", "seed", "top_p", "reasoning_effort",
    }:
        raise SystemExit("REFUSING: transport sampling vocabulary drift")
    temperature = sampling.get("temperature")
    if "temperature" in sampling and temperature is not None and (
        isinstance(temperature, bool) or not isinstance(temperature, (int, float))
        or not 0 <= temperature <= 2
    ):
        raise SystemExit("REFUSING: transport temperature drift")
    top_p = sampling.get("top_p")
    if "top_p" in sampling and (
        isinstance(top_p, bool) or not isinstance(top_p, (int, float)) or not 0 <= top_p <= 1
    ):
        raise SystemExit("REFUSING: transport top_p drift")
    if "seed" in sampling and (
        isinstance(sampling["seed"], bool) or not isinstance(sampling["seed"], int)
    ):
        raise SystemExit("REFUSING: transport seed drift")
    effort = sampling.get("reasoning_effort")
    if effort is not None and effort not in {"none", "minimal", "low", "medium", "high", "xhigh", "max"}:
        raise SystemExit("REFUSING: transport reasoning_effort drift")
    if effort not in (None, "none") and any(
        key in sampling and sampling[key] is not None for key in ("temperature", "top_p")
    ):
        raise SystemExit("REFUSING: non-none reasoning effort cannot carry temperature/top_p")
    binding = candidate.get("model_catalog_binding")
    if candidate.get("model_digest") is not None:
        raise SystemExit("REFUSING: a hosted remote-reader plan may not claim an unverified weight digest")
    if binding is None:
        if candidate.get("digest_source") != "provider-opaque":
            raise SystemExit("REFUSING: opaque hosted reader digest-source drift")
    elif not isinstance(binding, dict) or binding.get("source") != "openai:/models" \
            or binding.get("requested_model") != candidate.get("model") \
            or binding.get("weight_identity") != "provider-opaque" \
            or candidate.get("digest_source") != "provider-catalog:openai:/models" \
            or not isinstance(binding.get("entry_sha256"), str) \
            or len(binding["entry_sha256"]) != 71 \
            or not binding["entry_sha256"].startswith("sha256:") \
            or any(ch not in "0123456789abcdef" for ch in binding["entry_sha256"][7:]):
        raise SystemExit("REFUSING: hosted model-catalog binding drift")
