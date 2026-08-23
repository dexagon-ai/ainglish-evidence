#!/usr/bin/env python3
"""Build and validate the frozen some-or-all / some-but-not-all evidence packet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ("some-or-all", "some-but-not-all")

QUESTION_A = (
    "Which boundary profile follows? Lower endpoint: can the matching group have size zero? "
    "Upper endpoint: can it include the full named set?"
)
OPTIONS_A = (
    "zero impossible; full set possible",
    "zero impossible; full set impossible",
    "zero possible; full set possible",
    "zero possible; full set impossible",
)
QUESTION_B = (
    "Which boundary profile follows? Lower endpoint: must the matching group be nonempty? "
    "Upper endpoint: must a nonmatching member exist?"
)
OPTIONS_B = (
    "nonempty required; nonmatch not required",
    "nonempty required; nonmatch required",
    "nonempty not required; nonmatch not required",
    "nonempty not required; nonmatch required",
)
ANSWER_INDEX = {"some-or-all": 0, "some-but-not-all": 1}


# Every frame names a recoverable population with at least two members. The same
# 100 frames are rendered with both meanings, so topic and predicate cannot leak
# which upper-bound answer is correct.
FRAMES = [
    # incident response
    ("incident_response", "The incident review covered twelve service checks.", "service check", "service checks", "successful"),
    ("incident_response", "The containment plan listed eight isolation steps.", "isolation step", "isolation steps", "complete"),
    ("incident_response", "The response log tracked sixteen incident alerts.", "incident alert", "incident alerts", "acknowledged"),
    ("incident_response", "The evidence register contained six forensic images.", "forensic image", "forensic images", "verified"),
    ("incident_response", "The recovery board showed ten restoration tasks.", "restoration task", "restoration tasks", "finished"),
    ("incident_response", "The incident scope contained fourteen affected endpoints.", "affected endpoint", "affected endpoints", "isolated"),
    ("incident_response", "The review packet contained nine timeline entries.", "timeline entry", "timeline entries", "corroborated"),
    ("incident_response", "The preservation list named seven audit records.", "audit record", "audit records", "preserved"),
    ("incident_response", "The paging batch contained eleven operator notifications.", "operator notification", "operator notifications", "delivered"),
    ("incident_response", "The mitigation checklist contained five safety controls.", "safety control", "safety controls", "active"),
    # replicas and storage
    ("replicas", "The database cluster had twelve replicas.", "database replica", "database replicas", "current"),
    ("replicas", "The storage pool contained eight mirrors.", "storage mirror", "storage mirrors", "synchronized"),
    ("replicas", "The cache ring contained sixteen nodes.", "cache node", "cache nodes", "warmed"),
    ("replicas", "The search service maintained six indexes.", "search index", "search indexes", "rebuilt"),
    ("replicas", "The delivery network used ten regional copies.", "regional copy", "regional copies", "reachable"),
    ("replicas", "The recovery vault held fourteen snapshots.", "backup snapshot", "backup snapshots", "restorable"),
    ("replicas", "The ledger service maintained nine mirrors.", "ledger mirror", "ledger mirrors", "consistent"),
    ("replicas", "The reporting tier contained seven read replicas.", "read replica", "read replicas", "healthy"),
    ("replicas", "The package network exposed eleven artifact mirrors.", "artifact mirror", "artifact mirrors", "validated"),
    ("replicas", "The continuity plan named five failover targets.", "failover target", "failover targets", "ready"),
    # permissions
    ("permissions", "The quarterly review covered twelve access grants.", "access grant", "access grants", "approved"),
    ("permissions", "The directory contained eight administrator roles.", "administrator role", "administrator roles", "reviewed"),
    ("permissions", "The rotation batch contained sixteen API credentials.", "API credential", "API credentials", "rotated"),
    ("permissions", "The project used six service accounts.", "service account", "service accounts", "authorized"),
    ("permissions", "The policy register listed ten temporary exceptions.", "temporary exception", "temporary exceptions", "expired"),
    ("permissions", "The organization tracked fourteen repository permissions.", "repository permission", "repository permissions", "documented"),
    ("permissions", "The release group held nine signing keys.", "signing key", "signing keys", "protected"),
    ("permissions", "The firewall review covered seven network rules.", "network rule", "network rules", "enabled"),
    ("permissions", "The agent roster contained eleven delegated capabilities.", "delegated capability", "delegated capabilities", "scoped"),
    ("permissions", "The incident policy listed five emergency privileges.", "emergency privilege", "emergency privileges", "revoked"),
    # recipients and people
    ("recipients", "The notice list contained twelve intended recipients.", "intended recipient", "intended recipients", "notified"),
    ("recipients", "The review roster contained eight participants.", "review participant", "review participants", "invited"),
    ("recipients", "The recovery roster named sixteen key holders.", "key holder", "key holders", "contacted"),
    ("recipients", "The mailing list contained six subscribers.", "subscriber", "subscribers", "updated"),
    ("recipients", "The response rota listed ten on-call engineers.", "on-call engineer", "on-call engineers", "paged"),
    ("recipients", "The incident affected fourteen tenants.", "affected tenant", "affected tenants", "informed"),
    ("recipients", "The release group contained nine managers.", "release manager", "release managers", "briefed"),
    ("recipients", "The governance roster named seven data owners.", "data owner", "data owners", "consulted"),
    ("recipients", "The package set had eleven maintainers.", "package maintainer", "package maintainers", "alerted"),
    ("recipients", "The account list named five custodians.", "account custodian", "account custodians", "reached"),
    # monitoring and alerts
    ("alerts", "The dashboard displayed twelve latency alerts.", "latency alert", "latency alerts", "resolved"),
    ("alerts", "The monitoring window contained eight error alarms.", "error alarm", "error alarms", "investigated"),
    ("alerts", "The capacity report listed sixteen warnings.", "capacity warning", "capacity warnings", "cleared"),
    ("alerts", "The security queue contained six signals.", "security signal", "security signals", "triaged"),
    ("alerts", "The health monitor raised ten heartbeat alerts.", "heartbeat alert", "heartbeat alerts", "suppressed"),
    ("alerts", "The batch report contained fourteen timeout alarms.", "timeout alarm", "timeout alarms", "confirmed"),
    ("alerts", "The integrity scan produced nine warnings.", "integrity warning", "integrity warnings", "escalated"),
    ("alerts", "The certificate monitor raised seven alerts.", "certificate alert", "certificate alerts", "actioned"),
    ("alerts", "The quota service issued eleven notices.", "quota notice", "quota notices", "acknowledged"),
    ("alerts", "The configuration monitor found five drift signals.", "drift signal", "drift signals", "explained"),
    # inventory
    ("inventory", "The repair cabinet held twelve spare drives.", "spare drive", "spare drives", "labelled"),
    ("inventory", "The records room contained eight archive boxes.", "archive box", "archive boxes", "catalogued"),
    ("inventory", "The supply shelf held sixteen replacement cables.", "replacement cable", "replacement cables", "tested"),
    ("inventory", "The warehouse bay contained six pallets.", "warehouse pallet", "warehouse pallets", "inspected"),
    ("inventory", "The field programme used ten devices.", "field device", "field devices", "registered"),
    ("inventory", "The software pool contained fourteen licence seats.", "licence seat", "licence seats", "assigned"),
    ("inventory", "The laboratory rack held nine sample vials.", "sample vial", "sample vials", "sealed"),
    ("inventory", "The reading group borrowed seven library copies.", "library copy", "library copies", "returned"),
    ("inventory", "The equipment room contained eleven cases.", "equipment case", "equipment cases", "counted"),
    ("inventory", "The shelter stored five emergency kits.", "emergency kit", "emergency kits", "replenished"),
    # ordinary human situations
    ("ordinary", "The dinner booking named twelve guests.", "dinner guest", "dinner guests", "seated"),
    ("ordinary", "The course set eight assignments.", "classroom assignment", "classroom assignments", "submitted"),
    ("ordinary", "The garden bed contained sixteen plants.", "garden plant", "garden plants", "watered"),
    ("ordinary", "The carriage carried six passengers.", "train passenger", "train passengers", "checked"),
    ("ordinary", "The park area contained ten picnic tables.", "picnic table", "picnic tables", "occupied"),
    ("ordinary", "The collection desk held fourteen parcels.", "parcel", "parcels", "collected"),
    ("ordinary", "The committee had nine members.", "committee member", "committee members", "present"),
    ("ordinary", "The shopping list contained seven grocery items.", "grocery item", "grocery items", "discounted"),
    ("ordinary", "The hall had eleven windows.", "window", "windows", "opened"),
    ("ordinary", "The station rack held five bicycles.", "bicycle", "bicycles", "locked"),
    # compliance
    ("compliance", "The certification covered twelve control objectives.", "control objective", "control objectives", "met"),
    ("compliance", "The policy document contained eight clauses.", "policy clause", "policy clauses", "reviewed"),
    ("compliance", "The audit packet contained sixteen evidence items.", "evidence item", "evidence items", "accepted"),
    ("compliance", "The audit report listed six findings.", "audit finding", "audit findings", "closed"),
    ("compliance", "The privacy register held ten consent records.", "consent record", "consent records", "valid"),
    ("compliance", "The archive policy contained fourteen retention rules.", "retention rule", "retention rules", "applied"),
    ("compliance", "The risk register listed nine exceptions.", "risk exception", "risk exceptions", "renewed"),
    ("compliance", "The supplier packet contained seven declarations.", "vendor declaration", "vendor declarations", "signed"),
    ("compliance", "The staff course contained eleven modules.", "training module", "training modules", "completed"),
    ("compliance", "The case file contained five legal notices.", "legal notice", "legal notices", "delivered"),
    # deployments
    ("deployments", "The release train contained twelve candidates.", "release candidate", "release candidates", "promoted"),
    ("deployments", "The migration plan listed eight steps.", "migration step", "migration steps", "executed"),
    ("deployments", "The rollout controlled sixteen feature flags.", "feature flag", "feature flags", "enabled"),
    ("deployments", "The release bundle contained six build artifacts.", "build artifact", "build artifacts", "signed"),
    ("deployments", "The verification suite contained ten smoke tests.", "smoke test", "smoke tests", "passed"),
    ("deployments", "The worker pool contained fourteen processes.", "worker process", "worker processes", "restarted"),
    ("deployments", "The database contained nine shards.", "database shard", "database shards", "upgraded"),
    ("deployments", "The rollout package contained seven configuration bundles.", "configuration bundle", "configuration bundles", "loaded"),
    ("deployments", "The canary pool contained eleven instances.", "canary instance", "canary instances", "stable"),
    ("deployments", "The release plan named five rollback checkpoints.", "rollback checkpoint", "rollback checkpoints", "saved"),
    # science and logistics
    ("science_logistics", "The experiment produced twelve sensor readings.", "sensor reading", "sensor readings", "retained"),
    ("science_logistics", "The laboratory received eight specimens.", "specimen", "specimens", "analysed"),
    ("science_logistics", "The trial enrolled sixteen participants.", "trial participant", "trial participants", "followed"),
    ("science_logistics", "The telescope session produced six frames.", "telescope frame", "telescope frames", "calibrated"),
    ("science_logistics", "The survey used ten weather stations.", "weather station", "weather stations", "reporting"),
    ("science_logistics", "The depot scheduled fourteen delivery vehicles.", "delivery vehicle", "delivery vehicles", "dispatched"),
    ("science_logistics", "The journey contained nine route segments.", "route segment", "route segments", "reopened"),
    ("science_logistics", "The port received seven shipping containers.", "shipping container", "shipping containers", "scanned"),
    ("science_logistics", "The terminal operated eleven boarding gates.", "boarding gate", "boarding gates", "staffed"),
    ("science_logistics", "The convoy carried five freight manifests.", "freight manifest", "freight manifests", "reconciled"),
]


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def rotate(values: tuple[str, ...], shift: int) -> list[str]:
    shift %= len(values)
    return list(values[shift:] + values[:shift])


def question_spec(index: int) -> tuple[str, tuple[str, ...]]:
    return (QUESTION_A, OPTIONS_A) if index % 2 == 0 else (QUESTION_B, OPTIONS_B)


def render(form: str, index: int, comparator: str) -> dict:
    domain, context, singular, plural, prop = FRAMES[index]
    question, options = question_spec(index)
    answer = options[ANSWER_INDEX[form]]
    form_offset = 0 if form == "some-or-all" else 2
    marked = f"{context} {form.capitalize()} {plural} were {prop}."
    if comparator == "careful":
        if form == "some-or-all":
            english_clause = (
                f"At least one {singular} was {prop}, and every {singular} may have been {prop}."
            )
        else:
            english_clause = (
                f"At least one {singular} was {prop}, and at least one {singular} was not {prop}."
            )
        english = f"{context} {english_clause}"
    elif comparator == "bare":
        english = f"{context} Some {plural} were {prop}."
    else:
        raise AssertionError(comparator)
    return {
        "id": f"some-boundary-{form.replace('-', '')}-{comparator}-{index + 1:03d}",
        "english": english,
        "ainglish": marked,
        "question": question,
        "options": rotate(options, index + form_offset),
        "answer": answer,
        "form": form,
        "comparison": (
            "marked_vs_complete_careful_english"
            if comparator == "careful"
            else "marked_vs_bare_some_descriptive_diagnostic"
        ),
        "scenario_id": f"frame-{index + 1:03d}",
        "strata": {"domain": domain, "question_polarity": "endpoint" if index % 2 == 0 else "requirement"},
    }


def calibration_items(form: str) -> list[dict]:
    """Construct-free explicit-vs-unresolved positive controls, balanced by question style."""
    contexts = [
        "The audit examined a fixed roster of twelve entries.",
        "The review covered a fixed set of eight records.",
        "The check concerned a named pool of sixteen devices.",
        "The report described a fixed list of six recipients.",
        "The scan covered a named collection of ten files.",
        "The survey concerned a fixed group of fourteen members.",
        "The inspection covered a named batch of nine parcels.",
        "The test concerned a fixed suite of seven cases.",
        "The census covered a named roster of eleven accounts.",
        "The log described a fixed set of five events.",
        "The review covered a named pool of thirteen samples.",
        "The exercise concerned a fixed group of four teams.",
        "The inventory covered a named set of fifteen tools.",
        "The run concerned a fixed batch of eighteen jobs.",
        "The check covered a named roster of twenty nodes.",
        "The poll concerned a fixed group of three delegates.",
    ]
    rows = []
    for index, context in enumerate(contexts):
        question, options = question_spec(index)
        answer = options[ANSWER_INDEX[form]]
        if form == "some-or-all":
            explicit = (
                "The matching group contains at least one member, while membership by the entire "
                "named set remains compatible with the report."
            )
        else:
            explicit = (
                "The matching group contains at least one member and leaves at least one named "
                "member outside that group."
            )
        rows.append({
            "id": f"some-boundary-cal-{form.replace('-', '')}-{index + 1:02d}",
            "english": f"{context} The report does not disclose either boundary of the matching group.",
            "ainglish": f"{context} {explicit}",
            "question": question,
            "options": rotate(options, index + (0 if form == "some-or-all" else 2)),
            "answer": answer,
            "calibration": True,
            "set": "construct_free_explicit_vs_unresolved",
        })
    return rows


def build_items(form: str, comparator: str) -> list[dict]:
    return [render(form, index, comparator) for index in range(len(FRAMES))] + calibration_items(form)


def validate(items: list[dict], form: str, comparator: str) -> dict:
    real = [item for item in items if not item.get("calibration")]
    calibration = [item for item in items if item.get("calibration")]
    assert len(real) == 100 and len(calibration) == 16
    assert len({item["id"] for item in items}) == len(items)
    assert {item["form"] for item in real} == {form}
    assert all(item["answer"] in item["options"] for item in items)
    assert all(len(item["options"]) == len(set(item["options"])) == 4 for item in items)
    assert all(item["comparison"].endswith(
        "careful_english" if comparator == "careful" else "descriptive_diagnostic"
    ) for item in real)
    assert all(item["ainglish"] != item["english"] for item in items)
    assert all(item["scenario_id"] == f"frame-{index + 1:03d}" for index, item in enumerate(real))
    assert Counter(item["strata"]["domain"] for item in real) == Counter({
        "incident_response": 10,
        "replicas": 10,
        "permissions": 10,
        "recipients": 10,
        "alerts": 10,
        "inventory": 10,
        "ordinary": 10,
        "compliance": 10,
        "deployments": 10,
        "science_logistics": 10,
    })
    assert Counter(item["strata"]["question_polarity"] for item in real) == Counter({
        "endpoint": 50, "requirement": 50
    })
    positions = Counter(item["options"].index(item["answer"]) for item in real)
    assert positions == Counter({0: 25, 1: 25, 2: 25, 3: 25})
    for item in real:
        marker = form.capitalize()
        assert marker in item["ainglish"] and marker not in item["question"]
        if comparator == "careful":
            assert "At least one" in item["english"]
            if form == "some-or-all":
                assert "every" in item["english"] and "may have been" in item["english"]
            else:
                assert item["english"].count("at least one") == 1  # second occurrence is capitalised
                assert "At least one" in item["english"] and "was not" in item["english"]
        else:
            assert ". Some " in item["english"]
    return {
        "form": form,
        "comparison": comparator,
        "real_items": len(real),
        "calibration_items": len(calibration),
        "domains": dict(sorted(Counter(item["strata"]["domain"] for item in real).items())),
        "question_polarities": dict(sorted(Counter(item["strata"]["question_polarity"] for item in real).items())),
        "answer_positions": {str(key): positions[key] for key in range(4)},
    }


def write_packet(path: Path, kind: str, items: list[dict]) -> dict:
    digest = canonical_sha(items)
    packet = {"kind": kind, "sha256": digest, "items": items}
    path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"path": path.name, "items_sha256": digest, "file_sha256": canonical_sha(packet)}


def main() -> None:
    assert len(FRAMES) == 100
    assert len({(row[1], row[2], row[3], row[4]) for row in FRAMES}) == 100
    receipts = []
    validations = []
    for form in FORMS:
        for comparator in ("careful", "bare"):
            items = build_items(form, comparator)
            validations.append(validate(items, form, comparator))
            stem = form.replace("-", "_")
            receipts.append(write_packet(
                ROOT / f"{stem}-{comparator}-items.json",
                f"ainglish.panel.items.v1:{form}-vs-{comparator}",
                items,
            ))

    # Cross-file invariants: each form has the same 100 semantic frames and the
    # careful and bare packets differ only in comparator text and identifiers.
    frame_sets = defaultdict(set)
    for form in FORMS:
        for comparator in ("careful", "bare"):
            frame_sets[(form, comparator)] = {
                item["scenario_id"] for item in build_items(form, comparator)
                if not item.get("calibration")
            }
    assert all(frames == {f"frame-{index:03d}" for index in range(1, 101)} for frames in frame_sets.values())

    receipt = {
        "kind": "ainglish.evidence.freeze-receipt.v1",
        "reader_calls": 0,
        "scientific_boundary": (
            "Two unpooled 100-item claim carriers compare each marker only with its complete "
            "careful-English meaning. Bare some is frozen only in separate descriptive diagnostics."
        ),
        "files": receipts,
        "validation": validations,
    }
    (ROOT / "freeze-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
