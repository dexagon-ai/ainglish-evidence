#!/usr/bin/env python3
"""Build a fresh, four-campaign moved-direction comprehension carrier without model calls."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
QUALIFICATION = REPO / "reader-qualification-v7-2026-08-25" / "selected-result.json"
SEED = 2026082637
SLUG = "moved-earlier-moved-later-which-way-did-the-meeting-move-2"
PUBLIC_ID = "a-3kzhb61snecx3zmt"
SUGGESTIONS_GENERATED_AT = "2026-08-26T08:18:13+00:00"
FORMS = ("moved-earlier", "moved-later")
COMPARATORS = ("careful", "bare")
DOMAINS = (
    ("meetings", "coordination meeting"),
    ("maintenance", "maintenance window"),
    ("jobs", "batch job"),
    ("governance", "ballot close"),
    ("deadlines", "submission deadline"),
    ("delivery", "delivery slot"),
)
BARE_FAMILY = (
    "moved forward",
    "moved back",
    "moved up",
    "brought forward",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sealed(value: dict) -> dict:
    document = dict(value)
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    return document


def rotate(values: list[str], index: int) -> list[str]:
    shift = index % len(values)
    return values[shift:] + values[:shift]


def schedule_context(domain_index: int, frame_index: int, current: str) -> tuple[str, str]:
    domain, noun = DOMAINS[domain_index]
    serial = frame_index + 1
    event = f"{noun} {domain[0].upper()}{serial:03d}"
    context = f"At 2026-12-01T09:00Z, the agreed schedule lists {event} for {current}."
    return event, context


def calendar_frame(domain_index: int, local_index: int, frame_index: int) -> list[dict]:
    current = date(2027, 1, 20) + timedelta(days=domain_index * 71 + local_index * 6)
    amount = 1 + ((domain_index + local_index) % 4)
    unit = "day" if amount == 1 else "days"
    prior = current - timedelta(days=amount)
    following = current + timedelta(days=amount)
    event, context = schedule_context(domain_index, frame_index, current.isoformat())
    bare_family = BARE_FAMILY[frame_index % len(BARE_FAMILY)]
    bare = f'{context} A notice says: "{event} has been {bare_family} by {amount} {unit}."'
    question = f"Which listed date does the notice assign to {event}?"
    options = rotate([prior.isoformat(), following.isoformat(), "cannot determine from the notice"], frame_index)
    return [
        make_world(
            form=form,
            domain=DOMAINS[domain_index][0],
            probe="calendar_recovery",
            frame_index=frame_index,
            context=context,
            event=event,
            bare=bare,
            careful=(
                f'{context} A notice says: "{event} has been rescheduled by {amount} {unit} to a date '
                f'{"before" if form == "moved-earlier" else "after"} its current scheduled date."'
            ),
            marked=f'{context} A notice says: "{event} is {form} by {amount} {unit}."',
            question=question,
            options=options,
            answer=prior.isoformat() if form == "moved-earlier" else following.isoformat(),
            bare_family=bare_family,
            derivation={
                "current": current.isoformat(),
                "amount_days": amount,
                "earlier": prior.isoformat(),
                "later": following.isoformat(),
            },
        )
        for form in FORMS
    ]


def action_frame(domain_index: int, local_index: int, frame_index: int) -> list[dict]:
    day = date(2027, 2, 1) + timedelta(days=domain_index * 67 + local_index * 5)
    hour = 10 + ((domain_index + local_index) % 6)
    current = datetime(day.year, day.month, day.day, hour, 0, tzinfo=timezone.utc)
    amount = 1 + ((domain_index * 2 + local_index) % 4)
    unit = "hour" if amount == 1 else "hours"
    before = current - timedelta(hours=amount)
    after = current + timedelta(hours=amount)
    current_text = current.strftime("%Y-%m-%dT%H:%MZ")
    event, context = schedule_context(domain_index, frame_index, current_text)
    bare_family = BARE_FAMILY[frame_index % len(BARE_FAMILY)]
    bare = f'{context} A notice says: "{event} has been {bare_family} by {amount} {unit}."'
    question = f"An automatic trigger remains set to {current_text}. Relative to {event}'s new occurrence, what will that trigger do?"
    options = rotate(
        ["it will run before the occurrence", "it will run after the occurrence", "it will run at the occurrence"],
        frame_index,
    )
    return [
        make_world(
            form=form,
            domain=DOMAINS[domain_index][0],
            probe="action_consequence",
            frame_index=frame_index,
            context=context,
            event=event,
            bare=bare,
            careful=(
                f'{context} A notice says: "{event} has been rescheduled by {amount} {unit} to a time '
                f'{"before" if form == "moved-earlier" else "after"} its current scheduled time."'
            ),
            marked=f'{context} A notice says: "{event} is {form} by {amount} {unit}."',
            question=question,
            options=options,
            answer="it will run after the occurrence" if form == "moved-earlier" else "it will run before the occurrence",
            bare_family=bare_family,
            derivation={
                "current": current_text,
                "amount_hours": amount,
                "earlier": before.strftime("%Y-%m-%dT%H:%MZ"),
                "later": after.strftime("%Y-%m-%dT%H:%MZ"),
            },
        )
        for form in FORMS
    ]


def scope_frame(domain_index: int, local_index: int, frame_index: int) -> list[dict]:
    current = date(2028, 1, 10) + timedelta(days=domain_index * 53 + local_index * 9)
    event, context = schedule_context(domain_index, frame_index, current.isoformat())
    bare_family = BARE_FAMILY[frame_index % len(BARE_FAMILY)]
    bare = f'{context} A notice says only: "{event} has been {bare_family}."'
    probes = (
        ("amount_not_claimed", "Does the notice state the size of the schedule change?"),
        ("absolute_time_not_claimed", "Does the notice state the newly assigned date or time?"),
        ("notification_not_claimed", "Does the notice state that every participant received the change?"),
        ("finality_not_claimed", "Does the notice state that no later rescheduling may supersede this change?"),
    )
    probe, question = probes[local_index % len(probes)]
    options = rotate(["yes", "no", "the notice does not state that a schedule change occurred"], frame_index)
    return [
        make_world(
            form=form,
            domain=DOMAINS[domain_index][0],
            probe=probe,
            frame_index=frame_index,
            context=context,
            event=event,
            bare=bare,
            careful=(
                f'{context} A notice says only: "{event} has been rescheduled to a time '
                f'{"before" if form == "moved-earlier" else "after"} its current schedule."'
            ),
            marked=f'{context} A notice says only: "{event} is {form}."',
            question=question,
            options=options,
            answer="no",
            bare_family=bare_family,
            derivation={"current": current.isoformat(), "unstated_axis": probe},
        )
        for form in FORMS
    ]


def make_world(**fields: object) -> dict:
    form = str(fields.pop("form"))
    frame_index = int(fields["frame_index"])
    return {
        "id": f"move-{frame_index + 1:03d}-{form.removeprefix('moved-')}",
        "scenario_id": f"move-frame-{frame_index + 1:03d}",
        "world_pair_id": f"move-world-pair-{frame_index + 1:03d}",
        "form": form,
        **fields,
    }


def scientific_worlds() -> list[dict]:
    rows = []
    frame_index = 0
    for domain_index in range(len(DOMAINS)):
        for local_index in range(8):
            rows.extend(calendar_frame(domain_index, local_index, frame_index))
            frame_index += 1
        for local_index in range(8):
            rows.extend(action_frame(domain_index, local_index, frame_index))
            frame_index += 1
        for local_index in range(4):
            rows.extend(scope_frame(domain_index, local_index, frame_index))
            frame_index += 1
    assert frame_index == 120 and len(rows) == 240
    return rows


def calibrations(campaign: str) -> list[dict]:
    objects = ("amber key", "blue card", "cedar seal", "dune token", "elm pass", "fern badge", "gold tag", "hazel slip")
    rows = []
    for index, obj in enumerate(objects):
        rows.append({
            "id": f"{campaign}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"A note names the {obj} but gives no drawer number.",
            "ainglish": f"A note states that the {obj} is in drawer six.",
            "question": "Does the note state that the named object is in drawer six?",
            "options": rotate(["yes", "no", "cannot tell"], index),
            "answer": "yes",
            "set": "construct-free explicit-location known positive",
        })
    return rows


def campaign_rows(worlds: list[dict], form: str, comparator: str) -> list[dict]:
    scientific = []
    for world in worlds:
        if world["form"] != form:
            continue
        scientific.append({
            "id": f"{world['id']}-{comparator}",
            "scenario_id": world["scenario_id"],
            "world_pair_id": world["world_pair_id"],
            "marker": form,
            "english": world[comparator],
            "ainglish": world["marked"],
            "question": world["question"],
            "options": world["options"],
            "answer": world["answer"],
            "strata": {
                "domain": world["domain"],
                "probe": world["probe"],
                "form": form,
                "comparator": comparator,
                "bare_family": world["bare_family"],
            },
            "derivation": world["derivation"],
        })
    campaign = f"{form}-vs-{comparator}"
    return scientific + calibrations(campaign)


def build() -> tuple[dict[str, dict], dict, dict]:
    qualification = json.loads(QUALIFICATION.read_text(encoding="utf-8"))
    if qualification.get("roster_ready") or qualification.get("fixed_roster"):
        raise SystemExit("REFUSING: the frozen v7 blocker no longer matches its terminal receipt")
    worlds = scientific_worlds()
    campaigns = {}
    index_rows = {}
    for form in FORMS:
        for comparator in COMPARATORS:
            name = f"{form}-vs-{comparator}"
            rows = campaign_rows(worlds, form, comparator)
            rows_digest = hashlib.sha256(canonical(rows)).hexdigest()
            payload = {
                "kind": "ainglish.moved-direction-comprehension-items.v1",
                "campaign": name,
                "proposal_slug": SLUG,
                "seed": SEED,
                "items_sha256": rows_digest,
                "design": "120 fresh scientific pairs for one form and one comparator, plus eight construct-free planted-effect calibration rows; never pool forms or comparators.",
                "items": rows,
            }
            campaigns[name] = payload
            scientific = rows[:-8]
            index_rows[name] = {
                "file": f"items-{name}.json",
                "items_sha256": rows_digest,
                "scientific": len(scientific),
                "calibration": 8,
                "domains": {domain: sum(row["strata"]["domain"] == domain for row in scientific) for domain, _ in DOMAINS},
                "probe_groups": {
                    "calendar_recovery": sum(row["strata"]["probe"] == "calendar_recovery" for row in scientific),
                    "action_consequence": sum(row["strata"]["probe"] == "action_consequence" for row in scientific),
                    "overreading": sum(row["strata"]["probe"] not in {"calendar_recovery", "action_consequence"} for row in scientific),
                },
                "answer_positions": {
                    chr(65 + position): sum(row["options"].index(row["answer"]) == position for row in scientific)
                    for position in range(3)
                },
            }
    contract = sealed({
        "kind": "ainglish.moved-direction-live-contract-receipt.v1",
        "selection_suggestions_generated_at": SUGGESTIONS_GENERATED_AT,
        "fresh_proposal_read_performed": True,
        "snapshot_scope": "selected live fields only; re-read the full proposal before any governance write",
        "slug": SLUG,
        "public_id": PUBLIC_ID,
        "stage": "measured",
        "form": "moved-earlier / moved-later",
        "proposer": "Reticuli",
        "evidence_contract": {
            "claim_carrier": ["comprehension_accuracy_delta"],
            "prerequisites": [{"metric": "token_delta", "at_most": 2}, "tag_fidelity"],
        },
        "live_evidence_readiness": {
            "evidence_ready": False,
            "satisfied": ["token_delta"],
            "missing_evidence": ["comprehension_accuracy_delta", "tag_fidelity"],
        },
        "design_constraints_applied": {
            "minimum_items_per_form": 100,
            "separate_form_reporting": True,
            "comparators": ["full careful-English mapping", "balanced identical bare wording"],
            "required_domains": [domain for domain, _ in DOMAINS],
            "required_probes": ["calendar/date recovery", "old-trigger action consequence", "over-reading"],
            "non_inferiority_margin_percentage_points": -5,
        },
    })
    index = sealed({
        "kind": "ainglish.moved-direction-comprehension-freeze.v1",
        "seed": SEED,
        "model_calls": 0,
        "governance_writes": 0,
        "proposal_contract_sha256": contract["content_sha256"],
        "worlds": {
            "frames": 120,
            "hidden_intent_worlds": 240,
            "forms": {form: sum(row["form"] == form for row in worlds) for form in FORMS},
            "paired_bare_surface_identity": True,
        },
        "campaigns": index_rows,
        "blocker": {
            "status": "items_ready_reader_roster_blocked",
            "qualification_file": str(QUALIFICATION.relative_to(REPO)),
            "qualification_sha256": qualification["content_sha256"],
            "roster_ready": qualification["roster_ready"],
            "fixed_roster": qualification["fixed_roster"],
            "effect": "Do not build a runspec, mint an attempt, or expose these items to a model until a separately frozen qualification produces at least two distinct eligible reader lineages.",
        },
    })
    return campaigns, contract, index


def main() -> None:
    campaigns, contract, index = build()
    for name, payload in campaigns.items():
        (ROOT / f"items-{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "proposal-contract.json").write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
