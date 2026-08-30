#!/usr/bin/env python3
"""Build a form-separated comprehension carrier for next-up / next-week offline."""

from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026083061
SLUG = "next-up-day-date-next-week-day-date-weekstart-which-next-fri"
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
BASE_WEEKS = (
    ("2024-02-26", "Monday", "leap-boundary"),
    ("2025-12-29", "Sunday", "year-boundary"),
    ("2026-03-30", "Monday", "month-boundary"),
    ("2026-08-24", "Sunday", "ordinary"),
)
DOMAINS = (
    "release review", "maintenance window", "appeal hearing", "dataset handoff",
    "incident drill", "audit meeting", "backup verification", "editorial review",
    "safety inspection", "deployment checkpoint", "ballot review", "research call",
    "manifest signing", "archive transfer",
)
PROPERTIES = (
    ("time_of_day", "a time of day"),
    ("timezone", "a timezone for the resulting civil date"),
    ("recurrence", "a recurrence schedule"),
    ("deadline_inclusion", "whether a deadline is inclusive"),
    ("business_day_adjustment", "a weekend or holiday adjustment"),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def resolve_next_up(anchor: date, target: int) -> date:
    delta = (target - anchor.weekday()) % 7
    return anchor + timedelta(days=delta or 7)


def resolve_next_week(anchor: date, target: int, weekstart: str) -> date:
    weekstart_index = WEEKDAYS.index(weekstart)
    current_start = anchor - timedelta(days=(anchor.weekday() - weekstart_index) % 7)
    return current_start + timedelta(days=7 + ((target - weekstart_index) % 7))


def rendered_answer(anchor: date, result: date) -> str:
    return f"{result.isoformat()} (+{(result - anchor).days} days)"


def answer_options(anchor: date, correct: date, other: date, ordinal: int) -> list[str]:
    candidates = [other, correct - timedelta(days=7), correct + timedelta(days=7), anchor,
                  correct - timedelta(days=1), correct + timedelta(days=1)]
    wrong = []
    for candidate in candidates:
        value = rendered_answer(anchor, candidate)
        if candidate != correct and value not in wrong:
            wrong.append(value)
        if len(wrong) == 3:
            break
    assert len(wrong) == 3
    position = ordinal % 4
    wrong.insert(position, rendered_answer(anchor, correct))
    return wrong


def base_context(anchor: date, target_name: str, domain: str, ordinal: int) -> str:
    context = (
        f"The {domain} uses local civil dates. The declared anchor is {anchor.isoformat()} "
        f"({WEEKDAYS[anchor.weekday()]}), and the requested weekday is {target_name}."
    )
    if ordinal % 4 == 0:
        context += " A source timestamp has already been resolved to that civil date under its stated timezone."
    return context


def instruction(form: str, comparison: str, anchor: date, target_name: str, weekstart: str, domain: str) -> str:
    if comparison == "bare":
        return f"Schedule the {domain} for next {target_name}, taking {anchor.isoformat()} as the anchor date."
    if form == "next-up":
        return (
            f"Schedule the {domain} for the first {target_name} strictly after {anchor.isoformat()}; "
            "the anchor itself is excluded and no calendar-week claim is made."
        )
    return (
        f"Schedule the {domain} for {target_name} in the seven-day calendar week immediately after "
        f"the week containing {anchor.isoformat()}, with weeks starting {weekstart}."
    )


def marked(form: str, anchor: date, target_name: str, weekstart: str, domain: str) -> str:
    marker = (f"next-up({target_name}@{anchor.isoformat()})" if form == "next-up"
              else f"next-week({target_name}@{anchor.isoformat()};{weekstart})")
    return f"Schedule the {domain} for {marker}."


def scientific_rows(form: str, comparison: str) -> list[dict]:
    rows = []
    ordinal = 0
    for base_text, weekstart, epoch in BASE_WEEKS:
        base = date.fromisoformat(base_text)
        assert base.weekday() == 0
        for anchor_offset in range(7):
            anchor = base + timedelta(days=anchor_offset)
            for target_index, target_name in enumerate(WEEKDAYS):
                next_up = resolve_next_up(anchor, target_index)
                next_week = resolve_next_week(anchor, target_index, weekstart)
                correct = next_up if form == "next-up" else next_week
                other = next_week if form == "next-up" else next_up
                domain = DOMAINS[ordinal % len(DOMAINS)]
                context = base_context(anchor, target_name, domain, ordinal)
                rows.append({
                    "id": f"next-weekday-{form}-{comparison}-{ordinal + 1:03d}",
                    "english": context + " Instruction: " + instruction(form, comparison, anchor, target_name, weekstart, domain),
                    "ainglish": context + " Instruction: " + marked(form, anchor, target_name, weekstart, domain),
                    "question": "Which exact ISO civil date is selected, and how many days after the anchor is it?",
                    "options": answer_options(anchor, correct, other, ordinal),
                    "answer": rendered_answer(anchor, correct),
                    "form": form,
                    "comparison": comparison,
                    "scenario_id": f"next-weekday-{epoch}-{anchor_offset + 1}-{target_index + 1}",
                    "strata": {
                        "epoch": epoch, "anchor_weekday": WEEKDAYS[anchor.weekday()],
                        "target_weekday": target_name, "weekstart": weekstart,
                        "days_after_anchor": (correct - anchor).days,
                        "constructors_diverge": next_up != next_week,
                        "timestamp_already_resolved": ordinal % 4 == 0,
                    },
                })
                ordinal += 1
    assert ordinal == 196
    return rows


def calibrations(form: str, comparison: str) -> list[dict]:
    rows = []
    for index in range(12):
        answer = "yes" if index % 2 == 0 else "no"
        options = ["yes", "no", "cannot tell"]
        shift = index % 3
        options = options[shift:] + options[:shift]
        rows.append({
            "id": f"next-weekday-{form}-{comparison}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"Literal control {index + 1}: bay nine is {'open' if answer == 'yes' else 'closed'}.",
            "ainglish": f"Literal control {index + 1}: bay nine is {'open' if answer == 'yes' else 'closed'}.",
            "question": "Is bay nine described as open?", "options": options, "answer": answer,
            "set": "construct-free literal control",
        })
    return rows


def build_primary(form: str, comparison: str) -> tuple[dict, dict]:
    scientific = scientific_rows(form, comparison)
    rows = scientific + calibrations(form, comparison)
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    filename = f"items-{form}-{comparison}.json"
    packet = {
        "kind": "dexagon.ainglish.next-weekday-comprehension-carrier.v1",
        "proposal_revision": SLUG, "form": form, "comparison": comparison,
        "seed": SEED, "sha256": digest,
        "population": "196 exact joint date-and-offset cells plus 12 construct-free calibrations",
        "primary_population": "84 divergent cells; report 112 convergent cells separately as controls",
        "aggregation": "form-separated paired accuracy delta; report divergent and convergent strata separately; never pool forms or comparator classes",
        "reader_calls": 0, "items": rows,
    }
    return packet, {
        "file": filename, "items_sha256": digest, "scientific": 196, "calibration": 12,
        "divergent": sum(row["strata"]["constructors_diverge"] for row in scientific),
        "convergent": sum(not row["strata"]["constructors_diverge"] for row in scientific),
    }


def build_nonclaims(form: str) -> tuple[dict, dict]:
    rows = []
    for property_index, (key, phrase) in enumerate(PROPERTIES):
        for index in range(14):
            base_text, weekstart, _ = BASE_WEEKS[index % 4]
            anchor = date.fromisoformat(base_text) + timedelta(days=index % 7)
            target_name = WEEKDAYS[(index * 3 + property_index) % 7]
            domain = DOMAINS[index]
            positive = (index + property_index) % 2 == 0
            question = (f"Does this instruction specify {phrase}?" if positive
                        else f"Does this instruction leave {phrase} unspecified?")
            answer = "no" if positive else "yes"
            options = ["yes", "no", "cannot tell"]
            shift = (index + property_index) % 3
            options = options[shift:] + options[:shift]
            rows.append({
                "id": f"next-weekday-{form}-nonclaim-{key}-{index + 1:02d}",
                "ainglish": base_context(anchor, target_name, domain, index) + " Instruction: " + marked(form, anchor, target_name, weekstart, domain),
                "question": question, "options": options, "answer": answer, "form": form,
                "scenario_id": f"nonclaim-{key}-{index + 1:02d}",
                "strata": {"property": key, "question_polarity": "claims" if positive else "leaves_unspecified"},
            })
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    filename = f"diagnostics-{form}.json"
    packet = {
        "kind": "dexagon.ainglish.next-weekday-nonclaim-diagnostics.v1",
        "proposal_revision": SLUG, "form": form, "seed": SEED, "sha256": digest,
        "population": "70 secondary nonclaim checks: fourteen per prohibited inference",
        "aggregation": "report each property separately; these rows never enter primary comprehension accuracy",
        "reader_calls": 0, "items": rows,
    }
    return packet, {"file": filename, "items_sha256": digest, "scientific": 70}


def main() -> None:
    campaigns = {}
    for form in ("next-up", "next-week"):
        for comparison in ("careful", "bare"):
            packet, receipt = build_primary(form, comparison)
            (ROOT / receipt["file"]).write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            campaigns[f"{form}-vs-{comparison}"] = receipt
    diagnostics = {}
    for form in ("next-up", "next-week"):
        packet, receipt = build_nonclaims(form)
        (ROOT / receipt["file"]).write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        diagnostics[form] = receipt
    index = {
        "kind": "dexagon.ainglish.next-weekday-comprehension-freeze.v1",
        "proposal_revision": SLUG, "seed": SEED, "campaigns": campaigns,
        "nonclaim_diagnostics": diagnostics, "reader_calls": 0, "governance_writes": 0,
        "execution_gate": "live evidence work still requests this original, exact packet is committed, and at least two independent reader lineages pass the same construct-free qualification packet",
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
