#!/usr/bin/env python3
"""Mint, run, and file the controlled evidential-tag fidelity original once."""

from __future__ import annotations

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
QUALIFICATION = REPO / "send-snapshot-live-view-comprehension-v1-2026-09-03" / "runspec-local-qualified.json"
SLUG = "evidential-tags-obs-inf-rep-src-with-instrument-recall-and-p-2"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


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
    post("/api/generate", {"model": model, "prompt": "", "stream": False, "keep_alive": 0}, timeout=60)


def choice_prompt(case: dict) -> tuple[str, dict[str, str]]:
    codes = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    mapping = {codes[index]: value for index, value in enumerate(case["options"])}
    rendered = "\n".join(f"{code}: {value}" for code, value in mapping.items())
    text = (
        "Use this evidential-tag reference literally:\n"
        "obs: = direct personal observation; obs(I): = instrument I reported it; "
        "inf: = inference without named premises; inf(P): = inference from named premises P; "
        "rep(S): = report from external source S; rep(self-past): = own earlier memory, unverified now.\n\n"
        f"Source event: {case['source_event']}\nProposition: {case['proposition']}\n"
        f"Task: {case['instruction']}\nChoices:\n{rendered}\n"
        "Answer with EXACTLY one choice code and nothing else."
    )
    return text, mapping


def get(path: str) -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=30) as response:
        return json.load(response)


def gpu_preflight(panel: list[dict]) -> list[dict]:
    output = subprocess.run([
        "nvidia-smi", "--query-gpu=index,name,memory.free,utilization.gpu", "--format=csv,noheader,nounits",
    ], check=True, capture_output=True, text=True).stdout
    rows = []
    for line in output.splitlines():
        index, name, free, utilization = [part.strip() for part in line.split(",", 3)]
        rows.append({"index": int(index), "name": name, "free_mib": int(free), "utilization": int(utilization)})
    if sum(row["free_mib"] for row in rows) < 36_000 or max(row["utilization"] for row in rows) > 35:
        raise RuntimeError("GPU gate failed")
    if get("/api/ps").get("models"):
        raise RuntimeError("an Ollama model is already resident")
    installed = {row["name"]: row["digest"] for row in get("/api/tags").get("models", [])}
    for reader in panel:
        expected = reader["model_digest"].removeprefix("sha256:")
        if installed.get(reader["model"]) != expected:
            raise RuntimeError(f"model digest drift for {reader['name']}")
    return rows


