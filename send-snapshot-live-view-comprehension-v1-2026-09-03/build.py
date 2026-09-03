#!/usr/bin/env python3
"""Build the 144-item snapshot-versus-live-view comprehension carrier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "send-snapshot-version-ref-to-recipient-grant-live-view"
DOMAINS = [
    ("document", "runbook", "Nia"),
    ("spreadsheet", "capacity-sheet", "Oren"),
    ("code artifact", "release-bundle", "Pava"),
    ("dashboard", "incident-board", "Quin"),
    ("media file", "training-video", "Rhea"),
    ("policy record", "retention-policy", "Soren"),
]
EVENTS = ("source-edit", "source-deletion", "grant-revocation", "later-read")
PROBES = ("core", "authority-boundary", "evidence-boundary")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(values: list[str], offset: int) -> list[str]:
    offset %= len(values)
    return values[offset:] + values[:offset]


def place_answer(values: list[str], answer: str, position: int) -> list[str]:
    """Rotate without changing content so correct positions are exactly counterbalanced."""
    return rotate(values, values.index(answer) - position)


def event_context(event: str, object_name: str, version: str, next_version: str) -> str:
    return {
        "source-edit": f"Later, the canonical {object_name} is edited from {version} to {next_version}.",
        "source-deletion": f"Later, the canonical {object_name} is deleted from its source service.",
        "grant-revocation": f"Later, access to the canonical {object_name} is revoked for the recipient.",
        "later-read": f"At a later read, the canonical {object_name} contains {next_version} rather than {version}.",
    }[event]


def consequence_options(event: str, probe: str, version: str, next_version: str) -> tuple[str, str]:
    """Return the two consequence/boundary answers, snapshot pole first.

    The wording deliberately omits the implementation choice.  The four answer options can
    therefore cross two implementation answers with two consequence answers, making the two
    questions separately scoreable instead of hiding both judgements in one atomic label.
    """
    if probe == "authority-boundary":
        return (
            "no edit or redistribution right follows, and a separately authorised copy is unaffected",
            "edit and redistribution rights follow, and every separately authorised copy is erased",
        )
    if probe == "evidence-boundary":
        return (
            "the instruction alone proves no later receipt, retention, opening, or service-reachability event",
            "the instruction itself proves receipt, retention, opening, and service reachability",
        )
    return {
        "source-edit": (
            f"the recipient-visible content stays at {version}",
            f"a successful later read shows the current {next_version} contents",
        ),
        "source-deletion": (
            "the delivered and retained representation remains available after source deletion",
            "future access through the source-backed permission cannot retrieve the deleted object",
        ),
        "grant-revocation": (
            "the delivered and retained representation remains available after source access is revoked",
            "future access through the revoked permission is denied",
        ),
        "later-read": (
            f"opening the retained representation shows {version}",
            f"a successful read dereferences the canonical object and shows {next_version}",
        ),
    }[event]


def answer_options(event: str, probe: str, form: str, version: str, next_version: str) -> tuple[list[str], str, dict[str, dict[str, str]]]:
    snapshot_consequence, live_consequence = consequence_options(event, probe, version, next_version)
    expected_implementation = "snapshot" if form == "send-snapshot" else "live-view"
    # Boundary questions share one conservative correct answer across the two implementation
    # poles. Core consequence questions instead recover the topology-dependent later state.
    expected_consequence = (
        "snapshot" if probe == "core" and form == "send-snapshot"
        else "live-view" if probe == "core"
        else "conservative"
    )
    consequences = (
        [("conservative", snapshot_consequence), ("overclaim", live_consequence)]
        if probe != "core"
        else [("snapshot", snapshot_consequence), ("live-view", live_consequence)]
    )
    implementations = [
        ("snapshot", "transmit an independent representation of the named frozen version"),
        ("live-view", "grant revocable read-only access to the canonical object"),
    ]
    options: list[str] = []
    components: dict[str, dict[str, str]] = {}
    answer = ""
    for implementation, implementation_text in implementations:
        for consequence, consequence_text in consequences:
            option = f"Implementation: {implementation_text}. Consequence or boundary: {consequence_text}."
            options.append(option)
            components[option] = {
                "implementation": implementation,
                "consequence": consequence,
                "implementation_correct": implementation == expected_implementation,
                "consequence_correct": consequence == expected_consequence,
            }
            if implementation == expected_implementation and consequence == expected_consequence:
                answer = option
    assert answer
    return options, answer, components


def scientific_items() -> list[dict]:
    items: list[dict] = []
    row = 0
    for domain_index, (domain, object_name, recipient) in enumerate(DOMAINS, 1):
        for event_index, event in enumerate(EVENTS, 1):
            for probe_index, probe in enumerate(PROBES, 1):
                version = f"v{domain_index}{event_index}{probe_index}"
                next_version = f"v{domain_index}{event_index}{probe_index + 4}"
                common = (
                    f"The named {domain} is the canonical {object_name}. "
                    + event_context(event, object_name, version, next_version)
                )
                if probe == "core":
                    common += " For a fixed transfer, delivery and retention succeed; for a live grant, no independent copy or alternative grant exists."
                elif probe == "authority-boundary":
                    common += " The recipient already holds a separate copy under another authority; the instruction says nothing else about edit or redistribution rights."
                else:
                    common += " No receipt, opening audit, or service-reachability observation is available."
                careful_snapshot = (
                    f"Instruction: send {recipient} an independent fixed representation of exactly "
                    f"{object_name} {version}. Do not grant continuing access to the source. Later "
                    "source changes, deletion, or revocation cannot alter or withdraw a delivered "
                    "and retained representation. Sending does not itself prove receipt."
                )
                careful_live = (
                    f"Instruction: grant {recipient} a revocable read-only capability to the stable "
                    f"canonical object {object_name}. Each successful read shows its then-current "
                    "contents. Do not intentionally transfer a durable independent copy. This grants "
                    "no edit or redistribution right and does not prove that the object was opened."
                )
                for form, careful, marked in (
                    ("send-snapshot", careful_snapshot, f"Instruction: send-snapshot({object_name}@{version}, to={recipient})."),
                    ("grant-live-view", careful_live, f"Instruction: grant-live-view({object_name}, to={recipient})."),
                ):
                    row += 1
                    options, answer, components = answer_options(event, probe, form, version, next_version)
                    ordered = place_answer(options, answer, (row - 1) % 4)
                    items.append({
                        "id": f"snapshot-live-fresh-{row:03d}",
                        "scenario_id": f"snapshot-live-scenario-{row:03d}",
                        "english": common + " " + careful,
                        "ainglish": common + " " + marked,
                        "question": (
                            "Answer both questions by choosing the one option with both answers correct. "
                            "(1) Which implementation satisfies the instruction? "
                            "(2) What later consequence or authority/evidence boundary follows?"
                        ),
                        "questions": [
                            "Which implementation satisfies the instruction?",
                            "What later consequence or authority/evidence boundary follows?",
                        ],
                        "options": ordered,
                        "answer": answer,
                        "option_components": components,
                        "settlement_stratum": f"{form}-{domain_index}-{event}",
                        "strata": {"form": form, "domain": domain, "event": event, "probe": probe},
                    })
    return items


def calibration_items() -> list[dict]:
    rows = [
        ("owner", "Either Ula or Venn owns the rollback.", "Ula, not Venn, owns the rollback.", "Who owns the rollback?", ["Venn", "cannot tell", "Ula"], "Ula"),
        ("region", "The active mirror is in either Bern or Quito.", "The active mirror is in Quito, not Bern.", "Where is the active mirror?", ["Bern", "Quito", "cannot tell"], "Quito"),
        ("state", "The lease is either current or expired.", "The lease is expired, not current.", "What is the lease state?", ["cannot tell", "expired", "current"], "expired"),
        ("cause", "Either a stale key or a full queue caused the fault.", "A stale key, not a full queue, caused the fault.", "What caused the fault?", ["a full queue", "a stale key", "cannot tell"], "a stale key"),
        ("order", "The copper job ran either before or after the jade job.", "The copper job ran after, not before, the jade job.", "When did the copper job run?", ["after", "cannot tell", "before"], "after"),
        ("count", "The batch contains either six or eleven records.", "The batch contains six records, not eleven.", "How many records are present?", ["eleven", "six", "cannot tell"], "six"),
        ("actor", "Either Wira or Xeno signed the receipt.", "Xeno, not Wira, signed the receipt.", "Who signed the receipt?", ["cannot tell", "Wira", "Xeno"], "Xeno"),
        ("colour", "The flag is either coral or indigo.", "The flag is coral, not indigo.", "What colour is the flag?", ["coral", "indigo", "cannot tell"], "coral"),
    ]
    return [{
        "id": f"snapshot-live-cal-{i:02d}",
        "english": cold,
        "ainglish": planted,
        "question": question,
        "options": options,
        "answer": answer,
        "calibration": True,
        "calibration_scope": "target-independent",
        "strata": {"control": name},
    } for i, (name, cold, planted, question, options, answer) in enumerate(rows, 1)]


def main() -> None:
    scientific = scientific_items()
    controls = calibration_items()
    assert len(scientific) == 144 and len(controls) == 8
    assert len({item["id"] for item in scientific + controls}) == 152
    assert {item["strata"]["form"] for item in scientific} == {"send-snapshot", "grant-live-view"}
    assert all(sum(item["strata"]["form"] == form for item in scientific) == 72 for form in ("send-snapshot", "grant-live-view"))
    assert len({item["settlement_stratum"] for item in scientific}) == 48
    items = scientific + controls
    digest = hashlib.sha256(canonical(items)).hexdigest()
    artifact = {
        "kind": "dexagon.ainglish.snapshot-live-view-comprehension-carrier.v1",
        "proposal_revision": SLUG,
        "sha256": digest,
        "population": "144 fresh topology/consequence rows: 72 per form across six domains, four consequence events and three boundary probes, plus eight target-independent controls",
        "aggregation": "equal-weight mean of forty-eight separately reported form-by-domain-by-consequence strata; both question components and every boundary-probe cell remain in public sidecars",
        "reader_calls": 0,
        "items": items,
    }
    (ROOT / "items.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"scientific": len(scientific), "calibration": len(controls), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
