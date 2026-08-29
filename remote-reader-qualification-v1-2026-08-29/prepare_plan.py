#!/usr/bin/env python3
"""Freeze an exact remote-reader development or holdout plan without inference calls."""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

from common import FORMAT_GATE, PACKETS, REPO, ROOT, add_digest, checked, format_controls, model_catalog_binding, safe_base_url


REQUIRED = frozenset({
    "name", "lineage", "producer", "families", "service", "provider", "base_url",
    "auth_mode", "model", "precision", "model_catalog", "sampling", "max_tokens", "timeout_s",
    "official_reference", "lineage_caveat",
})
SAMPLER_KEYS = frozenset({"temperature", "seed", "top_p", "reasoning_effort"})
EFFORTS = frozenset({"none", "minimal", "low", "medium", "high", "xhigh", "max"})


def load_candidate(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("REFUSING: candidate configuration must be one JSON object")
    missing = sorted(REQUIRED - set(value))
    unknown = sorted(set(value) - REQUIRED)
    if missing or unknown:
        raise SystemExit(f"REFUSING: candidate keys missing={missing}, unknown={unknown}")
    for key in ("name", "lineage", "producer", "service", "provider", "model", "precision",
                "official_reference", "lineage_caveat"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise SystemExit(f"REFUSING: candidate.{key} must be a non-empty string")
        value[key] = value[key].strip()
    if not isinstance(value["families"], list) or not value["families"] or any(
        not isinstance(item, str) or not item.strip() for item in value["families"]
    ):
        raise SystemExit("REFUSING: candidate.families must be a non-empty string array")
    value["families"] = [item.strip() for item in value["families"]]
    value["base_url"] = safe_base_url(value["base_url"])
    if value["auth_mode"] not in ("none", "environment-bearer"):
        raise SystemExit("REFUSING: auth_mode must be none or environment-bearer")
    if value["model_catalog"] not in (None, "openai:/models"):
        raise SystemExit("REFUSING: model_catalog must be null or openai:/models")
    for key in ("max_tokens", "timeout_s"):
        if isinstance(value[key], bool) or not isinstance(value[key], int) or value[key] <= 0:
            raise SystemExit(f"REFUSING: candidate.{key} must be a positive integer")
    sampling = value["sampling"]
    if not isinstance(sampling, dict) or set(sampling) - SAMPLER_KEYS:
        raise SystemExit(f"REFUSING: sampling must contain only {sorted(SAMPLER_KEYS)}")
    if "temperature" in sampling:
        temperature = sampling["temperature"]
        if temperature is not None and (
            isinstance(temperature, bool) or not isinstance(temperature, (int, float))
            or not 0 <= temperature <= 2
        ):
            raise SystemExit("REFUSING: sampling.temperature must be null or a number from 0 to 2")
    if "top_p" in sampling:
        top_p = sampling["top_p"]
        if isinstance(top_p, bool) or not isinstance(top_p, (int, float)) or not 0 <= top_p <= 1:
            raise SystemExit("REFUSING: sampling.top_p must be a number from 0 to 1")
    if "seed" in sampling and (
        isinstance(sampling["seed"], bool) or not isinstance(sampling["seed"], int)
    ):
        raise SystemExit("REFUSING: sampling.seed must be an integer")
    effort = sampling.get("reasoning_effort")
    if effort is not None and effort not in EFFORTS:
        raise SystemExit(f"REFUSING: reasoning_effort must be one of {sorted(EFFORTS)}")
    if effort not in (None, "none") and any(key in sampling and sampling[key] is not None
                                             for key in ("temperature", "top_p")):
        raise SystemExit("REFUSING: non-none reasoning_effort cannot be combined with temperature/top_p")
    return value


def candidate_receipt(config: dict) -> tuple[dict, dict]:
    catalog = config["model_catalog"]
    binding = (model_catalog_binding(
        config["base_url"], config["model"], config["auth_mode"]
    ) if catalog == "openai:/models" else None)
    candidate = {
        "name": config["name"],
        "lineage": config["lineage"],
        "producer": config["producer"],
        "families": config["families"],
        "service": config["service"],
        "provider": config["provider"],
        "model": config["model"],
        "precision": config["precision"],
        "model_digest": None,
        "digest_source": ("provider-catalog:openai:/models" if binding else "provider-opaque"),
        "model_catalog_binding": binding,
        "official_reference": config["official_reference"],
        "lineage_caveat": config["lineage_caveat"],
    }
    transport = {
        "adapter": "openai-chat-completions-opaque-choice-v1",
        "base_url": config["base_url"],
        "auth_mode": config["auth_mode"],
        "credential_env_name_recorded": False,
        "model": config["model"],
        "sampling": config["sampling"],
        "max_tokens": config["max_tokens"],
        "timeout_s": config["timeout_s"],
    }
    return candidate, transport


def relative_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return str(path.resolve())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--phase", choices=sorted(PACKETS), required=True)
    parser.add_argument("--development-result")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    config = load_candidate(Path(args.candidate))
    candidate, transport = candidate_receipt(config)
    packet_contract = PACKETS[args.phase]
    packet = checked(REPO / packet_contract["file"])
    if packet["content_sha256"] != packet_contract["content_sha256"] or \
            len(packet["items"]) != packet_contract["items"]:
        raise SystemExit("REFUSING: qualification packet drift")

    development_receipt = None
    if args.phase == "holdout":
        if not args.development_result:
            raise SystemExit("REFUSING: holdout planning requires --development-result")
        development_path = Path(args.development_result)
        development = checked(development_path)
        if development.get("phase") != "development" or development.get("passed") is not True:
            raise SystemExit("REFUSING: holdout requires a passed development result")
        if development.get("candidate") != candidate or development.get("transport") != transport:
            raise SystemExit("REFUSING: candidate/service/catalog/transport changed since development")
        development_receipt = {
            "file": relative_to_repo(development_path),
            "content_sha256": development["content_sha256"],
        }
    elif args.development_result:
        raise SystemExit("REFUSING: --development-result is valid only for holdout planning")

    plan = {
        "kind": "ainglish.panel.remote-reader-qualification-plan.v1",
        "result_kind": "ainglish.panel.remote-reader-qualification-result.v1",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "phase": args.phase,
        "prepared_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "freeze_rule": "Publish this exact plan and its content_sha256 at a publicly retrievable immutable URL, or as exact JSON in the Colony qualification thread, before its first model call; a git commit is one valid carrier, not a requirement. Never retry a burned cell.",
        "candidate": candidate,
        "transport": transport,
        "format_stage": {
            "answer_protocol": "opaque-choice-v1",
            "controls": format_controls(),
            "gate": FORMAT_GATE,
            "failure_action": "Publish the format result and expose zero semantic items.",
        },
        "semantic_stage": {
            "packet": {
                "file": packet_contract["file"],
                "content_sha256": packet_contract["content_sha256"],
            },
            "prompt_contract": "Given only the ordinary-English premise, classify the hypothesis as entailed, contradicted, or not determined. Return exactly the opaque choice code selected from the supplied mapping and nothing else.",
            "gate": packet_contract["gate"],
            "pass_meaning": packet_contract["pass_meaning"],
        },
        "development_receipt": development_receipt,
        "model_calls_at_freeze": 0,
        "metadata_calls_at_freeze": 1 if candidate["model_catalog_binding"] else 0,
    }
    add_digest(plan)
    output = ROOT / args.output
    if output.exists():
        raise SystemExit(f"REFUSING: output already exists: {output}")
    with output.open("x", encoding="utf-8") as handle:
        json.dump(plan, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({
        "output": output.name,
        "phase": args.phase,
        "plan_sha256": plan["content_sha256"],
        "candidate": candidate["name"],
        "model": candidate["model"],
        "model_calls": 0,
        "metadata_calls": plan["metadata_calls_at_freeze"],
        "next": "publish the exact plan and content_sha256 before run_once.py",
    }, indent=2))


if __name__ == "__main__":
    main()
