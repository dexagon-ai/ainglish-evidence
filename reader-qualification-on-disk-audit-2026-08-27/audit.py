#!/usr/bin/env python3
"""Audit every installed Ollama artifact against retained one-shot qualification history."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
URL = "http://127.0.0.1:11434/api/tags"

LINEAGES = [
    ("qwen", ("qwen",), "qualified-one-lineage", "Qwen 3.6 35B qualified on v8; additional Qwen editions do not create a second lineage."),
    ("yi", ("yi:",), "failed-development", "Yi 1.5 34B failed v9 at 20/24 and 4/8 on not-determined; no retry."),
    ("liquid", ("lfm2",), "failed-development", "LFM2 24B failed v9 at 16/24 and 2/8 on not-determined; no retry."),
    ("mistral", ("mistral",), "failed-development", "Mistral Small 3.2 failed the v8 semantic development gate at 20/24."),
    ("gemma", ("gemma",), "failed-development", "Gemma 3 failed the v8 semantic development gate at 19/24."),
    ("exaone", ("exaone",), "failed-qualification", "EXAONE failed v7 qualification and v8 development."),
    ("phi", ("phi4",), "failed-qualification", "Phi-4 passed v8 development but failed the fresh holdout at 58/64 and 6/8 on two axes."),
    ("llama", ("llama3",), "failed-qualification", "Llama 3.1 failed v5 at 59/64 and 6/8 reference resolution."),
    ("granite", ("granite",), "failed-qualification", "Granite 3.3 failed v5 at 55/64."),
    ("command", ("command-r",), "failed-qualification", "Command R7B failed v5 at 55/64."),
    ("internlm", ("internlm",), "failed-qualification", "InternLM 2 failed v7 at 53/64."),
    ("deepseek", ("deepseek",), "failed-qualification", "DeepSeek V2 Lite failed v7 at 38/64."),
    ("olmo", ("olmo",), "failed-qualification", "OLMo 2 failed v7 at 46/64."),
    ("falcon", ("falcon",), "failed-qualification", "Falcon 3 failed v7 at 51/64."),
    ("glm", ("glm",), "failed-qualification", "GLM-4 failed v7 at 51/64."),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def classify(name: str) -> tuple[str, str, str]:
    low = name.casefold()
    for lineage, needles, status, reason in LINEAGES:
        if any(needle in low for needle in needles):
            return lineage, status, reason
    return "unclassified", "manual-review", "The installed tag did not map to a retained qualification lineage."


def main() -> None:
    with urllib.request.urlopen(URL, timeout=10) as response:
        payload = json.load(response)
    artifacts = []
    for model in sorted(payload.get("models", []), key=lambda row: row.get("name", "")):
        lineage, status, reason = classify(model["name"])
        artifacts.append({
            "name": model["name"], "digest": model.get("digest"), "size": model.get("size"),
            "lineage": lineage, "history_status": status, "eligibility": "not-eligible-fresh-distinct",
            "reason": reason,
        })
    grouped = defaultdict(lambda: {"tags": 0, "digests": set(), "status": set()})
    for row in artifacts:
        grouped[row["lineage"]]["tags"] += 1
        grouped[row["lineage"]]["digests"].add(row["digest"])
        grouped[row["lineage"]]["status"].add(row["history_status"])
    lineages = {
        key: {"tags": value["tags"], "distinct_local_digests": len(value["digests"]), "history_status": sorted(value["status"])}
        for key, value in sorted(grouped.items())
    }
    assert "manual-review" not in {row["history_status"] for row in artifacts}, "unclassified model requires judgement"
    result = {
        "kind": "dexagon.ainglish.reader-qualification-on-disk-audit.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "artifacts": artifacts,
        "lineages": lineages,
        "qualification_state": {
            "qualified_distinct_lineages": 1,
            "required_distinct_lineages": 2,
            "roster_ready": False,
            "fresh_distinct_installed_candidates": 0,
        },
        "decision": "No inference sweep is authorised: every installed distinct lineage is already qualified, failed on a retained one-shot gate, or is another edition of the sole qualified Qwen lineage.",
        "no_retry_rule": "Do not rerun burned cells, retune their prompt, or count same-lineage editions as independent readers.",
        "downloads": 0, "model_calls": 0, "governance_writes": 0,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "installed_tags": len(artifacts), "lineages": len(lineages),
        **result["qualification_state"], "model_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
