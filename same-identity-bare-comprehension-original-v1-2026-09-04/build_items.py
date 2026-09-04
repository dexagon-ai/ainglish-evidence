#!/usr/bin/env python3
"""Build a fresh marked-versus-bare-same comprehension carrier without reader calls."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NAMES = [
    ("Asha", "Ben"), ("Celine", "Dev"), ("Evan", "Fara"), ("Gita", "Hale"),
    ("Isla", "Joon"), ("Kemi", "Luis"), ("Mara", "Ned"), ("Opal", "Pia"),
    ("Quin", "Rafi"), ("Suri", "Tao"), ("Uma", "Vera"), ("Wren", "Xavi"),
    ("Yuki", "Zane"), ("Ada", "Bran"), ("Cleo", "Deni"), ("Esra", "Finn"),
]
NOUNS = [
    "recovery plan", "deployment board", "incident graph", "release ledger",
    "routing model", "review workbook", "inventory map", "decision record",
    "service schedule", "risk notebook", "maintenance chart", "contact register",
    "audit journal", "capacity table", "change log", "handoff checklist",
]
KIND_OBJECTS = [
    ("configuration bundle", "normalized-field comparison", "09:25 UTC"),
    ("policy package", "semantic-clause comparison", "revision 31"),
    ("database image", "row-and-column digest", "Wednesday noon"),
    ("API contract", "normalized-schema diff", "build 904"),
    ("routing graph", "ordered-edge comparison", "16:40 UTC"),
    ("translation catalogue", "key-value digest", "release 27"),
    ("permission profile", "effective-rights comparison", "deployment 12"),
    ("feature manifest", "enabled-flag comparison", "checkpoint 14"),
    ("workflow plan", "normalized-step diff", "commit 9bd"),
    ("price catalogue", "currency-and-value check", "4 September"),
    ("alert registry", "identifier-and-severity diff", "07:15 UTC"),
    ("retention policy", "period-and-scope comparison", "review 16"),
    ("parser table", "production-rule digest", "candidate 8"),
    ("access matrix", "principal-permission comparison", "01:00 UTC"),
    ("build record", "dependency-version diff", "pipeline 812"),
    ("localization bundle", "message-key comparison", "language freeze 5"),
]
NAME_OBJECTS = [
    "backup set", "release artifact", "customer extract", "settings file",
    "operations guide", "model snapshot", "database export", "policy memo",
    "container artifact", "migration program", "test summary", "invoice group",
    "signature record", "schema archive", "training segment", "incident exhibit",
]


def rotate(options: list[str], amount: int) -> list[str]:
    amount %= len(options)
    return options[amount:] + options[:amount]


def scientific_items() -> list[dict]:
    rows = []
    relation_options = [
        "one shared object",
        "separate objects verified equal under the named check at the named moment",
        "only the object names are known to match",
    ]
    for index, ((left, right), noun) in enumerate(zip(NAMES, NOUNS, strict=True), 1):
        bare = f"{left} and {right} edit the same {noun}."
        marked = f"{left} and {right} edit the same-one {noun}."
        common = {"english": bare, "ainglish": marked, "settlement_stratum": "same-one", "form": "same-one"}
        rows.append({
            **common, "id": f"one-{index:02d}-propagation", "probe": "propagation",
            "question": f"After {left} changes the {noun}, has the {noun} {right} reaches changed too?",
            "options": rotate(["yes", "no", "not determined"], index), "answer": "yes",
        })
        rows.append({
            **common, "id": f"one-{index:02d}-relation", "probe": "relation-basis",
            "question": "Which relationship does the message assert?",
            "options": rotate(relation_options, index + 1), "answer": relation_options[0],
        })

    for index, (noun, check, moment) in enumerate(KIND_OBJECTS, 1):
        bare = f"Site East and site West have the same {noun}."
        marked = f"Site East has a same-kind {noun} to site West's ({check}, as of {moment})."
        common = {"english": bare, "ainglish": marked, "settlement_stratum": "same-kind", "form": "same-kind"}
        rows.append({
            **common, "id": f"kind-{index:02d}-propagation", "probe": "propagation",
            "question": f"If East changes its {noun} after {moment}, must West's {noun} change too?",
            "options": rotate(["yes", "no", "not determined"], index + 2), "answer": "no",
        })
        if index in {1, 5, 9, 13}:
            rows.append({
                **common, "id": f"kind-{index:02d}-laundering", "probe": "relation-laundering",
                "question": "Does the named comparison establish that the two objects are byte-for-byte equal?",
                "options": rotate(["yes", "no", "not determined"], index), "answer": "no",
            })
        else:
            named_relation = f"separate objects verified equal by {check} at {moment}"
            options = ["one shared object", named_relation, "only the object names are known to match"]
            rows.append({
                **common, "id": f"kind-{index:02d}-relation", "probe": "relation-basis",
                "question": "Which relationship does the message assert?",
                "options": rotate(options, index + 1), "answer": named_relation,
            })

    for index, ((left, right), noun) in enumerate(zip(NAMES, NAME_OBJECTS, strict=True), 1):
        bare = f"Store {left} and store {right} have the same {noun}."
        marked = f"Store {left} and store {right} have a same-name {noun}."
        common = {"english": bare, "ainglish": marked, "settlement_stratum": "same-name", "form": "same-name"}
        rows.append({
            **common, "id": f"name-{index:02d}-equality", "probe": "content-equality",
            "question": f"Does the message establish that the two {noun}s have equal contents?",
            "options": rotate(["yes", "no", "not determined"], index + 1), "answer": "no",
        })
        rows.append({
            **common, "id": f"name-{index:02d}-relation", "probe": "relation-basis",
            "question": "Which relationship does the message assert?",
            "options": rotate(relation_options, index + 2), "answer": relation_options[2],
        })
    return rows


def calibration_items() -> list[dict]:
    controls = [
        ("Ari", "Bela", "owns the vault key"), ("the copper worker", "the silver worker", "closed the batch"),
        ("queue Fern", "queue Moss", "received the last job"), ("node Lake", "node Ridge", "passed the check"),
        ("reviewer One", "reviewer Two", "approved the patch"), ("route East", "route West", "carried the packet"),
        ("archive Red", "archive Blue", "holds the signed page"), ("service Dawn", "service Dusk", "handled the call"),
        ("team Elm", "team Ash", "owns the incident"), ("sensor Rain", "sensor Snow", "raised the warning"),
        ("agent P", "agent Q", "filed the note"), ("build 71", "build 72", "is the candidate"),
        ("room Lily", "room Rose", "is reserved"), ("model Sun", "model Moon", "produced the result"),
        ("record 27", "record 28", "is authoritative"), ("adapter C", "adapter D", "is active"),
    ]
    rows = []
    for index, (answer, other, predicate) in enumerate(controls, 1):
        rows.append({
            "id": f"control-{index:02d}",
            "english": f"Either {answer} or {other} {predicate}.",
            "ainglish": f"{answer}, not {other}, {predicate}.",
            "question": f"Which one {predicate}?",
            "options": rotate([answer, other, "cannot tell"], index),
            "answer": answer,
            "calibration": True,
            "calibration_scope": "target-independent",
        })
    return rows


def main() -> None:
    scientific = scientific_items()
    calibration = calibration_items()
    rows = scientific + calibration
    assert len(scientific) == 96 and len(calibration) == 16
    assert len({row["id"] for row in rows}) == len(rows)
    assert len({(row["english"], row["ainglish"]) for row in scientific}) == 48
    counts = {}
    for row in scientific:
        counts[row["settlement_stratum"]] = counts.get(row["settlement_stratum"], 0) + 1
    assert counts == {"same-one": 32, "same-kind": 32, "same-name": 32}
    output = ROOT / "items.json"
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    index = {
        "kind": "dexagon.ainglish.same-identity-bare-carrier-index.v1",
        "scientific_items": 96,
        "frames": 48,
        "calibration_items": 16,
        "settlement_strata": counts,
        "items_sha256": digest,
        "model_calls": 0,
    }
    index["content_sha256"] = sha256(json.dumps(index, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
