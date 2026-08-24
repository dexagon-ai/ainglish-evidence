#!/usr/bin/env python3
"""Build the frozen may-as-* comprehension carrier and comparator diagnostics."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
SEED = 2026082442
FORCES = ("permission", "possibility")

# domain, severity, neutral context, actor, active predicate, passive subject, passive participle
#
# Contexts deliberately avoid policy, likelihood, capability, and evidence cues. Each operation is
# rendered once in each force, using opposite voices, so subject matter cannot identify the force.
OPERATIONS = [
    ("security", "high", "A tenant archive is queued for the overnight export.", "The export worker", "transmit the tenant archive", "The tenant archive", "transmitted by the export worker"),
    ("security", "high", "A compromised credential remains in the incident workspace.", "The incident bot", "disable the compromised credential", "The compromised credential", "disabled by the incident bot"),
    ("security", "low", "The sealed logs are listed in the quarterly review packet.", "The auditor", "inspect the sealed logs", "The sealed logs", "inspected by the auditor"),
    ("security", "high", "Emergency traffic is waiting at the regional gateway.", "The router", "forward the emergency traffic", "The emergency traffic", "forwarded by the router"),
    ("security", "low", "A recovery snapshot is mounted in the archive workspace.", "The recovery service", "decrypt the recovery snapshot", "The recovery snapshot", "decrypted by the recovery service"),
    ("security", "low", "An incident summary is ready in the review folder.", "The analyst", "disclose the incident summary", "The incident summary", "disclosed by the analyst"),
    ("deployments", "high", "A signed package is waiting in the release channel.", "The release bot", "publish the signed package", "The signed package", "published by the release bot"),
    ("deployments", "high", "The payment queue is stalled behind an old worker.", "The maintainer", "restart the payment queue", "The payment queue", "restarted by the maintainer"),
    ("deployments", "low", "A canary build has completed its smoke checks.", "The scheduler", "promote the canary build", "The canary build", "promoted by the scheduler"),
    ("deployments", "high", "A customer table is named in the migration plan.", "The migration worker", "alter the customer table", "The customer table", "altered by the migration worker"),
    ("deployments", "low", "A compromised release is still visible in the package index.", "The package agent", "revoke the compromised release", "The compromised release", "revoked by the package agent"),
    ("deployments", "low", "The search index changed during the latest rollout.", "The operator", "roll back the search index", "The search index", "rolled back by the operator"),
    ("data", "high", "Expired snapshots remain in the retention batch.", "The archive service", "purge the expired snapshots", "The expired snapshots", "purged by the archive service"),
    ("data", "high", "Duplicate records appear in the import staging area.", "The import worker", "delete the duplicate records", "The duplicate records", "deleted by the import worker"),
    ("data", "low", "The search catalog is listed in the maintenance window.", "The indexer", "rebuild the search catalog", "The search catalog", "rebuilt by the indexer"),
    ("data", "high", "A recovery archive is attached to the restoration case.", "The backup service", "read the recovery archive", "The recovery archive", "read by the backup service"),
    ("data", "low", "A case file has reached the end of its active period.", "The retention bot", "move the case file", "The case file", "moved by the retention bot"),
    ("data", "low", "A deleted report is named in the restoration request.", "The records agent", "restore the deleted report", "The deleted report", "restored by the records agent"),
    ("infrastructure", "high", "The primary pump is vibrating during the restart sequence.", "The cooling controller", "stop the primary pump", "The primary pump", "stopped by the cooling controller"),
    ("infrastructure", "high", "Regional traffic is accumulating at the east gateway.", "The failover agent", "switch the regional traffic", "The regional traffic", "switched by the failover agent"),
    ("infrastructure", "low", "A degraded shard is listed in the storage console.", "The storage worker", "detach the degraded shard", "The degraded shard", "detached by the storage worker"),
    ("infrastructure", "low", "A duplicate alarm is repeating in the overnight dashboard.", "The monitor", "silence the duplicate alarm", "The duplicate alarm", "silenced by the monitor"),
    ("infrastructure", "low", "A standby node is idle beside the active pool.", "The capacity bot", "allocate the standby node", "The standby node", "allocated by the capacity bot"),
    ("infrastructure", "high", "An edge certificate expires at the end of the shift.", "The certificate agent", "replace the edge certificate", "The edge certificate", "replaced by the certificate agent"),
    ("finance", "high", "A disputed payment is attached to the customer case.", "The billing agent", "refund the disputed payment", "The disputed payment", "refunded by the billing agent"),
    ("finance", "high", "Reserve funds are staged in the treasury workspace.", "The treasury bot", "transfer the reserve funds", "The reserve funds", "transferred by the treasury bot"),
    ("finance", "low", "An invoice carries the tax code from last quarter.", "The invoice worker", "change the invoice tax code", "The invoice tax code", "changed by the invoice worker"),
    ("finance", "high", "A merchant account appears in the current fraud batch.", "The fraud service", "freeze the merchant account", "The merchant account", "frozen by the fraud service"),
    ("finance", "low", "The salary batch is complete in the payroll workspace.", "The payroll agent", "release the salary batch", "The salary batch", "released by the payroll agent"),
    ("finance", "low", "A settled ledger is attached to the reconciliation case.", "The audit bot", "reopen the settled ledger", "The settled ledger", "reopened by the audit bot"),
    ("communications", "high", "The primary operator has not answered the incident page.", "The notification service", "contact the backup operator", "The backup operator", "contacted by the notification service"),
    ("communications", "high", "A reported message remains in the public discussion.", "The moderation agent", "hide the reported message", "The reported message", "hidden by the moderation agent"),
    ("communications", "low", "A customer notice is still in the outbound folder.", "The mail worker", "resend the customer notice", "The customer notice", "resent by the mail worker"),
    ("communications", "high", "A private briefing is scheduled in the conference room.", "The conference bot", "record the private briefing", "The private briefing", "recorded by the conference bot"),
    ("communications", "low", "The status page still shows the morning summary.", "The publishing agent", "edit the status page", "The status page", "edited by the publishing agent"),
    ("communications", "low", "A localized alert is ready in the translation queue.", "The translation worker", "release the localized alert", "The localized alert", "released by the translation worker"),
    ("science", "high", "A contaminated sample is isolated on the laboratory bench.", "The laboratory robot", "discard the contaminated sample", "The contaminated sample", "discarded by the laboratory robot"),
    ("science", "low", "An anomaly label is attached to the latest analysis run.", "The analysis agent", "revise the anomaly label", "The anomaly label", "revised by the analysis agent"),
    ("science", "high", "The telescope mirror is parked after the calibration pass.", "The telescope controller", "reposition the telescope mirror", "The telescope mirror", "repositioned by the telescope controller"),
    ("science", "high", "A participant record is sealed in the trial workspace.", "The trial system", "unblind the participant record", "The participant record", "unblinded by the trial system"),
    ("science", "low", "An outlier reading remains in the sensor stream.", "The sensor service", "suppress the outlier reading", "The outlier reading", "suppressed by the sensor service"),
    ("science", "low", "A genomic summary is complete in the research archive.", "The archive bot", "publish the genomic summary", "The genomic summary", "published by the archive bot"),
    ("logistics", "low", "A sealed pallet is waiting beside the loading bay.", "The warehouse bot", "move the sealed pallet", "The sealed pallet", "moved by the warehouse bot"),
    ("logistics", "high", "A medical shipment is approaching the closed bridge.", "The routing agent", "divert the medical shipment", "The medical shipment", "diverted by the routing agent"),
    ("logistics", "high", "A freight container is held at the inspection lane.", "The customs service", "open the freight container", "The freight container", "opened by the customs service"),
    ("logistics", "low", "A delivery route is still present in tomorrow's schedule.", "The fleet bot", "cancel the delivery route", "The delivery route", "cancelled by the fleet bot"),
    ("logistics", "low", "A spare battery is tagged for the field team.", "The depot worker", "release the spare battery", "The spare battery", "released by the depot worker"),
    ("logistics", "high", "A damaged module is secured beneath the service crane.", "The crane controller", "lift the damaged module", "The damaged module", "lifted by the crane controller"),
    ("healthcare", "high", "An urgent referral is waiting in the triage queue.", "The triage agent", "forward the urgent referral", "The urgent referral", "forwarded by the triage agent"),
    ("healthcare", "high", "A controlled dose is prepared in the pharmacy station.", "The pharmacy bot", "release the controlled dose", "The controlled dose", "released by the pharmacy bot"),
    ("healthcare", "low", "A patient summary is attached to the transfer packet.", "The records worker", "disclose the patient summary", "The patient summary", "disclosed by the records worker"),
    ("healthcare", "high", "A surgery slot remains on tomorrow's theatre list.", "The scheduling agent", "cancel the surgery slot", "The surgery slot", "cancelled by the scheduling agent"),
    ("healthcare", "low", "A failed scan remains in the imaging workspace.", "The imaging service", "delete the failed scan", "The failed scan", "deleted by the imaging service"),
    ("healthcare", "low", "A critical result is visible in the laboratory feed.", "The laboratory system", "flag the critical result", "The critical result", "flagged by the laboratory system"),
    ("ordinary", "low", "A borrowed book reaches its due date this afternoon.", "The library bot", "renew the borrowed book", "The borrowed book", "renewed by the library bot"),
    ("ordinary", "low", "A meeting room is empty during the afternoon slot.", "The office agent", "reserve the meeting room", "The meeting room", "reserved by the office agent"),
    ("ordinary", "high", "The side entrance is closed during the evening event.", "The building controller", "unlock the side entrance", "The side entrance", "unlocked by the building controller"),
    ("ordinary", "high", "A dinner booking remains in the venue calendar.", "The event service", "cancel the dinner booking", "The dinner booking", "cancelled by the event service"),
    ("ordinary", "low", "An assignment deadline appears in the classroom portal.", "The classroom bot", "extend the assignment deadline", "The assignment deadline", "extended by the classroom bot"),
    ("ordinary", "high", "The irrigation cycle is queued during a water shortage.", "The garden controller", "start the irrigation cycle", "The irrigation cycle", "started by the garden controller"),
]

QUESTION_BLOCKS = {
    "verification_record": {
        "question": "Which source would directly verify the specific claim made by the target sentence?",
        "options": [
            "the rulebook entry governing the operation",
            "the writer's information snapshot from that moment",
            "a fresh test of the mechanism",
            "the later event log",
        ],
        "permission": "the rulebook entry governing the operation",
        "possibility": "the writer's information snapshot from that moment",
    },
    "direct_falsifier": {
        "question": "Which later finding would directly falsify the target sentence without relying on whether the event eventually occurred?",
        "options": [
            "no applicable rule granted the operation when the message was written",
            "the writer's information at that time ruled the outcome out",
            "the mechanism could not perform the operation",
            "the operation did not later occur",
        ],
        "permission": "no applicable rule granted the operation when the message was written",
        "possibility": "the writer's information at that time ruled the outcome out",
    },
    "correction_ledger": {
        "question": "If only the modal claim is withdrawn while technical facts stay unchanged, which ledger needs correction?",
        "options": [
            "the governing-grant ledger",
            "the contemporaneous uncertainty model",
            "the mechanism inventory",
            "the later outcome history",
        ],
        "permission": "the governing-grant ledger",
        "possibility": "the contemporaneous uncertainty model",
    },
    "operational_followup": {
        "question": "Which follow-up tests what the target sentence actually asserts?",
        "options": [
            "confirm the governing grant",
            "reconstruct what the writer could rule out at that moment",
            "stress-test the mechanism",
            "wait to see whether the event happens",
        ],
        "permission": "confirm the governing grant",
        "possibility": "reconstruct what the writer could rule out at that moment",
    },
}

CONTEXT_CUES = re.compile(
    r"(?i)\b(?:may|might|permit|permission|allowed|authorize|authority|policy|possible|"
    r"impossible|likely|likelihood|forecast|risk|evidence|capable|capability|can|cannot)\b"
)


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()


def rotate_to_position(options: list[str], answer: str, position: int) -> list[str]:
    current = options.index(answer)
    shift = (current - position) % len(options)
    return options[shift:] + options[:shift]


def sentence(force: str, voice: str, actor: str, active: str, subject: str, passive: str, form: str) -> str:
    if form == "marked":
        modal = f"may-as-{force}"
    elif form == "bare":
        modal = "may"
    elif form == "careful":
        modal = "is permitted to" if force == "permission" else "might"
    elif form == "allowed_to":
        if force != "permission":
            raise ValueError("allowed-to is permission-only")
        modal = "is allowed-to"
    else:
        raise ValueError(form)
    if voice == "active":
        return f"{actor} {modal} {active}."
    if form in {"careful", "allowed_to"} and force == "permission":
        # Keep modal position and grammatical passive voice without implying that an object grants.
        return f"{subject} {modal} be {passive}."
    return f"{subject} {modal} be {passive}."


def calibration_items() -> list[dict]:
    messages = [
        ("The handoff explicitly directs the auditor to inspect the rulebook entry governing the operation.", "the rulebook entry governing the operation"),
        ("The handoff explicitly directs the auditor to inspect the writer's information snapshot from that moment.", "the writer's information snapshot from that moment"),
        ("The handoff explicitly directs the auditor to run a fresh test of the mechanism.", "a fresh test of the mechanism"),
        ("The handoff explicitly directs the auditor to inspect the later event log.", "the later event log"),
    ]
    options = QUESTION_BLOCKS["verification_record"]["options"]
    rows = []
    for index in range(16):
        explicit, answer = messages[index % 4]
        rows.append({
            "id": f"may-modal-calibration-{index + 1:02d}",
            "english": "The handoff says to inspect the relevant source before acting.",
            "ainglish": explicit,
            "question": "Which source does the handoff explicitly direct the auditor to inspect?",
            "options": rotate_to_position(list(options), answer, index % 4),
            "answer": answer,
            "calibration": True,
            "strata": {"calibration_block": "construct_free_explicit_vs_unresolved"},
        })
    return rows


def real_items() -> list[dict]:
    rows = []
    force_seen = Counter()
    qnames = list(QUESTION_BLOCKS)
    for frame_index, operation in enumerate(OPERATIONS):
        domain, severity, context, actor, active, passive_subject, passive = operation
        assert CONTEXT_CUES.search(context) is None, context
        for voice_index, voice in enumerate(("active", "passive")):
            force = (
                "permission" if (frame_index + voice_index) % 2 == 0 else "possibility"
            )
            within_force = force_seen[force]
            force_seen[force] += 1
            qname = qnames[within_force % len(qnames)]
            question = QUESTION_BLOCKS[qname]
            answer = question[force]
            options = rotate_to_position(list(question["options"]), answer, within_force % 4)
            objective_state = "possible" if within_force % 2 == 0 else "impossible"
            other_state = "positive" if (within_force // 2) % 2 == 0 else "negative"
            authority_state = (
                "permitted" if force == "permission" or other_state == "positive" else "forbidden"
            )
            speaker_evidence_state = (
                "leaves_open" if force == "possibility" or other_state == "positive" else "rules_out"
            )
            marked = sentence(force, voice, actor, active, passive_subject, passive, "marked")
            careful = sentence(force, voice, actor, active, passive_subject, passive, "careful")
            bare = sentence(force, voice, actor, active, passive_subject, passive, "bare")
            allowed_to = (
                sentence(force, voice, actor, active, passive_subject, passive, "allowed_to")
                if force == "permission" else None
            )
            objective_fact = (
                "Later, a separate mechanism test found the operation executable at the message time."
                if objective_state == "possible" else
                "Later, a separate mechanism test found the operation technically blocked at the message time."
            )
            authority_fact = (
                "A later rulebook audit found an applicable grant at the message time."
                if authority_state == "permitted" else
                "A later rulebook audit found the operation forbidden at the message time."
            )
            evidence_fact = (
                "A later reconstruction found that the writer's information did not rule the outcome out."
                if speaker_evidence_state == "leaves_open" else
                "A later reconstruction found that the writer's information ruled the outcome out."
            )
            # Facts arrive after the target sentence and report the two ledgers the marker does
            # not assert. Permission rows expose capability + speaker evidence; possibility rows
            # expose capability + authority. Cross-cell facts are therefore visible to the reader
            # without serving as a lexical cue before the modal sentence.
            later_facts = (
                f"{objective_fact} {evidence_fact}"
                if force == "permission" else f"{objective_fact} {authority_fact}"
            )
            bare_target = f"{context} {bare}"
            item_id = f"may-modal-{frame_index + 1:03d}-{voice}-{force}"
            rows.append({
                "id": item_id,
                "english": f"{context} {careful} {later_facts}",
                "ainglish": f"{context} {marked} {later_facts}",
                "question": question["question"],
                "options": options,
                "answer": answer,
                "force": force,
                "scenario_id": f"may-frame-{frame_index + 1:03d}",
                "bare_message": f"{bare_target} {later_facts}",
                "bare_target_message": bare_target,
                "candidate_permission_message": f"{context} {sentence('permission', voice, actor, active, passive_subject, passive, 'careful')}",
                "candidate_possibility_message": f"{context} {sentence('possibility', voice, actor, active, passive_subject, passive, 'careful')}",
                "allowed_to_message": f"{context} {allowed_to} {later_facts}" if allowed_to else None,
                "strata": {
                    "domain": domain,
                    "severity": severity,
                    "voice": voice,
                    "question_kind": qname,
                    "authority_state": authority_state,
                    "objective_state": objective_state,
                    "speaker_evidence_state": speaker_evidence_state,
                    "load_bearing_cross_cell": (
                        "permitted_but_impossible"
                        if force == "permission" and objective_state == "impossible"
                        else "forbidden_but_possible"
                        if force == "possibility" and authority_state == "forbidden" and objective_state == "possible"
                        else "other"
                    ),
                },
            })
    return rows


def validate(real: list[dict], calibration: list[dict]) -> dict:
    assert len(OPERATIONS) == 60
    assert len(real) == 120 and len(calibration) == 16
    assert len({row["id"] for row in real + calibration}) == 136
    assert Counter(row["force"] for row in real) == Counter(permission=60, possibility=60)
    assert Counter(row["strata"]["voice"] for row in real) == Counter(active=60, passive=60)
    assert Counter(row["strata"]["severity"] for row in real) == Counter(high=60, low=60)
    assert Counter(row["strata"]["domain"] for row in real) == Counter({
        "security": 12, "deployments": 12, "data": 12, "infrastructure": 12,
        "finance": 12, "communications": 12, "science": 12, "logistics": 12,
        "healthcare": 12, "ordinary": 12,
    })
    assert Counter(row["options"].index(row["answer"]) for row in real) == Counter({0: 30, 1: 30, 2: 30, 3: 30})
    assert Counter(row["strata"]["question_kind"] for row in real if row["force"] == "permission") == Counter({name: 15 for name in QUESTION_BLOCKS})
    assert Counter(row["strata"]["question_kind"] for row in real if row["force"] == "possibility") == Counter({name: 15 for name in QUESTION_BLOCKS})
    for force in FORCES:
        subset = [row for row in real if row["force"] == force]
        assert Counter(row["strata"]["objective_state"] for row in subset) == Counter(possible=30, impossible=30)
    possibility = [row for row in real if row["force"] == "possibility"]
    permission = [row for row in real if row["force"] == "permission"]
    assert Counter(row["strata"]["authority_state"] for row in possibility) == Counter(permitted=30, forbidden=30)
    assert Counter(row["strata"]["speaker_evidence_state"] for row in permission) == Counter(leaves_open=30, rules_out=30)
    assert sum(row["strata"]["load_bearing_cross_cell"] == "permitted_but_impossible" for row in real) == 30
    assert sum(row["strata"]["load_bearing_cross_cell"] == "forbidden_but_possible" for row in real) == 15
    assert len({row["bare_target_message"] for row in real}) == 120
    for row in real + calibration:
        assert row["answer"] in row["options"] and len(set(row["options"])) == 4
        assert row["english"] != row["ainglish"]
    for row in real:
        assert "may-as-" not in row["question"]
        assert all("may-as-" not in option for option in row["options"])
        assert row["force"] in row["ainglish"] and row["force"] not in row["english"]
        assert row["bare_target_message"].count(" may ") == 1
        target_end = row["bare_target_message"]
        assert row["bare_message"].startswith(target_end + " Later,")
        assert (row["allowed_to_message"] is not None) == (row["force"] == "permission")
    return {
        "real_items": 120,
        "calibration_items": 16,
        "forces": {"permission": 60, "possibility": 60},
        "domains": 10,
        "voices": {"active": 60, "passive": 60},
        "severity": {"high": 60, "low": 60},
        "question_kinds": {name: 30 for name in QUESTION_BLOCKS},
        "answer_positions": {str(index): 30 for index in range(4)},
        "cross_cells": {"permitted_but_impossible": 30, "forbidden_but_possible": 15},
        "admissibility": (
            "120 unique bare-may messages, generated from neutral contexts that contain none of "
            "the declared authority, possibility, capability, likelihood, or evidence cues; both "
            "force expansions are grammatical by the same renderer before force assignment"
        ),
    }


def document(kind: str, items: list[dict], summary: dict) -> dict:
    return {
        "kind": kind,
        "seed": SEED,
        "items": items,
        "sha256": canonical_sha(items),
        "summary": summary,
    }


def main() -> None:
    real = real_items()
    calibration = calibration_items()
    summary = validate(real, calibration)

    hidden_build_fields = (
        "bare_message", "bare_target_message", "candidate_permission_message",
        "candidate_possibility_message", "allowed_to_message",
    )
    claim = [{key: value for key, value in row.items() if key not in hidden_build_fields} for row in real] + calibration
    bare = [{
        **{key: value for key, value in row.items() if key not in ("english", *hidden_build_fields)},
        "english": row["bare_message"],
        "comparison": "marked_vs_bare_may_descriptive_diagnostic",
    } for row in real] + calibration
    allowed = [{
        **{key: value for key, value in row.items() if key not in ("english", *hidden_build_fields)},
        "english": row["allowed_to_message"],
        "comparison": "may_as_permission_vs_ratified_allowed_to_practical_diagnostic",
    } for row in real if row["force"] == "permission"] + calibration
    gate = [{
        "id": row["id"],
        "scenario_id": row["scenario_id"],
        "bare_message": row["bare_target_message"],
        "neutral_context_gate": True,
        "candidate_permission_reading": row["candidate_permission_message"],
        "candidate_possibility_reading": row["candidate_possibility_message"],
    } for row in real]

    outputs = {
        "claim-items.json": document("ainglish.may-modal.claim-items.v1", claim, summary),
        "bare-items.json": document("ainglish.may-modal.bare-diagnostic-items.v1", bare, {**summary, "role": "descriptive only"}),
        "allowed-to-items.json": document("ainglish.may-modal.allowed-to-diagnostic-items.v1", allowed, {
            "real_items": 60, "calibration_items": 16, "force": "permission", "role": "primary practical comparator diagnostic",
        }),
        "admissibility-gate.json": {
            "kind": "ainglish.may-modal.construct-blind-admissibility.v1",
            "rule": (
                "Retain only a unique affirmative bare-may message whose preceding context contains "
                "none of the frozen force/capability cues and for which both force expansions are "
                "produced by the same grammar renderer before scoring. This is a deterministic "
                "construct-blind gate, not a human judgment of naturalness."
            ),
            "items": gate,
            "sha256": canonical_sha(gate),
            "retained": len(gate),
            "rejected": 0,
        },
    }
    for name, value in outputs.items():
        (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{name}: {value.get('sha256')} ({len(value.get('items', []))} rows)")


if __name__ == "__main__":
    main()
