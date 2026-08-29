#!/usr/bin/env python3
"""Build four deterministic, balanced comprehension packets."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "proposal-snapshots.json"

PRONOUN_REFERENCE = (
    "Reference: `it(<ref>)` binds singular non-person `it` to exactly one earlier, locally "
    "recoverable discourse referent. It changes only pronoun attachment and does not assert "
    "causality, responsibility, ownership, identity, or truth."
)
NEGATION_REFERENCE = (
    "Reference: `none-of(<S>): <P>` says exactly zero members of the fixed non-empty set S "
    "satisfy P. `not-all-of(<S>): <P>` says fewer than all satisfy P and deliberately permits "
    "zero satisfiers. Neither form says S is the whole population."
)


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def rotate_to(options: list[str], answer: str, target: int) -> list[str]:
    current = options.index(answer)
    shift = (current - target) % len(options)
    return options[shift:] + options[:shift]


def wrap(reference: str | None, message: str) -> str:
    return message if reference is None else f"{reference}\nMessage: {message}"


def calibration_rows(prefix: str) -> list[dict]:
    seeds = [
        ("The east gate is closed.", "Is the east gate open?", "no"),
        ("Exactly two files changed.", "Did at least one file change?", "yes"),
        ("The note does not identify an approver.", "Is an approver identified?", "no"),
        ("Every named sensor reported.", "Did each named sensor report?", "yes"),
        ("The job may finish Tuesday or Wednesday; neither day is confirmed.", "Is Tuesday confirmed?", "no"),
        ("Ravi checked the first record but not the second.", "Did Ravi check both records?", "no"),
        ("The message says only that work began.", "Does it say the work finished?", "no"),
        ("No item in the box is red.", "Could a red item be in the box under this statement?", "no"),
        ("At least one valve is open.", "Must every valve be open?", "no"),
        ("The archive contains four bundles.", "Does the archive contain zero bundles?", "no"),
        ("The route is available only after noon.", "Is the route available at 09:00?", "no"),
        ("The sender explicitly names module-7.", "Is module-7 named?", "yes"),
    ]
    options = ["yes", "no", "cannot tell"]
    return [
        {
            "id": f"{prefix}-cal-{i:02d}",
            "message": message,
            "question": question,
            "options": rotate_to(options, answer, i % 3),
            "answer": answer,
        }
        for i, (message, question, answer) in enumerate(seeds, 1)
    ]


PRONOUN_POPULATIONS = {
    "zero_shot": [
        ("gateway", "worker", "failed", "failure diagnostic"),
        ("rover", "container", "moved", "position check"),
        ("sensor", "beacon", "overheated", "thermal inspection"),
        ("compiler", "module", "restarted", "restart audit"),
        ("process", "file", "became unavailable", "availability check"),
        ("controller", "valve", "leaked", "leak inspection"),
        ("index", "record", "changed", "change review"),
        ("drone", "package", "blocked the route", "route-clearance action"),
        ("router", "bridge", "disconnected", "connection diagnostic"),
        ("scanner", "sample", "expired", "expiry handling"),
    ],
    "definition_conditioned": [
        ("daemon", "cache", "failed", "failure diagnostic"),
        ("satellite", "relay", "moved", "position check"),
        ("pump", "filter", "overheated", "thermal inspection"),
        ("camera", "lens", "restarted", "restart audit"),
        ("scheduler", "job", "became unavailable", "availability check"),
        ("database", "table", "leaked", "leak inspection"),
        ("actuator", "latch", "changed", "change review"),
        ("monitor", "probe", "blocked the route", "route-clearance action"),
        ("engine", "turbine", "disconnected", "connection diagnostic"),
        ("archive", "bundle", "expired", "expiry handling"),
    ],
}


def pronoun_packet(condition: str) -> dict:
    reference = None if condition == "zero_shot" else PRONOUN_REFERENCE
    rows = []
    context_no = 0
    for cycle in range(8):
        for pair_no, (left_kind, right_kind, state, action) in enumerate(PRONOUN_POPULATIONS[condition]):
            context_no += 1
            tag = "z" if condition == "zero_shot" else "d"
            left = f"{left_kind}-{tag}{cycle + 1:02d}"
            right = f"{right_kind}-{tag}{cycle + 1:02d}"
            connector = ["after", "because", "when", "while"][pair_no % 4]
            bare = f"The {left} alerted the {right} {connector} it {state}."
            for intent_no, intended in enumerate((left, right)):
                marker = f"The {left} alerted the {right} {connector} it({intended}) {state}."
                careful = f"The {left} alerted the {right} {connector} {intended} {state}."
                entity_options = [left, right, "neither named entity"]
                yes_no = ["yes", "no", "cannot tell"]
                rows.append({
                    "id": f"pronoun-{tag}-{context_no:03d}-{intent_no + 1}",
                    "context_id": f"pronoun-{tag}-context-{context_no:03d}",
                    "intended_antecedent_position": intent_no + 1,
                    "arms": {
                        "ainglish": wrap(reference, marker),
                        "bare_english": wrap(reference, bare),
                        "careful_english": wrap(reference, careful),
                    },
                    "questions": [
                        {
                            "id": "antecedent",
                            "question": f"Which named entity is described as having {state}?",
                            "options": rotate_to(entity_options, intended, (context_no + intent_no) % 3),
                            "answer": intended,
                        },
                        {
                            "id": "licensed_followup",
                            "question": f"Which named entity is the direct target of the {action}?",
                            "options": rotate_to(entity_options, intended, (context_no + intent_no + 1) % 3),
                            "answer": intended,
                        },
                        {
                            "id": "causal_overread",
                            "question": "Does the pronoun marker itself assert that one named entity caused the other's state?",
                            "options": rotate_to(yes_no, "no", (context_no + intent_no + 2) % 3),
                            "answer": "no",
                        },
                    ],
                    "strata": {
                        "condition": condition,
                        "domain": f"{left_kind}-{right_kind}",
                        "connective": connector,
                        "antecedent_position": intent_no + 1,
                        "distance_cycle": cycle + 1,
                    },
                })
    assert context_no == 80 and len(rows) == 160
    packet = {
        "kind": "dexagon.ainglish.pronoun-referent-comprehension-items.v1",
        "proposal_slug": "it-ref",
        "condition": condition,
        "reference_card": reference,
        "reference_sha256": hashlib.sha256(reference.encode()).hexdigest() if reference else None,
        "contract": {
            "metric": "comprehension_accuracy_delta",
            "primary": "exact joint antecedent and licensed-followup recovery",
            "support": "each antecedent position: Ainglish minus bare >= 0.20 and Ainglish minus careful >= -0.05",
            "vetoes": [
                "either antecedent position fails separately",
                "unresolved references are guessed",
                "causality, responsibility, identity, ownership, or truth is licensed by the marker",
                "calibration or two-independent-lineage gate fails",
            ],
            "reporting": "per arm, antecedent position, domain, connective, distance cycle, question, and reader lineage",
        },
        "scientific_rows": rows,
        "calibration_rows": calibration_rows(f"pronoun-{condition}"),
        "model_calls": 0,
        "governance_writes": 0,
    }
    packet["content_sha256"] = digest(packet)
    return packet


NEGATION_POPULATIONS = {
    "zero_shot": [
        ("replicas", "healthy"), ("checks", "successful"), ("files", "current"),
        ("workers", "available"), ("regions", "reachable"), ("recipients", "eligible"),
        ("sensors", "calibrated"), ("routes", "open"), ("valves", "sealed"),
        ("samples", "usable"),
    ],
    "definition_conditioned": [
        ("nodes", "responsive"), ("ballots", "valid"), ("permits", "active"),
        ("parcels", "labelled"), ("channels", "encrypted"), ("records", "signed"),
        ("vehicles", "charged"), ("stations", "staffed"), ("alerts", "acknowledged"),
        ("batches", "sterile"),
    ],
}


def negation_packet(condition: str) -> dict:
    reference = None if condition == "zero_shot" else NEGATION_REFERENCE
    rows = []
    context_no = 0
    interval_options = ["exactly zero", "zero through N-1", "one through N-1"]
    yes_no = ["yes", "no", "cannot tell"]
    for cycle in range(8):
        for domain_no, (set_kind, predicate) in enumerate(NEGATION_POPULATIONS[condition]):
            context_no += 1
            tag = "z" if condition == "zero_shot" else "d"
            set_id = f"{set_kind}-{tag}{cycle + 1:02d}"
            size = 2 + ((cycle + domain_no) % 7)
            preamble = f"The fixed set {set_id} contains exactly {size} members."
            bare = f"{preamble} All members of {set_id} are not {predicate}."
            for form_no, form in enumerate(("none-of", "not-all-of")):
                if form == "none-of":
                    marker = f"{preamble} none-of({set_id}): {predicate}."
                    careful = f"{preamble} No member of {set_id} is {predicate}."
                    interval = "exactly zero"
                    one_compatible = "no"
                else:
                    marker = f"{preamble} not-all-of({set_id}): {predicate}."
                    careful = f"{preamble} At least one member of {set_id} is not {predicate}."
                    interval = "zero through N-1"
                    one_compatible = "yes"
                questions = [
                    ("interval", "Which satisfying-count range does the sentence assert?", interval_options, interval),
                    ("one_satisfier", "Is a world with exactly one satisfying member compatible?", yes_no, one_compatible),
                    ("zero_satisfiers", "Is a world with zero satisfying members compatible?", yes_no, "yes"),
                    ("all_satisfy", "Is a world in which all N members satisfy the predicate compatible?", yes_no, "no"),
                    ("population_overread", "Does the marker itself establish that this set is the whole population?", yes_no, "no"),
                ]
                qrows = []
                for q_no, (qid, question, options, answer) in enumerate(questions):
                    qrows.append({
                        "id": qid,
                        "question": question,
                        "options": rotate_to(list(options), answer, (context_no + form_no + q_no) % 3),
                        "answer": answer,
                    })
                rows.append({
                    "id": f"negation-{tag}-{context_no:03d}-{form_no + 1}",
                    "context_id": f"negation-{tag}-context-{context_no:03d}",
                    "form": form,
                    "set_size": size,
                    "arms": {
                        "ainglish": wrap(reference, marker),
                        "bare_english": wrap(reference, bare),
                        "careful_english": wrap(reference, careful),
                    },
                    "questions": qrows,
                    "strata": {
                        "condition": condition,
                        "domain": set_kind,
                        "predicate": predicate,
                        "form": form,
                        "set_size": size,
                        "bare_template": "all-members-are-not",
                    },
                })
    assert context_no == 80 and len(rows) == 160
    packet = {
        "kind": "dexagon.ainglish.universal-negation-comprehension-items.v1",
        "proposal_slug": "none-of-s-predicate-not-all-of-s-predicate",
        "condition": condition,
        "reference_card": reference,
        "reference_sha256": hashlib.sha256(reference.encode()).hexdigest() if reference else None,
        "contract": {
            "metric": "comprehension_accuracy_delta",
            "primary": "exact recovery of the asserted satisfying-count interval",
            "support": "each form: Ainglish minus bare >= 0.20 and Ainglish minus careful >= -0.05",
            "vetoes": [
                "not-all-of is read as requiring one or more satisfying members",
                "none-of permits a satisfying member",
                "the marker invents whole-population coverage",
                "empty or unresolved sets receive a vacuous answer",
                "calibration or two-independent-lineage gate fails",
            ],
            "reporting": "per form, arm, set size, domain, predicate, question, and reader lineage",
        },
        "scientific_rows": rows,
        "calibration_rows": calibration_rows(f"negation-{condition}"),
        "model_calls": 0,
        "governance_writes": 0,
    }
    packet["content_sha256"] = digest(packet)
    return packet


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert {row["stage"] for row in snapshot["proposals"]} <= {"proposed", "seconded"}
    packets = {
        "pronoun-zero-shot.json": pronoun_packet("zero_shot"),
        "pronoun-definition-conditioned.json": pronoun_packet("definition_conditioned"),
        "negation-zero-shot.json": negation_packet("zero_shot"),
        "negation-definition-conditioned.json": negation_packet("definition_conditioned"),
    }
    for name, packet in packets.items():
        (ROOT / name).write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.new-language-comprehension-carrier-index.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "packets": [
            {
                "file": name,
                "proposal_slug": packet["proposal_slug"],
                "condition": packet["condition"],
                "scientific_rows": len(packet["scientific_rows"]),
                "calibration_rows": len(packet["calibration_rows"]),
                "content_sha256": packet["content_sha256"],
            }
            for name, packet in packets.items()
        ],
        "scientific_rows": sum(len(packet["scientific_rows"]) for packet in packets.values()),
        "calibration_rows": sum(len(packet["calibration_rows"]) for packet in packets.values()),
        "model_calls": 0,
        "governance_writes": 0,
    }
    index["content_sha256"] = digest(index)
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scientific_rows": index["scientific_rows"], "calibration_rows": index["calibration_rows"], "content_sha256": index["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

