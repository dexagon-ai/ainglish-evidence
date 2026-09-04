#!/usr/bin/env python3
"""Build four fresh aggregate-only comprehension replication carriers."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def rotate(answer: str, distractors: list[str], index: int) -> list[str]:
    values = [answer, *distractors]
    assert len(values) == 4 and len(set(values)) == 4
    offset = index % 4
    return values[offset:] + values[:offset]


def calibration(prefix: str) -> list[dict]:
    objects = [
        ("acorn ticket", "bay 17"), ("bronze tag", "shelf 24"),
        ("cerulean folder", "rack 31"), ("driftwood key", "bay 42"),
        ("egret card", "shelf 53"), ("fallow token", "rack 64"),
        ("ginger seal", "bay 75"), ("heather note", "shelf 86"),
        ("ivory disk", "rack 97"), ("juniper pass", "bay 108"),
        ("khaki badge", "shelf 119"), ("lilac slip", "rack 120"),
        ("marble token", "bay 131"), ("navy seal", "shelf 142"),
        ("opal card", "rack 153"), ("poppy key", "bay 164"),
    ]
    rows = []
    for index, (thing, place) in enumerate(objects):
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The register mentions the {thing}, but gives no storage location.",
            "ainglish": f"The register says the {thing} is stored in {place}.",
            "question": f"Where does the message say the {thing} is stored?",
            "options": rotate(place, ["the intake room", "the dispatch room", "no location is stated"], index),
            "answer": place,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def group_scope() -> list[dict]:
    domains = [
        ("regions", "conversion rate", "rollout"), ("clinics", "recovery rate", "treatment"),
        ("models", "accuracy", "deployment"), ("queues", "failure rate", "capacity change"),
        ("schools", "attendance rate", "programme"), ("warehouses", "damage rate", "supplier"),
        ("teams", "completion rate", "workflow"), ("devices", "latency", "firmware"),
        ("districts", "employment rate", "policy"), ("auditors", "agreement rate", "method"),
        ("batches", "defect rate", "release"), ("routes", "delivery rate", "carrier"),
    ]
    rows = []
    for case in range(8):
        for d, (groups, metric, action) in enumerate(domains):
            ref = f"{groups}-set-{case + 41}-{d + 3}"
            threshold = 55 + ((case * 7 + d * 3) % 35)
            index = len(rows)
            answer = "No; the statement requires the threshold to hold separately in every named group"
            rows.append({
                "id": f"group-each-{case + 1:02d}-{d + 1:02d}",
                "english": f"Using membership revision {ref}, the {metric} exceeds {threshold}% in every named {groups[:-1]}, with each one assessed separately under the same rule and window.",
                "ainglish": f"each-group({ref}): {metric}>{threshold}% under the declared rule and window.",
                "question": f"Could one named {groups[:-1]} be at or below {threshold}% without contradicting this message?",
                "options": rotate(answer, [
                    "Yes; only the pooled observations must exceed the threshold",
                    "Yes; the message requires equal effect sizes but not threshold passage",
                    "The message does not identify which group set is in scope",
                ], index),
                "answer": answer,
                "form": "each-group",
                "probe": "member-level entailment",
            })
            index = len(rows)
            answer = "Yes; the combined result can exceed the threshold even when one named group does not"
            rows.append({
                "id": f"group-combined-{case + 1:02d}-{d + 1:02d}",
                "english": f"Using membership revision {ref}, after the observations from all named {groups} are combined under the declared weighting and denominator, the pooled {metric} exceeds {threshold}%; no member-level result is asserted.",
                "ainglish": f"groups-combined({ref}): {metric}>{threshold}% under the declared weighting, denominator, and window.",
                "question": f"Could one named {groups[:-1]} be at or below {threshold}% without contradicting this message?",
                "options": rotate(answer, [
                    "No; every named group must separately exceed the threshold",
                    "No; the message asserts equal effect sizes in every group",
                    "The message does not identify which group set is in scope",
                ], index),
                "answer": answer,
                "form": "groups-combined",
                "probe": "aggregate-only entailment",
            })
    assert len(rows) == 192
    return rows + calibration("group-scope")


def difference_scope() -> list[dict]:
    domains = [
        ("validators", "artifact", "checksum"), ("editors", "draft", "revision-id"),
        ("labs", "sensor", "serial-number"), ("agents", "dataset", "dataset-id"),
        ("branches", "package", "build-hash"), ("regions", "supplier", "company-id"),
        ("reviewers", "model", "model-id"), ("workers", "mirror", "snapshot-id"),
        ("auditors", "ledger", "ledger-hash"), ("teams", "route", "route-id"),
    ]
    rows = []
    for case in range(8):
        for d, (actors, item, key) in enumerate(domains):
            ref = f"reference-{item}-{case + 61}-{d + 5}"
            group = f"{actors}-group-{case + 71}-{d + 7}"
            index = len(rows)
            answer = "Two group members may choose the same non-reference key"
            rows.append({
                "id": f"difference-ref-{case + 1:02d}-{d + 1:02d}",
                "english": f"Every {item} selected by members of {group} must have a {key} unequal to {ref}'s {key}; members are allowed to repeat the same qualifying {item}.",
                "ainglish": f"select({group}, {item}) different-from({ref}, by={key}).",
                "question": "Which assignment is permitted by the message?",
                "options": rotate(answer, [
                    "A member may choose the reference key",
                    "Every member must choose a pairwise-unique key",
                    "A different display name is sufficient even when the declared key matches",
                ], index),
                "answer": answer,
                "form": "different-from",
                "probe": "reference exclusion without pairwise uniqueness",
            })
            index = len(rows)
            answer = "One member may match the external reference if all group members remain pairwise different"
            rows.append({
                "id": f"difference-across-{case + 1:02d}-{d + 1:02d}",
                "english": f"The {item}s selected for distinct members of {group} must have pairwise-unequal {key}s; matching the external {ref}'s {key} is allowed.",
                "ainglish": f"select({group}, {item}) different-across({group}, by={key}); external-ref={ref}.",
                "question": "Which assignment is permitted by the message?",
                "options": rotate(answer, [
                    "Two group members may use the same key",
                    "All group members may repeat one non-reference key",
                    "Different display names are sufficient when declared keys match",
                ], index),
                "answer": answer,
                "form": "different-across",
                "probe": "pairwise uniqueness without reference exclusion",
            })
    assert len(rows) == 160
    return rows + calibration("difference-scope")


def proposal_decision() -> list[dict]:
    domains = [
        ("Ari", "route L", "change board"), ("Bela", "vendor M", "procurement panel"),
        ("Cato", "patch N", "release manager"), ("Dina", "date P", "programme chair"),
        ("Eli", "model Q", "safety lead"), ("Fara", "budget R", "finance committee"),
        ("Gita", "site S", "operations director"), ("Hugo", "policy T", "governance council"),
        ("Inez", "design U", "architecture group"), ("Jori", "dataset V", "research lead"),
        ("Kira", "supplier W", "contract owner"), ("Lio", "workflow X", "service board"),
    ]
    rows = []
    for case in range(8):
        for d, (actor, option, authority) in enumerate(domains):
            ref = f"record-{case + 81}-{d + 9}"
            index = len(rows)
            answer = "It records an offered option, not an operative selection"
            rows.append({
                "id": f"proposal-by-{case + 1:02d}-{d + 1:02d}",
                "english": f"In {ref}, {actor} offered {option} for consideration; nobody is reported to have operatively selected it.",
                "ainglish": f"proposal-by({actor}): {option}; record={ref}.",
                "question": "What status for the option does this sentence itself establish?",
                "options": rotate(answer, [
                    f"It is the operative choice of the {authority}",
                    "It commands the reader to implement the option",
                    "It grants permission to implement the option",
                ], index),
                "answer": answer,
                "form": "proposal-by",
                "probe": "offer versus selection",
            })
            index = len(rows)
            answer = f"It records {option} as operatively selected by the {authority}"
            rows.append({
                "id": f"decision-by-{case + 1:02d}-{d + 1:02d}",
                "english": f"In {ref}, the {authority} operatively selected {option}; the sentence reports that choice but does not itself command or grant permission.",
                "ainglish": f"decision-by({authority}): {option}; record={ref}.",
                "question": "What status for the option does this sentence itself establish?",
                "options": rotate(answer, [
                    f"It is only an option offered by {actor}",
                    "It commands the reader to implement the option",
                    "It grants permission to implement the option",
                ], index),
                "answer": answer,
                "form": "decision-by",
                "probe": "selection without force laundering",
            })
    assert len(rows) == 192
    return rows + calibration("proposal-decision")


def preference_release() -> list[dict]:
    actions = [
        "attach the diagnostic log", "join the optional call", "add a second diagram",
        "bring a dessert", "run the extended benchmark", "copy the archive locally",
        "write an extra summary", "reserve the larger room", "include the raw transcript",
        "send a paper copy",
    ]
    relations = ["peer", "superior", "subordinate", "peer", "superior"]
    forms = [
        ("rather-not", "the action was omitted", "Yes; omission matches the sender's stated preference"),
        ("fine-either-way", "the action was completed", "Yes; completion is acceptable and no preference is stated"),
        ("would-welcome", "the action was completed", "Yes; completion matches the sender's stated preference"),
    ]
    rows = []
    for f, (form, outcome, answer) in enumerate(forms):
        for index in range(50):
            action = actions[index % len(actions)]
            relation = relations[index % len(relations)]
            # The same bare byte string is crossed with all three hidden intentions. A
            # preferred default cannot therefore score all three worlds correctly.
            release = f"You do not need to {action} for request {index + 101}."
            marked = release[:-1] + f", {form}."
            row_index = len(rows)
            rows.append({
                "id": f"preference-{form}-{index + 1:02d}",
                "english": release,
                "ainglish": marked,
                "question": f"The receiver knows only this message and {outcome}. Did the outcome match what the sender wanted?",
                "options": rotate(answer, [
                    "No; the outcome conflicts with the sender's stated preference",
                    "Cannot tell from the message whether the outcome matched what the sender wanted",
                    "The message made the optional action obligatory",
                ], row_index),
                "answer": answer,
                "form": form,
                "probe": "preference recovery from a balanced bare release",
                "power_relation": relation,
            })
    assert len(rows) == 150
    return rows + calibration("preference-release")


def write(name: str, public_id: str, slug: str, construct: str, target: str,
          comparator: dict, items: list[dict]) -> dict:
    payload = {
        "kind": "dexagon.ainglish.dispute-settlement-carrier.v1",
        "proposal_public_id": public_id,
        "proposal_revision": slug,
        "construct": construct,
        "replicates_hash": target,
        "comparator": comparator,
        "items": items,
        "reader_calls": 0,
    }
    path = ROOT / f"{name}.items.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    science = [row for row in items if not row.get("calibration")]
    return {
        "name": name,
        "public_id": public_id,
        "slug": slug,
        "construct": construct,
        "replicates_hash": target,
        "comparator": comparator,
        "file": path.name,
        "items_sha256": sha256(canonical(items)).hexdigest(),
        "scientific_items": len(science),
        "calibration_items": len(items) - len(science),
        "forms": dict(sorted(Counter(row["form"] for row in science).items())),
        "probes": dict(sorted(Counter(row["probe"] for row in science).items())),
    }


def main() -> None:
    careful = {"kind": "complete-careful-english-v1"}
    campaigns = [
        write("group-scope", "a-4fsc7etzs8ctsjwp", "each-group-group-set-ref-clause-groups-combined-group-set", "each-group / groups-combined", "92d85061748d813965520e6be3f6e57e1c8549fe65d98f2407f86c94b565e293", careful, group_scope()),
        write("difference-scope", "a-f9x2xwcjxp01xhtd", "different-from-ref-by-key-different-across-group-by-key", "different-from / different-across", "15bb5a3cc90f945b71752bdae3d93d2702a4cd67af6ea2859948e65d044f33f4", careful, difference_scope()),
        write("proposal-decision", "a-abfbkq5mhjxr5nr7", "proposal-by-p-decision-by-a-say-whether-an-option-is-offered", "proposal-by / decision-by", "312b0fb0a5ae0f7fe2693597d5391ea95458cd87648097307666dea0ceb2ac6a", careful, proposal_decision()),
        write("preference-release", "a-cef29htze4cmyz4b", "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2", "rather-not / fine-either-way / would-welcome", "edb44cee446c7105302049ca72135bdb23268325771a8612217fe7deeaf9751f", {"kind": "bare-untagged-release-v1"}, preference_release()),
    ]
    output = {
        "kind": "dexagon.ainglish.dispute-settlement-wave.v1",
        "model_calls": 0,
        "legacy_filing": "aggregate-only; locally audited form balance is not a server settlement-strata declaration",
        "training_asymmetry": "Present readers have ordinary-English training and are not assumed to have seen Ainglish.",
        "campaigns": {row["name"]: row for row in campaigns},
    }
    output["content_sha256"] = sha256(canonical(output)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"campaigns": len(campaigns), "content_sha256": output["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
