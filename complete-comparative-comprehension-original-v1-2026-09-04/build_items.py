#!/usr/bin/env python3
"""Build 96 role-ambiguity frames, two independent probes per frame, without model calls."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NAMES = [
    ("Mira", "Jonah", "Priya"), ("Nadia", "Oren", "Luca"),
    ("Tessa", "Malik", "Rina"), ("Hana", "Dario", "Sofia"),
    ("Inez", "Caleb", "Mei"), ("Leila", "Anton", "Zara"),
    ("Noor", "Emil", "Aya"), ("Sana", "Theo", "Kira"),
    ("Anya", "Ravi", "Marta"), ("Elena", "Basil", "Niko"),
    ("Cora", "Yusuf", "Alina"), ("Freya", "Omar", "Lena"),
    ("Dina", "Hugo", "Mina"), ("Kaia", "Pavel", "Nora"),
    ("Amira", "Felix", "Yara"), ("Lila", "Mateo", "Rosa"),
]
HUMAN_VERBS = [
    "praised", "consulted", "challenged", "trusted", "contacted", "supported", "criticized", "recommended",
    "questioned", "thanked", "briefed", "observed", "mentored", "interviewed", "assisted", "encouraged",
]
TECH_NOUNS = [
    ("operator Mira", "service Atlas", "operator Jonah", "service Boreal"),
    ("engineer Nadia", "cluster Cedar", "engineer Oren", "cluster Delta"),
    ("analyst Tessa", "server Ember", "analyst Malik", "server Fjord"),
    ("reviewer Hana", "gateway Grove", "reviewer Dario", "gateway Harbor"),
    ("maintainer Inez", "node Iris", "maintainer Caleb", "node Jade"),
    ("controller Leila", "router Kite", "controller Anton", "router Lunar"),
    ("auditor Noor", "database Maple", "auditor Emil", "database Nimbus"),
    ("planner Sana", "cache Opal", "planner Theo", "cache Pine"),
    ("tester Anya", "device Quartz", "tester Ravi", "device Rowan"),
    ("curator Elena", "archive Sable", "curator Basil", "archive Tide"),
    ("inspector Cora", "sensor Umber", "inspector Yusuf", "sensor Vale"),
    ("trainer Freya", "model Willow", "trainer Omar", "model Xenon"),
    ("dispatcher Dina", "queue Yarrow", "dispatcher Hugo", "queue Zenith"),
    ("editor Kaia", "controller Amber", "editor Pavel", "controller Bronze"),
    ("monitor Amira", "process Copper", "monitor Felix", "process Denim"),
    ("builder Lila", "adapter Elm", "builder Mateo", "adapter Flint"),
]


def rotate(options: list[str], amount: int) -> list[str]:
    amount %= len(options)
    return options[amount:] + options[:amount]


def live_surface(index: int, form: str, role: str, site: str) -> tuple[str, str, str, str]:
    actor, target, rival = NAMES[index]
    verb = HUMAN_VERBS[index]
    if site == "direct-object":
        bare = f"{actor} {verb} {target} more often than {rival}."
        doer = f"{actor} {verb} {target} more often than {rival} did."
        done_to = f"{actor} {verb} {target} more often than {actor} {verb} {rival}."
        full_doer = f"{actor} {verb} {target} more often than {rival} {verb} {target}."
        full_done = done_to
        doer_answer = f"{actor}'s action toward {target} exceeded {rival}'s action toward {target}"
        done_answer = f"{actor}'s action toward {target} exceeded {actor}'s action toward {rival}"
    elif site == "kept-preposition":
        bare = f"{actor} worked with {target} more often than {rival}."
        doer = f"{actor} worked with {target} more often than {rival} did."
        done_to = f"{actor} worked with {target} more often than with {rival}."
        full_doer = f"{actor} worked with {target} more often than {rival} worked with {target}."
        full_done = f"{actor} worked with {target} more often than {actor} worked with {rival}."
        doer_answer = f"{actor}'s work with {target} was more frequent than {rival}'s work with {target}"
        done_answer = f"{actor}'s work with {target} was more frequent than {actor}'s work with {rival}"
    else:
        bare = f"{target} was more helpful to {actor} than {rival}."
        doer = f"{target} was more helpful to {actor} than {rival} was."
        done_to = f"{target} was more helpful to {actor} than to {rival}."
        full_doer = f"{target} was more helpful to {actor} than {rival} was helpful to {actor}."
        full_done = f"{target} was more helpful to {actor} than {target} was helpful to {rival}."
        doer_answer = f"{target}'s helpfulness to {actor} exceeded {rival}'s helpfulness to {actor}"
        done_answer = f"{target}'s helpfulness to {actor} exceeded {target}'s helpfulness to {rival}"
    marked = doer if form == "doer-completed" else done_to
    if form == "full-rival-clause":
        marked = full_doer if role == "rival-doer" else full_done
    return bare, marked, doer_answer, done_answer


def clash_surface(index: int, form: str, role: str, site: str) -> tuple[str, str, str, str]:
    person, first_object, other_person, other_object = TECH_NOUNS[index]
    # The rival's semantic type forces the intended role in the bare arm: a person can act but is
    # not a deployable object; an object can be acted on but cannot itself perform the action.
    rival = other_person if role == "rival-doer" else other_object
    if site == "direct-object":
        bare = f"{person} rebooted {first_object} more often than {rival}."
        doer = f"{person} rebooted {first_object} more often than {rival} did."
        done_to = f"{person} rebooted {first_object} more often than {person} rebooted {rival}."
        full_doer = f"{person} rebooted {first_object} more often than {rival} rebooted {first_object}."
        full_done = done_to
        doer_answer = f"{person}'s reboots of {first_object} exceeded {rival}'s reboots of {first_object}"
        done_answer = f"{person}'s reboots of {first_object} exceeded {person}'s reboots of {rival}"
    elif site == "kept-preposition":
        bare = f"{person} deployed code to {first_object} more often than {rival}."
        doer = f"{person} deployed code to {first_object} more often than {rival} did."
        done_to = f"{person} deployed code to {first_object} more often than to {rival}."
        full_doer = f"{person} deployed code to {first_object} more often than {rival} deployed code to {first_object}."
        full_done = f"{person} deployed code to {first_object} more often than {person} deployed code to {rival}."
        doer_answer = f"{person}'s deployments to {first_object} exceeded {rival}'s deployments to {first_object}"
        done_answer = f"{person}'s deployments to {first_object} exceeded {person}'s deployments to {rival}"
    else:
        bare = f"{first_object} was more useful to {person} than {rival}."
        doer = f"{first_object} was more useful to {person} than {rival} was."
        done_to = f"{first_object} was more useful to {person} than to {rival}."
        full_doer = f"{first_object} was more useful to {person} than {rival} was useful to {person}."
        full_done = f"{first_object} was more useful to {person} than {first_object} was useful to {rival}."
        doer_answer = f"{first_object}'s usefulness to {person} exceeded {rival}'s usefulness to {person}"
        done_answer = f"{first_object}'s usefulness to {person} exceeded {first_object}'s usefulness to {rival}"
    marked = doer if form == "doer-completed" else done_to
    if form == "full-rival-clause":
        marked = full_doer if role == "rival-doer" else full_done
    return bare, marked, doer_answer, done_answer


def scientific_items() -> list[dict]:
    rows = []
    sites = ["direct-object", "kept-preposition", "adjective-complement"]
    strata = [
        ("doer-live", "doer-completed", "type-live"),
        ("doer-clash", "doer-completed", "type-clash"),
        ("done-to-live", "done-to-completed", "type-live"),
        ("done-to-clash", "done-to-completed", "type-clash"),
        ("full-live", "full-rival-clause", "type-live"),
        ("full-clash", "full-rival-clause", "type-clash"),
    ]
    for stratum_index, (stratum, form, context_type) in enumerate(strata):
        for index in range(16):
            role = (
                "rival-doer" if form == "doer-completed" else
                "rival-done-to" if form == "done-to-completed" else
                ("rival-doer" if index % 2 == 0 else "rival-done-to")
            )
            eligible_sites = sites if context_type == "type-live" else sites[:2]
            site = eligible_sites[(index + stratum_index) % len(eligible_sites)]
            surface = live_surface(index, form, role, site) if context_type == "type-live" else clash_surface(index, form, role, site)
            bare, marked, doer_answer, done_answer = surface
            correct_role = doer_answer if role == "rival-doer" else done_answer
            other_role = done_answer if role == "rival-doer" else doer_answer
            role_options = rotate([correct_role, other_role, "the message does not determine either comparison"], index + stratum_index)
            common = {
                "english": bare,
                "ainglish": marked,
                "settlement_stratum": stratum,
                "form": form,
                "context_type": context_type,
                "role_site": site,
                "intended_role": role,
            }
            rows.append({
                **common,
                "id": f"{stratum}-{index + 1:02d}-role",
                "probe": "role-recovery",
                "question": "Which comparison does the message assert?",
                "options": role_options,
                "answer": correct_role,
            })
            overread_options = rotate(["yes", "no", "not determined"], index + stratum_index + 1)
            rows.append({
                **common,
                "id": f"{stratum}-{index + 1:02d}-level",
                "probe": "rival-level-overread",
                "question": "Was the rival comparison level above zero?",
                "options": overread_options,
                "answer": "not determined",
            })
    return rows


def calibration_items() -> list[dict]:
    subjects = [
        ("the amber worker", "the violet worker", "processed the last batch"),
        ("Mira", "Jonah", "holds the recovery key"),
        ("queue Cedar", "queue Delta", "received the final task"),
        ("node East", "node West", "passed the integrity check"),
        ("the first reviewer", "the second reviewer", "approved the change"),
        ("route North", "route South", "carried the packet"),
        ("archive A", "archive B", "contains the signed record"),
        ("service Red", "service Blue", "handled the request"),
        ("team Lake", "team Hill", "owns the incident"),
        ("sensor Pine", "sensor Oak", "raised the alert"),
        ("agent K", "agent L", "filed the report"),
        ("build 41", "build 42", "is the release candidate"),
        ("room Aspen", "room Birch", "is reserved now"),
        ("model Jade", "model Quartz", "produced the output"),
        ("record 17", "record 18", "is authoritative"),
        ("adapter M", "adapter N", "is active"),
    ]
    rows = []
    for index, (answer, other, predicate) in enumerate(subjects, 1):
        options = rotate([answer, other, "cannot tell"], index)
        rows.append({
            "id": f"control-{index:02d}",
            "english": f"Either {answer} or {other} {predicate}.",
            "ainglish": f"{answer}, not {other}, {predicate}.",
            "question": f"Which one {predicate}?",
            "options": options,
            "answer": answer,
            "calibration": True,
            "calibration_scope": "target-independent",
        })
    return rows


def main() -> None:
    scientific = scientific_items()
    calibration = calibration_items()
    rows = scientific + calibration
    assert len(scientific) == 192 and len(calibration) == 16
    assert len({row["id"] for row in rows}) == len(rows)
    counts = {}
    for row in scientific:
        counts[row["settlement_stratum"]] = counts.get(row["settlement_stratum"], 0) + 1
    assert set(counts.values()) == {32}
    assert sum(row["probe"] == "role-recovery" for row in scientific) == 96
    assert sum(row["probe"] == "rival-level-overread" for row in scientific) == 96
    output = ROOT / "items.json"
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    role_output = ROOT / "role-items.json"
    role_rows = [row for row in scientific if row["probe"] == "role-recovery"] + calibration
    role_output.write_text(json.dumps(role_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    overread_output = ROOT / "overread-items.json"
    overread_rows = [row for row in scientific if row["probe"] == "rival-level-overread"] + calibration
    overread_output.write_text(json.dumps(overread_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.complete-comparative-carrier-index.v1",
        "scientific_items": 192,
        "frames": 96,
        "calibration_items": 16,
        "settlement_strata": counts,
        "items_sha256": sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "role_items_sha256": sha256(json.dumps(role_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "overread_items_sha256": sha256(json.dumps(overread_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "model_calls": 0,
    }
    index["content_sha256"] = sha256(json.dumps(index, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
