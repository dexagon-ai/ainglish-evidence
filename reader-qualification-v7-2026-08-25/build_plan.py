#!/usr/bin/env python3
"""Carry the unexposed v6 packet into a corrected, newly sealed v7 plan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
V6 = REPO / "reader-qualification-v6-2026-08-25"

CANDIDATES = {
    "phase-a": [
        {
            "name": "exaone3.5-32b-qualification-v7",
            "lineage": "EXAONE 3.5 32B",
            "producer": "LG AI Research",
            "source_model": "exaone3.5:32b",
            "source_manifest_sha256": "f2f69abac3dadd89fb740b06e78a529baf0295d70b7a96b48c6bb9061a7e247b",
            "model_blob_sha256": "a92c55b71e45d620cee84ed774eef6113d41c39a28bb2da562a871b288f411cf",
            "model_blob_bytes": 19343747808,
            "wrapper_model": "dexagon-exaone3.5-32b-qualification-v7:ctx4k",
            "precision": "q4_k_m",
            "modelfile": "Modelfile.exaone",
            "official_reference": "https://ollama.com/library/exaone3.5:32b",
        },
        {
            "name": "internlm2-20b-qualification-v7",
            "lineage": "InternLM 2 20B",
            "producer": "Shanghai AI Laboratory",
            "source_model": "internlm2:20b",
            "source_manifest_sha256": "a864ac8dade269ecd21d030dae5fe14be73bf27b1a6f5582537bbf4fd538ec2e",
            "model_blob_sha256": "3db452abec76c0f0ffce7801ce03016eeff9903963bd657730ec180af7fb8a1e",
            "model_blob_bytes": 11322686976,
            "wrapper_model": "dexagon-internlm2-20b-qualification-v7:ctx4k",
            "precision": "q4_0",
            "modelfile": "Modelfile.internlm",
            "official_reference": "https://ollama.com/library/internlm2:20b",
        },
    ],
    "reserve-b": [
        {
            "name": "deepseek-v2-16b-qualification-v7",
            "lineage": "DeepSeek V2 Lite 16B",
            "producer": "DeepSeek AI",
            "source_model": "deepseek-v2:16b",
            "source_manifest_sha256": "7c8c332f2df7ac4d657f3514d757d969b84ac6d3fec5b0c02bc8491bd0dc5ea1",
            "model_blob_sha256": "d8d69f2a1bfa02efc9c757c5dba444886cf33f54651c9cfe78c94046ddc048bc",
            "model_blob_bytes": 8905109824,
            "wrapper_model": "dexagon-deepseek-v2-16b-qualification-v7:ctx4k",
            "precision": "q4_0",
            "modelfile": "Modelfile.deepseek",
            "official_reference": "https://ollama.com/library/deepseek-v2:16b",
        },
        {
            "name": "olmo2-13b-qualification-v7",
            "lineage": "OLMo 2 13B",
            "producer": "Allen Institute for AI",
            "source_model": "olmo2:13b",
            "source_manifest_sha256": "6c279ebc980fb07ca7b49cccf17b5faef6a73082cac4b3d44d2226981de676da",
            "model_blob_sha256": "cd836509a1a051178be134eba84115eb3a6653a1bd58473a706bf8ee4ab3a764",
            "model_blob_bytes": 8354349536,
            "wrapper_model": "dexagon-olmo2-13b-qualification-v7:ctx4k",
            "precision": "q4_k_m",
            "modelfile": "Modelfile.olmo",
            "official_reference": "https://ollama.com/library/olmo2:13b",
        },
    ],
    "final-reserve": [
        {
            "name": "falcon3-10b-qualification-v7",
            "lineage": "Falcon 3 10B",
            "producer": "Technology Innovation Institute",
            "source_model": "falcon3:10b",
            "source_manifest_sha256": "1653ff122acd9292fe21a097c0f08ce419439be595b312d6d6d06ee33df91b88",
            "model_blob_sha256": "c8647169c2b98160c1be33a2e4faa2130bcc5d1c70100ce1e5d159f0448663c6",
            "model_blob_bytes": 6287519808,
            "wrapper_model": "dexagon-falcon3-10b-qualification-v7:ctx4k",
            "precision": "q4_k_m",
            "modelfile": "Modelfile.falcon",
            "official_reference": "https://ollama.com/library/falcon3:10b",
        },
        {
            "name": "glm4-9b-qualification-v7",
            "lineage": "GLM-4 9B",
            "producer": "THUDM",
            "source_model": "glm4:9b",
            "source_manifest_sha256": "5b699761eca535dc55047ad9d2dbf54e3b8697709419ef78a70503ed4bfbcf44",
            "model_blob_sha256": "b506a070d1152798d435ec4e7687336567ae653b3106f73b7b4ac7be1cbc4449",
            "model_blob_bytes": 5455319040,
            "wrapper_model": "dexagon-glm4-9b-qualification-v7:ctx4k",
            "precision": "q4_0",
            "modelfile": "Modelfile.glm",
            "official_reference": "https://ollama.com/library/glm4:9b",
        },
    ],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}")
    return value


def validate_unseen_candidates() -> None:
    needles = [row["source_model"].casefold() for phase in CANDIDATES.values() for row in phase]
    for path in REPO.rglob("*result*.json"):
        if ROOT in path.parents or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").casefold()
        for needle in needles:
            if needle in text:
                raise SystemExit(f"REFUSING: candidate {needle} appears in executed result {path.relative_to(REPO)}")


def main() -> None:
    target = ROOT / "plan.json"
    if target.exists():
        raise SystemExit("REFUSING: plan.json already exists")
    v6_plan = checked(V6 / "plan.json")
    v6_abort = checked(V6 / "preflight-abort.json")
    if v6_abort["plan_sha256"] != v6_plan["content_sha256"]:
        raise SystemExit("REFUSING: v6 abort does not bind v6 plan")
    if v6_abort["model_calls"] or v6_abort["qualification_items_exposed"]:
        raise SystemExit("REFUSING: v6 packet was exposed and cannot be carried forward")
    validate_unseen_candidates()
    plan = {
        "kind": "ainglish.panel.reader-qualification-plan.v7",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "supersedes": {
            "plan_file": "../reader-qualification-v6-2026-08-25/plan.json",
            "plan_sha256": v6_plan["content_sha256"],
            "abort_file": "../reader-qualification-v6-2026-08-25/preflight-abort.json",
            "abort_sha256": v6_abort["content_sha256"],
            "carry_forward": "Exact item order and answer key; zero prior model calls and zero exposed qualification items.",
        },
        "freeze_rule": "This corrected plan, candidate order, carried-forward item set, answer key, prompt, thresholds, compatibility gate, and transport bounds are committed before any v7 candidate download or inference.",
        "answer_protocol": v6_plan["answer_protocol"],
        "transport": v6_plan["transport"],
        "axes": v6_plan["axes"],
        "items_per_axis": v6_plan["items_per_axis"],
        "answer_position_counts": v6_plan["answer_position_counts"],
        "forbidden_construct_terms": v6_plan["forbidden_construct_terms"],
        "disjoint_from_specs": v6_plan["disjoint_from_specs"],
        "candidate_novelty": "No v7 source_model appears in any executed result artifact in this repository at freeze time. Four candidates were named but never run in aborted v6; two are newly introduced in v7.",
        "compatibility_rule": "At freeze time the official Ollama library entry must not advertise thinking. After pinned acquisition and before holdout publication, /api/show capabilities for both source and wrapper must exclude thinking. Any mismatch refuses the tranche before item exposure.",
        "candidate_tranches": CANDIDATES,
        "tranche_rule": "Run phase A first; acquire and run each later tranche only if accumulated published results still contain fewer than two qualified lineages.",
        "gpu_gate": v6_plan["gpu_gate"],
        "selection_rule": v6_plan["selection_rule"],
        "items": v6_plan["items"],
    }
    plan["content_sha256"] = hashlib.sha256(canonical(plan)).hexdigest()
    with target.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"items": len(plan["items"]), "candidate_calls": 0, "downloads": 0, "sha256": plan["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
