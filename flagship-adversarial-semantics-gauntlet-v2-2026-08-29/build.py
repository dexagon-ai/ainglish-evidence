#!/usr/bin/env python3
"""Validate curated semantics and freeze the v2 gauntlet."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "constructs.json"
ITEMS_PATH = ROOT / "items.json"
PROMPTS_PATH = ROOT / "prompts.jsonl"
ROSTER_PATH = ROOT / "reader-roster.json"
PLAN_PATH = ROOT / "RUN_PLAN.json"
CHECKSUM_PATH = ROOT / "SHA256SUMS.preregistered"
OLLAMA = "http://127.0.0.1:11434"
MODELS = ("qwen3.5:9b", "gemma3:12b", "mistral-small3.2:24b-instruct-2506-q4_K_M")
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


def get(path: str) -> dict[str, Any]:
    with urllib.request.urlopen(OLLAMA + path, timeout=30) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} returned non-object")
    return value


def require_text(record: dict[str, Any], key: str, where: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{where}.{key} must be non-empty text")
    return value


def add(rows: list[dict[str, Any]], construct: dict[str, Any], pole: str, family: str, text: str, conclusion: str, expected: str) -> None:
    if expected not in LABELS:
        raise RuntimeError(f"{construct['slug']} {pole}/{family}: invalid expected label")
    rows.append({
        "id": f"f{construct['rank']:02d}-{family}-{pole}",
        "rank": construct["rank"],
        "slug": construct["slug"],
        "form": construct["form"],
        "reference": construct["reference"],
        "pole": pole,
        "family": family,
        "text": text,
        "candidate_conclusion": conclusion,
        "expected": expected,
    })


def prompt_for(reference: str, rows: list[dict[str, Any]]) -> str:
    tasks = [
        {"id": row["id"], "actual_message": row["text"], "candidate_conclusion": row["candidate_conclusion"]}
        for row in rows
    ]
    return "\n\n".join((
        "Classify ten independent semantic judgements under the supplied Ainglish reference.",
        "Reference: " + reference,
        (
            "Use entailed only when the candidate must follow; contradicted only when it must be false; "
            "otherwise use underdetermined. Do not treat a contrasted form pair as logical complements "
            "unless the reference warrants that relation. Quoted illustrations are not assertions."
        ),
        "Frozen items:\n" + json.dumps(tasks, ensure_ascii=False, separators=(",", ":")),
        (
            'Return JSON only: {"answers":[{"id":"item-id","label":"entailed|contradicted|underdetermined"}]}. '
            "Include every requested ID exactly once and no other IDs or keys."
        ),
    ))


def main() -> None:
    generated = (ITEMS_PATH, PROMPTS_PATH, ROSTER_PATH, PLAN_PATH, CHECKSUM_PATH)
    existing = [path.name for path in generated if path.exists()]
    if existing:
        raise SystemExit("REFUSING: frozen artifacts already exist: " + ", ".join(existing))
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    constructs = source.get("constructs")
    if not isinstance(constructs, list) or len(constructs) != 18:
        raise RuntimeError("exactly 18 constructs are required")
    if [row.get("rank") for row in constructs] != list(range(1, 19)):
        raise RuntimeError("ranks must be the ordered integers 1..18")
    if len({row.get("slug") for row in constructs}) != 18:
        raise RuntimeError("construct slugs must be unique")

    rows: list[dict[str, Any]] = []
    for construct in constructs:
        where = construct["slug"]
        for key in ("slug", "form", "reference"):
            require_text(construct, key, where)
        for pole, other in (("left", "right"), ("right", "left")):
            record = construct.get(pole)
            opposite = construct.get(other)
            if not isinstance(record, dict) or not isinstance(opposite, dict):
                raise RuntimeError(f"{where}: missing pole records")
            for key in ("message", "entailed", "cross", "cross_expected", "overread"):
                require_text(record, key, f"{where}.{pole}")
            add(rows, construct, pole, "direct_entailment", record["message"], record["entailed"], "entailed")
            add(rows, construct, pole, "cross_relation", record["message"], record["cross"], record["cross_expected"])
            add(rows, construct, pole, "boundary_overread", record["message"], record["overread"], "underdetermined")
            distractor = (
                f'Quoted illustration only; it is not asserted: "{opposite["message"]}"\n'
                f'Actual message to evaluate: {record["message"]}'
            )
            add(rows, construct, pole, "quoted_opposite_distractor", distractor, record["entailed"], "entailed")
            scope = (
                f"Two independent actual records follow.\nRecord L: {construct['left']['message']}\n"
                f"Record R: {construct['right']['message']}\nEvaluate only record {'L' if pole == 'left' else 'R'}."
            )
            add(rows, construct, pole, "dual_record_scope", scope, record["entailed"], "entailed")
    if len(rows) != 180 or len({row["id"] for row in rows}) != 180:
        raise RuntimeError("expected 180 unique items")

    item_doc = {
        "schema": "ainglish.flagship-adversarial-items.v2",
        "source_sha256": digest(SOURCE_PATH),
        "population": "18 editorial flagships x 2 poles x 5 scenario families",
        "items": rows,
    }
    item_doc["content_sha256"] = hashlib.sha256(canonical(item_doc)).hexdigest()
    prompts = []
    for construct in constructs:
        subset = [row for row in rows if row["rank"] == construct["rank"]]
        prompt = prompt_for(construct["reference"], subset)
        prompts.append({
            "rank": construct["rank"],
            "slug": construct["slug"],
            "item_ids": [row["id"] for row in subset],
            "prompt": prompt,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        })
    prompt_bytes = b"".join(canonical(row) for row in prompts)

    tags = {row.get("name"): row for row in get("/api/tags").get("models", [])}
    missing = [name for name in MODELS if name not in tags]
    if missing:
        raise RuntimeError("already-installed reader missing; no pull attempted: " + ", ".join(missing))
    readers = []
    for name in MODELS:
        row = tags[name]
        artifact_digest = row.get("digest")
        if not isinstance(artifact_digest, str) or len(artifact_digest) != 64:
            raise RuntimeError(f"{name}: invalid served digest")
        readers.append({
            "tag": name,
            "digest": artifact_digest,
            "reader_id": f"ollama/{name}@sha256:{artifact_digest}",
            "details": row.get("details"),
            "size": row.get("size"),
        })
    roster = {
        "schema": "ainglish.flagship-adversarial-reader-roster.v2",
        "selection": "Three distinct already-installed general-purpose model families used by v1; no downloads.",
        "ollama_version": get("/api/version").get("version"),
        "readers": readers,
    }
    roster["content_sha256"] = hashlib.sha256(canonical(roster)).hexdigest()
    plan = {
        "schema": "ainglish.flagship-adversarial-run-plan.v2",
        "items_sha256": item_doc["content_sha256"],
        "prompts_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
        "roster_sha256": roster["content_sha256"],
        "constructs": 18,
        "cells_per_reader": 180,
        "calls_per_reader": 18,
        "planned_calls": 54,
        "planned_cells": 540,
        "request": {
            "stream": False,
            "format": "json",
            "think": False,
            "keep_alive": "15m",
            "options": {"num_ctx": 8192, "num_predict": 768, "seed": 2026082903, "temperature": 0},
        },
        "answer_channel": "message.content only; thinking is retained but never parsed",
        "retry_policy": "no inference retries; malformed batch invalidates all ten requested cells",
        "governance_evidence": False,
        "downloads": 0,
    }
    ITEMS_PATH.write_bytes(pretty(item_doc))
    PROMPTS_PATH.write_bytes(prompt_bytes)
    ROSTER_PATH.write_bytes(pretty(roster))
    PLAN_PATH.write_bytes(pretty(plan))

    inputs = (ROOT / "README.md", ROOT / "RUN_PROTOCOL.md", SOURCE_PATH, ROOT / "build.py", ROOT / "audit.py", ROOT / "run_ollama.py", ROOT / "analyse.py", ITEMS_PATH, PROMPTS_PATH, ROSTER_PATH, PLAN_PATH)
    missing_inputs = [path.name for path in inputs if not path.exists()]
    if missing_inputs:
        raise RuntimeError("missing checksum inputs: " + ", ".join(missing_inputs))
    CHECKSUM_PATH.write_text("".join(f"{digest(path)}  {os.path.relpath(path, ROOT)}\n" for path in inputs), encoding="utf-8")
    print(json.dumps({"ok": True, "constructs": 18, "items": 180, "readers": 3, "planned_calls": 54, "downloads": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
