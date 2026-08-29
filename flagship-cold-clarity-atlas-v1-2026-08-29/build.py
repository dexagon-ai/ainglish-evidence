#!/usr/bin/env python3
"""Build the frozen five-condition flagship clarity packet without model calls."""

from __future__ import annotations

import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent

CONDITIONS = [
    ("ainglish_cold", "canonical", False),
    ("ainglish_defined", "canonical", True),
    ("careful_english", "careful", False),
    ("bare_english", "bare", False),
    ("corrupted_ainglish", "corrupted", False),
]


def frame(identifier: str, pole: str, canonical: str, careful: str, bare: str, corrupted: str, question: str, answer: str) -> dict[str, str]:
    return {
        "id": identifier,
        "pole": pole,
        "canonical": canonical,
        "careful": careful,
        "bare": bare,
        "corrupted": corrupted,
        "question": question,
        "answer": answer,
    }


CONSTRUCTS: list[dict[str, Any]] = [
    {
        "rank": 1,
        "key": "list_completeness",
        "slug": "among-others-and-no-others-is-the-list-the-whole-list-2",
        "choices": {
            "open": "The sender explicitly does not claim that the named members are the complete same-kind set in scope.",
            "closed": "The sender claims that the named members are the complete same-kind set in scope.",
            "unspecified": "The message does not say whether the named members are the complete set.",
        },
        "frames": [
            frame("formats-open", "among_others", "The export accepts CSV, Parquet, among-others.", "The export accepts CSV and Parquet, and this list is not claimed complete.", "The export accepts CSV and Parquet.", "The export accepts CSV, Parquet, among others.", "What completeness commitment does the sender make about accepted export formats?", "open"),
            frame("allowlist-closed", "and_no_others", "The deployment allowlist admits agent-a, agent-b, and-no-others.", "The deployment allowlist admits agent-a and agent-b and no other agents in this deployment.", "The deployment allowlist admits agent-a and agent-b.", "The deployment allowlist admits agent-a, agent-b, and no others.", "What completeness commitment does the sender make about admitted agents in this deployment?", "closed"),
            frame("retries-open", "among_others", "Retry on HTTP 429, HTTP 503, among-others.", "Retry on HTTP 429 and HTTP 503, and this list of retry statuses is not claimed complete.", "Retry on HTTP 429 and HTTP 503.", "Retry on HTTP 429, HTTP 503, among others.", "What completeness commitment does the sender make about retry-triggering HTTP statuses?", "open"),
            frame("regions-closed", "and_no_others", "Store replicas in London, Dublin, and-no-others.", "Store replicas in London and Dublin and in no other regions within this storage scope.", "Store replicas in London and Dublin.", "Store replicas in London, Dublin, and no others.", "What completeness commitment does the sender make about storage regions?", "closed"),
            frame("channels-open", "among_others", "Notify by email, webhook, among-others.", "Notify by email and webhook, and this list of notification channels is not claimed complete.", "Notify by email and webhook.", "Notify by email, webhook, among others.", "What completeness commitment does the sender make about notification channels?", "open"),
            frame("images-closed", "and_no_others", "The endpoint accepts PNG, WebP, and-no-others.", "The endpoint accepts PNG and WebP and no other image formats in this endpoint scope.", "The endpoint accepts PNG and WebP.", "The endpoint accepts PNG, WebP, and no others.", "What completeness commitment does the sender make about accepted image formats?", "closed"),
            frame("roles-open", "among_others", "Deployment participants include reviewer, operator, among-others.", "Deployment participants include reviewer and operator, and this list of participant roles is not claimed complete.", "Deployment participants include reviewer and operator.", "Deployment participants include reviewer, operator, among others.", "What completeness commitment does the sender make about deployment participant roles?", "open"),
            frame("commands-closed", "and_no_others", "The recovery interface permits inspect, restore, and-no-others.", "The recovery interface permits inspect and restore and no other commands in this interface.", "The recovery interface permits inspect and restore.", "The recovery interface permits inspect, restore, and no others.", "What completeness commitment does the sender make about recovery commands?", "closed"),
        ],
    },
    {
        "rank": 2,
        "key": "role_cardinality",
        "slug": "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
        "choices": {
            "multiple_allowed": "Two distinct qualifying principals may perform the action without violating the instruction.",
            "exactly_one": "Exactly one distinct qualifying principal must perform the action; two would violate the instruction.",
            "unspecified": "The message does not determine whether one or several qualifying principals are required.",
        },
        "frames": [
            frame("reviewers-many", "one_or_more", "one-or-more(reviewer): approve release R.", "At least one distinct reviewer must approve release R; additional qualifying reviewers are permitted.", "A reviewer must approve release R.", "one or more(reviewer): approve release R.", "If two distinct qualifying reviewers both approve release R, what follows?", "multiple_allowed"),
            frame("auditor-one", "exactly_one", "exactly-one(auditor): sign report Q.", "One and only one distinct auditor must sign report Q; two auditors signing would violate the instruction.", "An auditor must sign report Q.", "exactly one(auditor): sign report Q.", "If two distinct qualifying auditors both sign report Q, what follows?", "exactly_one"),
            frame("operators-many", "one_or_more", "one-or-more(operator): restart service S.", "At least one distinct operator must restart service S; additional qualifying operators are permitted.", "An operator must restart service S.", "one or more(operator): restart service S.", "If two distinct qualifying operators both restart service S, what follows?", "multiple_allowed"),
            frame("custodian-one", "exactly_one", "exactly-one(custodian): acknowledge transfer T.", "One and only one distinct custodian must acknowledge transfer T; two custodians acknowledging would violate the instruction.", "A custodian must acknowledge transfer T.", "exactly one(custodian): acknowledge transfer T.", "If two distinct qualifying custodians both acknowledge transfer T, what follows?", "exactly_one"),
            frame("maintainers-many", "one_or_more", "one-or-more(maintainer): authorize patch P.", "At least one distinct maintainer must authorize patch P; additional qualifying maintainers are permitted.", "A maintainer must authorize patch P.", "one or more(maintainer): authorize patch P.", "If two distinct qualifying maintainers both authorize patch P, what follows?", "multiple_allowed"),
            frame("witness-one", "exactly_one", "exactly-one(witness): attest event E.", "One and only one distinct witness must attest event E; two witnesses attesting would violate the instruction.", "A witness must attest event E.", "exactly one(witness): attest event E.", "If two distinct qualifying witnesses both attest event E, what follows?", "exactly_one"),
            frame("approvers-many", "one_or_more", "one-or-more(approver): unlock account A.", "At least one distinct approver must unlock account A; additional qualifying approvers are permitted.", "An approver must unlock account A.", "one or more(approver): unlock account A.", "If two distinct qualifying approvers both unlock account A, what follows?", "multiple_allowed"),
            frame("dispatcher-one", "exactly_one", "exactly-one(dispatcher): release job J.", "One and only one distinct dispatcher must release job J; two dispatchers releasing it would violate the instruction.", "A dispatcher must release job J.", "exactly one(dispatcher): release job J.", "If two distinct qualifying dispatchers both release job J, what follows?", "exactly_one"),
        ],
    },
    {
        "rank": 3,
        "key": "event_or_state_recurrence",
        "slug": "repeat-event-restore-state",
        "choices": {
            "repeat": "A matching earlier event by the same resolved actor and participants is backgrounded.",
            "restore": "Only the named result state is backgrounded; an earlier matching event or actor is not required.",
            "unspecified": "The message does not choose between an earlier matching event and an earlier result state.",
        },
        "frames": [
            frame("gate-repeat", "repeat_event", "repeat-event: Mara opened gate G.", "Mara opened gate G, and Mara had opened that same gate before.", "Mara opened gate G again.", "repeat event: Mara opened gate G.", "Which earlier condition does the message commit to?", "repeat"),
            frame("gate-restore", "restore_state", "restore-state(open(gate-G)): Noel opened gate G.", "Noel opened gate G, and gate G had been open during an earlier interval; this does not require an earlier opening by Noel.", "Noel opened gate G again.", "restore state(open(gate-G)): Noel opened gate G.", "Which earlier condition does the message commit to?", "restore"),
            frame("service-repeat", "repeat_event", "repeat-event: Ivo started service S.", "Ivo started service S, and Ivo had started that same service before.", "Ivo started service S again.", "repeat event: Ivo started service S.", "Which earlier condition does the message commit to?", "repeat"),
            frame("service-restore", "restore_state", "restore-state(running(service-S)): Priya started service S.", "Priya started service S, and service S had been running during an earlier interval; this does not require an earlier start by Priya.", "Priya started service S again.", "restore state(running(service-S)): Priya started service S.", "Which earlier condition does the message commit to?", "restore"),
            frame("seal-repeat", "repeat_event", "repeat-event: Chen sealed container C.", "Chen sealed container C, and Chen had sealed that same container before.", "Chen sealed container C again.", "repeat event: Chen sealed container C.", "Which earlier condition does the message commit to?", "repeat"),
            frame("seal-restore", "restore_state", "restore-state(sealed(container-C)): Asha sealed container C.", "Asha sealed container C, and container C had been sealed during an earlier interval; this does not require an earlier sealing by Asha.", "Asha sealed container C again.", "restore state(sealed(container-C)): Asha sealed container C.", "Which earlier condition does the message commit to?", "restore"),
            frame("account-repeat", "repeat_event", "repeat-event: Omar enabled account A.", "Omar enabled account A, and Omar had enabled that same account before.", "Omar enabled account A again.", "repeat event: Omar enabled account A.", "Which earlier condition does the message commit to?", "repeat"),
            frame("account-restore", "restore_state", "restore-state(enabled(account-A)): Bea enabled account A.", "Bea enabled account A, and account A had been enabled during an earlier interval; this does not require an earlier enabling by Bea.", "Bea enabled account A again.", "restore state(enabled(account-A)): Bea enabled account A.", "Which earlier condition does the message commit to?", "restore"),
        ],
    },
    {
        "rank": 4,
        "key": "pronoun_number",
        "slug": "they-one-they-many-say-whether-they-is-one-actor-or-several",
        "choices": {
            "singular": "The pronoun denotes exactly one actor or entity.",
            "plural": "The pronoun denotes two or more actors or entities.",
            "unspecified": "The message does not state whether the pronoun denotes one actor or several.",
        },
        "frames": [
            frame("approval-one", "they_one", "they-one approved release R.", "Exactly one person or entity, referred to without specifying gender, approved release R.", "They approved release R.", "they one approved release R.", "How many approving actors does the pronoun itself denote?", "singular"),
            frame("approval-many", "they_many", "they-many approved release S.", "Two or more people or entities approved release S.", "They approved release S.", "they many approved release S.", "How many approving actors does the pronoun itself denote?", "plural"),
            frame("receipt-one", "they_one", "they-one signed receipt A.", "Exactly one person or entity, referred to without specifying gender, signed receipt A.", "They signed receipt A.", "they one signed receipt A.", "How many signing actors does the pronoun itself denote?", "singular"),
            frame("receipt-many", "they_many", "they-many signed receipt B.", "Two or more people or entities signed receipt B.", "They signed receipt B.", "they many signed receipt B.", "How many signing actors does the pronoun itself denote?", "plural"),
            frame("alert-one", "they_one", "they-one acknowledged alert X.", "Exactly one person or entity, referred to without specifying gender, acknowledged alert X.", "They acknowledged alert X.", "they one acknowledged alert X.", "How many acknowledging actors does the pronoun itself denote?", "singular"),
            frame("alert-many", "they_many", "they-many acknowledged alert Y.", "Two or more people or entities acknowledged alert Y.", "They acknowledged alert Y.", "they many acknowledged alert Y.", "How many acknowledging actors does the pronoun itself denote?", "plural"),
            frame("transfer-one", "they_one", "they-one authorized transfer T1.", "Exactly one person or entity, referred to without specifying gender, authorized transfer T1.", "They authorized transfer T1.", "they one authorized transfer T1.", "How many authorizing actors does the pronoun itself denote?", "singular"),
            frame("transfer-many", "they_many", "they-many authorized transfer T2.", "Two or more people or entities authorized transfer T2.", "They authorized transfer T2.", "they many authorized transfer T2.", "How many authorizing actors does the pronoun itself denote?", "plural"),
        ],
    },
    {
        "rank": 5,
        "key": "claim_source",
        "slug": "observed-reported-by-inferred-from-mark-where-a-claim-came-f",
        "choices": {
            "observed": "The speaker claims direct observation or measurement and says receipts exist or can be produced.",
            "reported": "The claim is attributed to a named source and the speaker has not independently verified it.",
            "inferred": "The speaker says the claim was concluded from a stated basis without direct observation.",
            "unspecified": "The message does not state the speaker's epistemic source for the claim.",
        },
        "frames": [
            frame("build-observed", "observed", "observed: Build 812 passed.", "I directly ran or observed build 812 pass; receipts exist or can be produced.", "Build 812 passed.", "observed Build 812 passed.", "What epistemic source does the message assign to the speaker's claim?", "observed"),
            frame("build-reported", "reported", "reported(Mira): Build 813 passed.", "Mira reports that build 813 passed; I have not independently verified it.", "Build 813 passed.", "reported Mira Build 813 passed.", "What epistemic source does the message assign to the speaker's claim?", "reported"),
            frame("build-inferred", "inferred", "inferred(log-pattern-L7): Build 814 passed.", "I conclude from log pattern L7 that build 814 passed, without directly observing it.", "Build 814 passed.", "inferred from log-pattern-L7 Build 814 passed.", "What epistemic source does the message assign to the speaker's claim?", "inferred"),
            frame("sensor-observed", "observed", "observed: Sensor K reads 18 degrees.", "I directly observed or measured sensor K reading 18 degrees; receipts exist or can be produced.", "Sensor K reads 18 degrees.", "observed Sensor K reads 18 degrees.", "What epistemic source does the message assign to the speaker's claim?", "observed"),
            frame("supplier-reported", "reported", "reported(Supplier-Z): Part P shipped.", "Supplier Z reports that part P shipped; I have not independently verified it.", "Part P shipped.", "reported Supplier-Z Part P shipped.", "What epistemic source does the message assign to the speaker's claim?", "reported"),
            frame("checksum-inferred", "inferred", "inferred(checksum-match): Archive A is unchanged.", "I conclude from the checksum match that archive A is unchanged, without directly observing that fact.", "Archive A is unchanged.", "inferred from checksum-match Archive A is unchanged.", "What epistemic source does the message assign to the speaker's claim?", "inferred"),
            frame("invoice-observed", "observed", "observed: Invoice I contains three lines.", "I directly observed invoice I containing three lines; receipts exist or can be produced.", "Invoice I contains three lines.", "observed Invoice I contains three lines.", "What epistemic source does the message assign to the speaker's claim?", "observed"),
            frame("monitor-reported", "reported", "reported(Status-Monitor): Service S is healthy.", "Status Monitor reports that service S is healthy; I have not independently verified it.", "Service S is healthy.", "reported Status-Monitor Service S is healthy.", "What epistemic source does the message assign to the speaker's claim?", "reported"),
        ],
    },
    {
        "rank": 6,
        "key": "failure_contract",
        "slug": "attempt-ensure-say-whether-the-instruction-tolerates-failure",
        "choices": {
            "attempt": "An honest failed attempt followed by a failure report can satisfy the instruction.",
            "ensure": "The required end state must hold; stopping after a failed attempt does not satisfy the instruction.",
            "unspecified": "The message does not state whether an honest failed attempt can satisfy the instruction.",
        },
        "frames": [
            frame("upload-attempt", "attempt", "attempt: Upload archive A.", "Try to upload archive A and report success or failure; an honest failed attempt can satisfy this instruction.", "Upload archive A.", "attempt Upload archive A.", "If the upload still fails after an honest execution and the failure is reported, is this instruction satisfied?", "attempt"),
            frame("upload-ensure", "ensure", "ensure: Upload archive B.", "Make archive B successfully uploaded; do not stop at a failed attempt.", "Upload archive B.", "ensure Upload archive B.", "If the upload still fails after an honest execution and the failure is reported, is this instruction satisfied?", "ensure"),
            frame("notify-attempt", "attempt", "attempt: Notify recipient R.", "Try to notify recipient R and report success or failure; an honest failed attempt can satisfy this instruction.", "Notify recipient R.", "attempt Notify recipient R.", "If notification still fails after an honest execution and the failure is reported, is this instruction satisfied?", "attempt"),
            frame("notify-ensure", "ensure", "ensure: Notify recipient S.", "Make recipient S successfully notified; do not stop at a failed attempt.", "Notify recipient S.", "ensure Notify recipient S.", "If notification still fails after an honest execution and the failure is reported, is this instruction satisfied?", "ensure"),
            frame("backup-attempt", "attempt", "attempt: Create backup K.", "Try to create backup K and report success or failure; an honest failed attempt can satisfy this instruction.", "Create backup K.", "attempt Create backup K.", "If backup creation still fails after an honest execution and the failure is reported, is this instruction satisfied?", "attempt"),
            frame("backup-ensure", "ensure", "ensure: Create backup L.", "Make backup L successfully created; do not stop at a failed attempt.", "Create backup L.", "ensure Create backup L.", "If backup creation still fails after an honest execution and the failure is reported, is this instruction satisfied?", "ensure"),
            frame("lock-attempt", "attempt", "attempt: Acquire lock M.", "Try to acquire lock M and report success or failure; an honest failed attempt can satisfy this instruction.", "Acquire lock M.", "attempt Acquire lock M.", "If lock acquisition still fails after an honest execution and the failure is reported, is this instruction satisfied?", "attempt"),
            frame("lock-ensure", "ensure", "ensure: Acquire lock N.", "Make lock N successfully acquired; do not stop at a failed attempt.", "Acquire lock N.", "ensure Acquire lock N.", "If lock acquisition still fails after an honest execution and the failure is reported, is this instruction satisfied?", "ensure"),
        ],
    },
]


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shuffled_options(slug: str, frame_id: str, condition: str, frame_index: int, expected_semantic: str, choices: dict[str, str]) -> list[dict[str, str]]:
    expected_row = (expected_semantic, choices[expected_semantic])
    rows = [(semantic, text) for semantic, text in choices.items() if semantic != expected_semantic]
    seed = int(hashlib.sha256(f"2026082904|{slug}|{frame_id}|{condition}".encode()).hexdigest()[:16], 16)
    random.Random(seed).shuffle(rows)
    desired_index = frame_index % len(choices)
    rows.insert(desired_index, expected_row)
    return [{"label": chr(65 + index), "semantic": semantic, "text": text} for index, (semantic, text) in enumerate(rows)]


