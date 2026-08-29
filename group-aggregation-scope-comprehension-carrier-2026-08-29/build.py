#!/usr/bin/env python3
"""Build a balanced, answer-bearing group-scope comprehension population."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082941
ANSWERS = ("yes", "no", "not stated")

DOMAINS = (
    ("regions", "region", ("North", "South"), "checkout success rate"),
    ("model-families", "model family", ("Atlas", "Birch"), "exact-match accuracy"),
    ("age-bands", "age band", ("younger", "older"), "recovery rate"),
    ("data-centres", "data centre", ("East", "West"), "request success rate"),
    ("review-teams", "review team", ("Blue", "Gold"), "defect-detection rate"),
    ("customer-tiers", "customer tier", ("Basic", "Plus"), "renewal rate"),
    ("device-classes", "device class", ("Handheld", "Desktop"), "update success rate"),
    ("delivery-zones", "delivery zone", ("Urban", "Rural"), "on-time arrival rate"),
    ("language-cohorts", "language cohort", ("Coastal", "Inland"), "task completion rate"),
    ("risk-bands", "risk band", ("Low", "High"), "repayment rate"),
    ("hospital-sites", "hospital site", ("Central", "Valley"), "discharge recovery rate"),
    ("queue-classes", "queue class", ("Interactive", "Batch"), "job completion rate"),
)

TABLES_INCREASE = {
    "each_only": {
        "A": {"before_success": 90, "before_total": 100, "after_success": 19, "after_total": 20},
        "B": {"before_success": 1, "before_total": 10, "after_success": 2, "after_total": 10},
    },
    "combined_only": {
        "A": {"before_success": 18, "before_total": 20, "after_success": 89, "after_total": 100},
        "B": {"before_success": 2, "before_total": 10, "after_success": 1, "after_total": 10},
    },
    "both": {
        "A": {"before_success": 5, "before_total": 10, "after_success": 7, "after_total": 10},
        "B": {"before_success": 4, "before_total": 10, "after_success": 6, "after_total": 10},
    },
    "mixed_combined": {
        "A": {"before_success": 8, "before_total": 10, "after_success": 7, "after_total": 10},
        "B": {"before_success": 1, "before_total": 10, "after_success": 9, "after_total": 10},
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def reverse_table(table: dict) -> dict:
    return {
        name: {
            "before_success": values["after_success"],
            "before_total": values["after_total"],
            "after_success": values["before_success"],
            "after_total": values["before_total"],
        }
        for name, values in table.items()
    }


def placed(answer: str, position: int) -> list[str]:
    others = [value for value in ANSWERS if value != answer]
    others.insert(position, answer)
    return others


def prompt_parts(direction: str, metric: str, member: str, probe: str) -> tuple[str, dict[str, str]]:
    later = "higher" if direction == "increased" else "lower"
    opposite = "lower" if direction == "increased" else "higher"
    aggregate_opposite = "downward" if direction == "increased" else "upward"
    if probe == "member_same":
        question = f"According to the report, must the later {metric} for {member} be {later} than its earlier value?"
        expected = {"each-group": "yes", "groups-combined": "not stated"}
    elif probe == "member_opposite_compatible":
        question = f"Could the later {metric} for {member} be {opposite} without contradicting the report?"
        expected = {"each-group": "no", "groups-combined": "yes"}
    elif probe == "aggregate_opposite":
        question = f"Does the report assert that the grand {metric} moved {aggregate_opposite}?"
        expected = {"each-group": "not stated", "groups-combined": "no"}
    else:
        raise AssertionError(probe)
    return question, expected


def truth(table: dict, direction: str) -> tuple[bool, bool]:
    rates = {
        name: (
            values["before_success"] / values["before_total"],
            values["after_success"] / values["after_total"],
        )
        for name, values in table.items()
    }
    compare = (lambda before, after: after > before) if direction == "increased" else (lambda before, after: after < before)
    each = all(compare(before, after) for before, after in rates.values())
    before_success = sum(values["before_success"] for values in table.values())
    before_total = sum(values["before_total"] for values in table.values())
    after_success = sum(values["after_success"] for values in table.values())
    after_total = sum(values["after_total"] for values in table.values())
    combined = compare(before_success / before_total, after_success / after_total)
    return each, combined


def main() -> None:
    snapshot = json.loads((ROOT / "proposal-snapshot.json").read_text(encoding="utf-8"))
    rows = []
    for scenario_index in range(96):
        domain, singular, members, metric = DOMAINS[scenario_index % len(DOMAINS)]
        cycle = scenario_index // len(DOMAINS) + 1
        reference = f"{domain}@scope-{cycle}"
        direction = "increased" if cycle % 2 else "decreased"
        probe = ("member_same", "member_opposite_compatible", "aggregate_opposite")[scenario_index % 3]
        question, expected = prompt_parts(direction, metric, members[0], probe)
        bare = f"Across all {domain} in {reference}, {metric} {direction}."
        form_worlds = {
            "each-group": "each_only" if scenario_index % 2 == 0 else "both",
            "groups-combined": ("combined_only", "mixed_combined", "both")[scenario_index % 3],
        }
        for form_index, form in enumerate(("each-group", "groups-combined")):
            world = form_worlds[form]
            base_table = TABLES_INCREASE[world]
            table = base_table if direction == "increased" else reverse_table(base_table)
            renamed = {members[index]: values for index, values in enumerate(table.values())}
            each_truth, combined_truth = truth(renamed, direction)
            if form == "each-group":
                assert each_truth
                ainglish = f"each-group({reference}): {metric} {direction}."
                careful = f"In every {singular} named by {reference}, considered separately, {metric} {direction}."
            else:
                assert combined_truth
                ainglish = f"groups-combined({reference}): {metric} {direction}."
                careful = f"After records from all {domain} named by {reference} are treated as one total, {metric} {direction}."
            answer = expected[form]
            rows.append(
                {
                    "item_id": f"scope-{scenario_index + 1:03d}-{form}",
                    "scenario_id": f"scope-{scenario_index + 1:03d}",
                    "form": form,
                    "domain": domain,
                    "group_set_ref": reference,
                    "members": list(members),
                    "metric": metric,
                    "direction": direction,
                    "probe": probe,
                    "world": world,
                    "hidden_table": renamed,
                    "derived_truth": {"each_group": each_truth, "groups_combined": combined_truth},
                    "ainglish": ainglish,
                    "bare": bare,
                    "careful": careful,
                    "question": question,
                    "options": placed(answer, scenario_index % 3),
                    "answer": answer,
                    "hidden_table_exposed_to_reader": False,
                }
            )
    assert len(rows) == 192
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    packet = {
        "kind": "dexagon.ainglish.group-aggregation-scope-comprehension-items.v1",
        "proposal_slug": snapshot["surface"]["slug"],
        "surface_sha256": snapshot["surface_sha256"],
        "seed": SEED,
        "population": (
            "192 form-balanced assertion-scope items: 96 each-group and 96 groups-combined, "
            "paired by identical bare surface across hidden intentions"
        ),
        "items_sha256": digest,
        "items": rows,
    }
    (ROOT / "items.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    templates = []
    for form in ("each-group", "groups-combined"):
        subset = [row for row in rows if row["form"] == form]
        subset_digest = hashlib.sha256(canonical(subset)).hexdigest()
        for comparator in ("bare", "careful"):
            templates.append(
                {
                    "name": f"{form.replace('-', '_')}_vs_{comparator}",
                    "form": form,
                    "comparator": comparator,
                    "items": len(subset),
                    "items_sha256": subset_digest,
                    "metric": "comprehension_accuracy_delta",
                    "ainglish_field": "ainglish",
                    "english_field": comparator,
                    "question_field": "question",
                    "options_field": "options",
                    "answer_field": "answer",
                    "prediction": (
                        "delta at least +20 percentage points"
                        if comparator == "bare"
                        else "Ainglish no more than 5 percentage points below careful English"
                    ),
                    "aggregation": "report this form and comparator separately; never pool forms or comparator classes",
                }
            )
    template_digest = hashlib.sha256(canonical(templates)).hexdigest()
    (ROOT / "templates.json").write_text(
        json.dumps(
            {
                "kind": "dexagon.ainglish.group-aggregation-scope-comprehension-templates.v1",
                "items_sha256": digest,
                "templates_sha256": template_digest,
                "templates": templates,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    index = {
        "kind": "dexagon.ainglish.group-aggregation-scope-comprehension-freeze.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "items_path": "items.json",
        "items_sha256": digest,
        "templates_path": "templates.json",
        "templates_sha256": template_digest,
        "items": len(rows),
        "forms": {form: sum(row["form"] == form for row in rows) for form in ("each-group", "groups-combined")},
        "comparators": ["bare", "careful"],
        "scientific_attempts": 4,
        "qualification": {
            "required_distinct_base_lineages": 2,
            "current_roster_ready": False,
            "activation": "only through an immutable qualification receipt passed before any scientific reader call",
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "items": len(rows),
                "forms": index["forms"],
                "templates": len(templates),
                "items_sha256": digest,
                "templates_sha256": template_digest,
                "content_sha256": index["content_sha256"],
                "model_calls": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
