#!/usr/bin/env python3
"""Build two answer-bearing populations and their same-cell token prerequisites."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
from statistics import median
import sys


ROOT = Path(__file__).resolve().parent
SEED = 2026082943
COMPARATORS = ("bare", "careful", "practical")

AVERAGE_FORMS = ("mean-of", "median-of")
DELETION_FORMS = ("removed-from", "erased-from")

DATASETS = (
    (1, 2, 2, 3, 42),
    (-42, -3, -2, -2, -1),
    (2, 4, 6, 8, 10),
    (1, 3, 7, 9),
    (1, 4, 4, 4, 11),
    (-8, -5, -3, -1, 2),
    (10, 10, 11, 12, 107),
    (-2, 0, 10, 12),
    (1, 2, 3, 4, 40),
    (1, 1, 5, 5),
)

AVERAGE_DOMAINS = (
    ("response-ms", "milliseconds"),
    ("pay-gbp", "pounds"),
    ("queue-depth", "jobs"),
    ("delivery-days", "days"),
    ("sensor-error", "units"),
    ("claim-cost", "pounds"),
    ("energy-kwh", "kilowatt-hours"),
    ("recovery-hours", "hours"),
)

AVERAGE_HARD_CELLS = (
    "mean-above-four-of-five",
    "negative-values",
    "mean-equals-median",
    "even-median-not-observed",
    "duplicated-central-values",
    "population-time-window-change",
    "outlier-sensitivity",
    "different-exclusion-rules",
    "sample-versus-target-population",
    "weighted-rolling-categorical-not-licensed",
)

DELETION_DOMAINS = (
    "customer-profile", "support-ticket", "document", "photo", "message",
    "model-input", "invoice", "health-record", "source-archive", "device-backup",
)

DELETION_HARD_CELLS = (
    "customer-hidden-support-visible",
    "direct-id-absent-search-visible",
    "primary-clear-stale-replica-visible",
    "feature-view-hidden-api-visible",
    "one-principal-revoked-another-visible",
    "object-store-version-omitted-from-inventory",
    "point-in-time-wal-omitted-from-inventory",
    "delayed-replica-omitted-from-inventory",
    "content-free-tombstone-outside-object-boundary",
    "declared-cryptographic-erasure-model",
    "derived-data-outside-object-boundary",
    "backup-after-observation-epoch",
    "authorization-legal-future-inference",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def write_new(name: str, value: object) -> None:
    path = ROOT / name
    if path.exists() and "--refresh-before-freeze" not in sys.argv:
        raise SystemExit(f"REFUSING: {name} already exists")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def placed(correct: str, distractors: list[str], position: int) -> list[str]:
    assert correct not in distractors and len(set(distractors)) == len(distractors)
    result = list(distractors)
    result.insert(position, correct)
    return result


def number(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator / value.denominator:.2f}"


def average_question(form: str, ref: str, value: str, cell: str) -> tuple[str, str, list[str]]:
    if cell == "mean-above-four-of-five":
        return (
            "Does the report guarantee that a majority of individual observations equal or exceed the reported number?",
            "no",
            ["yes", "not stated"],
        )
    if cell == "negative-values":
        return (
            "Does the report assert that the number is an expected future value?",
            "no",
            ["yes", "not stated"],
        )
    if cell == "mean-equals-median":
        return (
            "If both statistics happen to have the same numeric value, may the writer silently substitute the other statistic's form?",
            "no",
            ["yes", "not stated"],
        )
    if cell == "even-median-not-observed":
        correct = "no"
        return (
            f"Must an individual observation in {ref} equal the reported {value}?",
            correct,
            [answer for answer in ("yes", "no", "not stated") if answer != correct],
        )
    if cell == "duplicated-central-values":
        correct = "no"
        return (
            "Does the report assert that the result is the most common value?",
            correct,
            ["yes", "not stated"],
        )
    if cell == "population-time-window-change":
        correct = "no"
        return (
            f"May a later report silently substitute {ref}-next-window and still claim the same population?",
            correct,
            ["yes", "not stated"],
        )
    if cell == "outlier-sensitivity":
        correct = "yes" if form == "mean-of" else "no"
        return (
            "If one extreme observation becomes still more extreme without crossing another observation, must this statistic change?",
            correct,
            [answer for answer in ("yes", "no", "not stated") if answer != correct],
        )
    if cell == "different-exclusion-rules":
        correct = "no"
        return (
            "Does the report permit comparing its number with a second report that silently uses different exclusions?",
            correct,
            ["yes", "not stated"],
        )
    if cell == "sample-versus-target-population":
        correct = "the exact referenced sample only"
        return (
            "If the referenced bytes are a sample, what population does the assertion cover?",
            correct,
            ["the wider target population automatically", "an expected future population"],
        )
    correct = "no"
    return (
        "Does this marker by itself license a weighted, rolling, approximate, or categorical-mode estimator?",
        correct,
        ["yes", "not stated"],
    )


def build_average() -> tuple[dict, dict]:
    rows = []
    for scenario, ((domain, unit), values) in enumerate(
        ((domain, values) for domain in AVERAGE_DOMAINS for values in DATASETS), 1
    ):
        ref = f"{domain}@heldout-{scenario:03d}-v1"
        mean_value = Fraction(sum(values), len(values))
        median_value = Fraction(median(values))
        cell = AVERAGE_HARD_CELLS[(scenario - 1) % len(AVERAGE_HARD_CELLS)]
        for form_index, form in enumerate(AVERAGE_FORMS):
            exact = mean_value if form == "mean-of" else median_value
            shown = number(exact)
            diagnostic_question, diagnostic_answer, diagnostic_distractors = average_question(form, ref, shown, cell)
            arithmetic = f"unweighted arithmetic mean of every observation in {ref}"
            middle = f"sorted middle value (or middle-pair mean) of every observation in {ref}"
            primary = arithmetic if form == "mean-of" else middle
            other_primary = middle if form == "mean-of" else arithmetic
            answer = f"{primary}; follow-up answer: {diagnostic_answer}"
            distractors = [
                f"{other_primary}; follow-up answer: {diagnostic_answer}",
                f"{primary}; follow-up answer: {diagnostic_distractors[0]}",
            ]
            question = f"Which complete interpretation is justified? Follow-up: {diagnostic_question}"
            ainglish = f"{form}({ref}) = {shown} {unit}."
            if form == "mean-of":
                careful = (
                    f"The unweighted arithmetic mean of every numeric observation in the exact finite "
                    f"population {ref} is {shown} {unit}."
                )
                practical = f"mean({ref}) = {shown} {unit}."
            else:
                careful = (
                    f"The median of every numeric observation in the exact finite population {ref}, using "
                    f"the mean of the two middle observations for an even count, is {shown} {unit}."
                )
                practical = f"median({ref}) = {shown} {unit}."
            bare = f"The average for {ref} is {shown} {unit}."
            position = ((scenario - 1) * 2 + form_index) % 3
            rows.append({
                "id": f"average-{scenario:03d}-{form}",
                "scenario_id": f"average-{scenario:03d}",
                "form": form,
                "hard_cell": cell,
                "population_ref": ref,
                "unit": unit,
                "hidden_values": list(values),
                "derived_mean": number(mean_value),
                "derived_median": number(median_value),
                "ainglish": ainglish,
                "bare": bare,
                "careful": careful,
                "practical": practical,
                "question": question,
                "options": placed(answer, distractors, position),
                "answer": answer,
                "primary_statistic_population": primary,
                "diagnostic_question": diagnostic_question,
                "diagnostic_answer": diagnostic_answer,
                "hidden_values_exposed_to_reader": False,
            })
    assert len(rows) == 160
    packet = {
        "kind": "dexagon.ainglish.average-statistic-comprehension-items.v1",
        "proposal_slug": "mean-of-population-ref-value-median-of-population-ref-value",
        "seed": SEED,
        "population": "160 held-out rows: 80 immutable datasets, each matched across mean-of and median-of",
        "comparators": list(COMPARATORS),
        "items": rows,
    }
    packet["items_sha256"] = sha(rows)
    token_rows = [{
        "item_id": row["id"],
        "form": row["form"],
        "semantic_cell": row["hard_cell"],
        "population_ref": row["population_ref"],
        "ainglish": row["ainglish"],
        "english": row["careful"],
    } for form in AVERAGE_FORMS for row in [r for r in rows if r["form"] == form][:16]]
    token = token_packet(
        "average-statistic", packet["proposal_slug"], AVERAGE_FORMS, token_rows,
        "complete careful English preserving statistic, exact finite population reference, value, and unit",
    )
    return packet, token


def deletion_question(form: str, surface: str, inventory: str, cell: str) -> tuple[str, str, list[str]]:
    if cell in {"customer-hidden-support-visible", "direct-id-absent-search-visible", "feature-view-hidden-api-visible", "one-principal-revoked-another-visible"}:
        correct = "yes" if form == "removed-from" else "not stated"
        return (
            f"Does the report establish absence under every admissible query in {surface}?",
            correct,
            [answer for answer in ("yes", "no", "not stated") if answer != correct],
        )
    if cell in {
        "object-store-version-omitted-from-inventory",
        "point-in-time-wal-omitted-from-inventory",
        "delayed-replica-omitted-from-inventory",
    }:
        omitted = {
            "object-store-version-omitted-from-inventory": "an object-store version",
            "point-in-time-wal-omitted-from-inventory": "a point-in-time write-ahead log",
            "delayed-replica-omitted-from-inventory": "a delayed replica",
        }[cell]
        return (
            f"May {omitted} outside {inventory} still hold a matching copy without contradicting the bounded report?",
            "yes",
            ["no", "not stated"],
        )
    if cell in {"primary-clear-stale-replica-visible", "declared-cryptographic-erasure-model"}:
        correct = "not stated" if form == "removed-from" else "yes"
        return (
            f"Does the report establish that no matching representation is recoverable in any locus enumerated by {inventory}?",
            correct,
            [answer for answer in ("yes", "no", "not stated") if answer != correct],
        )
    if cell == "backup-after-observation-epoch":
        correct = "no"
        return (
            "After the named later restore or rewrite invalidates the receipt, does the old report establish the object is still absent now?",
            correct,
            ["yes", "not stated"],
        )
    if cell in {"content-free-tombstone-outside-object-boundary", "derived-data-outside-object-boundary"}:
        correct = "no"
        noun = "content-free tombstone" if cell.startswith("content-free") else "derived record outside the object's declared boundary"
        return (
            f"Does a remaining {noun} by itself contradict the bounded report?",
            correct,
            ["yes", "not stated"],
        )
    correct = "no"
    return (
        "Does the report by itself establish authorization, legal compliance, retention satisfaction, and future non-recreation?",
        correct,
        ["yes", "not stated"],
    )


def build_deletion() -> tuple[dict, dict]:
    rows = []
    for scenario in range(1, 81):
        domain = DELETION_DOMAINS[(scenario - 1) % len(DELETION_DOMAINS)]
        cell = DELETION_HARD_CELLS[(scenario - 1) % len(DELETION_HARD_CELLS)]
        obj = f"{domain}-{scenario:03d}"
        surface = f"{domain}-surface-receipt@{scenario:03d}-r1"
        inventory = f"{domain}-inventory-receipt@{scenario:03d}-v1"
        epoch = f"2026-08-{(scenario - 1) % 28 + 1:02d}T{(scenario - 1) % 24:02d}:00Z"
        for form_index, form in enumerate(DELETION_FORMS):
            diagnostic_question, diagnostic_answer, diagnostic_distractors = deletion_question(form, surface, inventory, cell)
            surface_scope = f"query-bounded absence in {surface} at {epoch}; other surfaces and copies unasserted"
            inventory_scope = f"recoverability absence in every locus of {inventory} at {epoch}; outside and later copies unasserted"
            primary = surface_scope if form == "removed-from" else inventory_scope
            other_primary = inventory_scope if form == "removed-from" else surface_scope
            answer = f"{primary}; follow-up answer: {diagnostic_answer}"
            distractors = [
                f"{other_primary}; follow-up answer: {diagnostic_answer}",
                f"{primary}; follow-up answer: {diagnostic_distractors[0]}",
            ]
            question = f"Which complete interpretation is justified? Follow-up: {diagnostic_question}"
            if form == "removed-from":
                ainglish = f"{obj} removed-from({surface}) as_of({epoch})."
                careful = (
                    f"At {epoch}, no admissible query in the exact bounded retrieval surface receipt "
                    f"{surface} returns or addresses {obj}; other surfaces and storage copies are unasserted."
                )
                practical = f"{obj} was removed from the active view named by {surface} at {epoch}."
            else:
                ainglish = f"{obj} erased-from({inventory}) as_of({epoch})."
                careful = (
                    f"At {epoch}, no representation matching {obj}'s declared boundary remains recoverable "
                    f"in any storage locus enumerated by {inventory} under its declared recovery model; "
                    f"outside and later copies are unasserted."
                )
                practical = f"{obj} was erased from all listed copies in {inventory} at {epoch}."
            bare = f"{obj} was deleted at {epoch}."
            position = ((scenario - 1) * 2 + form_index) % 3
            rows.append({
                "id": f"deletion-{scenario:03d}-{form}",
                "scenario_id": f"deletion-{scenario:03d}",
                "form": form,
                "hard_cell": cell,
                "object_ref": obj,
                "surface_ref": surface,
                "inventory_ref": inventory,
                "epoch": epoch,
                "ainglish": ainglish,
                "bare": bare,
                "careful": careful,
                "practical": practical,
                "question": question,
                "options": placed(answer, distractors, position),
                "answer": answer,
                "primary_scope_epoch": primary,
                "diagnostic_question": diagnostic_question,
                "diagnostic_answer": diagnostic_answer,
                "semantic_scope": (
                    "query-bounded surface absence; other roles, queries, regions, and copies unasserted"
                    if form == "removed-from"
                    else "inventory-bounded recoverability absence; outside, later, and recreated copies unasserted"
                ),
            })
    assert len(rows) == 160
    packet = {
        "kind": "dexagon.ainglish.deletion-depth-comprehension-items.v1",
        "proposal_slug": "o-removed-from-surface-o-erased-from-inventory-2",
        "seed": SEED + 1,
        "population": "160 held-out rows: 80 persistence scenarios, each matched across removed-from and erased-from",
        "comparators": list(COMPARATORS),
        "items": rows,
    }
    packet["items_sha256"] = sha(rows)
    token_rows = [{
        "item_id": row["id"],
        "form": row["form"],
        "semantic_cell": row["hard_cell"],
        "scope_ref": row["surface_ref"] if row["form"] == "removed-from" else row["inventory_ref"],
        "ainglish": row["ainglish"],
        "english": row["careful"],
    } for form in DELETION_FORMS for row in [r for r in rows if r["form"] == form][:16]]
    token = token_packet(
        "deletion-depth", packet["proposal_slug"], DELETION_FORMS, token_rows,
        "complete careful English preserving object, receipt-bounded scope, observation epoch, and unasserted outside scope",
    )
    return packet, token


def token_packet(kind: str, slug: str, forms: tuple[str, str], rows: list[dict], comparison: str) -> dict:
    counts = {form: sum(row["form"] == form for row in rows) for form in forms}
    assert len(rows) == 32 and counts == {form: 16 for form in forms}
    packet = {
        "kind": f"dexagon.ainglish.{kind}-token-items.v1",
        "proposal_slug": slug,
        "metric": "token_delta",
        "forms": list(forms),
        "form_counts": counts,
        "comparison": comparison,
        "acceptance": {"least_favourable_balanced_mean_at_most": 0},
        "evidentiary_limit": (
            "present price prerequisite only; English but not these Ainglish surfaces may appear in "
            "current tokenizer training data, and token count cannot establish comprehension"
        ),
        "test_set": rows,
    }
    packet["items_sha256"] = sha(rows)
    packet["content_sha256"] = sha(packet)
    return packet


def templates(name: str, packet: dict, forms: tuple[str, str]) -> dict:
    values = []
    for form in forms:
        subset = [row for row in packet["items"] if row["form"] == form]
        for comparator in COMPARATORS:
            values.append({
                "name": f"{name}-{form}-vs-{comparator}",
                "proposal_slug": packet["proposal_slug"],
                "form": form,
                "comparator": comparator,
                "metric": "comprehension_accuracy_delta",
                "items": len(subset),
                "items_sha256": sha(subset),
                "ainglish_field": "ainglish",
                "english_field": comparator,
                "question_field": "question",
                "options_field": "options",
                "answer_field": "answer",
                "aggregation": "this form and comparator only; never pool forms or comparator classes",
                "activation": {
                    "required_distinct_base_lineages": 2,
                    "qualification_receipts_required": True,
                    "reader_calls_before_mint": 0,
                    "current_roster_ready": False,
                },
            })
    result = {"kind": f"dexagon.ainglish.{name}-comprehension-templates.v1", "templates": values}
    result["templates_sha256"] = sha(values)
    return result


def main() -> None:
    snapshot = json.loads((ROOT / "proposal-snapshots.json").read_text(encoding="utf-8"))
    sealed = dict(snapshot)
    expected = sealed.pop("content_sha256")
    if sha(sealed) != expected:
        raise SystemExit("REFUSING: snapshot digest drift")
    for key in ("average", "deletion"):
        if snapshot["proposals"][key]["surface"]["stage"] != "seconded":
            raise SystemExit(f"REFUSING: frozen {key} surface was not seconded")
    average, average_token = build_average()
    deletion, deletion_token = build_deletion()
    average_templates = templates("average-statistic", average, AVERAGE_FORMS)
    deletion_templates = templates("deletion-depth", deletion, DELETION_FORMS)
    artifacts = {
        "average-comprehension-items.json": average,
        "average-comprehension-templates.json": average_templates,
        "average-token-items.json": average_token,
        "deletion-comprehension-items.json": deletion,
        "deletion-comprehension-templates.json": deletion_templates,
        "deletion-token-items.json": deletion_token,
    }
    for name, value in artifacts.items():
        write_new(name, value)
    index = {
        "kind": "dexagon.ainglish.newly-seconded-flagship-carriers-freeze.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "artifacts": {name: sha(value) for name, value in artifacts.items()},
        "scientific_items": {"average": 160, "deletion": 160},
        "token_pairs": {"average": 32, "deletion": 32},
        "comprehension_templates": {"average": 6, "deletion": 6},
        "reader_activation": "closed until an immutable two-lineage qualified panel is supplied before mint",
        "model_calls": 0,
        "tokenizer_calls": 0,
        "governance_writes": 0,
    }
    index["content_sha256"] = sha(index)
    write_new("index.json", index)
    print(json.dumps({
        "scientific_items": index["scientific_items"],
        "token_pairs": index["token_pairs"],
        "comprehension_templates": index["comprehension_templates"],
        "content_sha256": index["content_sha256"],
        "model_calls": 0,
        "tokenizer_calls": 0,
        "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
