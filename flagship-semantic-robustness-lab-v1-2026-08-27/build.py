#!/usr/bin/env python3
"""Freeze a definition-grounded robustness battery for all 17 flagships."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082771
MODELS = [
    {"name": "qwen3.5:9b-q4_k_m", "digest_prefix": "6488c96fa5fa", "family": "Qwen 3.5 9B"},
    {"name": "gemma3:12b", "digest_prefix": "f4031aab637d", "family": "Gemma 3 12B"},
    {"name": "mistral-small3.2:24b-instruct-2506-q4_K_M", "digest_prefix": "5a408ab55df5", "family": "Mistral Small 3.2 24B"},
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def row(slug: str, form: str, left: str, right: str, left_definition: str,
        right_definition: str, left_example: str, right_example: str) -> dict:
    return locals()


CONSTRUCTS = [
    row("we-including-you-we-excluding-you-clusivity-mark-whether-we--4", "we-including-you / we-excluding-you", "including", "excluding", "the speaker's we-group includes the addressee", "the speaker's we-group excludes the addressee", "we-including-you will review the draft.", "we-excluding-you will review the draft."),
    row("you-one-you-all-say-whether-you-addresses-one-recipient-or-t", "you-one / you-all", "one", "all", "one addressee is addressed", "every member of the addressed group is addressed", "you-one should approve the change.", "you-all should approve the change."),
    row("fact-not-known-choice-not-made-distinguish-missing-evidence-", "fact-not-known / choice-not-made", "unknown", "unmade", "the relevant fact is not known", "the relevant choice has not yet been made", "fact-not-known — region.", "choice-not-made — region."),
    row("no-delegation-one-hop-delegation-allowed-state-whether-a-tas", "no-delegation / one-hop-delegation-allowed", "none", "one-hop", "the assignee must not hand the task off", "the assignee may hand the task to a direct delegate, who may not delegate again", "Complete the audit, no-delegation.", "Complete the audit, one-hop-delegation-allowed."),
    row("each-alone-as-one-distributive-vs-collective-does-the-plural", "each-alone / as-one", "separate", "collective", "every group member acts separately", "the group acts collectively as one body", "The agents each-alone signed.", "The agents as-one signed."),
    row("by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3", "by-unknown / by-withheld", "unknown", "withheld", "the writer does not know the actor", "the writer knows the actor but does not disclose it", "The file was deleted by-unknown.", "The file was deleted by-withheld."),
    row("start-by-complete-by-say-which-task-event-a-deadline-constra", "start-by / complete-by", "start", "complete", "the action must begin no later than the stated time", "the action must finish no later than the stated time", "Migrate start-by(Friday).", "Migrate complete-by(Friday)."),
    row("or-both-not-both-english-or-never-says-whether-both-is-allow", "or-both / not-both", "both-allowed", "both-forbidden", "either alternative or both alternatives may be selected", "the two alternatives must not both be selected", "Choose red or-both blue.", "Choose red not-both blue."),
    row("true-as-worded-false-as-worded-unambiguous-answers-to-negati", "true-as-worded / false-as-worded", "true", "false", "the exact proposition as worded, including its negation, is true", "the exact proposition as worded, including its negation, is false", "Did the job not fail? true-as-worded.", "Did the job not fail? false-as-worded."),
    row("moved-earlier-moved-later-which-way-did-the-meeting-move-2", "moved-earlier / moved-later", "earlier", "later", "the replacement schedule is earlier than the prior schedule", "the replacement schedule is later than the prior schedule", "The meeting moved-earlier to Tuesday.", "The meeting moved-later to Tuesday."),
    row("among-others-and-no-others-is-the-list-the-whole-list-2", "among-others / and-no-others", "open-list", "closed-list", "the listed members are examples and the list is not claimed complete", "the listed members are the complete list in scope", "Affected: API, worker, among-others.", "Affected: API, worker, and-no-others."),
    row("some-or-all-some-but-not-all-does-some-leave-room-for-all-2", "some-or-all / some-but-not-all", "all-possible", "all-excluded", "at least one member qualifies and every member may qualify", "at least one but fewer than every member qualifies", "some-or-all workers may retry.", "some-but-not-all workers may retry."),
    row("may-as-permission-may-as-possibility-does-may-authorize-an-a", "may-as-permission / may-as-possibility", "permission", "possibility", "an applicable authority permits the action", "under the writer's evidence the action could occur", "The worker may-as-permission retry.", "The worker may-as-possibility retry."),
    row("whole-s-part-s-declare-whether-a-reported-set-is-the-complet", "whole(S) / part(S)", "whole", "part", "the reported members are the complete set in scope", "the reported members are only a subset of the set in scope", "whole(failed-jobs): 7, 9.", "part(failed-jobs): 7, 9."),
    row("proposal-by-p-decision-by-a-say-whether-an-option-is-offered", "proposal-by(P) / decision-by(A)", "proposal", "decision", "the named party offered an option without making it binding", "the named authority made the option a binding decision", "proposal-by(chair): deploy Friday.", "decision-by(chair): deploy Friday."),
    row("one-or-more-role-exactly-one-role-does-a-reviewer-require-at", "one-or-more(role) / exactly-one(role)", "one-or-more", "exactly-one", "at least one holder of the role must act and more than one may act", "exactly one holder of the role must act", "one-or-more(reviewer): approve the release.", "exactly-one(reviewer): approve the release."),
    row("repeat-event-restore-state-did-again-repeat-the-action-or-on-2", "repeat-event / restore-state", "repeat", "restore", "the same event is performed another time", "a change is made to re-establish a named result state, whether or not the same event is repeated", "repeat-event: Mara opened the gate.", "restore-state(open(gate)): Mara opened the gate."),
]


def dehyphenated(text: str) -> str:
    return text.replace("-", " ")


def main() -> None:
    if len(CONSTRUCTS) != 17 or len({row["slug"] for row in CONSTRUCTS}) != 17:
        raise SystemExit("REFUSING: expected 17 distinct constructs")
    items = []
    for rank, construct in enumerate(CONSTRUCTS, 1):
        cases = [
            ("canonical", "left", construct["left_example"]),
            ("canonical", "right", construct["right_example"]),
            ("hyphen_loss", "left", dehyphenated(construct["left_example"])),
            ("hyphen_loss", "right", dehyphenated(construct["right_example"])),
            ("careful_english", "left", f"This says that {construct['left_definition']}."),
            ("careful_english", "right", f"This says that {construct['right_definition']}."),
            ("opposite_distractor", "left", f"For contrast, {construct['right_definition']}. Actual message: {construct['left_example']}"),
            ("opposite_distractor", "right", f"For contrast, {construct['left_definition']}. Actual message: {construct['right_example']}"),
        ]
        for variant, expected, text in cases:
            items.append({
                "id": f"flagship-{rank:02d}-{variant}-{expected}",
                "rank": rank,
                "slug": construct["slug"],
                "form": construct["form"],
                "left_label": construct["left"],
                "right_label": construct["right"],
                "left_definition": construct["left_definition"],
                "right_definition": construct["right_definition"],
                "variant": variant,
                "text": text,
                "expected": expected,
            })
    packet = {
        "kind": "dexagon.ainglish.flagship-semantic-robustness-items.v1",
        "seed": SEED,
        "population": "17 pinned flagships x 2 poles x 4 controlled surface conditions",
        "constructs": 17,
        "items": len(items),
        "items_sha256": hashlib.sha256(canonical(items)).hexdigest(),
        "rows": items,
    }
    (ROOT / "items.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plan = {
        "kind": "dexagon.ainglish.flagship-semantic-robustness-plan.v1",
        "purpose": "development-only fault localization across flagship semantics; never governance evidence or reader qualification",
        "items_sha256": packet["items_sha256"],
        "models": MODELS,
        "execution": {
            "one_call_per_construct_per_model": True,
            "calls": 51,
            "temperature": 0,
            "seed": SEED,
            "context": 4096,
            "retry_policy": "none",
            "parse_policy": "retain exact response; malformed or missing cells score incorrect",
        },
        "estimands": [
            "exact two-pole classification accuracy by model and surface condition",
            "least-favourable model accuracy for each flagship",
            "drop from canonical to hyphen-loss and opposite-distractor conditions",
        ],
        "claim_boundaries": [
            "The reference definitions are provided in every prompt, so this does not measure cold comprehension.",
            "These models are a convenience sample already present on disk, not a representative population.",
            "No result from this lab is eligible to settle, confirm, oppose, or ratify a proposal.",
            "No retry, prompt tuning, or model download follows observation of the frozen cells.",
        ],
        "model_downloads": 0,
        "governance_writes": 0,
    }
    plan["content_sha256"] = hashlib.sha256(canonical(plan)).hexdigest()
    (ROOT / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"constructs": 17, "items": len(items), "items_sha256": packet["items_sha256"], "plan_sha256": plan["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
