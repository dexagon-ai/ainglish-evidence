#!/usr/bin/env python3
"""Verify and execute the frozen local gauntlet without retry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OLLAMA = "http://127.0.0.1:11434"
OUTPUT = ROOT / "responses.jsonl"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def get(path: str) -> dict:
    with urllib.request.urlopen(OLLAMA + path, timeout=30) as response:
        return json.load(response)


def post(path: str, payload: dict, timeout: int = 900) -> dict:
    request = urllib.request.Request(
        OLLAMA + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def verify(require_clean: bool) -> tuple[dict, list[dict], list[dict]]:
    listed = {}
    for line in (ROOT / "SHA256SUMS.preregistered").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        actual = digest(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"checksum drift: {relative}")
        listed[relative] = actual
    if require_clean:
        if git("status", "--porcelain"):
            raise RuntimeError("evidence repository is not clean")
        if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
            raise RuntimeError("frozen protocol is not public at origin/main")
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text())
    roster = json.loads((ROOT / "reader-roster.json").read_text())
    prompts = [json.loads(line) for line in (ROOT / "prompts.jsonl").read_text().splitlines() if line]
    tags = {row.get("name"): row for row in get("/api/tags").get("models", [])}
    for reader in roster["readers"]:
        if tags.get(reader["tag"], {}).get("digest") != reader["digest"]:
            raise RuntimeError(f"reader digest drift: {reader['tag']}")
    if len(prompts) != plan["calls_per_reader"]:
        raise RuntimeError("prompt count drift")
    return plan, roster["readers"], prompts


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    plan, readers, prompts = verify(require_clean=mode == "run")
    if mode == "verify":
        print(json.dumps({"status": "ok", "readers": len(readers), "prompts": len(prompts), "planned_calls": plan["planned_calls"]}))
        return
    if mode != "run":
        raise SystemExit("usage: run_ollama.py verify|run")
    if OUTPUT.exists():
        raise SystemExit("REFUSING: responses.jsonl already exists")
    if get("/api/ps").get("models"):
        raise RuntimeError("an Ollama model is already resident")
    compute_apps = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if compute_apps:
        raise RuntimeError("GPU preflight failed: a compute process is active")
    smi = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total,memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for line in smi:
        total, free, utilization = [int(part.strip()) for part in line.split(",")]
        if free < total - 2048 or utilization > 5:
            raise RuntimeError("GPU preflight failed: a device is in use")
    schema = {
        "type": "object",
        "properties": {
            "answers": {
                "type": "array",
                "minItems": 12,
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "choice": {"type": "string", "enum": ["A", "B", "C"]},
                    },
                    "required": ["id", "choice"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["answers"],
        "additionalProperties": False,
    }
    with OUTPUT.open("xb") as handle:
        for reader in readers:
            for prompt in prompts:
                request = {
                    "model": reader["tag"],
                    "messages": [{"role": "user", "content": prompt["prompt"]}],
                    "format": schema,
                    **{key: value for key, value in plan["request"].items() if key != "options"},
                    "options": plan["request"]["options"],
                }
                try:
                    response = post("/api/chat", request)
                    error = None
                except Exception as exc:
                    response = None
                    error = f"{type(exc).__name__}: {exc}"
                record = {
                    "reader_id": reader["reader_id"],
                    "model": reader["tag"],
                    "family": prompt["family"],
                    "item_ids": prompt["item_ids"],
                    "prompt_sha256": prompt["prompt_sha256"],
                    "response": response,
                    "error": error,
                }
                handle.write(canonical(record))
                handle.flush()
                print(f"completed {reader['tag']} / {prompt['family']}", flush=True)
            post("/api/generate", {"model": reader["tag"], "prompt": "", "stream": False, "keep_alive": 0}, timeout=120)


if __name__ == "__main__":
    main()
