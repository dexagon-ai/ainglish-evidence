#!/usr/bin/env python3
"""Freeze Command R development and holdout plans from non-answer-bearing metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift at {path}")
    return value


def seal(value: dict) -> dict:
    value["content_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    return value


def shared_candidate() -> dict:
    return {
        "lineage": "Command R 35B",
        "producer": "Cohere",
        "source_model": "command-r:35b-08-2024-q4_K_M",
        "source_manifest_sha256": "376304b5a50577f311bfc4fb75cc1217e71b77906b48bb07b652647af760a7bd",
        "capabilities": ["completion", "tools"],
        "details": {
            "family": "command-r",
            "families": ["command-r"],
            "parameter_size": "32.3B",
            "quantization_level": "Q4_K_M",
            "format": "gguf",
            "parent_model": "",
        },
        "template_sha256": "922095537bc1278418b3aeff5c9bdde0c61a5c6adb7573498b09791a95044068",
        "template_length_chars": 2864,
        "official_reference": "https://ollama.com/library/command-r",
        "independence_caveat": (
            "Distinct Cohere family from Qwen, Gemma, Ornith, and Seed; the Reticuli host, "
            "Ollama runtime, and generic qualification harness remain shared infrastructure."
        ),
    }


def format_stage() -> dict:
    source = checked(REPO / "reader-format-structured-v1-2026-08-26" / "plan.json")
    return {
        "source_plan": {
            "file": "reader-format-structured-v1-2026-08-26/plan.json",
            "content_sha256": source["content_sha256"],
        },
        "controls": source["controls"],
        "gate": source["compatibility_gate"],
        "failure_action": "Publish the format result and expose zero semantic items.",
    }


def transport(seed: int) -> dict:
    return {
        "adapter": "ollama-native-chat-json-schema-v1",
        "think": False,
        "temperature": 0,
        "seed": seed,
        "num_ctx": 4096,
        "max_tokens": 16,
        "timeout_s": 600,
        "format": {
            "type": "object",
            "properties": {"answer": {"type": "string", "enum": ["A", "B", "C"]}},
            "required": ["answer"],
            "additionalProperties": False,
        },
    }


def prior_evidence() -> dict:
    return {
        "same_digest_public_reader_receipt": {
            "manifest_hash": "7200b1736f5a760108c5f5305109d2a53f5c5b3415e3ff96bfa87ea389b5ff51",
            "at": "2026-08-29T11:34:07+00:00",
            "meaning": "The exact artifact was installed and served by an independent operator on the selection day; this is not a qualification receipt.",
        },
        "construct_specific_adverse_calibration": {
            "commit": "6c32a4a75c30c1e1feb41baba79f884857104974",
            "path": "they-one-they-many-comprehension-2026-08-29/REFUSAL-run1.json",
            "raw_sha256": "574e90833f4e0a25ed88a35ad0aa8b0e01be4ba79fb6ef327225270f5d57b1b5",
            "canonical_sha256": "bbae58feda80ce0c1dc0c3b9b7dd4ddbe7a5a2ec60e8d2693764f15f5bd8744c",
            "command_r_detectable": 1 / 3,
            "command_r_other": 1 / 3,
            "command_r_gap": 0,
            "panel_gap": 7 / 24,
            "minimum_gap": 0.5,
            "real_cells_attempted": 0,
            "interpretation": (
                "Adverse for that construct-specific calibration and disclosed before this plan; "
                "not a general disqualification and not evidence in favor of Command R."
            ),
        },
    }


def main() -> None:
    candidate = shared_candidate()
    common = {
        "candidate": candidate,
        "runtime": {
            "ollama_version": "0.32.7",
            "structured_output_reference": "https://docs.ollama.com/capabilities/structured-outputs",
        },
        "format_stage": format_stage(),
        "gpu_gate": {
            "ollama_base_url": "http://127.0.0.1:11434",
            "minimum_total_free_mib": 36000,
            "maximum_utilization_percent": 35,
        },
        "prior_evidence": prior_evidence(),
    }
    development_packet = checked(
        REPO / "reader-qualification-calibration-v1-2026-08-26" / "development-packet.json"
    )
    development = seal({
        "kind": "ainglish.panel.reader-command-r-development-plan.v1",
        "result_kind": "ainglish.panel.reader-command-r-development-result.v1",
        "evidentiary_status": "reader development only; never qualification or proposal evidence",
        "phase": "development-command-r-35b",
        "freeze_rule": (
            "This plan and the conditional holdout plan are committed and public before the "
            "first Command R call; never tune or retry after observing a cell."
        ),
        **common,
        "semantic_stage": {
            "packet": {
                "file": "reader-qualification-calibration-v1-2026-08-26/development-packet.json",
                "content_sha256": development_packet["content_sha256"],
            },
            "prompt_contract": (
                "Given only the ordinary-English premise, classify the hypothesis as entailed, "
                "contradicted, or not determined. Return the opaque choice code selected from the supplied mapping."
            ),
            "gate": {
                "valid_json_cells_required": 24,
                "schema_exact_cells_required": 24,
                "correct_cells_required": 22,
                "correct_per_axis_required": 2,
                "correct_per_label_required": 7,
                "thinking_bytes_required": 0,
                "fault_cells_required": 0,
            },
            "pass_meaning": (
                "Eligible only for the separately frozen v10 holdout; this exposed packet never qualifies the reader."
            ),
        },
        "transport": transport(2026082967),
        "result_file": "development-command-r-result.json",
        "journal_file": "development-command-r-attempt-journal.jsonl",
    })

    holdout_packet = checked(REPO / "reader-qualification-v10-general-2026-08-29" / "holdout.json")
    holdout = seal({
        "kind": "ainglish.panel.reader-qualification-plan.v8",
        "instance": "v10-general-2026-08-29-command-r-supplement",
        "result_kind": "ainglish.panel.reader-qualification-result.v8",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "scope": "general Ainglish comprehension carriers only; not any restricted roster",
        "phase": "holdout-command-r",
        "freeze_rule": (
            "This conditional plan is public before the Command R development call. It remains "
            "inert unless the exact development plan passes once without tuning."
        ),
        **common,
        "development_gate": {
            "plan_file": "development-command-r-plan.json",
            "plan_sha256": development["content_sha256"],
            "result_file": development["result_file"],
            "required": "sealed result binds the exact candidate and plan, with v8_holdout_eligible=true",
        },
        "semantic_stage": {
            "packet": {
                "file": "reader-qualification-v10-general-2026-08-29/holdout.json",
                "content_sha256": holdout_packet["content_sha256"],
            },
            "prompt_contract": (
                "Given only the ordinary-English premise, classify the hypothesis as entailed, "
                "contradicted, or not determined. Return the opaque choice code selected from the supplied mapping."
            ),
            "gate": {
                "valid_json_cells_required": 64,
                "schema_exact_cells_required": 64,
                "correct_cells_required": 60,
                "correct_per_axis_required": 7,
                "correct_per_label_required": 0,
                "thinking_bytes_required": 0,
                "fault_cells_required": 0,
            },
            "pass_meaning": "Qualified ordinary-English reader lineage for prospectively frozen general-scope Ainglish panels.",
        },
        "transport": transport(2026082968),
        "result_file": "holdout-command-r-result.json",
        "journal_file": "holdout-command-r-attempt-journal.jsonl",
    })

    for name, value in (
        ("development-command-r-plan.json", development),
        ("holdout-command-r-plan.json", holdout),
    ):
        (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = seal({
        "kind": "ainglish.panel.reader-command-r-prospect-index.v1",
        "candidate_manifest_sha256": candidate["source_manifest_sha256"],
        "plans": [
            {"file": "development-command-r-plan.json", "content_sha256": development["content_sha256"], "activation": "next"},
            {"file": "holdout-command-r-plan.json", "content_sha256": holdout["content_sha256"], "activation": "only after exact development pass"},
        ],
        "adverse_prior_disclosed": True,
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    })
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "development_plan_sha256": development["content_sha256"],
        "holdout_plan_sha256": holdout["content_sha256"],
        "index_sha256": index["content_sha256"],
        "adverse_prior_disclosed": True,
    }, indent=2))


if __name__ == "__main__":
    main()
