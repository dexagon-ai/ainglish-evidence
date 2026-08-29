#!/usr/bin/env python3
"""Build fresh, form-separated definition-conditioned learnability items."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
N = 48
SEED = 2026082943
CAMPAIGNS = {
    "one-or-more": ("role-cardinality", "one-or-more", "role"),
    "exactly-one": ("role-cardinality", "exactly-one", "role"),
    "may-as-permission": ("may-force", "may-as-permission", "may"),
    "may-as-possibility": ("may-force", "may-as-possibility", "may"),
    "some-or-all": ("some-boundary", "some-or-all", "some"),
    "some-but-not-all": ("some-boundary", "some-but-not-all", "some"),
    "whole": ("set-coverage", "whole", "coverage"),
    "part": ("set-coverage", "part", "coverage"),
}
ROLES = ("reviewer", "operator", "auditor", "maintainer", "approver", "inspector", "editor", "signer")
ACTIONS = ("approve release", "inspect archive", "sign receipt", "review patch", "accept handoff", "verify backup")
SUBJECTS = ("operator", "service", "worker", "reviewer", "scheduler", "client", "auditor", "maintainer")
VERBS = ("restart", "publish", "retry", "archive", "notify", "deploy", "revoke", "restore")
POPULATIONS = ("replicas", "checks", "alerts", "recipients", "files", "workers", "records", "regions")
SETS = ("fleet-A", "allowlist-B", "archive-C", "sample-D", "queue-E", "inventory-F", "roster-G", "catalog-H")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def placed(answer: str, alternatives: list[str], position: int) -> list[str]:
    assert answer not in alternatives and len(set(alternatives)) == 2
    values = list(alternatives)
    values.insert(position % 3, answer)
    return values


def item(campaign: str, index: int, message: str, question: str, answer: str,
         alternatives: list[str], probe: str) -> dict:
    return {
        "id": f"learn-d-{campaign}-{index + 1:03d}",
        "english": message,
        "ainglish": message,
        "question": question,
        "options": placed(answer, alternatives, index % 3),
        "answer": answer,
        "marker": campaign,
        "probe": probe,
        "scenario_id": f"learnability-wave-d-{campaign}-{index + 1:03d}",
    }


def role(marker: str) -> list[dict]:
    at_least = marker == "one-or-more"
    rows = []
    for index in range(N):
        named_role = ROLES[index % len(ROLES)]
        action = ACTIONS[index % len(ACTIONS)]
        probe = index % 6
        if probe == 0:
            observed = "No qualifying principal performed it."
            question = "Is the bounded instruction satisfied?"
            answer, alternatives = "no", ["yes", "not stated"]
        elif probe == 1:
            observed = "One distinct qualifying principal performed it once."
            question = "Is the bounded instruction satisfied?"
            answer, alternatives = "yes", ["no", "not stated"]
        elif probe == 2:
            observed = "Two distinct qualifying principals each performed it once."
            question = "Is the bounded instruction satisfied?"
            answer = "yes" if at_least else "no"
            alternatives = ["no" if at_least else "yes", "not stated"]
        elif probe == 3:
            observed = "One qualifying principal has performed it once; a second is available."
            question = "May the second qualifying principal also perform this same bounded action?"
            answer = "yes" if at_least else "no"
            alternatives = ["no" if at_least else "yes", "not stated"]
        elif probe == 4:
            observed = "One qualifying principal performed it twice under the same identity."
            question = "How many distinct qualifying principals does that record contain?"
            answer, alternatives = "one", ["two", "cannot tell"]
        else:
            observed = "The record names qualifying principals but says nothing about their relationships."
            question = "Does the marker itself assert that the principals are independent and non-delegating?"
            answer, alternatives = "no", ["yes", "only for reviewers"]
        message = (
            f"Work order {2100 + index}: {marker}({named_role}): {action} for bounded item "
            f"{3100 + index}. Record: {observed}"
        )
        rows.append(item(marker, index, message, question, answer, alternatives, f"role-{probe}"))
    return rows


def may_force(marker: str) -> list[dict]:
    permission = marker == "may-as-permission"
    rows = []
    for index in range(N):
        subject = SUBJECTS[index % len(SUBJECTS)]
        verb = VERBS[index % len(VERBS)]
        probe = index % 6
        message = f"Status {2200 + index}: the {subject} {marker} {verb} item {3200 + index}."
        if probe == 0:
            question = "Which force does the marked sentence express?"
            answer = "authorization" if permission else "possible occurrence"
            alternatives = ["possible occurrence" if permission else "authorization", "completed event"]
        elif probe == 1:
            question = "Which record would directly contradict the marked claim?"
            answer = "the governing permission record" if permission else "the live outcome model"
            alternatives = ["the live outcome model" if permission else "the governing permission record", "the event log proving completion"]
        elif probe == 2:
            question = "Does this marker by itself claim that the event is likely?"
            answer = "no" if permission else "it claims possibility, not a probability level"
            alternatives = (["yes", "only if permission is current"] if permission else ["yes, likely", "no occurrence is possible"])
        elif probe == 3:
            question = "Does this marker by itself grant authority to perform the action?"
            answer = "yes" if permission else "no"
            alternatives = ["no" if permission else "yes", "only after it occurs"]
        elif probe == 4:
            question = "Could the marked claim remain true if policy permits the action but a hard technical block makes it impossible?"
            answer = "yes" if permission else "no"
            alternatives = ["no" if permission else "yes", "not stated"]
        else:
            question = "Could the marked claim remain true if policy forbids the action but working credentials make it technically possible?"
            answer = "no" if permission else "yes"
            alternatives = ["yes" if permission else "no", "not stated"]
        rows.append(item(marker, index, message, question, answer, alternatives, f"may-{probe}"))
    return rows


def some(marker: str) -> list[dict]:
    permits_all = marker == "some-or-all"
    rows = []
    for index in range(N):
        population = POPULATIONS[index % len(POPULATIONS)]
        size = 3 + (index % 6)
        message = f"Outcome {2300 + index}: {marker} of the {size} {population} satisfied check {3300 + index}."
        probe = index % 6
        if probe == 0:
            question = "Would zero satisfying members contradict the statement?"
            answer, alternatives = "yes", ["no", "not stated"]
        elif probe == 1:
            question = "Is a world in which every member satisfied the check compatible with the statement?"
            answer = "yes" if permits_all else "no"
            alternatives = ["no" if permits_all else "yes", "only when nobody counted"]
        elif probe == 2:
            question = "Must at least one member have failed the check?"
            answer = "no" if permits_all else "yes"
            alternatives = ["yes" if permits_all else "no", "not stated"]
        elif probe == 3:
            question = "Does the marker state the exact number that satisfied the check?"
            answer, alternatives = "no", ["yes", "only for sets under ten"]
        elif probe == 4:
            question = "Does the marker itself claim that the named population is a complete census rather than a sample?"
            answer, alternatives = "no", ["yes", "only for some-but-not-all"]
        else:
            question = "Does the marker assert that the writer has not counted the satisfying members?"
            answer, alternatives = "no", ["yes", "only for some-or-all"]
        rows.append(item(marker, index, message, question, answer, alternatives, f"some-{probe}"))
    return rows


def coverage(marker: str) -> list[dict]:
    complete = marker == "whole"
    rows = []
    for index in range(N):
        named_set = SETS[index % len(SETS)]
        first, second = f"member-{4100 + index}", f"member-{5100 + index}"
        message = f"Coverage report {2400 + index}: {marker}({named_set}) = {{{first}, {second}}}."
        probe = index % 6
        if probe == 0:
            question = "May another in-scope member exist outside the reported set?"
            answer = "no" if complete else "yes"
            alternatives = ["yes" if complete else "no", "not stated"]
        elif probe == 1:
            question = "Is a rate computed from the reported rows a population rate or a subset rate?"
            answer = "population rate" if complete else "subset rate"
            alternatives = ["subset rate" if complete else "population rate", "not stated"]
        elif probe == 2:
            question = "Does absence from the reported rows establish absence from the named reference population?"
            answer = "yes" if complete else "no"
            alternatives = ["no" if complete else "yes", "only for archived sets"]
        elif probe == 3:
            question = "Does the marker claim that the reported rows are a proper subset of the named reference population?"
            answer = "no" if complete else "yes"
            alternatives = ["yes" if complete else "no", "not stated"]
        elif probe == 4:
            question = "Does this marker by itself assert that every reported row is factually correct?"
            answer, alternatives = "no", ["yes", "only for whole sets"]
        else:
            question = "Does this marker define what belongs to the named reference population?"
            answer, alternatives = "no", ["yes", "only for part sets"]
        rows.append(item(marker, index, message, question, answer, alternatives, f"coverage-{probe}"))
    return rows


def calibrations(campaign: str) -> list[dict]:
    objects = ("ivory token", "jade seal", "kelp disk", "linen key", "moss card", "navy badge", "opal pass", "pearl tag")
    rows = []
    for index, obj in enumerate(objects):
        locker = 71 + index
        answer = f"locker {locker}"
        rows.append({
            "id": f"learn-d-{campaign}-cal-{index + 1:02d}",
            "calibration": True,
            "calibration_scope": "target-independent",
            "calibration_construct": "zun-location-control-v1",
            "english": f"The routing slip labels the {obj} zun({locker}), but supplies no definition of zun.",
            "ainglish": f"Control entry: zun(<N>) means the labelled object is stored in locker N.\n\nThe routing slip labels the {obj} zun({locker}).",
            "question": f"Where does the control place the {obj}?",
            "options": placed(answer, [f"locker {locker + 1}", "not inferable"], index % 3),
            "answer": answer,
        })
    return rows


def entry_text(surface: dict) -> str:
    sections = [
        "Ainglish register entry",
        f"Title: {surface['title']}",
        f"Form: {surface['form']}",
        "Standard-English mapping:\n" + surface["english_mapping"],
    ]
    if surface.get("example_ainglish"):
        sections.append("Registered Ainglish examples:\n" + surface["example_ainglish"])
    if surface.get("example_english"):
        sections.append("Registered standard-English examples:\n" + surface["example_english"])
    return "\n\n".join(sections) + "\n"


def main() -> None:
    snapshots = json.loads((ROOT / "proposal-snapshots.json").read_text())
    builders = {"role": role, "may": may_force, "some": some, "coverage": coverage}
    entries = {}
    for proposal_key, record in snapshots["proposals"].items():
        text = entry_text(record["surface"])
        path = ROOT / f"entry-{proposal_key}.txt"
        path.write_text(text)
        entries[proposal_key] = {
            "path": path.name,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "proposal_slug": record["surface"]["slug"],
            "surface_sha256": record["surface_sha256"],
        }

    index = {
        "kind": "dexagon.ainglish.flagship-learnability-wave-d-freeze.v1",
        "seed": SEED,
        "model_calls": 0,
        "governance_writes": 0,
        "campaigns": {},
    }
    seen = set()
    for campaign, (proposal_key, marker, builder_name) in CAMPAIGNS.items():
        scientific = builders[builder_name](marker)
        calibration = calibrations(campaign)
        rows = scientific + calibration
        current = {(row["english"], row["ainglish"], row["question"]) for row in scientific}
        assert len(scientific) == N and len(calibration) == 8 and len(current) == N
        assert not current & seen
        seen |= current
        assert all(row["english"] == row["ainglish"] and marker in row["english"] for row in scientific)
        assert [sum(row["options"].index(row["answer"]) == position for row in scientific) for position in range(3)] == [16, 16, 16]
        item_sha = hashlib.sha256(canonical(rows)).hexdigest()
        payload = {
            "kind": "dexagon.ainglish.flagship-learnability-items.v2",
            "campaign": campaign,
            "proposal_key": proposal_key,
            "marker": marker,
            "seed": SEED,
            "sha256": item_sha,
            "items": rows,
        }
        path = ROOT / f"items-{campaign}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        index["campaigns"][campaign] = {
            "proposal_key": proposal_key,
            "marker": marker,
            "items_path": path.name,
            "items_sha256": item_sha,
            "scientific_items": N,
            "calibration_items": 8,
            "entry": entries[proposal_key],
        }
    index["proposal_snapshot_sha256"] = snapshots["content_sha256"]
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"campaigns": len(CAMPAIGNS), "scientific_items": len(CAMPAIGNS) * N, "content_sha256": index["content_sha256"]}))


if __name__ == "__main__":
    main()
