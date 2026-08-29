#!/usr/bin/env python3
"""Run the publicly frozen atlas once against exact installed Ollama artifacts."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
RESULTS = ROOT / "results"
OLLAMA = "http://127.0.0.1:11434"
PRINT_LOCK = threading.Lock()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def request(path: str, payload: dict[str, Any] | None = None, timeout: int = 1800) -> dict[str, Any]:
    data = None if payload is None else canonical(payload)
    req = urllib.request.Request(OLLAMA + path, data=data, headers={"Content-Type": "application/json"} if data is not None else {}, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} returned non-object")
    return value


def paths(reader_number: int) -> tuple[Path, Path]:
    return RESULTS / f"reader-{reader_number:02d}.jsonl", RESULTS / f"reader-{reader_number:02d}.inflight.json"


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(pretty(value))
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def append_synced(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical(value))
        handle.flush()
        os.fsync(handle.fileno())


def verify() -> dict[str, Any]:
    failures = []
    for line in (ROOT / "SHA256SUMS.preregistered").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing preregistered file: {relative}")
        elif digest(path) != expected:
            failures.append(f"preregistered digest mismatch: {relative}")
    audit = subprocess.run(["python3", str(ROOT / "audit.py")], cwd=REPO, capture_output=True, text=True)
    if audit.returncode:
        failures.append("input audit failed: " + (audit.stderr.strip() or audit.stdout.strip()))
    roster_packet = json.loads((ROOT / "reader-roster.json").read_text(encoding="utf-8"))
    tags = {row.get("name"): row for row in request("/api/tags").get("models", []) if isinstance(row, dict)}
    for reader in roster_packet["readers"]:
        served = tags.get(reader["tag"])
        if served is None or served.get("digest") != reader["digest"]:
            failures.append(f"served artifact changed or disappeared: {reader['tag']}")
    version = subprocess.run(["ollama", "--version"], check=True, capture_output=True, text=True).stdout.strip()
    if version != roster_packet["ollama_version"]:
        failures.append(f"Ollama version drift: expected {roster_packet['ollama_version']!r}, got {version!r}")
    tracked = [line.split("  ", 1)[1] for line in (ROOT / "SHA256SUMS.preregistered").read_text(encoding="utf-8").splitlines()] + ["SHA256SUMS.preregistered"]
    relative_root = ROOT.relative_to(REPO)
    tracked_paths = [str(relative_root / name) for name in tracked]
    if subprocess.run(["git", "diff", "--quiet", "--", *tracked_paths], cwd=REPO).returncode or subprocess.run(["git", "diff", "--cached", "--quiet", "--", *tracked_paths], cwd=REPO).returncode:
        failures.append("preregistered files have uncommitted changes")
    for path in tracked_paths:
        if subprocess.run(["git", "ls-files", "--error-unmatch", path], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            failures.append(f"preregistered file is not tracked: {path}")
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(relative_root)], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    fetch = subprocess.run(["git", "fetch", "origin", "main", "--quiet"], cwd=REPO)
    if fetch.returncode or not commit or subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=REPO).returncode:
        failures.append("preregistering commit is not public on origin/main")
    if failures:
        raise RuntimeError("; ".join(failures))
    return {"ok": True, "readers": len(roster_packet["readers"]), "prompts": 30, "public_commit": commit, "audit": json.loads(audit.stdout)}


def allowed_labels(items: list[dict[str, Any]]) -> dict[str, set[str]]:
    return {row["id"]: {option["label"] for option in row["options"]} for row in items}


def parse_answers(content: str, expected: dict[str, set[str]]) -> tuple[dict[str, str], str | None]:
    try:
        value = json.loads(content.strip())
        if not isinstance(value, dict) or set(value) != {"answers"} or not isinstance(value["answers"], list):
            raise ValueError("top-level contract mismatch")
        answers: dict[str, str] = {}
        for row in value["answers"]:
            if not isinstance(row, dict) or set(row) != {"id", "label"}:
                raise ValueError("answer-row contract mismatch")
            item_id, label = row["id"], row["label"]
            if not isinstance(item_id, str) or item_id in answers:
                raise ValueError("missing-string or duplicate answer ID")
            if item_id not in expected or label not in expected[item_id]:
                raise ValueError("unknown ID or option label")
            answers[item_id] = label
        if set(answers) != set(expected):
            raise ValueError("answer IDs do not exactly match requested population")
        return answers, None
    except (json.JSONDecodeError, ValueError) as exc:
        return {}, str(exc)


def recover_inflight(reader_number: int) -> None:
    journal, inflight_path = paths(reader_number)
    if not inflight_path.exists():
        return
    inflight = json.loads(inflight_path.read_text(encoding="utf-8"))
    append_synced(journal, {**inflight, "valid": False, "answers": {}, "content": "", "thinking": "", "error": "interrupted before response receipt", "wall_ms": None, "receipt": None})
    inflight_path.unlink()


def run_reader(reader_number: int, reader: dict[str, Any], prompts: list[dict[str, Any]], item_groups: dict[tuple[str, str], list[dict[str, Any]]], request_plan: dict[str, Any]) -> int:
    journal, inflight_path = paths(reader_number)
    completed = {(row["key"], row["condition"]) for row in jsonl(journal)}
    for prompt_index, prompt in enumerate(prompts, 1):
        key = (prompt["key"], prompt["condition"])
        if key in completed:
            continue
        common = {
            "reader_number": reader_number,
            "reader_id": reader["reader_id"],
            "model": reader["tag"],
            "rank": prompt["rank"],
            "key": prompt["key"],
            "slug": prompt["slug"],
            "condition": prompt["condition"],
            "item_ids": prompt["item_ids"],
            "prompt_sha256": prompt["prompt_sha256"],
        }
        atomic_write(inflight_path, common)
        started = time.monotonic()
        try:
            receipt = request("/api/chat", {"model": reader["tag"], "messages": [{"role": "user", "content": prompt["prompt"]}], **request_plan})
            message = receipt.get("message") if isinstance(receipt.get("message"), dict) else {}
            content = message.get("content") if isinstance(message.get("content"), str) else ""
            thinking = message.get("thinking") if isinstance(message.get("thinking"), str) else ""
            answers, error = parse_answers(content, allowed_labels(item_groups[key]))
            row = {**common, "valid": error is None, "answers": answers, "content": content, "thinking": thinking, "error": error, "wall_ms": round((time.monotonic() - started) * 1000, 3), "receipt": receipt}
        except Exception as exc:
            row = {**common, "valid": False, "answers": {}, "content": "", "thinking": "", "error": f"{type(exc).__name__}: {exc}", "wall_ms": round((time.monotonic() - started) * 1000, 3), "receipt": None}
        append_synced(journal, row)
        inflight_path.unlink(missing_ok=True)
        completed.add(key)
        with PRINT_LOCK:
            print(f"reader {reader_number}/6 {reader['tag']} call {prompt_index:02d}/30 {prompt['key']}/{prompt['condition']}: {'valid' if row['valid'] else 'invalid'}", flush=True)
    try:
        request("/api/generate", {"model": reader["tag"], "keep_alive": 0}, timeout=90)
    except Exception:
        pass
    return len(completed)


def run(workers: int) -> None:
    receipt = verify()
    print(json.dumps(receipt, sort_keys=True), flush=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    roster = json.loads((ROOT / "reader-roster.json").read_text(encoding="utf-8"))["readers"]
    prompts = jsonl(ROOT / "prompts.jsonl")
    items = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))["items"]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for prompt in prompts:
        groups[(prompt["key"], prompt["condition"])] = [row for row in items if row["key"] == prompt["key"] and row["condition"] == prompt["condition"]]
    request_plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))["request"]
    for number in range(1, len(roster) + 1):
        recover_inflight(number)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_reader, number, reader, prompts, groups, request_plan) for number, reader in enumerate(roster, 1)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    calls = sum(len(jsonl(paths(number)[0])) for number in range(1, len(roster) + 1))
    planned = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))["planned_calls"]
    print(json.dumps({"status": "complete" if calls == planned else "partial", "calls": calls, "planned": planned}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.workers <= 2:
        raise SystemExit("workers must be 1 or 2")
    try:
        print(json.dumps(verify(), sort_keys=True)) if args.command == "verify" else run(args.workers)
    except Exception as exc:
        print(f"REFUSING: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
