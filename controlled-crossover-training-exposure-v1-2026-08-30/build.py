#!/usr/bin/env python3
"""Build disjoint cross-over training corpora and evaluation prompts without model calls."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
ATLAS = REPO / "flagship-cold-clarity-atlas-v1-2026-08-29"
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
BASE_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
GROUPS = {
    "a": ["list_completeness", "pronoun_number", "claim_source"],
    "b": ["role_cardinality", "event_or_state_recurrence", "failure_contract"],
}
TRAIN_ROWS_PER_CONSTRUCT = 600
EVAL_FRAMES_PER_CONSTRUCT = 48
SYSTEM = (
    "Choose only the operational consequence licensed by the message. Do not assume unstated "
    "intentions. Return exactly one JSON object {\"answer\":\"<OPTION LABEL>\"} and no prose."
)

TRAIN_VOCAB = {
    "roles": ["reviewer", "auditor", "operator", "maintainer", "custodian", "approver", "dispatcher", "verifier"],
    "actors": ["Ari", "Bo", "Cy", "Di", "Eli", "Fia", "Gus", "Hana"],
    "objects": ["artifact", "record", "service", "bundle", "account", "job", "archive", "vault"],
    "kinds": ["format", "region", "status", "channel", "role", "command", "transport", "codec"],
    "sources": ["Mira", "Node-Q", "Supplier-Z", "Monitor-P", "Ledger-K", "Agent-V"],
    "bases": ["log-pattern", "checksum-match", "counter-delta", "trace-link", "receipt-chain", "sensor-trend"],
    "role_actions": ["approve", "sign", "release", "unlock", "verify", "archive"],
    "pronoun_actions": ["approved", "signed", "released", "checked", "acknowledged", "authorized"],
    "events": [("opened", "open", "gate"), ("started", "running", "service"), ("sealed", "sealed", "container"), ("enabled", "enabled", "account"), ("connected", "connected", "link"), ("unlocked", "unlocked", "vault")],
    "failure_actions": [("upload", "uploaded"), ("notify", "notified"), ("create", "created"), ("acquire", "acquired"), ("deliver", "delivered"), ("synchronize", "synchronized")],
}
EVAL_VOCAB = {
    "roles": ["inspector", "archivist", "moderator", "controller", "steward", "witness"],
    "actors": ["Jae", "Kira", "Luis", "Mei", "Nia", "Otto"],
    "objects": ["capsule", "manifest", "daemon", "package", "credential", "batch"],
    "kinds": ["dialect", "zone", "signal", "route", "permission", "mode"],
    "sources": ["Relay-X", "Team-U", "Probe-R", "Vendor-W", "Index-H", "Agent-N"],
    "bases": ["audit-path", "hash-agreement", "timing-shift", "event-chain", "sample-pattern", "graph-edge"],
    "role_actions": ["certify", "endorse", "dispatch", "open", "inspect", "preserve"],
    "pronoun_actions": ["certified", "endorsed", "dispatched", "inspected", "preserved", "accepted"],
    "events": [("mounted", "mounted", "volume"), ("activated", "active", "device"), ("closed", "closed", "channel"), ("armed", "armed", "sensor"), ("restored", "available", "endpoint"), ("engaged", "engaged", "clutch")],
    "failure_actions": [("publish", "published"), ("transmit", "transmitted"), ("reserve", "reserved"), ("attach", "attached"), ("index", "indexed"), ("commit", "committed")],
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pick(values: list[Any], index: int, offset: int = 0) -> Any:
    return values[(index + offset) % len(values)]


def options(choices: dict[str, str], expected: str, index: int, salt: str) -> list[dict[str, str]]:
    rest = [(semantic, text) for semantic, text in choices.items() if semantic != expected]
    seed = int(hashlib.sha256(f"2026083001|{salt}|{index}".encode()).hexdigest()[:16], 16)
    random.Random(seed).shuffle(rest)
    rest.insert(index % len(choices), (expected, choices[expected]))
    return [{"label": chr(65 + position), "semantic": semantic, "text": text} for position, (semantic, text) in enumerate(rest)]


def render_user(message: str, question: str, rows: list[dict[str, str]]) -> str:
    parts = [f"MESSAGE: {message}", f"QUESTION: {question}"]
    parts.extend(f"{row['label']}. {row['text']}" for row in rows)
    return "\n".join(parts)


def semantic_example(key: str, index: int, split: str, choices: dict[str, str]) -> dict[str, Any]:
    vocab = TRAIN_VOCAB if split == "train" else EVAL_VOCAB
    token = f"{split}-{index:04d}"
    if key == "list_completeness":
        kind = pick(vocab["kinds"], index)
        first, second = f"{kind}-{token}-alpha", f"{kind}-{token}-beta"
        if index % 2 == 0:
            pole, answer = "among_others", "open"
            canonical_message = f"Supported {kind}s: {first}, {second}, among-others."
            careful = f"Supported {kind}s include {first} and {second}, and this list is explicitly not claimed complete."
        else:
            pole, answer = "and_no_others", "closed"
            canonical_message = f"Supported {kind}s: {first}, {second}, and-no-others."
            careful = f"Supported {kind}s are {first} and {second} and no other {kind}s in this scope."
        bare = f"Supported {kind}s: {first} and {second}."
        question = f"What completeness commitment is made about supported {kind}s in this scope?"
    elif key == "role_cardinality":
        role = pick(vocab["roles"], index)
        obj = f"{pick(vocab['objects'], index, 2)}-{token}"
        action = pick(vocab["role_actions"], index)
        if index % 2 == 0:
            pole, answer = "one_or_more", "multiple_allowed"
            canonical_message = f"one-or-more({role}): {action} {obj}."
            careful = f"At least one distinct {role} must {action} {obj}; additional qualifying {role}s are permitted."
        else:
            pole, answer = "exactly_one", "exactly_one"
            canonical_message = f"exactly-one({role}): {action} {obj}."
            careful = f"One and only one distinct {role} must {action} {obj}; two qualifying {role}s doing so would violate the instruction."
        bare = f"A {role} must {action} {obj}."
        question = f"If two distinct qualifying {role}s both {action} {obj}, what follows?"
    elif key == "event_or_state_recurrence":
        actor = pick(vocab["actors"], index)
        event, state, obj_type = pick(vocab["events"], index)
        obj = f"{obj_type}-{token}"
        if index % 2 == 0:
            pole, answer = "repeat_event", "repeat"
            canonical_message = f"repeat-event: {actor} {event} {obj}."
            careful = f"{actor} {event} {obj}, and {actor} had performed that same event on {obj} before."
        else:
            pole, answer = "restore_state", "restore"
            canonical_message = f"restore-state({state}({obj})): {actor} {event} {obj}."
            careful = f"{actor} {event} {obj}, and {obj} had been in the state {state} during an earlier interval; no earlier matching event by {actor} is required."
        bare = f"{actor} {event} {obj} again."
        question = "Which earlier condition does the message commit to?"
    elif key == "pronoun_number":
        obj = f"{pick(vocab['objects'], index)}-{token}"
        action = pick(vocab["pronoun_actions"], index)
        if index % 2 == 0:
            pole, answer = "they_one", "singular"
            canonical_message = f"they-one {action} {obj}."
            careful = f"Exactly one person or entity, referred to without specifying gender, {action} {obj}."
        else:
            pole, answer = "they_many", "plural"
            canonical_message = f"they-many {action} {obj}."
            careful = f"Two or more people or entities {action} {obj}."
        bare = f"They {action} {obj}."
        question = "How many actors does the message commit to for this action?"
    elif key == "claim_source":
        obj = f"{pick(vocab['objects'], index)}-{token}"
        claim = f"{obj} is ready"
        selector = index % 3
        if selector == 0:
            pole, answer = "observed", "observed"
            canonical_message = f"observed: {claim}."
            careful = f"I directly observed or measured that {claim}; receipts exist or can be produced."
        elif selector == 1:
            source = pick(vocab["sources"], index)
            pole, answer = "reported", "reported"
            canonical_message = f"reported({source}): {claim}."
            careful = f"{source} reports that {claim}; I have not independently verified it."
        else:
            basis = f"{pick(vocab['bases'], index)}-{token}"
            pole, answer = "inferred", "inferred"
            canonical_message = f"inferred({basis}): {claim}."
            careful = f"I conclude from {basis} that {claim}, without directly observing it."
        bare = f"{claim.capitalize()}."
        question = "What epistemic source does the message assign to the speaker's claim?"
    elif key == "failure_contract":
        obj = f"{pick(vocab['objects'], index, 3)}-{token}"
        action, past_participle = pick(vocab["failure_actions"], index)
        if index % 2 == 0:
            pole, answer = "attempt", "attempt"
            canonical_message = f"attempt: {action} {obj}."
            careful = f"Try to {action} {obj} and report success or failure; an honest failed attempt can satisfy this instruction."
        else:
            pole, answer = "ensure", "ensure"
            canonical_message = f"ensure: {action} {obj}."
            careful = f"Make {obj} successfully {past_participle}; do not stop at a failed attempt."
        bare = f"{action.capitalize()} {obj}."
        question = "If the action still fails after an honest execution and the failure is reported, is the instruction satisfied?"
    else:
        raise KeyError(key)
    return {
        "pole": pole,
        "answer": answer,
        "canonical": canonical_message,
        "careful": careful,
        "bare": bare,
        "question": question,
        "choices": choices,
    }


def make_messages(example: dict[str, Any], condition: str, index: int, salt: str, include_answer: bool) -> tuple[list[dict[str, str]], str, list[dict[str, str]]]:
    expected_semantic = "unspecified" if condition == "bare_english" else example["answer"]
    rows = options(example["choices"], expected_semantic, index, salt)
    expected = next(row["label"] for row in rows if row["semantic"] == expected_semantic)
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": render_user(example[{"ainglish_cold": "canonical", "careful_english": "careful", "bare_english": "bare"}[condition]], example["question"], rows)},
    ]
    if include_answer:
        messages.append({"role": "assistant", "content": json.dumps({"answer": expected}, separators=(",", ":"))})
    return messages, expected, rows


def main() -> None:
    source = json.loads((ATLAS / "constructs.json").read_text(encoding="utf-8"))
    source_by_key = {row["key"]: row for row in source["constructs"]}
    if set(source_by_key) != set(GROUPS["a"] + GROUPS["b"]):
        raise RuntimeError("atlas source population drift")
    source_pins = {
        "schema": "ainglish.crossover-exposure-source-pins.v1",
        "source_path": str(ATLAS.relative_to(REPO)),
        "source_constructs_sha256": digest(ATLAS / "constructs.json"),
        "source_proposal_snapshot_sha256": digest(ATLAS / "proposal-snapshot.json"),
        "groups": GROUPS,
        "training_vocabulary": TRAIN_VOCAB,
        "evaluation_vocabulary": EVAL_VOCAB,
        "constructs": [{key: row[key] for key in ("rank", "key", "slug", "public_id", "title", "stage_at_capture", "form", "english_mapping", "choices")} for row in source["constructs"]],
    }
    source_pins["content_sha256"] = hashlib.sha256(canonical(source_pins)).hexdigest()
    (ROOT / "source-pins.json").write_bytes(pretty(source_pins))

    train_hashes = {}
    for group, keys in GROUPS.items():
        rows = []
        for key in keys:
            choices = source_by_key[key]["choices"]
            for index in range(TRAIN_ROWS_PER_CONSTRUCT):
                example = semantic_example(key, index, "train", choices)
                messages, expected, option_rows = make_messages(example, "ainglish_cold", index, f"train-{group}-{key}", True)
                rows.append({
                    "id": f"train-{group}-{key}-{index:04d}", "group": group, "key": key, "slug": source_by_key[key]["slug"],
                    "pole": example["pole"], "expected": expected, "options": option_rows, "messages": messages,
                })
        random.Random(2026083002).shuffle(rows)
        path = ROOT / f"train-{group}.jsonl"
        path.write_bytes(b"".join(canonical(row) for row in rows))
        train_hashes[path.name] = {"rows": len(rows), "sha256": digest(path)}

    eval_rows = []
    for key in GROUPS["a"] + GROUPS["b"]:
        choices = source_by_key[key]["choices"]
        for index in range(EVAL_FRAMES_PER_CONSTRUCT):
            example = semantic_example(key, index, "eval", choices)
            for condition_index, condition in enumerate(("ainglish_cold", "careful_english", "bare_english")):
                label_index = index + condition_index
                messages, expected, option_rows = make_messages(example, condition, label_index, f"eval-{key}-{condition}", False)
                eval_rows.append({
                    "id": f"eval-{key}-{index:04d}-{condition}", "frame_id": f"eval-{key}-{index:04d}",
                    "key": key, "slug": source_by_key[key]["slug"], "exposure_group": "a" if key in GROUPS["a"] else "b",
                    "pole": example["pole"], "condition": condition, "expected": expected,
                    "expected_semantic": "unspecified" if condition == "bare_english" else example["answer"],
                    "options": option_rows, "messages": messages,
                })
    random.Random(2026083004).shuffle(eval_rows)
    (ROOT / "eval.jsonl").write_bytes(b"".join(canonical(row) for row in eval_rows))

    plan = {
        "schema": "ainglish.controlled-crossover-exposure-plan.v1",
        "base_model": BASE_MODEL,
        "base_revision": BASE_REVISION,
        "groups": GROUPS,
        "training": {
            "rows_per_construct": TRAIN_ROWS_PER_CONSTRUCT, "rows_per_adapter": TRAIN_ROWS_PER_CONSTRUCT * 3,
            "epochs": 2.0, "seed": 2026083003, "max_length": 256,
            "per_device_batch_size": 4, "gradient_accumulation_steps": 4, "learning_rate": 0.0002,
            "quantization": {"bits": 4, "type": "nf4", "double_quant": True, "compute_dtype": "bfloat16"},
            "lora": {"r": 16, "alpha": 32, "dropout": 0.05, "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]},
            "save_checkpoints": False, "artifact_size_ceiling_bytes": 1073741824,
        },
        "evaluation": {
            "frames_per_construct": EVAL_FRAMES_PER_CONSTRUCT, "arms": ["ainglish_cold", "careful_english", "bare_english"],
            "prompts_per_condition": len(eval_rows), "model_conditions": ["base", "adapter-a", "adapter-b"],
            "planned_predictions": len(eval_rows) * 3, "batch_size": 16, "seed": 2026083005,
            "decoding": {"do_sample": False, "max_new_tokens": 16}, "retry_policy": "none",
        },
        "adapter_paths": {
            "a": "/home/dexagon/codex/dexagon/artifacts/ainglish-crossover-a-20260830",
            "b": "/home/dexagon/codex/dexagon/artifacts/ainglish-crossover-b-20260830",
        },
        "outputs": {**train_hashes, "eval.jsonl": {"rows": len(eval_rows), "sha256": digest(ROOT / "eval.jsonl")}, "source-pins.json": {"sha256": digest(ROOT / "source-pins.json")}},
        "downloads": 0, "governance_evidence": False, "development_only": True,
    }
    (ROOT / "RUN_PLAN.json").write_bytes(pretty(plan))

    checksum_files = [
        "RUN_PROTOCOL.md", "build.py", "audit.py", "integrity.py", "train.py", "freeze_artifacts.py", "evaluate.py", "analyse.py",
        "source-pins.json", "train-a.jsonl", "train-b.jsonl", "eval.jsonl", "RUN_PLAN.json",
    ]
    missing = [name for name in checksum_files if not (ROOT / name).is_file()]
    if missing:
        raise RuntimeError(f"cannot seal missing files: {missing}")
    (ROOT / "SHA256SUMS.preregistered").write_text("".join(f"{digest(ROOT / name)}  {name}\n" for name in checksum_files), encoding="utf-8")
    print(json.dumps({
        "train": train_hashes, "evaluation_rows": len(eval_rows), "planned_predictions": len(eval_rows) * 3,
        "evaluation_expected_labels": dict(Counter(row["expected"] for row in eval_rows)),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
