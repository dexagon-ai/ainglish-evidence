#!/usr/bin/env python3
"""Freeze the v3 ordinary-English development screen before any reader call."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "development.json"
AXES = [
    "quantifier_force", "set_membership", "negation_scope",
    "disjunction", "conditional", "reference_resolution",
]


RAW = [
    ("quantifier_force", "Some of the eight checks passed; the note gives no further count.", "Did all eight checks pass?", "cannot tell", ["yes", "no"]),
    ("quantifier_force", "Every listed signer approved the waiver.", "Is any listed signer still unapproved?", "no", ["yes", "cannot tell"]),
    ("quantifier_force", "Exactly three of the five valves were inspected.", "Were all five valves inspected?", "no", ["yes", "cannot tell"]),
    ("quantifier_force", "Not every invoice was reconciled.", "Was at least one invoice left unreconciled?", "yes", ["no", "cannot tell"]),
    ("set_membership", "Asha, you as the reader, and Lin are assigned to inspect the archive.", "Is the reader assigned to inspect the archive?", "yes", ["no", "cannot tell"]),
    ("set_membership", "The maintainers will rotate the key. You are an observer, not a maintainer.", "Is the reader expected to rotate the key?", "no", ["yes", "cannot tell"]),
    ("set_membership", "Everyone addressed on the memo must reply. The memo is addressed to Dana and to you.", "Must the reader reply?", "yes", ["no", "cannot tell"]),
    ("set_membership", "Only members of the red team may approve the release. The reader's team is not stated.", "May the reader approve the release?", "cannot tell", ["yes", "no"]),
    ("negation_scope", "Do not archive either draft.", "Does archiving one draft comply?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "It is not required that both reviewers sign.", "Does this sentence forbid both reviewers from signing?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "No reviewer except Mina may edit the ledger.", "May a reviewer other than Mina edit the ledger?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "The report does not say that Kim failed the check.", "Did Kim fail the check?", "cannot tell", ["yes", "no"]),
    ("disjunction", "Run pump A or pump B, possibly both.", "Would running both pumps comply?", "yes", ["no", "cannot tell"]),
    ("disjunction", "Run either pump A or pump B, but not both.", "Would running both pumps comply?", "no", ["yes", "cannot tell"]),
    ("disjunction", "At least one of the two mirrors must be checked.", "Must exactly one mirror be checked?", "no", ["yes", "cannot tell"]),
    ("disjunction", "Choose one of the two migration windows and use only that window.", "May both windows be used?", "no", ["yes", "cannot tell"]),
    ("conditional", "If the checksum fails, rerun the transfer. The checksum failed.", "Is a rerun required?", "yes", ["no", "cannot tell"]),
    ("conditional", "Rerun the transfer only if the checksum fails. The checksum passed.", "Is a rerun permitted by this rule?", "no", ["yes", "cannot tell"]),
    ("conditional", "Unless approval arrives, pause the rollout. The message does not say whether approval arrived.", "Must the rollout be paused?", "cannot tell", ["yes", "no"]),
    ("conditional", "If the alarm fires, the door unlocks. The door unlocked.", "Did the alarm necessarily fire?", "no", ["yes", "cannot tell"]),
    ("reference_resolution", "Maya sent Lio the report. Lio archived it.", "Who archived the report?", "Lio", ["Maya", "cannot tell"]),
    ("reference_resolution", "The amber file and the blue file were compared. The latter was deleted.", "Which file was deleted?", "the blue file", ["the amber file", "cannot tell"]),
    ("reference_resolution", "Nora told Priya that her badge had expired.", "Whose badge had expired?", "cannot tell", ["Nora's", "Priya's"]),
    ("reference_resolution", "Sam reviewed the old policy and the replacement policy. The former was withdrawn.", "Which policy was withdrawn?", "the old policy", ["the replacement policy", "cannot tell"]),
]


def items() -> list[dict]:
    out = []
    for index, (axis, message, question, answer, distractors) in enumerate(RAW):
        options = list(distractors)
        options.insert(index % 3, answer)
        out.append({
            "id": f"v3-dev-{axis}-{index + 1:02d}", "axis": axis,
            "message": message, "question": question, "options": options, "answer": answer,
        })
    return out


def main() -> None:
    if OUT.exists():
        raise SystemExit("REFUSING: development.json already exists")
    rows = items()
    positions = [row["options"].index(row["answer"]) for row in rows]
    if {position: positions.count(position) for position in range(3)} != {0: 8, 1: 8, 2: 8}:
        raise SystemExit("REFUSING: answer positions are not balanced")
    spec = {
        "kind": "ainglish.panel.reader-qualification-development.v3",
        "result_kind": "ainglish.panel.reader-qualification-development-result.v3",
        "purpose": "Develop new construct-blind Qwen reader editions without reading the later qualification holdout.",
        "evidentiary_status": "instrument development only; never proposal evidence or a qualification result",
        "sdk_version": "0.2.34",
        "sdk_commit": "aac3ea50d48d76ce41b96c9f762d5c05dc53b4b5",
        "sdk_panel_path": "/home/dexagon/codex/dexagon/worktrees/sdk-attempt-manifest-v2-20260823/src/ainglish/panel.py",
        "answer_protocol": "opaque-choice-v1",
        "axes": AXES, "items_per_axis": 4,
        "forbidden_construct_terms": [
            "some-or-all", "some-but-not-all", "we-including-you", "we-excluding-you",
            "proposal-by", "decision-by", "or-both", "not-both", "fact-not-known",
            "choice-not-made", "ainglish",
        ],
        "disjoint_from_specs": [
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-tournament-2026-08-23/spec.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v2-2026-08-24/development.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v2-2026-08-24/holdout.json",
        ],
        "gpu_gate": {
            "ollama_base_url": "http://127.0.0.1:11434", "ollama_ps": "http://127.0.0.1:11434/api/ps",
            "minimum_total_free_mib": 36000, "maximum_utilization_percent": 30,
        },
        "selection_rule": {
            "exact_code_cells_required": 24, "correct_cells_required": 22,
            "correct_per_axis_required": 3, "minimum_distinct_qualified_lineages": 1,
            "status": "development diagnostic only; final qualification is frozen separately on an untouched holdout",
        },
        "panel": [
            {
                "name": "qwen3.8-27b-screen-q4_k_m", "lineage": "Qwen 3.8 27B", "provider": "ollama",
                "model": "dexagon-qwen3.8-27b-screen:ctx4k",
                "model_digest": "sha256:97a12d32a43050d86486d7d3a4253036603e5209ae717da488f95b46c704df47",
                "precision": "q4_k_m", "max_tokens": 16, "timeout_s": 120,
                "temperature": 0, "seed": 2026082403, "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
            },
            {
                "name": "qwen2.5-7b-literal-v3-q4_k_m", "lineage": "Qwen 2.5 7B", "provider": "ollama",
                "model": "dexagon-qwen2.5-7b-literal-v3:ctx4k",
                "model_digest": "sha256:ba3f85f29dd86fdf52a87f20b1d30634c7fc1460341e1cd23a2463c2eaa5fd68",
                "precision": "q4_k_m", "max_tokens": 16, "timeout_s": 120,
                "temperature": 0, "seed": 2026082403, "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
            },
        ],
        "items": rows,
    }
    OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "items": len(rows), "answer_positions": {str(i): positions.count(i) for i in range(3)}}))


if __name__ == "__main__":
    main()