def main() -> None:
    attempt_path = ROOT / "fidelity-attempt.json"
    partial_path = ROOT / "fidelity-partial.json"
    result_path = ROOT / "fidelity-result.json"
    receipt_path = ROOT / "fidelity-measurement.json"
    if any(path.exists() for path in (attempt_path, partial_path, result_path, receipt_path)):
        raise SystemExit("REFUSING: fidelity receipt exists; never rerun")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: source commit is not public at origin/main")
    cases = json.loads((ROOT / "fidelity-cases.json").read_text())
    index = json.loads((ROOT / "index.json").read_text())
    cases_sha = hashlib.sha256(canonical(cases)).hexdigest()
    if len(cases) != 96 or cases_sha != index["fidelity"]["sha256"]:
        raise SystemExit("REFUSING: fidelity population drift")
    qualification = json.loads(QUALIFICATION.read_text())
    receipts = qualification.get("reader_qualifications") or []
    if len(receipts) != 2 or not all(row.get("result", {}).get("passed") for row in receipts):
        raise SystemExit("REFUSING: current target-independent reader roster did not qualify")
    now = datetime.now(timezone.utc)
    if any(datetime.fromisoformat(row["valid_until"]) <= now for row in receipts):
        raise SystemExit("REFUSING: a reader qualification has expired")
    receipt_by_digest = {row["reader"]["model_digest"]: row for row in receipts}
    panel = []
    for reader in qualification.get("panel") or []:
        receipt = receipt_by_digest.get(reader.get("model_digest"))
        if not receipt:
            raise SystemExit("REFUSING: panel reader has no matching qualification receipt")
        panel.append({**reader, "lineage": receipt["lineage"]["key"]})
    if len({row["lineage"] for row in panel}) < 2:
        raise SystemExit("REFUSING: fewer than two qualified reader lineages")
    devices = gpu_preflight(panel)
    client = ainglish_client()
    identity = client.whoami()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: evidential-tags lifecycle is not the current measured surface")
    if (proposal.get("proposer") or {}).get("sub") == identity.get("sub"):
        raise SystemExit("REFUSING: the executing principal is the proposer")
    if any(row.get("metric") == "tag_fidelity" and not row.get("is_replication") for row in proposal.get("measurements", [])):
        raise SystemExit("REFUSING: a tag_fidelity original already exists")
    work = {
        row.get("metric"): row
        for row in (proposal.get("evidence_readiness") or {}).get("work_items") or []
    }.get("tag_fidelity") or {}
    if work.get("state") != "submit_original":
        raise SystemExit(f"REFUSING: fresh proposal no longer requests tag_fidelity original: {work!r}")
    manifest = {
        "kind": "ainglish.evidential-tags-controlled-fidelity-manifest.v1",
        "metric": "tag_fidelity",
        "formula_version": 2,
        "construct": "evidential-tags controlled exact application",
        "models": [row["name"] for row in panel],
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/evidential-tags-fidelity-and-carrier-2026-08-25/fidelity-cases.json",
        "items_sha256": cases_sha,
        "population": "96 blinded controlled-use cases, exactly 16 per declared evidential-tag form",
        "aggregation": "least-favourable exact tag-application fraction across qualified reader lineages",
        "source": {"repository": "dexagon-ai/ainglish-evidence", "commit": commit},
        "qualification_sha256": hashlib.sha256(canonical({
            "panel": qualification.get("panel"),
            "reader_qualifications": receipts,
        })).hexdigest(),
        "reader_qualifications": receipts,
        "training_asymmetry": (
            "These present readers were trained primarily on ordinary English and are not "
            "assumed to have seen Ainglish. This controlled audit measures current zero-shot "
            "tag application, not expected performance after Ainglish-aware training."
        ),
    }
    estimand = "The least-favourable exact warranted-prefix application fraction across every cell of a frozen balanced 96-case controlled-use audit and every separately qualified reader lineage."
    gates = [
            "fresh authenticated suggestions and a fresh proposal read precede mint",
            "the current lifecycle has no tag_fidelity original",
            "the answer-bearing 96-case population and runner are public before mint or model calls",
            "all six declared forms contribute exactly sixteen cases",
            "at least two distinct reader lineages passed the frozen ordinary-English holdout",
            "every exact, inexact, null, adverse, or transport outcome is retained without retry",
            "this controlled-use estimand is disclosed separately from organic adoption fidelity",
        ]
    planned_sample = {
            "metric": "tag_fidelity", "cases": 96, "cases_per_form": 16,
            "readers": len(panel), "reader_lineages": [row["lineage"] for row in panel],
            "cells": 96 * len(panel), "items_sha256": cases_sha,
        }
    server_preflight = client.preflight_attempt(
        SLUG, manifest, estimand, gates, planned_sample,
        proposal_revision=SLUG,
    )
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=estimand,
        admissibility_gates=gates,
        planned_sample=planned_sample,
        proposal_revision=SLUG,
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({
        "attempt": opened, "source_commit": commit, "suggestions_generated_at": suggestions.get("generated_at"),
        "gpu_preflight": devices, "manifest_commitment": manifest_commitment(manifest),
        "server_preflight": server_preflight,
    }, indent=2) + "\n")
    rows = []
    try:
        for reader in panel:
            for case in cases:
                prompt, mapping = choice_prompt(case)
                response = post("/api/chat", {
                    "model": reader["model"], "messages": [{"role": "user", "content": prompt}],
                    "think": False, "stream": False, "keep_alive": -1,
                    "options": {"temperature": 0, "seed": reader["seed"], "num_predict": 4, "num_ctx": 4096},
                }, timeout=reader["timeout_s"])
                raw = ((response.get("message") or {}).get("content") or "")
                thinking = ((response.get("message") or {}).get("thinking") or "")
                code = raw.strip().upper()
                exact = len(code) == 1 and code in mapping
                parsed = mapping.get(code) if exact else None
                rows.append({
                    "reader": reader["name"], "lineage": reader["lineage"], "model": reader["model"],
                    "model_digest": reader["model_digest"], "case_id": case["id"], "form": case["form"],
                    "expected": case["answer"], "parsed": parsed, "exact_code": exact,
                    "correct": parsed == case["answer"], "thinking_bytes": len(thinking.encode()),
                    "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                })
            unload(reader["model"])
            partial_path.write_text(json.dumps({"attempt_id": opened["attempt_id"], "rows": rows}, indent=2) + "\n")
            print(f"completed {reader['name']}", flush=True)
    except Exception as exc:
        partial_path.write_text(json.dumps({"attempt_id": opened["attempt_id"], "rows": rows, "error": f"{type(exc).__name__}: {exc}"}, indent=2) + "\n")
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            client.abort_attempt(opened["attempt_id"], "controlled tag-fidelity harness failed", {
                "partial_sha256": hashlib.sha256(partial_path.read_bytes()).hexdigest(), "completed_cells": len(rows),
            }, failed_gate_kind="harness_error")
        raise
    per_member = []
    by_form = {}
    for reader in panel:
        own = [row for row in rows if row["reader"] == reader["name"]]
        value = sum(row["correct"] for row in own) / len(own)
        per_member.append({"model": reader["name"], "value": value})
        by_form[reader["name"]] = {
            form: sum(row["correct"] for row in own if row["form"] == form) / sum(row["form"] == form for row in own)
            for form in sorted({row["form"] for row in own})
        }
    value = min(row["value"] for row in per_member)
    result = {
        "kind": "ainglish.evidential-tags-controlled-fidelity-result.v1",
        "attempt_id": opened["attempt_id"], "manifest": manifest,
        "value": value, "per_member": per_member, "per_form": by_form,
        "exact_code_cells": sum(row["exact_code"] for row in rows),
        "thinking_bytes": sum(row["thinking_bytes"] for row in rows), "rows": rows,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    payload = {
        "metric": "tag_fidelity", "formula_version": 2,
        "value": value, "value_lo": min(row["value"] for row in per_member),
        "value_hi": max(row["value"] for row in per_member),
        "panel_models": [row["name"] for row in panel], "per_member": per_member,
        "manifest": manifest, "attempt_id": opened["attempt_id"],
    }
    filed = client.measure(SLUG, payload)
    receipt_path.write_text(json.dumps({"request": payload, "receipt": filed}, indent=2, ensure_ascii=False) + "\n")
    partial_path.unlink(missing_ok=True)
    print(json.dumps({"attempt_id": opened["attempt_id"], "value": value, "per_member": per_member, "per_form": by_form}, indent=2))


if __name__ == "__main__":
    main()
