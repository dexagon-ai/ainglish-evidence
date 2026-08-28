#!/usr/bin/env python3
"""Build frozen test-outcome and silence-default carriers without inference or governance writes."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PLACEHOLDER = "REPLACE_AFTER_FIRST_COMMIT"

TEST_SLUG = "test-run-t-test-passed-t-did-tested-mean-the-check-happened-"
SILENCE_SLUG = "go-unless-no-t-hold-until-yes-say-what-the-addressee-s-silen"
SOME_SLUG = "some-or-all-some-but-not-all-does-some-leave-room-for-all-2"
MAY_SLUG = "may-as-permission-may-as-possibility-does-may-authorize-an-a"

TEST_CONTEXTS = [
    ("backup B17", "restore-v4@run-817", "restore completes and its checksum matches"),
    ("release artifact R42", "signature-v2@run-204", "the signature verifies and the manifest matches"),
    ("invoice pipeline P9", "reconcile-v3@run-611", "every declared balance check is satisfied"),
    ("access policy A6", "policy-audit-v5@run-330", "all mandatory policy assertions are satisfied"),
    ("model candidate M8", "eval-suite-v7@run-092", "every declared acceptance threshold is met"),
    ("route table N4", "routing-check-v2@run-508", "all declared reachability checks are satisfied"),
    ("inspection lot I3", "inspection-v6@run-144", "all declared inspection criteria are satisfied"),
    ("database snapshot D2", "integrity-v8@run-701", "all declared integrity criteria are satisfied"),
]
TEST_FORMS = ("test-run", "test-passed")
TEST_SEAMS = (
    "terminal_execution", "declared_acceptance", "all_subchecks", "broader_fitness",
    "current_fitness", "independent_verification",
)

SILENCE_CONTEXTS = [
    ("merge change 330", "change 330 is integrated", "change 330 remains open", "2026-08-31T17:00Z"),
    ("publish dataset 36", "dataset 36 is public", "dataset 36 remains private", "2026-09-01T09:00Z"),
    ("rotate key K8", "key K8 is rotated", "key K8 remains unchanged", "2026-09-01T12:00Z"),
    ("archive queue Q4", "queue Q4 is archived", "queue Q4 remains active", "2026-09-02T10:30Z"),
    ("enable route R7", "route R7 is enabled", "route R7 remains disabled", "2026-09-02T14:00Z"),
    ("send report C5", "report C5 is transmitted", "report C5 remains unsent", "2026-09-03T08:00Z"),
    ("remove replica P2", "replica P2 is removed", "replica P2 remains present", "2026-09-03T16:00Z"),
    ("start migration M6", "migration M6 is started", "migration M6 remains unstarted", "2026-09-04T11:00Z"),
]
SILENCE_FORMS = ("go-unless-no", "hold-until-yes")
BEHAVIOURS = ("silent", "decline", "defer", "question", "approve", "late_decline")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verify_seal(value: dict) -> None:
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected


def seal(value: dict) -> dict:
    unsigned = dict(value)
    unsigned.pop("content_sha256", None)
    unsigned["content_sha256"] = hashlib.sha256(canonical(unsigned)).hexdigest()
    return unsigned


def write(name: str, value: dict) -> dict:
    value = seal(value)
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return value


def rotate(values: list[str], offset: int) -> list[str]:
    at = offset % len(values)
    return values[at:] + values[:at]


def calibrations(prefix: str, marker: str, start: int) -> list[dict]:
    rows = []
    for index in range(12):
        bay = start + index
        answer = f"bay {bay}"
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The control note labels parcel {index + 1} {marker}({bay}), but gives no rule for {marker}.",
            "ainglish": f"Control rule: {marker}(N) means the labelled parcel is stored in bay N. The note labels parcel {index + 1} {marker}({bay}).",
            "question": "Where does the control rule place the parcel?",
            "options": rotate([answer, f"bay {bay + 1}", "dispatch desk", "not stated"], index),
            "answer": answer,
            "calibration_construct": f"target-independent {marker} location marker",
            "calibration_scope": "target-independent",
        })
    return rows


def test_surfaces(index: int, form: str) -> tuple[str, str]:
    subject, test_ref, criteria = TEST_CONTEXTS[index]
    common = (
        f"Case TST-{index + 1:02d}. The immutable reference {test_ref} names one procedure, "
        f"its declared criteria ('{criteria}'), and one particular execution. Its policy may satisfy "
        "a criterion through an allowed skip, expected failure, or signed waiver."
    )
    if form == "test-run":
        marked = f"{common} The {subject} test-run({test_ref})."
        careful = (
            f"{common} The named execution {test_ref} occurred on the {subject} and produced a "
            "terminal result. This statement does not say whether that result passed, failed, or "
            "was indeterminate."
        )
    else:
        marked = f"{common} The {subject} test-passed({test_ref})."
        careful = (
            f"{common} The named execution {test_ref} occurred on the {subject}, produced a terminal "
            "result, and every acceptance criterion declared for that run was satisfied. This does "
            "not say that every constituent subcheck executed."
        )
    return marked, careful


def test_rows() -> tuple[list[dict], list[dict], list[dict]]:
    scientific, bare, validity = [], [], []
    for index, (subject, test_ref, criteria) in enumerate(TEST_CONTEXTS):
        for form in TEST_FORMS:
            marked, careful = test_surfaces(index, form)
            definitions = [
                ("terminal_execution", "Does the target establish that the named execution reached a terminal result?", "yes"),
                ("declared_acceptance", "Does the target establish that every acceptance criterion declared for that run was satisfied?", "yes" if form == "test-passed" else "not established"),
                ("all_subchecks", "Does the target establish that every constituent subcheck executed?", "not established"),
                ("broader_fitness", "Does the target establish fitness outside the named procedure?", "not established"),
                ("current_fitness", "Does the target establish that the subject still satisfies the criteria now?", "not established"),
                ("independent_verification", "Does the target establish that an independent party performed the evaluation?", "not established"),
            ]
            bare_text = f"Case TST-{index + 1:02d}. The {subject} was tested with {test_ref}."
            for seam, question, answer in definitions:
                options = rotate(["yes", "no", "not established", "cannot determine"], index + len(form) + len(seam))
                row_id = f"tst-{form}-{seam}-{index + 1:02d}"
                scientific.append({
                    "id": row_id, "english": careful, "ainglish": marked, "question": question,
                    "options": options, "answer": answer, "form": form, "semantic_seam": seam,
                    "domain": subject, "test_reference": test_ref, "criteria": criteria,
                    "settlement_stratum": f"{form}.{seam}",
                })
                bare.append({
                    "id": row_id + "-bare", "source_scientific_id": row_id, "text": bare_text,
                    "question": question, "options": options, "descriptive_only": True,
                })
        invalid_cases = [
            ("missing-criteria", f"The {subject} test-passed(unversioned-{index + 1}).", "criteria cannot be recovered"),
            ("scheduled-only", f"The {subject} test-run({test_ref}), but the queue receipt says it never started.", "no terminal execution"),
        ]
        for kind, text, reason in invalid_cases:
            validity.append({
                "id": f"tst-validity-{kind}-{index + 1:02d}", "text": text,
                "question": "Is this a valid use of the target marker under the registered mapping?",
                "options": rotate(["valid", "invalid", "cannot determine"], index),
                "answer": "invalid", "invalidity": reason, "descriptive_only": True,
            })
    return scientific, bare, validity


def response_for(behaviour: str, deadline: str) -> str:
    return {
        "silent": f"At the evaluation instant {deadline}, no message from the addressee had arrived in the writer's inbox.",
        "decline": f"An explicit decline arrived in the writer's inbox before {deadline}; the exchange is evaluated immediately after {deadline}.",
        "defer": f"A request for more time arrived in the writer's inbox before {deadline}; the exchange is evaluated immediately after {deadline}.",
        "question": f"A question asking for a checksum arrived in the writer's inbox before {deadline}; it did not decline or defer the action, and the exchange is evaluated immediately after {deadline}.",
        "approve": f"An explicit authorization arrived in the writer's inbox before {deadline}; the exchange is evaluated immediately after {deadline}.",
        "late_decline": f"No earlier objection arrived; an explicit decline first reached the writer's inbox after {deadline}, and the exchange is evaluated immediately after that decline.",
    }[behaviour]


def silence_surfaces(index: int, form: str, behaviour: str) -> tuple[str, str, str]:
    action, completed, pending, deadline = SILENCE_CONTEXTS[index]
    response = response_for(behaviour, deadline)
    common = f"Case SIL-{index + 1:02d}. The writer addresses one named recipient. {response}"
    if form == "go-unless-no":
        marked = f"{common} The writer says: '{action}, go-unless-no({deadline})'."
        careful = (
            f"{common} The writer commits to {action} at {deadline} unless an explicit decline or "
            "deferral reaches the writer's inbox before then. A question is not an objection; an "
            "objection arriving after that instant is a new request rather than a retroactive veto."
        )
        executes = behaviour in {"silent", "question", "approve", "late_decline"}
    else:
        marked = f"{common} The writer says: '{action}, hold-until-yes'."
        careful = (
            f"{common} The writer commits not to {action} until that recipient explicitly authorizes "
            "it. Silence, a question, a decline, or a deferral does not release the hold, and the hold "
            "does not expire."
        )
        if behaviour == "approve":
            # Approval releases the hold.  The marker does not additionally promise
            # that ACTION has already completed by this evaluation instant.
            return marked, careful, "cannot determine"
        executes = False
    return marked, careful, completed if executes else pending


def silence_rows() -> tuple[list[dict], list[dict], list[dict]]:
    scientific, bare, boundary = [], [], []
    closings = [
        "Let me know if you have concerns.", "Please confirm.", "Thoughts?",
        "I will proceed unless I hear otherwise.", "Tell me if this is a problem.", "Awaiting your view.",
    ]
    for index, (action, completed, pending, deadline) in enumerate(SILENCE_CONTEXTS):
        for form in SILENCE_FORMS:
            for behaviour in BEHAVIOURS:
                marked, careful, answer = silence_surfaces(index, form, behaviour)
                options = rotate([completed, pending, "the action is reversed later", "cannot determine"], index + len(form) + len(behaviour))
                row_id = f"sil-{form}-{behaviour}-{index + 1:02d}"
                scientific.append({
                    "id": row_id, "english": careful, "ainglish": marked,
                    "question": "At the evaluation instant, which state follows from the writer's stated commitment?",
                    "options": options, "answer": answer, "form": form,
                    "addressee_behaviour": behaviour, "action": action, "deadline": deadline,
                    "clock_basis": "arrival in writer inbox", "settlement_stratum": f"{form}.{behaviour}",
                })
                bare.append({
                    "id": row_id + "-bare", "source_scientific_id": row_id,
                    "text": f"Case SIL-{index + 1:02d}. The writer says '{action}. {closings[(index + len(behaviour)) % len(closings)]}' {response_for(behaviour, deadline)}",
                    "question": "At the evaluation instant, which state follows from the writer's message?",
                    "options": options, "descriptive_only": True,
                })
            boundary.append({
                "id": f"sil-boundary-{form}-{index + 1:02d}",
                "text": f"The writer says '{action}, {form + '(' + deadline + ')' if form == 'go-unless-no' else form}'.",
                "question": "Does that wording alone establish both that the recipient received the message and that the writer has authority to act?",
                "options": rotate(["yes", "no", "cannot determine"], index), "answer": "no",
                "boundaries": ["receipt is not asserted", "authority is not manufactured"],
                "descriptive_only": True,
            })
    return scientific, bare, boundary


def artifact(name: str, public_id: str, slug: str, scientific: list[dict], calibration: list[dict]) -> dict:
    return write(f"{name}.items.json", {
        "kind": "dexagon.ainglish.flagship-comprehension-items.v1", "campaign": name,
        "proposal_public_id": public_id, "proposal_revision": slug,
        "scientific_items": len(scientific), "calibration_items": len(calibration),
        "items": calibration + scientific,
    })


def template(name: str, slug: str, construct: str, surface_sha: str, items_artifact: dict,
             description: str, seed: int, item_commit: str, sidecars: list[str],
             settlement_design: str) -> dict:
    items = items_artifact["items"]
    scientific = [row for row in items if not row.get("calibration")]
    strata = sorted(Counter(row["settlement_stratum"] for row in scientific))
    filename = f"{name}.items.json"
    items_sha = hashlib.sha256(canonical(items)).hexdigest()
    return write(f"{name}.template.json", {
        "kind": "dexagon.ainglish.manifest-bound-panel-template.v1",
        "proposal_revision": slug, "slug": slug, "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "comparator": {"kind": "complete-careful-english-v1", "description": description},
        "settlement_strata": [{"id": value, "weight": 1} for value in strata],
        "items": items,
        "panel": [
            {"name": "REPLACE-QUALIFIED-READER-A", "provider": "replace", "model": "replace"},
            {"name": "REPLACE-QUALIFIED-READER-B", "provider": "replace", "model": "replace"},
        ],
        "panel_neff": 2,
        "activation": {
            "runnable": False,
            "reason": "No exact eligible reader panel is bound; two independently qualified base-model lineages are required.",
            "how": "Activate from the immutable item URL, commit the runspec, mint before any reader call, and retain every outcome.",
        },
        "model_calls": 0, "governance_writes": 0, "construct": construct,
        "proposal_snapshot_sha256": surface_sha,
        "scientific_items": len(scientific), "calibration_items": len(items) - len(scientific),
        "settlement_design": settlement_design,
        "diagnostic_sidecars": [{"file": path, "governance_metric": None} for path in sidecars],
        "items_artifact": {
            "file": filename,
            "published_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{item_commit}/{ROOT.name}/{filename}",
            "items_sha256": items_sha,
            "activation_rule": "Bind these exact published bytes; mutable branch URLs are refused.",
        },
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item-commit", default=PLACEHOLDER)
    args = parser.parse_args()
    assert args.item_commit == PLACEHOLDER or re.fullmatch(r"[0-9a-f]{40}", args.item_commit)

    snapshot = json.loads((ROOT / "proposal-snapshot.json").read_text(encoding="utf-8"))
    verify_seal(snapshot)
    proposals = snapshot["proposals"]
    assert proposals[TEST_SLUG]["stage"] == proposals[SILENCE_SLUG]["stage"] == "measured"

    test_scientific, test_bare, test_validity = test_rows()
    silence_scientific, silence_bare, silence_boundary = silence_rows()
    test_cal = calibrations("tst", "pev", 410)
    silence_cal = calibrations("sil", "nuv", 510)
    test_items = artifact("test-outcome", proposals[TEST_SLUG]["public_id"], TEST_SLUG, test_scientific, test_cal)
    silence_items = artifact("silence-default", proposals[SILENCE_SLUG]["public_id"], SILENCE_SLUG, silence_scientific, silence_cal)
    write("test-outcome-bare-diagnostic.json", {"kind": "dexagon.ainglish.bare-english-diagnostic-items.v1", "governance_metric": None, "items": test_bare})
    write("test-outcome-validity-diagnostic.json", {"kind": "dexagon.ainglish.validity-diagnostic-items.v1", "governance_metric": None, "items": test_validity})
    write("silence-default-bare-diagnostic.json", {"kind": "dexagon.ainglish.bare-english-diagnostic-items.v1", "governance_metric": None, "items": silence_bare})
    write("silence-default-boundary-diagnostic.json", {"kind": "dexagon.ainglish.boundary-diagnostic-items.v1", "governance_metric": None, "items": silence_boundary})

    test_template = template(
        "test-outcome", TEST_SLUG, "test-run(<T>) / test-passed(<T>)",
        proposals[TEST_SLUG]["surface_sha256"], test_items,
        "Each form versus its complete current mapping; terminal execution, declared acceptance, constituent execution, broader/current fitness, and verifier identity are separate cells.",
        2026082803, args.item_commit,
        ["test-outcome-bare-diagnostic.json", "test-outcome-validity-diagnostic.json"],
        "form x semantic seam; each equal-weight cell is load-bearing",
    )
    silence_template = template(
        "silence-default", SILENCE_SLUG, "go-unless-no(<t>) / hold-until-yes",
        proposals[SILENCE_SLUG]["surface_sha256"], silence_items,
        "Each form versus its complete writer-commitment mapping across six addressee behaviours and the writer-inbox clock.",
        2026082804, args.item_commit,
        ["silence-default-bare-diagnostic.json", "silence-default-boundary-diagnostic.json"],
        "form x addressee behaviour; each equal-weight cell is load-bearing",
    )

    may_readiness = proposals[MAY_SLUG]["evidence_readiness"]
    some_measurements = [row for row in proposals[SOME_SLUG]["measurements"] if row["metric"] == "comprehension_accuracy_delta"]
    dispositions = {
        "some-or-all": {
            "proposal": SOME_SLUG, "action": "do_not_add_same_principal_reader_run",
            "reason": "Live comprehension evidence is disputed; resolve the disagreement or amend rather than dilute it.",
            "existing_comprehension_hashes": [row["manifest_hash"] for row in some_measurements],
        },
        "may-as": {
            "proposal": MAY_SLUG, "action": "do_not_spend_reader",
            "reason": "The prerequisite token_delta currently opposes; author repair or a genuinely independent challenge comes first.",
            "opposing_evidence": may_readiness.get("opposing_evidence", []),
        },
    }
    write("index.json", {
        "kind": "dexagon.ainglish.flagship-outcome-silence-wave-index.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "item_commit": args.item_commit,
        "outputs": {
            "test_outcome": {"items": "test-outcome.items.json", "template": "test-outcome.template.json", "scientific": len(test_scientific), "strata": len(TEST_FORMS) * len(TEST_SEAMS), "content_sha256": test_template["content_sha256"]},
            "silence_default": {"items": "silence-default.items.json", "template": "silence-default.template.json", "scientific": len(silence_scientific), "strata": len(SILENCE_FORMS) * len(BEHAVIOURS), "content_sha256": silence_template["content_sha256"]},
        },
        "dispositions": dispositions,
        "fresh_answer_bearing_items": len(test_scientific) + len(silence_scientific),
        "model_calls": 0, "tokenizer_calls": 0, "attempt_mints": 0, "governance_writes": 0,
    })
    print(json.dumps({"test_outcome": len(test_scientific), "silence_default": len(silence_scientific), "item_commit": args.item_commit, "dispositions": dispositions}, indent=2))


if __name__ == "__main__":
    main()
