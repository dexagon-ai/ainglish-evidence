#!/usr/bin/env python3
"""Freeze and execute the preregistered benchmark against existing Ollama readers."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BENCHMARK_ROOT = ROOT.parent / "end-to-end-agent-task-benchmark-v0.1-2026-08-28"
BENCHMARK_PATH = BENCHMARK_ROOT / "benchmark.py"
ROSTER_PATH = ROOT / "reader-roster.json"
PROMPTS_PATH = ROOT / "prompts.jsonl"
PLAN_PATH = ROOT / "RUN_PLAN.json"
CHECKSUM_PATH = ROOT / "SHA256SUMS.preregistered"
RESULTS_ROOT = ROOT / "results"
RESPONSES_PATH = RESULTS_ROOT / "responses.jsonl"
INFLIGHT_PATH = RESULTS_ROOT / "inflight.json"
OLLAMA_BASE = "http://127.0.0.1:11434"
FROZEN_AT = "2026-08-28T22:22:14Z"
SCHEDULE_SEED = 2026082801
DECODING_SEED = 20260828
REQUEST_TIMEOUT_SECONDS = 600
EMPTY_SENTINEL = "[EMPTY OUTPUT]"

ALLOWED_MODELS = (
    "command-r7b:latest",
    "deepseek-v2:16b",
    "exaone3.5:32b",
    "falcon3:10b",
    "gemma3:12b",
    "glm4:9b",
    "granite3.3:8b",
    "internlm2:20b",
    "lfm2:24b",
    "llama3.1:8b",
    "mistral-small3.2:24b-instruct-2506-q4_K_M",
    "olmo2:13b",
    "phi4:14b",
    "qwen2.5:7b",
    "qwen3.5:9b",
    "qwen3.5:27b",
    "qwen3.5:35b-a3b",
    "qwen3.6:27b",
    "qwen3.6:35b",
    "qwen3.8-27b-q4:latest",
    "solar-pro:22b",
    "yi:34b",
)

REQUEST_PARAMETERS = {
    "format": "json",
    "keep_alive": "15m",
    "options": {
        "num_ctx": 4096,
        "num_predict": 96,
        "seed": DECODING_SEED,
        "temperature": 0,
    },
    "stream": False,
    "think": False,
}

CHECKSUM_INPUTS = (
    ROOT / "README.md",
    ROOT / "RUN_PROTOCOL.md",
    ROOT / "run_ollama.py",
    ROOT / "analyse.py",
    ROSTER_PATH,
    PROMPTS_PATH,
    PLAN_PATH,
    BENCHMARK_ROOT / "README.md",
    BENCHMARK_ROOT / "SCORING.md",
    BENCHMARK_ROOT / "MANIFEST.json",
    BENCHMARK_ROOT / "tasks.json",
    BENCHMARK_ROOT / "benchmark.py",
)


def load_benchmark() -> Any:
    spec = importlib.util.spec_from_file_location("ainglish_agent_task_benchmark", BENCHMARK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark module from {BENCHMARK_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BENCHMARK = load_benchmark()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def append_synced(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical_json(record))
        handle.flush()
        os.fsync(handle.fileno())


def http_json(path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None if payload is None else canonical_json(payload)
    request = urllib.request.Request(
        OLLAMA_BASE + path,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        parsed = json.loads(response.read())
    if not isinstance(parsed, dict):
        raise RuntimeError(f"{path} returned a non-object")
    return parsed


def prepare() -> None:
    existing = [path for path in (ROSTER_PATH, PROMPTS_PATH, PLAN_PATH, CHECKSUM_PATH) if path.exists()]
    if existing:
        raise RuntimeError("refusing to replace frozen artifacts: " + ", ".join(str(path.name) for path in existing))

    tags_response = http_json("/api/tags")
    version_response = http_json("/api/version")
    available = {record.get("name"): record for record in tags_response.get("models", [])}
    missing = [name for name in ALLOWED_MODELS if name not in available]
    if missing:
        raise RuntimeError("allowlisted readers are not installed; no pull will be attempted: " + ", ".join(missing))

    roster = []
    seen_digests: set[str] = set()
    for index, name in enumerate(ALLOWED_MODELS, 1):
        tag = available[name]
        digest = tag.get("digest")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise RuntimeError(f"{name}: missing immutable SHA-256 digest")
        if digest in seen_digests:
            raise RuntimeError(f"{name}: allowlist contains a duplicate served digest")
        seen_digests.add(digest)
        show = http_json("/api/show", {"model": name})
        capabilities = show.get("capabilities", [])
        if "completion" not in capabilities:
            raise RuntimeError(f"{name}: artifact does not declare completion capability")
        reader_id = f"ollama/{name}@sha256:{digest}"
        roster.append({
            "index": index,
            "tag": name,
            "digest": digest,
            "reader_id": reader_id,
            "tag_record": tag,
            "served_artifact": show,
            "served_artifact_sha256": sha256_bytes(canonical_json(show)),
        })

    packet = BENCHMARK.load_tasks()
    cells = []
    for item in packet["items"]:
        for track in BENCHMARK.TRACKS:
            for arm in BENCHMARK.ARMS:
                prompt = BENCHMARK.prompt_for(item, arm, track)
                cells.append({
                    "item_id": item["id"],
                    "construct": item["construct"],
                    "arm": arm,
                    "track": track,
                    "prompt": prompt,
                    "prompt_sha256": sha256_bytes(prompt.encode()),
                    "clarification": item["clarification"],
                    "clarification_sha256": sha256_bytes(item["clarification"].encode()),
                })
    random.Random(SCHEDULE_SEED).shuffle(cells)
    scheduled = [
        {"order": order, "cell_id": f"cell-{order:03d}", **cell}
        for order, cell in enumerate(cells, 1)
    ]
    if len(scheduled) != 132:
        raise RuntimeError(f"expected 132 cells, got {len(scheduled)}")

    roster_doc = {
        "schema": "ainglish.agent-task-ollama-reader-roster.v0.1",
        "frozen_at": FROZEN_AT,
        "operator": "Dexagon",
        "ollama_base": OLLAMA_BASE,
        "ollama_version": version_response.get("version"),
        "selection": "explicit already-installed general-purpose completion tags",
        "exclusions": [
            "dexagon-* task-specialized aliases",
            "hf.co/* and other duplicate aliases or digests",
            "incomplete Hugging Face cache entries",
            "non-completion artifacts",
        ],
        "readers": roster,
    }
    plan = {
        "schema": "ainglish.agent-task-ollama-run-plan.v0.1",
        "frozen_at": FROZEN_AT,
        "benchmark_commit": "028052715cfa61744fab0ca92268f71073de2246",
        "task_packet_sha256": sha256_bytes(BENCHMARK.canonical_json(packet)),
        "schedule_seed": SCHEDULE_SEED,
        "decoding_seed": DECODING_SEED,
        "cells_per_reader": len(scheduled),
        "reader_count": len(roster),
        "planned_observations": len(scheduled) * len(roster),
        "parallelism": 1,
        "fresh_conversation_per_cell": True,
        "request_timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "request_parameters": REQUEST_PARAMETERS,
        "repair_wrapper": "Clarification from sender: <the frozen scripted clarification>\n\nRespond under the original JSON-only contract.",
        "retry_policy": "no inference retries; interrupted first calls are invalid and interrupted repairs are missing",
        "linkage": {
            "operator_to_project": "linked",
            "task_designer_to_project": "linked",
            "operator_to_task_designer": "linked",
            "model_training_exposure": "unknown",
            "reader_family_dependence": "unknown and plausibly shared",
        },
        "roster_sha256": sha256_bytes(pretty_json(roster_doc)),
        "prompts_sha256": sha256_bytes(b"".join(canonical_json(record) for record in scheduled)),
    }

    atomic_write(ROSTER_PATH, pretty_json(roster_doc))
    atomic_write(PROMPTS_PATH, b"".join(canonical_json(record) for record in scheduled))
    atomic_write(PLAN_PATH, pretty_json(plan))
    write_checksums()
    print(json.dumps({
        "ok": True,
        "readers": len(roster),
        "cells_per_reader": len(scheduled),
        "planned_observations": len(roster) * len(scheduled),
        "no_downloads": True,
    }, sort_keys=True))


def relative_label(path: Path) -> str:
    return os.path.relpath(path, ROOT)


def write_checksums() -> None:
    missing = [path for path in CHECKSUM_INPUTS if not path.exists()]
    if missing:
        raise RuntimeError("cannot freeze checksums; missing: " + ", ".join(map(str, missing)))
    lines = [f"{sha256_file(path)}  {relative_label(path)}\n" for path in CHECKSUM_INPUTS]
    atomic_write(CHECKSUM_PATH, "".join(lines).encode())


def verify() -> None:
    if not CHECKSUM_PATH.exists():
        raise RuntimeError("missing preregistered checksum file")
    failures = []
    count = 0
    for raw_line in CHECKSUM_PATH.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        digest, label = raw_line.split("  ", 1)
        path = (ROOT / label).resolve()
        count += 1
        if not path.exists():
            failures.append(f"missing {label}")
        elif sha256_file(path) != digest:
            failures.append(f"digest mismatch {label}")
    if failures:
        raise RuntimeError("preregistered verification failed: " + "; ".join(failures))
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    tags = {record.get("name"): record for record in http_json("/api/tags").get("models", [])}
    for reader in roster["readers"]:
        current = tags.get(reader["tag"])
        if current is None or current.get("digest") != reader["digest"]:
            raise RuntimeError(f"served artifact changed or disappeared: {reader['tag']}")
    print(json.dumps({"ok": True, "files": count, "readers": len(roster["readers"])}, sort_keys=True))


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_number}: corrupt JSONL: {exc}") from exc
            if not isinstance(row, dict):
                raise RuntimeError(f"{path}:{line_number}: non-object row")
            rows.append(row)
    return rows


def response_usage(receipt: dict[str, Any], wall_ms: float) -> dict[str, float]:
    usage: dict[str, float] = {}
    prompt_count = receipt.get("prompt_eval_count")
    eval_count = receipt.get("eval_count")
    if isinstance(prompt_count, (int, float)) and prompt_count >= 0:
        usage["input_tokens"] = prompt_count
    if isinstance(eval_count, (int, float)) and eval_count >= 0:
        usage["output_tokens"] = eval_count
    total_duration = receipt.get("total_duration")
    usage["latency_ms"] = (
        total_duration / 1_000_000
        if isinstance(total_duration, (int, float)) and total_duration >= 0
        else round(wall_ms, 3)
    )
    return usage


def strict_decision(raw: str, action_ids: set[str], usage: dict[str, float], where: str) -> tuple[dict[str, Any], str | None]:
    try:
        decoded = json.loads(raw.strip())
        if not isinstance(decoded, dict):
            raise BENCHMARK.ContractError("response must be a JSON object")
        expected_keys = {
            "act": {"decision", "actions"},
            "clarify": {"decision", "question"},
        }.get(decoded.get("decision"))
        if expected_keys is None or set(decoded) != expected_keys:
            raise BENCHMARK.ContractError("response keys do not exactly match the JSON-only contract")
        normalized = BENCHMARK.normalize_decision(decoded, action_ids, where)
        result = {"decision": normalized["decision"]}
        if normalized["decision"] == "act":
            result["actions"] = normalized["actions"]
        else:
            result["question"] = normalized["question"]
        result.update(usage)
        return result, None
    except (json.JSONDecodeError, BENCHMARK.ContractError) as exc:
        return {"decision": "invalid", "raw": raw if raw else EMPTY_SENTINEL, **usage}, str(exc)


def chat(model: str, messages: list[dict[str, str]]) -> tuple[dict[str, Any], float]:
    payload = {"model": model, "messages": messages, **REQUEST_PARAMETERS}
    started = time.monotonic()
    receipt = http_json("/api/chat", payload, timeout=REQUEST_TIMEOUT_SECONDS)
    return receipt, (time.monotonic() - started) * 1000


def receipt_raw(receipt: dict[str, Any]) -> str:
    message = receipt.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content if isinstance(content, str) else ""


def error_decision(label: str) -> dict[str, Any]:
    return {"decision": "invalid", "raw": f"[{label}]"}


def base_row(reader: dict[str, Any], cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "ainglish.agent-task-ollama-observation.v0.1",
        "reader_id": reader["reader_id"],
        "reader_tag": reader["tag"],
        "reader_digest": reader["digest"],
        "cell_id": cell["cell_id"],
        "schedule_order": cell["order"],
        "item_id": cell["item_id"],
        "construct": cell["construct"],
        "arm": cell["arm"],
        "track": cell["track"],
        "prompt_sha256": cell["prompt_sha256"],
        "clarification_sha256": cell["clarification_sha256"],
    }


def recover_inflight(completed: set[tuple[str, str]]) -> None:
    if not INFLIGHT_PATH.exists():
        return
    inflight = json.loads(INFLIGHT_PATH.read_text(encoding="utf-8"))
    key = (inflight["row"]["reader_id"], inflight["row"]["cell_id"])
    if key not in completed:
        row = inflight["row"]
        row["completed_at"] = utc_now()
        row["interrupted_inflight"] = True
        row["interrupted_phase"] = inflight["phase"]
        if inflight["phase"] == "first":
            row["first"] = error_decision("OUTCOME UNAVAILABLE AFTER INTERRUPTED IN-FLIGHT FIRST CALL")
            row["first_raw"] = None
        elif inflight["phase"] == "repair":
            row["first"] = inflight["first"]
            row["first_raw"] = inflight["first_raw"]
            row["first_receipt"] = inflight["first_receipt"]
            row["first_parse_error"] = inflight.get("first_parse_error")
            row["repair"] = None
            row["repair_raw"] = None
        else:
            raise RuntimeError(f"unknown in-flight phase: {inflight['phase']}")
        append_synced(RESPONSES_PATH, row)
    INFLIGHT_PATH.unlink(missing_ok=True)


def run_cell(reader: dict[str, Any], cell: dict[str, Any], packet_by_id: dict[str, Any]) -> dict[str, Any]:
    row = base_row(reader, cell)
    row["started_at"] = utc_now()
    action_ids = {action["id"] for action in packet_by_id[cell["item_id"]]["actions"]}
    messages = [{"role": "user", "content": cell["prompt"]}]
    atomic_write(INFLIGHT_PATH, pretty_json({"phase": "first", "row": row}))
    try:
        receipt, wall_ms = chat(reader["tag"], messages)
        raw = receipt_raw(receipt)
        first, parse_error = strict_decision(raw, action_ids, response_usage(receipt, wall_ms), "first")
        row.update({
            "first": first,
            "first_raw": raw,
            "first_parse_error": parse_error,
            "first_receipt": receipt,
            "first_client_wall_ms": round(wall_ms, 3),
        })
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, RuntimeError) as exc:
        row.update({
            "first": error_decision(f"FIRST CALL ERROR: {type(exc).__name__}: {exc}"),
            "first_raw": None,
            "first_parse_error": f"{type(exc).__name__}: {exc}",
            "first_receipt": None,
        })

    if row["first"]["decision"] == "clarify":
        repair_prompt = (
            "Clarification from sender: " + cell["clarification"]
            + "\n\nRespond under the original JSON-only contract."
        )
        repair_messages = messages + [
            {"role": "assistant", "content": row["first_raw"]},
            {"role": "user", "content": repair_prompt},
        ]
        atomic_write(INFLIGHT_PATH, pretty_json({
            "phase": "repair",
            "row": base_row(reader, cell) | {"started_at": row["started_at"]},
            "first": row["first"],
            "first_raw": row["first_raw"],
            "first_receipt": row["first_receipt"],
            "first_parse_error": row["first_parse_error"],
        }))
        try:
            receipt, wall_ms = chat(reader["tag"], repair_messages)
            raw = receipt_raw(receipt)
            repair, parse_error = strict_decision(raw, action_ids, response_usage(receipt, wall_ms), "repair")
            if repair["decision"] != "act":
                repair = None
                parse_error = "repair did not return an act decision"
            row.update({
                "repair": repair,
                "repair_raw": raw,
                "repair_parse_error": parse_error,
                "repair_receipt": receipt,
                "repair_client_wall_ms": round(wall_ms, 3),
            })
        except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, RuntimeError) as exc:
            row.update({
                "repair": None,
                "repair_raw": None,
                "repair_parse_error": f"{type(exc).__name__}: {exc}",
                "repair_receipt": None,
            })
    else:
        row["repair"] = None
    row["completed_at"] = utc_now()
    return row


def unload(model: str) -> None:
    try:
        http_json("/api/generate", {"model": model, "keep_alive": 0}, timeout=60)
    except Exception as exc:  # Administrative cleanup cannot change an observed result.
        print(f"warning: could not unload {model}: {exc}", file=sys.stderr)


def run() -> None:
    verify()
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))["readers"]
    cells = parse_jsonl(PROMPTS_PATH)
    packet = BENCHMARK.load_tasks()
    packet_by_id = {item["id"]: item for item in packet["items"]}
    existing = parse_jsonl(RESPONSES_PATH)
    completed = {(row.get("reader_id"), row.get("cell_id")) for row in existing}
    recover_inflight(completed)
    existing = parse_jsonl(RESPONSES_PATH)
    completed = {(row.get("reader_id"), row.get("cell_id")) for row in existing}
    planned = len(roster) * len(cells)
    print(f"starting/resuming {planned} planned observations; {len(completed)} already fixed", flush=True)
    for reader_index, reader in enumerate(roster, 1):
        reader_complete = 0
        for cell in cells:
            key = (reader["reader_id"], cell["cell_id"])
            if key in completed:
                reader_complete += 1
                continue
            row = run_cell(reader, cell, packet_by_id)
            append_synced(RESPONSES_PATH, row)
            INFLIGHT_PATH.unlink(missing_ok=True)
            completed.add(key)
            reader_complete += 1
            print(
                f"reader {reader_index:02d}/{len(roster):02d} {reader['tag']} "
                f"cell {reader_complete:03d}/{len(cells):03d} {cell['cell_id']} "
                f"{cell['track']}/{cell['arm']}: {row['first']['decision']}",
                flush=True,
            )
        unload(reader["tag"])
    print(json.dumps({"ok": True, "completed": len(completed), "planned": planned}, sort_keys=True))


def self_test() -> None:
    actions = {"do-a", "do-b"}
    usage = {"input_tokens": 10, "output_tokens": 5, "latency_ms": 2.5}
    valid, error = strict_decision('{"decision":"act","actions":["do-a"]}', actions, usage, "fixture")
    if error is not None or valid != {"decision": "act", "actions": ["do-a"], **usage}:
        raise RuntimeError("valid action fixture failed")
    clarify, error = strict_decision('{"decision":"clarify","question":"Which one?"}', actions, usage, "fixture")
    if error is not None or clarify["decision"] != "clarify":
        raise RuntimeError("valid clarification fixture failed")
    invalid_fixtures = (
        "```json\n{\"decision\":\"act\",\"actions\":[\"do-a\"]}\n```",
        '{"decision":"act","actions":["unknown"]}',
        '{"decision":"act","actions":["do-a"],"confidence":1}',
        '{"decision":"act","actions":["do-a"],"input_tokens":1}',
        "",
    )
    for raw in invalid_fixtures:
        decision, error = strict_decision(raw, actions, usage, "fixture")
        if error is None or decision["decision"] != "invalid":
            raise RuntimeError(f"invalid fixture was accepted: {raw!r}")
    BENCHMARK.self_test(BENCHMARK.load_tasks())
    print(json.dumps({"ok": True, "strict_parser_fixtures": 7, "benchmark_self_test": True}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify", "self-test", "run"))
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare()
        elif args.command == "verify":
            verify()
        elif args.command == "self-test":
            self_test()
        else:
            run()
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
