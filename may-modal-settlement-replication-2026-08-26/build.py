#!/usr/bin/env python3
"""Build wholly fresh may-force replication items without reader or governance calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082647
TARGET = "dba42c0e48b623502fb370067cf080a1b639a2bb621318400217f1f3d79b3e83"

DOMAINS = (
    "navigation", "archives", "scheduling", "publishing", "inventory",
    "laboratory", "billing", "education", "facilities", "support",
)
OPERATIONS = (
    ("the route coordinator", "reroute the survey vehicle", "the survey vehicle", "rerouted by the route coordinator"),
    ("the archive clerk", "transfer the sealed folder", "the sealed folder", "transferred by the archive clerk"),
    ("the calendar service", "reslot the inspection visit", "the inspection visit", "reslotted by the calendar service"),
    ("the release editor", "publish the corrected bulletin", "the corrected bulletin", "published by the release editor"),
    ("the stock controller", "move the reserve crate", "the reserve crate", "moved by the stock controller"),
    ("the bench assistant", "label the reference sample", "the reference sample", "labelled by the bench assistant"),
    ("the accounts worker", "reverse the duplicate charge", "the duplicate charge", "reversed by the accounts worker"),
    ("the course service", "reopen the marked exercise", "the marked exercise", "reopened by the course service"),
    ("the building controller", "unlock the west entrance", "the west entrance", "unlocked by the building controller"),
    ("the support agent", "close the resolved ticket", "the resolved ticket", "closed by the support agent"),
    ("the map reviewer", "replace the obsolete waypoint", "the obsolete waypoint", "replaced by the map reviewer"),
    ("the records service", "restore the indexed bundle", "the indexed bundle", "restored by the records service"),
    ("the booking worker", "cancel the duplicate appointment", "the duplicate appointment", "cancelled by the booking worker"),
    ("the copy editor", "withdraw the inaccurate notice", "the inaccurate notice", "withdrawn by the copy editor"),
    ("the depot robot", "release the spare module", "the spare module", "released by the depot robot"),
    ("the instrument service", "discard the tainted control", "the tainted control", "discarded by the instrument service"),
)

QUESTIONS = (
    {
        "question": "Which record would directly verify the modal claim in the target sentence?",
        "options": ["the governing grant at message time", "the writer's information at message time", "a mechanism test", "the later event history"],
        "permission": "the governing grant at message time",
        "possibility": "the writer's information at message time",
    },
    {
        "question": "Which finding would directly falsify the modal claim without relying on the eventual outcome?",
        "options": ["no governing grant existed at message time", "the writer's information ruled the outcome out", "the mechanism was unavailable", "the event did not later happen"],
        "permission": "no governing grant existed at message time",
        "possibility": "the writer's information ruled the outcome out",
    },
    {
        "question": "If only the modal claim is retracted, which record needs correction?",
        "options": ["the grant ledger", "the contemporaneous uncertainty record", "the mechanism inventory", "the later event log"],
        "permission": "the grant ledger",
        "possibility": "the contemporaneous uncertainty record",
    },
    {
        "question": "Which follow-up directly tests what the modal claim asserts?",
        "options": ["inspect the governing grant", "reconstruct what the writer could rule out", "stress-test the mechanism", "wait for the event"],
        "permission": "inspect the governing grant",
        "possibility": "reconstruct what the writer could rule out",
    },
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(options: list[str], answer: str, position: int) -> list[str]:
    current = options.index(answer)
    shift = (current - position) % len(options)
    return options[shift:] + options[:shift]


def target_sentence(force: str, voice: str, actor: str, action: str, subject: str, passive: str, marked: bool) -> str:
    if force == "permission":
        modal = "may-as-permission" if marked else "is permitted to"
    else:
        modal = "may-as-possibility" if marked else "might"
    if voice == "active":
        return f"{actor.capitalize()} {modal} {action}."
    if force == "permission" and not marked:
        return f"{subject.capitalize()} {modal} be {passive}."
    return f"{subject.capitalize()} {modal} be {passive}."


def scientific_items() -> list[dict]:
    rows = []
    for frame in range(80):
        domain = DOMAINS[frame % len(DOMAINS)]
        actor, action, subject, passive = OPERATIONS[(frame * 7 + 3) % len(OPERATIONS)]
        case = 7400 + frame
        context = f"Case MPR-{case} places {subject} in the {domain} work queue."
        objective = "possible" if frame % 2 == 0 else "impossible"
        authority = "permitted" if (frame // 2) % 2 == 0 else "forbidden"
        evidence = "open" if (frame // 4) % 2 == 0 else "ruled-out"
        mechanism_fact = (
            "A later mechanism audit found the operation executable at message time."
            if objective == "possible" else
            "A later mechanism audit found the operation technically blocked at message time."
        )
        grant_fact = (
            "A later records audit found a governing grant at message time."
            if authority == "permitted" else
            "A later records audit found the operation forbidden at message time."
        )
        evidence_fact = (
            "A later reconstruction found that the writer's information left the outcome open."
            if evidence == "open" else
            "A later reconstruction found that the writer's information ruled the outcome out."
        )
        for force_index, force in enumerate(("permission", "possibility")):
            voice = "active" if (frame + force_index) % 2 == 0 else "passive"
            q_index = (frame + force_index * 2) % len(QUESTIONS)
            block = QUESTIONS[q_index]
            answer = block[force]
            position = (frame * 2 + force_index) % 4
            later = f"{mechanism_fact} {evidence_fact if force == 'permission' else grant_fact}"
            rows.append({
                "id": f"mpr-{frame + 1:03d}-{force}",
                "english": f"{context} {target_sentence(force, voice, actor, action, subject, passive, False)} {later}",
                "ainglish": f"{context} {target_sentence(force, voice, actor, action, subject, passive, True)} {later}",
                "question": block["question"],
                "options": rotate(list(block["options"]), answer, position),
                "answer": answer,
                "form": f"may-as-{force}",
                "frame": frame + 1,
                "voice": voice,
                "domain": domain,
                "question_kind": ("verification", "falsifier", "correction", "followup")[q_index],
                "objective_state": objective,
                "authority_state": authority,
                "speaker_evidence_state": evidence,
                "cross_cell": (
                    "permitted_but_impossible" if force == "permission" and objective == "impossible"
                    else "forbidden_but_possible" if force == "possibility" and authority == "forbidden" and objective == "possible"
                    else "other"
                ),
            })
    return rows


def calibration_items() -> list[dict]:
    rows = []
    objects = ("cobalt disk", "hazel card", "ivory token", "juniper seal", "ochre key", "pearl tag", "quartz pass", "silver badge")
    for index, obj in enumerate(objects):
        bay = 81 + index
        answer = f"bay {bay}"
        options = rotate([answer, f"bay {bay + 1}", "not stated", "the dispatch desk"], answer, index % 4)
        rows.append({
            "id": f"mpr-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The note labels the {obj} vek({bay}), but gives no meaning for vek.",
            "ainglish": f"Control: vek(<N>) means the labelled object is stored in bay N. The note labels the {obj} vek({bay}).",
            "question": f"Where does the control place the {obj}?",
            "options": options,
            "answer": answer,
        })
    return rows


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    scientific = scientific_items()
    calibration = calibration_items()
    rows = scientific + calibration
    assert len(scientific) == 160 and len(calibration) == 8
    assert Counter(row["form"] for row in scientific) == Counter({"may-as-permission": 80, "may-as-possibility": 80})
    assert Counter(row["options"].index(row["answer"]) for row in scientific) == Counter({0: 40, 1: 40, 2: 40, 3: 40})
    packet = {
        "kind": "dexagon.ainglish.may-modal-settlement-items.v1",
        "seed": SEED,
        "slug": snapshot["proposal"]["slug"],
        "replicates_hash": TARGET,
        "scientific_items": 160,
        "calibration_items": 8,
        "items": rows,
        "sha256": hashlib.sha256(canonical(rows)).hexdigest(),
    }
    (ROOT / "items.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.may-modal-settlement-freeze.v1",
        "snapshot_sha256": snapshot["content_sha256"],
        "items_path": "items.json",
        "items_sha256": packet["sha256"],
        "replicates_hash": TARGET,
        "planned_sample": {"real_items": 160, "calibration_items": 8, "frames": 80, "forms": 2, "comparator": "careful"},
        "model_calls": 0,
        "governance_writes": 0,
        "blocker": "two distinct eligible qualified reader lineages",
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"scientific": 160, "calibration": 8, "items_sha256": packet["sha256"], "content_sha256": index["content_sha256"]}))


if __name__ == "__main__":
    main()

