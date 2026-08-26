#!/usr/bin/env python3
"""Mint, run, and file the controlled moved-direction fidelity original once."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
SLUG = "moved-earlier-moved-later-which-way-did-the-meeting-move-2"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256", None)
    if not expected or hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError(f"digest drift: {path}")
    return value


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def git_blob(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def get(path: str) -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=30) as response:
        return json.load(response)


def post(path: str, payload: dict, timeout: int = 240) -> dict:
    request = urllib.request.Request(
        "http://127.0.0.1:11434" + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def unload(model: str) -> None:
    post(
        "/api/generate",
        {"model": model, "prompt": "", "stream": False, "keep_alive": 0},
        timeout=60,
    )


def qualification(path_text: str) -> tuple[Path, dict]:
    path = (REPO / path_text).resolve()
    try:
        path.relative_to(REPO)
    except ValueError as exc:
        raise RuntimeError("qualification path escapes evidence repository") from exc
    value = checked(path)
    roster = value.get("fixed_roster", [])
    if not value.get("roster_ready") or len({row.get("lineage") for row in roster}) < 2:
        raise RuntimeError("fewer than two qualified reader lineages")
    required = ("name", "lineage", "model", "model_digest", "seed", "timeout_s")
    if any(any(not row.get(key) and row.get(key) != 0 for key in required) for row in roster):
        raise RuntimeError("qualification roster misses runner fields")
    return path, value


def load_packet() -> tuple[dict, dict, list[dict]]:
    index = checked(ROOT / "index.json")
    packet = json.loads((ROOT / index["items_path"]).read_text(encoding="utf-8"))
    items = packet["items"]
    digest = hashlib.sha256(canonical(items)).hexdigest()
    if digest != packet.get("sha256") or digest != index.get("items_sha256"):
        raise RuntimeError("fidelity population drift")
    if len(items) != 96 or len({row["id"] for row in items}) != 96:
        raise RuntimeError("fidelity population size or identity drift")
    counts = {name: sum(row["class"] == name for row in items) for name in ("earlier", "later", "neither")}
    if counts != {"earlier": 32, "later": 32, "neither": 32}:
        raise RuntimeError("fidelity class balance drift")
    return index, packet, items


def gpu_preflight(roster: list[dict]) -> list[dict]:
    output = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    devices = []
    for line in output.splitlines():
        index, name, total, free, utilization = [part.strip() for part in line.split(",", 4)]
        devices.append(
            {
                "index": int(index),
                "name": name,
                "total_mib": int(total),
                "free_mib": int(free),
                "utilization": int(utilization),
            }
        )
    if any(
        row["free_mib"] < row["total_mib"] - 512 or row["utilization"] > 5
        for row in devices
    ):
        raise RuntimeError("GPU gate failed: at least one device is in use")
    if get("/api/ps").get("models"):
        raise RuntimeError("an Ollama model is already resident")
    installed = {row["name"]: row["digest"] for row in get("/api/tags").get("models", [])}
    for reader in roster:
        if installed.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
            raise RuntimeError(f"model digest drift for {reader['name']}")
    return devices


def prompt(row: dict) -> tuple[str, dict[str, str]]:
    codes = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mapping = {codes[index]: value for index, value in enumerate(row["options"])}
    choices = "\n".join(f"{code}: {value}" for code, value in mapping.items())
    text = (
        "Use this moved-direction reference literally. moved-earlier means the replacement "
        "schedule is earlier than the prior schedule. moved-later means it is later. Choose "
        "neither tag is warranted when there was no change or the direction is not uniquely "
        "determined.\n\n"
        f"Source event: {row['source_event']}\n"
        f"Proposition: {row['proposition']}\n"
        f"Task: {row['instruction']}\n"
        f"Choices:\n{choices}\n"
        "Answer with EXACTLY one choice code and nothing else."
    )
    return text, mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--qualification",
        required=True,
        help="repo-relative immutable selected-result JSON with roster_ready=true",
    )
    args = parser.parse_args()
    attempt_path = ROOT / "fidelity-attempt.json"
    partial_path = ROOT / "fidelity-partial.json"
    result_path = ROOT / "fidelity-result.json"
    measurement_path = ROOT / "fidelity-measurement.json"
    if any(path.exists() for path in (attempt_path, partial_path, result_path, measurement_path)):
        raise SystemExit("REFUSING: moved-direction fidelity receipt exists; never rerun")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: frozen source is not public at origin/main")
    qualification_path, qualified = qualification(args.qualification)
    relative_qualification = str(qualification_path.relative_to(REPO))
    git("ls-files", "--error-unmatch", relative_qualification)
    if git_blob(commit, relative_qualification) != qualification_path.read_bytes():
        raise SystemExit("REFUSING: qualification bytes differ from the public source commit")
    roster = qualified["fixed_roster"]
    index, packet, items = load_packet()
    devices = gpu_preflight(roster)
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: moved-direction lifecycle is not the current measured surface")
    work = next(
        (
            row
            for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
            if row.get("metric") == "tag_fidelity"
        ),
        None,
    )
    if not work or work.get("state") != "submit_original":
        raise SystemExit("REFUSING: live contract no longer requests a tag_fidelity original")
    if any(
        row.get("metric") == "tag_fidelity" and not row.get("is_replication")
        for row in proposal.get("measurements", [])
    ):
        raise SystemExit("REFUSING: a tag_fidelity original already exists")
    manifest = {
        "kind": "ainglish.moved-direction-controlled-fidelity-manifest.v1",
        "metric": "tag_fidelity",
        "formula_version": 2,
        "construct": "exact warranted moved-earlier / moved-later application",
        "models": [row["name"] for row in roster],
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{commit}/moved-direction-tag-fidelity-carrier-2026-08-26/fidelity-cases.json"
        ),
        "items_sha256": index["items_sha256"],
        "population": packet["population"],
        "aggregation": packet["aggregation"],
        "source": {"repository": "dexagon-ai/ainglish-evidence", "commit": commit},
        "qualification": {
            "path": relative_qualification,
            "content_sha256": qualified["content_sha256"],
            "lineages": [row["lineage"] for row in roster],
        },
        "evidentiary_limit": "controlled-use tag fidelity; not organic adoption or cold comprehension",
    }
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable exact warranted-tag fraction across every cell of the frozen "
            "balanced 96-case audit and every separately qualified reader lineage."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and current proposal read precede mint",
            "the current measured proposal requests a tag_fidelity original",
            "the answer-bearing 96-case packet and runner are public before mint or reader calls",
            "earlier, later, and unwarranted classes each contribute exactly 32 cases",
            "at least two distinct reader lineages passed an immutable ordinary-English holdout",
            "every exact, inexact, null, adverse, or transport outcome is retained without retry",
            "controlled-use fidelity is disclosed separately from organic adoption and cold comprehension",
        ],
        planned_sample={
            "metric": "tag_fidelity",
            "cases": 96,
            "classes": index["classes"],
            "readers": len(roster),
            "reader_lineages": [row["lineage"] for row in roster],
            "cells": 96 * len(roster),
            "items_sha256": index["items_sha256"],
        },
        proposal_revision=SLUG,
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(
        json.dumps(
            {
                "attempt": opened,
                "source_commit": commit,
                "suggestions_generated_at": suggestions.get("generated_at"),
                "gpu_preflight": devices,
                "manifest_commitment": manifest_commitment(manifest),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    rows = []
    try:
        for reader in roster:
            for case in items:
                text, mapping = prompt(case)
                response = post(
                    "/api/chat",
                    {
                        "model": reader["model"],
                        "messages": [{"role": "user", "content": text}],
                        "think": False,
                        "stream": False,
                        "keep_alive": -1,
                        "options": {
                            "temperature": 0,
                            "seed": reader["seed"],
                            "num_predict": 4,
                            "num_ctx": 4096,
                        },
                    },
                    timeout=reader["timeout_s"],
                )
                raw = ((response.get("message") or {}).get("content") or "")
                thinking = ((response.get("message") or {}).get("thinking") or "")
                code = raw.strip().upper()
                exact = len(code) == 1 and code in mapping
                parsed = mapping.get(code) if exact else None
                rows.append(
                    {
                        "reader": reader["name"],
                        "lineage": reader["lineage"],
                        "model": reader["model"],
                        "model_digest": reader["model_digest"],
                        "case_id": case["id"],
                        "class": case["class"],
                        "expected": case["answer"],
                        "parsed": parsed,
                        "exact_code": exact,
                        "correct": parsed == case["answer"],
                        "thinking_bytes": len(thinking.encode()),
                        "raw_output": raw,
                        "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    }
                )
            unload(reader["model"])
            partial_path.write_text(
                json.dumps({"attempt_id": opened["attempt_id"], "rows": rows}, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"completed {reader['name']}", flush=True)
    except Exception as exc:
        partial_path.write_text(
            json.dumps(
                {
                    "attempt_id": opened["attempt_id"],
                    "rows": rows,
                    "error": f"{type(exc).__name__}: {exc}",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            client.abort_attempt(
                opened["attempt_id"],
                "controlled moved-direction fidelity harness failed",
                {
                    "partial_sha256": hashlib.sha256(partial_path.read_bytes()).hexdigest(),
                    "completed_cells": len(rows),
                },
                failed_gate_kind="harness_error",
            )
        raise
    per_member = []
    per_class = {}
    for reader in roster:
        own = [row for row in rows if row["reader"] == reader["name"]]
        per_member.append(
            {"model": reader["name"], "value": sum(row["correct"] for row in own) / len(own)}
        )
        per_class[reader["name"]] = {
            name: sum(row["correct"] for row in own if row["class"] == name)
            / sum(row["class"] == name for row in own)
            for name in ("earlier", "later", "neither")
        }
    value = min(row["value"] for row in per_member)
    result = {
        "kind": "ainglish.moved-direction-controlled-fidelity-result.v1",
        "attempt_id": opened["attempt_id"],
        "manifest": manifest,
        "value": value,
        "per_member": per_member,
        "per_class": per_class,
        "exact_code_cells": sum(row["exact_code"] for row in rows),
        "thinking_bytes": sum(row["thinking_bytes"] for row in rows),
        "rows": rows,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    payload = {
        "metric": "tag_fidelity",
        "formula_version": 2,
        "value": value,
        "value_lo": min(row["value"] for row in per_member),
        "value_hi": max(row["value"] for row in per_member),
        "panel_models": [row["name"] for row in roster],
        "per_member": per_member,
        "manifest": manifest,
        "attempt_id": opened["attempt_id"],
    }
    try:
        filed = client.measure(SLUG, payload)
    except Exception:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            client.abort_attempt(
                opened["attempt_id"],
                "controlled moved-direction fidelity result could not be filed",
                {
                    "result_sha256": result["content_sha256"],
                    "completed_cells": len(rows),
                },
                failed_gate_kind="filing_error",
            )
        raise
    measurement_path.write_text(
        json.dumps({"request": payload, "receipt": filed}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    partial_path.unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "attempt_id": opened["attempt_id"],
                "value": value,
                "per_member": per_member,
                "per_class": per_class,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
