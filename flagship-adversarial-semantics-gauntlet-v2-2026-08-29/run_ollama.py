#!/usr/bin/env python3
"""Run frozen construct batches against already-installed Ollama readers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CHECKSUM_PATH = ROOT / "SHA256SUMS.preregistered"
PROMPTS_PATH = ROOT / "prompts.jsonl"
ROSTER_PATH = ROOT / "reader-roster.json"
PLAN_PATH = ROOT / "RUN_PLAN.json"
RESULTS_ROOT = ROOT / "results"
RESPONSES_PATH = RESULTS_ROOT / "responses.jsonl"
INFLIGHT_PATH = RESULTS_ROOT / "inflight.json"
OLLAMA = "http://127.0.0.1:11434"
LABELS = {"entailed", "contradicted", "underdetermined"}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def request(path: str, payload: dict[str, Any] | None = None, timeout: int = 900) -> dict[str, Any]:
    data = None if payload is None else canonical(payload)
    req = urllib.request.Request(
        OLLAMA + path,
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} returned non-object")
    return value


def verify() -> None:
    failures = []
    for line in CHECKSUM_PATH.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = (ROOT / relative).resolve()
        if not path.exists():
            failures.append(f"missing {relative}")
        elif digest(path) != expected:
            failures.append(f"digest mismatch {relative}")
    if failures:
        raise RuntimeError("; ".join(failures))
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    tags = {row.get("name"): row for row in request("/api/tags").get("models", [])}
    for reader in roster["readers"]:
        if reader["tag"] not in tags or tags[reader["tag"]].get("digest") != reader["digest"]:
            raise RuntimeError(f"served artifact changed or disappeared: {reader['tag']}")
    status = subprocess.run(["git", "status", "--porcelain", "--", str(ROOT.relative_to(REPO))], cwd=REPO, check=True, capture_output=True, text=True).stdout
    if status.strip():
        raise RuntimeError("gauntlet files must be committed before inference")
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(ROOT.relative_to(REPO))], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "fetch", "origin", "main", "--quiet"], cwd=REPO, check=True)
    if not commit or subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=REPO).returncode:
        raise RuntimeError("preregistering commit is not public on origin/main")
    print(json.dumps({"ok": True, "readers": len(roster["readers"]), "prompts": len(jsonl(PROMPTS_PATH)), "public_commit": commit}, sort_keys=True))


def parse_answers(content: str, expected_ids: set[str]) -> tuple[dict[str, str], str | None]:
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
            if label not in LABELS:
                raise ValueError("unknown answer label")
            answers[item_id] = label
        if set(answers) != expected_ids:
            raise ValueError("answer IDs do not exactly match requested population")
        return answers, None
    except (json.JSONDecodeError, ValueError) as exc:
        return {}, str(exc)


def invalid_inflight(inflight: dict[str, Any]) -> dict[str, Any]:
    return {
        **inflight,
        "valid": False,
        "answers": {},
        "content": "",
        "thinking": "",
        "error": "interrupted before response receipt",
        "receipt": None,
    }


def run() -> None:
    verify()
    if INFLIGHT_PATH.exists():
        inflight = json.loads(INFLIGHT_PATH.read_text(encoding="utf-8"))
        append_synced(RESPONSES_PATH, invalid_inflight(inflight))
        INFLIGHT_PATH.unlink()
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))["readers"]
    prompts = jsonl(PROMPTS_PATH)
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    completed = {(row["reader_id"], row["rank"]) for row in jsonl(RESPONSES_PATH)}
    for reader_index, reader in enumerate(roster, 1):
        for prompt_index, prompt in enumerate(prompts, 1):
            key = (reader["reader_id"], prompt["rank"])
            if key in completed:
                continue
            common = {
                "reader_id": reader["reader_id"], "model": reader["tag"], "rank": prompt["rank"],
                "slug": prompt["slug"], "item_ids": prompt["item_ids"], "prompt_sha256": prompt["prompt_sha256"],
            }
            atomic_write(INFLIGHT_PATH, common)
            started = time.monotonic()
            try:
                receipt = request("/api/chat", {
                    "model": reader["tag"],
                    "messages": [{"role": "user", "content": prompt["prompt"]}],
                    **plan["request"],
                })
                message = receipt.get("message") if isinstance(receipt.get("message"), dict) else {}
                content = message.get("content") if isinstance(message.get("content"), str) else ""
                thinking = message.get("thinking") if isinstance(message.get("thinking"), str) else ""
                answers, error = parse_answers(content, set(prompt["item_ids"]))
                row = {
                    **common, "valid": error is None, "answers": answers, "content": content,
                    "thinking": thinking, "error": error, "wall_ms": round((time.monotonic() - started) * 1000, 3),
                    "receipt": receipt,
                }
            except Exception as exc:
                row = {
                    **common, "valid": False, "answers": {}, "content": "", "thinking": "",
                    "error": f"{type(exc).__name__}: {exc}", "wall_ms": round((time.monotonic() - started) * 1000, 3),
                    "receipt": None,
                }
            append_synced(RESPONSES_PATH, row)
            INFLIGHT_PATH.unlink(missing_ok=True)
            completed.add(key)
            print(f"reader {reader_index}/3 {reader['tag']} batch {prompt_index:02d}/18 rank-{prompt['rank']:02d}: {'valid' if row['valid'] else 'invalid'}", flush=True)
        try:
            request("/api/generate", {"model": reader["tag"], "keep_alive": 0}, timeout=60)
        except Exception:
            pass
    rows = jsonl(RESPONSES_PATH)
    print(json.dumps({"status": "complete" if len(rows) == 54 else "partial", "calls": len(rows), "planned": 54}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "run"))
    args = parser.parse_args()
    try:
        verify() if args.command == "verify" else run()
    except Exception as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
