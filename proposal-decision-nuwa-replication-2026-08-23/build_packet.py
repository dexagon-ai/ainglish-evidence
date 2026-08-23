#!/usr/bin/env python3
"""Build a fresh, balanced proposal-by replication packet without reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "proposal_decision_comprehension_2026_08_21" / "proposal_short_items.json"
SEED = 2026082361
QUESTION = (
    "Choose the three-part profile that follows from the message. Part 1: is the action only "
    "offered for consideration, operatively selected, invalid because the named source lacks "
    "standing, or impossible to determine? Part 2: may the record state that an existing choice "
    "has been made? Part 3: does this sentence itself command the reader or grant permission?"
)
OPTIONS = [
    "offered / no / no",
    "selected / yes / no",
    "invalid source / no / no",
    "selected / yes / yes",
    "cannot tell / cannot tell / cannot tell",
]
ANSWER = OPTIONS[0]


FRAMES = {
    "operational": [
        ("recovery coordinator", "rebuild the audit replica from the cold snapshot"),
        ("network reliability lead", "shift the overflow traffic to the western ingress"),
        ("database custodian", "compact the event ledger after the retention checkpoint"),
        ("release coordinator", "hold version 12.4 at the regional canary"),
        ("incident analyst", "capture a packet trace from the failing service mesh"),
        ("storage engineer", "move the archive shard onto encrypted object storage"),
        ("identity maintainer", "invalidate the dormant signing certificate"),
        ("observability lead", "increase trace sampling for the checkout path"),
        ("capacity planner", "reserve a second inference node for the evening load"),
        ("backup operator", "verify the monthly restore against an isolated database"),
        ("privacy engineer", "redact legacy identifiers from the export bundle"),
        ("queue maintainer", "drain the retry topic before changing its partition count"),
    ],
    "social": [
        ("community steward", "open a quiet room for first-time participants"),
        ("event organizer", "move the informal reception into the courtyard"),
        ("accessibility coordinator", "publish captions with the recorded workshop"),
        ("residency host", "invite the visiting fellows to the closing dinner"),
        ("library coordinator", "extend the equipment-loan window through Monday"),
        ("volunteer convener", "pair every new volunteer with an experienced guide"),
        ("facilities liaison", "keep one entrance open after the evening lecture"),
        ("program curator", "add a public question period after the demonstration"),
        ("member advocate", "translate the onboarding notice into three more languages"),
        ("travel coordinator", "book a shared coach from the station"),
        ("workshop facilitator", "split the final exercise into smaller groups"),
        ("archive editor", "publish the oral-history transcript with speaker notes"),
    ],
    "governance": [
        ("standards rapporteur", "circulate the draft interoperability rule for consultation"),
        ("budget secretary", "place the reserve allocation on next month's agenda"),
        ("ethics chair", "commission an external review of the consent procedure"),
        ("election officer", "trial ranked ballots in the advisory poll"),
        ("policy editor", "replace the temporary disclosure clause with a permanent one"),
        ("appeals clerk", "reopen the disputed case for written submissions"),
        ("audit delegate", "publish the minority opinion beside the committee report"),
        ("rules convener", "separate the quorum amendment from the voting amendment"),
        ("procurement observer", "invite two additional bids for the hosting contract"),
        ("records officer", "release the redacted minutes after the objection period"),
        ("safety representative", "require an incident drill before accreditation"),
        ("membership secretary", "create a non-voting observer category"),
    ],
    "scheduling": [
        ("production scheduler", "run the migration during Tuesday's low-traffic window"),
        ("training coordinator", "hold the model-safety session on the second Thursday"),
        ("maintenance planner", "inspect the cooling loop before the holiday shutdown"),
        ("editorial secretary", "move the copy deadline to noon on Wednesday"),
        ("interview coordinator", "reserve Friday morning for the final interviews"),
        ("deployment planner", "begin the phased rollout after the overnight backup"),
        ("conference producer", "schedule the protocol panel before the lunch break"),
        ("review coordinator", "close comments forty-eight hours before publication"),
        ("rota manager", "assign the database handover to the early shift"),
        ("research coordinator", "start the blinded evaluation after dataset freeze"),
        ("calendar steward", "move the recurring sync to the first Monday"),
        ("operations secretary", "hold the readiness review immediately after staging"),
    ],
}

CONTEXTS = [
    "No authorized choice has been entered. {role} writes, \"Perhaps we should {action}.\"",
    "Several participants already favor the idea, but the decision meeting is tomorrow. {role} writes, \"Could we {action}?\"",
    "A different course remains the operative choice. {role} writes, \"One option is to {action}.\"",
    "The note is explicitly part of a brainstorming round. {role} writes, \"Let's consider whether to {action}.\"",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(values: list[str], answer_position: int) -> list[str]:
    remaining = [value for value in values if value != ANSWER]
    output = list(remaining)
    output.insert(answer_position, ANSWER)
    return output


def build() -> dict:
    items = []
    ordinal = 0
    for domain, frames in FRAMES.items():
        for local_index, (role, action) in enumerate(frames):
            answer_position = ordinal % len(OPTIONS)
            english = CONTEXTS[local_index % len(CONTEXTS)].format(
                role=role.capitalize(), action=action,
            )
            prefix = english.split(f'{role.capitalize()} writes,', 1)[0]
            ainglish = (
                f"{prefix}proposal-by({role}): {action}."
                if prefix else f"proposal-by({role}): {action}."
            )
            items.append({
                "id": f"fresh-proposal-{ordinal + 1:02d}",
                "english": english,
                "ainglish": ainglish,
                "question": QUESTION,
                "options": rotate(OPTIONS, answer_position),
                "answer": ANSWER,
                "strata": {
                    "form": "proposal",
                    "baseline": "short",
                    "domain": domain,
                    "condition": f"proposal_fresh_variant_{local_index % 4}",
                    "answer_position": answer_position,
                },
            })
            ordinal += 1

    calibration_actions = [
        "archive the temporary channel",
        "reserve the smaller meeting room",
        "publish the draft agenda",
        "retain the older dashboard",
        "invite a second reviewer",
        "delay the rehearsal by one hour",
    ]
    calibration = []
    for index, action in enumerate(calibration_actions):
        answer_position = (index + 2) % len(OPTIONS)
        calibration.append({
            "id": f"fresh-calibration-{index + 1:02d}",
            "calibration": True,
            "english": (
                f"A status note mentions whether to {action}, but it does not say whether this is "
                "an option, an operative choice, or a directive."
            ),
            "ainglish": f"proposal-by(calibration author {index + 1}): {action}.",
            "question": QUESTION,
            "options": rotate(OPTIONS, answer_position),
            "answer": ANSWER,
            "strata": {"form": "proposal", "baseline": "short", "control": "planted_effect"},
        })

    assert ordinal == 48
    assert len({row["id"] for row in items + calibration}) == 54
    assert all(max(map(len, row["options"])) <= 39 for row in items + calibration)
    assert all(sum(row["strata"]["domain"] == d for row in items) == 12 for d in FRAMES)
    assert all(sum(row["strata"]["answer_position"] == p for row in items) in (9, 10) for p in range(5))

    old = json.loads(ORIGINAL.read_text(encoding="utf-8"))["items"]
    old_pairs = {(row["english"], row["ainglish"]) for row in old}
    new_pairs = {(row["english"], row["ainglish"]) for row in items + calibration}
    assert old_pairs.isdisjoint(new_pairs), "fresh packet overlaps the referenced original inputs"

    digest = hashlib.sha256(canonical(calibration + items)).hexdigest()
    return {
        "kind": "ainglish.evidence.packet.v1",
        "proposal": "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
        "replicates_hash": "312b0fb0a5ae0f7fe2693597d5391ea95458cd87648097307666dea0ceb2ac6a",
        "seed": SEED,
        "reader_calls": 0,
        "real_items": 48,
        "calibration_items": 6,
        "sha256": digest,
        "items": calibration + items,
    }


def main() -> None:
    document = build()
    (ROOT / "items.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    exact = hashlib.sha256((ROOT / "items.json").read_bytes()).hexdigest()
    receipt = {
        "kind": "ainglish.evidence.freeze.v1",
        "reader_calls": 0,
        "items_sha256": document["sha256"],
        "exact_file_sha256": exact,
        "real_items": document["real_items"],
        "calibration_items": document["calibration_items"],
        "original_complete_pair_overlap": 0,
    }
    (ROOT / "freeze-receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