def render_prompt(construct: dict[str, Any], proposal: dict[str, Any], condition: str, rows: list[dict[str, Any]], definition: bool) -> str:
    parts = [
        "Judge only the operational consequence licensed by each message.",
        "Do not use unstated intentions or world knowledge. If the load-bearing distinction is not stated, choose the option saying it is unspecified.",
        "Return exactly one JSON object of the form {\"answers\":[{\"id\":\"...\",\"label\":\"A\"}]}. Include every requested ID once, no extra keys, and no prose.",
    ]
    if definition:
        parts.extend([
            "",
            "AUTHORITATIVE REFERENCE CARD FOR THIS BATCH:",
            f"FORM: {proposal['form']}",
            f"MEANING: {proposal['english_mapping']}",
        ])
    parts.extend(["", f"BATCH: {construct['key']} / {condition}"])
    for row in rows:
        parts.extend(["", f"ID: {row['id']}", f"MESSAGE: {row['message']}", f"QUESTION: {row['question']}"])
        parts.extend(f"{option['label']}. {option['text']}" for option in row["options"])
    return "\n".join(parts).strip() + "\n"


def main() -> None:
    proposal_packet = json.loads((ROOT / "proposal-snapshot.json").read_text(encoding="utf-8"))
    roster = json.loads((ROOT / "reader-roster.json").read_text(encoding="utf-8"))
    proposal_by_slug = {row["slug"]: row for row in proposal_packet["proposals"]}
    if set(proposal_by_slug) != {row["slug"] for row in CONSTRUCTS}:
        raise RuntimeError("captured proposal population does not match construct specification")

    frozen_constructs = []
    items: list[dict[str, Any]] = []
    prompts: list[dict[str, Any]] = []
    for construct in CONSTRUCTS:
        proposal = proposal_by_slug[construct["slug"]]
        if not proposal.get("form") or not proposal.get("english_mapping"):
            raise RuntimeError(f"proposal lacks reference text: {construct['slug']}")
        frozen_constructs.append({
            "rank": construct["rank"],
            "key": construct["key"],
            "slug": construct["slug"],
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "stage_at_capture": proposal.get("stage"),
            "form": proposal["form"],
            "english_mapping": proposal["english_mapping"],
            "choices": construct["choices"],
            "frames": construct["frames"],
        })
        for condition, message_field, definition in CONDITIONS:
            batch = []
            for frame_index, source in enumerate(construct["frames"]):
                expected_semantic = "unspecified" if condition == "bare_english" else source["answer"]
                options = shuffled_options(construct["slug"], source["id"], condition, frame_index, expected_semantic, construct["choices"])
                expected = next(row["label"] for row in options if row["semantic"] == expected_semantic)
                item = {
                    "id": f"{construct['key']}-{source['id']}-{condition}",
                    "rank": construct["rank"],
                    "key": construct["key"],
                    "slug": construct["slug"],
                    "condition": condition,
                    "definition_in_prompt": definition,
                    "frame_id": source["id"],
                    "pole": source["pole"],
                    "message": source[message_field],
                    "question": source["question"],
                    "options": options,
                    "expected_semantic": expected_semantic,
                    "expected": expected,
                    "development_only": True,
                }
                batch.append(item)
                items.append(item)
            prompt = render_prompt(construct, proposal, condition, batch, definition)
            prompts.append({
                "rank": construct["rank"],
                "key": construct["key"],
                "slug": construct["slug"],
                "condition": condition,
                "definition_in_prompt": definition,
                "item_ids": [row["id"] for row in batch],
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            })

    construct_packet = {
        "schema": "ainglish.flagship-cold-clarity-constructs.v1",
        "proposal_snapshot_sha256": digest(ROOT / "proposal-snapshot.json"),
        "constructs": frozen_constructs,
    }
    construct_packet["content_sha256"] = hashlib.sha256(canonical(construct_packet)).hexdigest()
    (ROOT / "constructs.json").write_bytes(pretty(construct_packet))

    item_packet = {
        "schema": "ainglish.flagship-cold-clarity-items.v1",
        "development_only": True,
        "future_governance_reuse_forbidden": True,
        "conditions": [row[0] for row in CONDITIONS],
        "items": items,
    }
    item_packet["content_sha256"] = hashlib.sha256(canonical(item_packet)).hexdigest()
    (ROOT / "items.json").write_bytes(pretty(item_packet))
    (ROOT / "prompts.jsonl").write_bytes(b"".join(canonical(row) for row in prompts))

    response_format = {
        "type": "object",
        "additionalProperties": False,
        "required": ["answers"],
        "properties": {
            "answers": {
                "type": "array",
                "minItems": 8,
                "maxItems": 8,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "label"],
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string", "enum": ["A", "B", "C", "D"]},
                    },
                },
            }
        },
    }
    plan = {
        "schema": "ainglish.flagship-cold-clarity-run-plan.v1",
        "governance_evidence": False,
        "development_only": True,
        "downloads": 0,
        "constructs": len(CONSTRUCTS),
        "conditions": len(CONDITIONS),
        "frames_per_construct_condition": 8,
        "readers": len(roster["readers"]),
        "calls_per_reader": len(prompts),
        "planned_calls": len(prompts) * len(roster["readers"]),
        "planned_cells": len(items) * len(roster["readers"]),
        "retry_policy": "no inference retries; an interrupted or malformed batch remains eight invalid cells",
        "answer_channel": "message.content only; thinking and complete receipt retained but never parsed",
        "request": {
            "stream": False,
            "think": False,
            "keep_alive": "20m",
            "format": response_format,
            "options": {"temperature": 0, "seed": 2026082905, "num_ctx": 8192, "num_predict": 512},
        },
        "classification_thresholds": {
            "amendment_first": {"defined_below": 0.75, "careful_below": 0.80, "cold_below": 0.60},
            "strong": {"cold_at_least": 0.80, "careful_at_least": 0.85, "defined_at_least": 0.85, "corrupted_at_least": 0.75, "cold_minus_careful_at_least": -0.10},
            "fragile": {"corrupted_minus_cold_at_most": -0.15, "or_readers_below_half_cold_at_least": 2},
            "learnable": {"defined_at_least": 0.80, "defined_minus_cold_at_least": 0.10},
        },
        "proposal_snapshot_sha256": digest(ROOT / "proposal-snapshot.json"),
        "roster_sha256": digest(ROOT / "reader-roster.json"),
        "constructs_sha256": digest(ROOT / "constructs.json"),
        "items_sha256": digest(ROOT / "items.json"),
        "prompts_sha256": digest(ROOT / "prompts.jsonl"),
    }
    (ROOT / "RUN_PLAN.json").write_bytes(pretty(plan))

    checksum_files = [
        "RUN_PROTOCOL.md", "capture.py", "build.py", "audit.py", "run_ollama.py", "analyse.py",
        "proposal-snapshot.json", "reader-roster.json", "constructs.json", "items.json", "prompts.jsonl", "RUN_PLAN.json",
    ]
    missing = [name for name in checksum_files if not (ROOT / name).is_file()]
    if missing:
        raise RuntimeError(f"cannot seal missing files: {missing}")
    lines = [f"{digest(ROOT / name)}  {name}" for name in checksum_files]
    (ROOT / "SHA256SUMS.preregistered").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "constructs": len(CONSTRUCTS),
        "items": len(items),
        "prompts": len(prompts),
        "planned_calls": plan["planned_calls"],
        "planned_cells": plan["planned_cells"],
        "expected_labels": Counter(row["expected"] for row in items),
    }, default=dict, sort_keys=True))


if __name__ == "__main__":
    main()
