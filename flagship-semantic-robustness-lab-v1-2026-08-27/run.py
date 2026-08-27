#!/usr/bin/env python3
"""Execute the frozen no-download flagship robustness lab exactly once."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
HOST = os.environ.get("AINGLISH_OLLAMA_HOST", "http://127.0.0.1:11435")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256", None)
    if expected and hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError(f"digest drift: {path}")
    return value


def get(path: str) -> dict:
    with urllib.request.urlopen(HOST + path, timeout=30) as response:
        return json.load(response)


def post(path: str, payload: dict, timeout: int = 900) -> dict:
    request = urllib.request.Request(
        HOST + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def prompt(rows: list[dict]) -> str:
    first = rows[0]
    cases = [{"id": row["id"], "text": row["text"]} for row in rows]
    return (
        "Classify each message using the supplied reference literally. The left meaning is "
        f"'{first['left_label']}': {first['left_definition']}. The right meaning is "
        f"'{first['right_label']}': {first['right_definition']}. Ignore explanatory distractors "
        "when a sentence explicitly says 'Actual message'. Return one answer per input in the same "
        "order. label must be exactly 'left' or 'right'.\n\nInputs:\n" + json.dumps(cases, ensure_ascii=False)
    )


def main() -> None:
    result_path = ROOT / "result.json"
    if result_path.exists():
        raise SystemExit("REFUSING: result.json exists; this frozen lab is single-run")
    if subprocess.run(["git", "status", "--porcelain"], cwd=REPO, check=True, capture_output=True, text=True).stdout:
        raise SystemExit("REFUSING: evidence repository is not clean")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    origin = subprocess.run(["git", "rev-parse", "origin/main"], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    if commit != origin:
        raise SystemExit("REFUSING: frozen plan is not public at origin/main")
    plan = checked(ROOT / "plan.json")
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    actual_items_sha256 = hashlib.sha256(canonical(packet["rows"])).hexdigest()
    if not actual_items_sha256 == packet["items_sha256"] == plan["items_sha256"]:
        raise SystemExit("REFUSING: item digest drift")
    installed = {row["name"]: row["digest"] for row in get("/api/tags")["models"]}
    for model in plan["models"]:
        if not installed.get(model["name"], "").startswith(model["digest_prefix"]):
            raise SystemExit(f"REFUSING: installed digest mismatch for {model['name']}")
    grouped = defaultdict(list)
    for row in packet["rows"]:
        grouped[row["slug"]].append(row)
    calls = []
    scores = []
    schema = {
        "type": "object", "properties": {"answers": {"type": "array", "items": {
            "type": "object", "properties": {"id": {"type": "string"}, "label": {"type": "string", "enum": ["left", "right"]}},
            "required": ["id", "label"], "additionalProperties": False,
        }}}, "required": ["answers"], "additionalProperties": False,
    }
    for model in plan["models"]:
        for slug, rows in grouped.items():
            response = post("/api/generate", {
                "model": model["name"], "prompt": prompt(rows), "stream": False,
                "format": schema, "keep_alive": "2m",
                "options": {"temperature": 0, "seed": plan["execution"]["seed"], "num_ctx": plan["execution"]["context"]},
            })
            raw = response.get("response", "")
            parsed = None
            error = None
            try:
                parsed = json.loads(raw)
            except (TypeError, json.JSONDecodeError) as exc:
                error = f"{type(exc).__name__}: {exc}"
            answers = parsed.get("answers", []) if isinstance(parsed, dict) else []
            by_id = {answer.get("id"): answer.get("label") for answer in answers if isinstance(answer, dict)}
            cell_scores = []
            for row in rows:
                observed = by_id.get(row["id"])
                correct = observed == row["expected"]
                cell = {"id": row["id"], "variant": row["variant"], "expected": row["expected"], "observed": observed, "correct": correct}
                cell_scores.append(cell)
                scores.append({"model": model["name"], "slug": slug, **cell})
            calls.append({
                "model": model["name"], "digest": installed[model["name"]], "slug": slug,
                "raw_response": raw, "parse_error": error, "done_reason": response.get("done_reason"),
                "prompt_eval_count": response.get("prompt_eval_count"), "eval_count": response.get("eval_count"),
                "cells": cell_scores,
            })
        post("/api/generate", {"model": model["name"], "prompt": "", "stream": False, "keep_alive": 0}, timeout=60)
    variants = sorted({row["variant"] for row in scores})
    model_summary = {}
    for model in plan["models"]:
        cells = [row for row in scores if row["model"] == model["name"]]
        model_summary[model["name"]] = {
            "correct": sum(row["correct"] for row in cells), "total": len(cells),
            "accuracy": sum(row["correct"] for row in cells) / len(cells),
            "by_variant": {variant: {
                "correct": sum(row["correct"] for row in cells if row["variant"] == variant),
                "total": sum(row["variant"] == variant for row in cells),
            } for variant in variants},
        }
    construct_summary = {}
    for slug in grouped:
        cells = [row for row in scores if row["slug"] == slug]
        construct_summary[slug] = {
            "correct": sum(row["correct"] for row in cells), "total": len(cells),
            "accuracy": sum(row["correct"] for row in cells) / len(cells),
            "least_model_accuracy": min(
                sum(row["correct"] for row in cells if row["model"] == model["name"]) /
                sum(row["model"] == model["name"] for row in cells)
                for model in plan["models"]
            ),
        }
    result = {
        "kind": "dexagon.ainglish.flagship-semantic-robustness-result.v1",
        "started_from_commit": commit,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "plan_sha256": plan["content_sha256"], "items_sha256": plan["items_sha256"],
        "calls_expected": plan["execution"]["calls"], "calls_observed": len(calls),
        "model_summary": model_summary, "construct_summary": construct_summary,
        "calls": calls,
        "claim_boundaries": plan["claim_boundaries"],
        "model_downloads": 0, "governance_writes": 0,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"calls": len(calls), "models": model_summary, "content_sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
