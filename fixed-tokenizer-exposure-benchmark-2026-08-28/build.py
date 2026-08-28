#!/usr/bin/env python3
"""Freeze a compact exact-form recall/repair benchmark before model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROGRAM = ROOT.parent / "ainglish-learning-program-2026-08-25"
RELEASE = ROOT.parent.parent / "ainglish-releases" / "ainglish-training-v0.35.0"
GLOSSES = {
    "by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3": "Distinguish a missing doer whose identity the author does not know from one the author knows but deliberately omits.",
    "claim-tag": "Append both numeric confidence and a concrete falsifying observation to an assertion.",
    "ctl-control-declare-whether-a-null-result-could-have-been-ot-3": "Say whether a reported null or negative had a named positive control, or no positive control at all.",
    "each-alone-as-one-distributive-vs-collective-does-the-plural": "Say whether every member performs an action separately or the group performs it once collectively.",
    "eta-t-the-report-back-pin-silence-into-expectation-2": "Pin the expected time of the next status report without claiming completion by then.",
    "fact-not-known-choice-not-made-distinguish-missing-evidence-": "Distinguish an unresolved factual question from a decision that has not yet been made.",
    "force-suspended-mention-a-line-without-issuing-its-claims-re-3": "Present words for inspection without activating their claim, request, promise, or acknowledgement force.",
    "grader-is-graded-robust-word-based-form-of-grader-graded-2": "Declare that the same principal both performs an evaluation and is the object evaluated.",
    "human-needed-why-the-escalation-pin-when-a-human-must-decide-2": "Stop autonomous progress and name why a human decision is required.",
    "no-delegation-one-hop-delegation-allowed-state-whether-a-tas": "State either that no completion-bearing work may be handed to another principal or that direct delegates are allowed but may not redelegate.",
    "or-both-not-both-english-or-never-says-whether-both-is-allow": "State whether a two-way disjunction permits choosing both branches or requires exactly one.",
    "passed-not-applied-robust-word-based-form-of-passed-applied-2": "Say that a check, vote, or claim was accepted but was not actually enacted or used.",
    "start-by-complete-by-say-which-task-event-a-deadline-constra": "Distinguish a deadline for genuine execution to begin from a deadline for successful completion.",
    "still-the-liveness-marker-was-true-at-last-check-not-re-chec": "Say a property held at the last check but has not been rechecked since.",
    "stopped-done-under-c-complete-for-r-say-which-claim-your-don": "Distinguish merely ceasing work, succeeding only under named tested conditions, and an unqualified handoff ready for a named consumer.",
    "text-fixed-ref-meaning-fixed-ref-declare-which-invariants-a-": "Distinguish exact character preservation of a referenced passage from complete meaning preservation with rewording allowed.",
    "true-as-worded-false-as-worded-unambiguous-answers-to-negati": "Answer a polar question by asserting or denying its proposition exactly as worded, including written negation.",
    "we-including-you-we-excluding-you-clusivity-mark-whether-we--4": "Say whether first-person plural includes the addressee or excludes the addressee.",
    "you-one-you-all-say-whether-you-addresses-one-recipient-or-t": "Say whether second-person reference addresses one recipient or every recipient in the addressed group.",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    register_path = RELEASE / "data" / "register.jsonl"
    rows = [json.loads(line) for line in register_path.read_text(encoding="utf-8").splitlines() if line]
    manifest = json.loads((PROGRAM / "manifest.json").read_text(encoding="utf-8"))
    withheld = set(manifest["transfer_holdout_constructs"])
    if set(GLOSSES) != {row["slug"] for row in rows}:
        raise SystemExit("REFUSING: authored gloss population does not match the release")
    items = []
    for index, row in enumerate(rows, 1):
        gloss = GLOSSES[row["slug"]]
        if any(part.lower() in gloss.lower() for part in row["form"].replace("|", "/").split("/")):
            raise SystemExit(f"REFUSING: answer surface leaked into gloss for {row['slug']}")
        items.append({
            "id": f"form-{index:02d}",
            "slug": row["slug"],
            "exposure_class": "withheld_surface" if row["slug"] in withheld else "trained_surface",
            "gloss": gloss,
            "answer": row["form"],
            "repair_definition": row["english_mapping"],
        })
    document = {
        "kind": "dexagon.ainglish.fixed-tokenizer-exposure-benchmark.v1",
        "purpose": "Measure exact registered-form recall and the full interaction-token cost of one authoritative repair, with the same base weights, tokenizer and decoding before versus after a previously frozen Ainglish QLoRA adapter.",
        "source": {
            "release": "0.35.0",
            "register_sha256": sha(register_path),
            "learning_manifest_sha256": sha(PROGRAM / "manifest.json"),
            "development_training_sha256": manifest["outputs"]["train-dev.jsonl"]["sha256"],
        },
        "protocol": {
            "round_1": "Given only a fresh marker-free gloss, return the exact registered form and nothing else.",
            "round_2": "Only after an incorrect/invalid first answer, append the exact registered form and definition as an authoritative repair receipt and ask again.",
            "success": "Unicode-NFKC and whitespace-normalized output equals the registered form; no semantic grader.",
            "cost": "For every request, count the full chat-template input plus generated continuation with the one fixed Qwen tokenizer; a repair request therefore includes the repeated history.",
            "interpretation": "The 15 trained-surface rows test exposure uptake. The four deliberately withheld surfaces test transfer and are reported separately. This is product research, never governance evidence or independent confirmation.",
        },
        "items": items,
        "model_calls": 0,
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    (ROOT / "items.json").write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "trained": len(items) - len(withheld), "withheld": len(withheld), "content_sha256": document["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
