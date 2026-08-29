#!/usr/bin/env python3
"""Freeze a supplied-reference uncertainty overread gauntlet."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
OLLAMA = "http://127.0.0.1:11434"
MODELS = ("qwen3.5:9b", "gemma3:12b", "mistral-small3.2:24b-instruct-2506-q4_K_M")
FORMS = ("each-group", "groups-combined")
FAMILIES = ("significance", "interval", "equal_magnitude", "low_variance")
STATES = ("stated_true", "stated_false", "absent")
ANSWERS = ("yes", "no", "not stated")

REFERENCE = (
    "each-group(G): C says C holds separately for every member group in G and makes no pooled-result claim. "
    "groups-combined(G): C says C holds once on the combined records and makes no member-group claim. "
    "Neither marker by itself says that a change is statistically significant, that a confidence interval "
    "excludes zero, that estimates have low variance, or that effect magnitudes are equal. Those are separate "
    "claims and follow only when the message states them."
)

BOUNDARIES = {
    "significance": {
        "question": "Does the message assert that the directional change passed a named significance test?",
        "true": "A separate preregistered test is named and reports p=0.01 under alpha=0.05.",
        "false": "The message says no significance test was run and makes no significance claim.",
    },
    "interval": {
        "question": "Does the message assert that a named uncertainty interval excludes zero?",
        "true": "A separate sentence reports a 95% interval entirely above zero.",
        "false": "The message says no uncertainty interval was calculated or claimed.",
    },
    "equal_magnitude": {
        "question": "Does the message assert that the change has the same magnitude in every member group?",
        "true": "A separate audited table states that the change magnitude is identical in every member group.",
        "false": "A separate audited table states that the change magnitudes differ between member groups.",
    },
    "low_variance": {
        "question": "Does the message assert that the estimate has low variance under a named rule?",
        "true": "A separate variance report states that the estimate passes the named low-variance rule.",
        "false": "A separate variance report states that the estimate fails the named low-variance rule.",
    },
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def pretty(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get(path: str) -> dict:
    with urllib.request.urlopen(OLLAMA + path, timeout=30) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} returned non-object")
    return value


def placed(answer: str, position: int) -> list[str]:
    values = [value for value in ANSWERS if value != answer]
    values.insert(position, answer)
    return values


def prompt_for(family: str, rows: list[dict]) -> str:
    tasks = [
        {
            "id": row["id"],
            "message": row["message"],
            "question": row["question"],
            "choices": {chr(65 + index): value for index, value in enumerate(row["options"])},
        }
        for row in rows
    ]
    return "\n\n".join(
        (
            "Apply the supplied reference literally to twelve independent messages.",
            "Reference: " + REFERENCE,
            (
                "Answer what each full message asserts. A scope marker never supplies an uncertainty claim on its own. "
                "When a separate sentence states or denies the queried claim, use that sentence."
            ),
            "Frozen items:\n" + json.dumps(tasks, ensure_ascii=False, separators=(",", ":")),
            (
                'Return JSON only: {"answers":[{"id":"item-id","choice":"A|B|C"}]}. '
                "Include every requested ID exactly once and no other IDs or keys."
            ),
        )
    )


def main() -> None:
    generated = (
        ROOT / "items.json",
        ROOT / "prompts.jsonl",
        ROOT / "reader-roster.json",
        ROOT / "RUN_PLAN.json",
        ROOT / "SHA256SUMS.preregistered",
    )
    existing = [path.name for path in generated if path.exists()]
    if existing:
        raise SystemExit("REFUSING: frozen artifacts already exist: " + ", ".join(existing))
    rows = []
    index = 0
    for form in FORMS:
        for family in FAMILIES:
            boundary = BOUNDARIES[family]
            for repeat in range(2):
                for state in STATES:
                    base = (
                        f"{form}(regions@audit-{repeat + 1}): checkout success rate increased."
                    )
                    if state == "stated_true":
                        message = base + " " + boundary["true"]
                        answer = "yes"
                    elif state == "stated_false":
                        message = base + " " + boundary["false"]
                        answer = "no"
                    else:
                        message = base
                        answer = "not stated"
                    rows.append(
                        {
                            "id": f"ugb-{index + 1:02d}",
                            "form": form,
                            "family": family,
                            "state": state,
                            "message": message,
                            "question": boundary["question"],
                            "options": placed(answer, index % 3),
                            "answer": answer,
                        }
                    )
                    index += 1
    if len(rows) != 48 or len({row["id"] for row in rows}) != 48:
        raise RuntimeError("expected 48 unique items")
    if {answer: sum(row["answer"] == answer for row in rows) for answer in ANSWERS} != {answer: 16 for answer in ANSWERS}:
        raise RuntimeError("answer label imbalance")
    if [sum(row["options"].index(row["answer"]) == pos for row in rows) for pos in range(3)] != [16, 16, 16]:
        raise RuntimeError("answer position imbalance")

    items = {
        "schema": "ainglish.group-scope-uncertainty-boundary-items.v1",
        "reference": REFERENCE,
        "population": "2 forms x 4 uncertainty boundaries x 3 evidence states x 2 repeats",
        "items": rows,
    }
    items["content_sha256"] = hashlib.sha256(canonical(items)).hexdigest()
    prompts = []
    for family in FAMILIES:
        subset = [row for row in rows if row["family"] == family]
        prompt = prompt_for(family, subset)
        prompts.append(
            {
                "family": family,
                "item_ids": [row["id"] for row in subset],
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            }
        )
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
        readers.append(
            {
                "tag": name,
                "digest": artifact_digest,
                "reader_id": f"ollama/{name}@sha256:{artifact_digest}",
                "details": row.get("details"),
                "size": row.get("size"),
            }
        )
    roster = {
        "schema": "ainglish.group-scope-uncertainty-reader-roster.v1",
        "selection": "Three distinct already-installed general-purpose model families; no downloads.",
        "ollama_version": get("/api/version").get("version"),
        "readers": readers,
    }
    roster["content_sha256"] = hashlib.sha256(canonical(roster)).hexdigest()
    plan = {
        "schema": "ainglish.group-scope-uncertainty-run-plan.v1",
        "items_sha256": items["content_sha256"],
        "prompts_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
        "roster_sha256": roster["content_sha256"],
        "families": len(FAMILIES),
        "cells_per_reader": 48,
        "calls_per_reader": 4,
        "planned_calls": 12,
        "planned_cells": 144,
        "request": {
            "stream": False,
            "think": False,
            "keep_alive": "15m",
            "options": {"num_ctx": 8192, "num_predict": 1024, "seed": 2026082943, "temperature": 0},
        },
        "retry_policy": "no inference retries; malformed batch invalidates all twelve requested cells",
        "governance_evidence": False,
        "downloads": 0,
    }
    (ROOT / "items.json").write_bytes(pretty(items))
    (ROOT / "prompts.jsonl").write_bytes(prompt_bytes)
    (ROOT / "reader-roster.json").write_bytes(pretty(roster))
    (ROOT / "RUN_PLAN.json").write_bytes(pretty(plan))
    checksum_inputs = (ROOT / "README.md", ROOT / "build.py", ROOT / "run_ollama.py", ROOT / "analyse.py", *generated[:-1])
    missing_inputs = [path.name for path in checksum_inputs if not path.exists()]
    if missing_inputs:
        raise RuntimeError("missing checksum inputs: " + ", ".join(missing_inputs))
    (ROOT / "SHA256SUMS.preregistered").write_text(
        "".join(f"{digest(path)}  {os.path.relpath(path, ROOT)}\n" for path in checksum_inputs), encoding="utf-8"
    )
    print(json.dumps({"ok": True, "items": 48, "readers": 3, "planned_calls": 12, "downloads": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
