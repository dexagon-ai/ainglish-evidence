#!/usr/bin/env python3
"""Build a fresh, balanced careful-English replication carrier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "different-from-ref-by-key-different-across-group-by-key"
SEED = 2026090311

DOMAINS = [
    ("model", "models", "model ID", "model-id"),
    ("package", "packages", "checksum", "checksum"),
    ("container image", "container images", "digest", "digest"),
    ("worker", "workers", "owner", "owner"),
    ("endpoint", "endpoints", "region", "region"),
    ("dataset", "datasets", "revision", "revision"),
    ("compiler", "compilers", "version", "version"),
    ("certificate", "certificates", "serial number", "serial-number"),
    ("route", "routes", "target", "target"),
    ("queue", "queues", "account", "account"),
    ("policy", "policies", "policy ID", "policy-id"),
    ("replica", "replicas", "zone", "zone"),
    ("provider", "providers", "model ID", "model-id"),
    ("archive", "archives", "checksum", "checksum"),
    ("controller", "controllers", "version", "version"),
    ("adapter", "adapters", "owner", "owner"),
    ("index", "indexes", "schema ID", "schema-id"),
    ("template", "templates", "revision", "revision"),
    ("secret", "secrets", "key ID", "key-id"),
    ("runtime", "runtimes", "build ID", "build-id"),
]

GROUPS = [
    ("Ari", "Bela", "Cyra"),
    ("Daro", "Esme", "Fenn"),
    ("Gita", "Hale", "Ivo"),
    ("Jora", "Kian", "Luma"),
    ("Miro", "Nell", "Orin"),
]

PROFILES = [
    ("both", True, True),
    ("reference-only", True, False),
    ("across-only", False, True),
    ("neither", False, False),
]

OPTIONS = [
    "permitted: every difference required by the instruction holds",
    "permitted: the present match or repetition is outside the instruction's claim",
    "violates: a selected key matches the external reference key",
    "violates: two group members selected the same key",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotated(options: list[str], offset: int) -> list[str]:
    offset %= len(options)
    return options[offset:] + options[:offset]


def choice_values(domain_index: int, ref_differs: bool, across_differs: bool) -> tuple[str, list[str]]:
    reference = f"R{domain_index + 31:02d}"
    a = f"A{domain_index + 47:02d}"
    b = f"B{domain_index + 53:02d}"
    c = f"C{domain_index + 61:02d}"
    if ref_differs and across_differs:
        return reference, [a, b, c]
    if ref_differs:
        return reference, [a, a, b]
    if across_differs:
        return reference, [reference, a, b]
    return reference, [reference, a, a]


def scientific_items() -> list[dict]:
    items: list[dict] = []
    row = 0
    for domain_index, (noun, plural, key, key_marker) in enumerate(DOMAINS):
        actors = GROUPS[domain_index % len(GROUPS)]
        for profile, ref_differs, across_differs in PROFILES:
            reference, values = choice_values(domain_index, ref_differs, across_differs)
            facts = (
                f"External reference Baseline-{domain_index + 1} has {key} {reference}. "
                + " ".join(
                    f"{actor} selected {noun.title()}-{domain_index + 1}{chr(65 + i)}, "
                    f"whose {key} is {value}."
                    for i, (actor, value) in enumerate(zip(actors, values, strict=True))
                )
            )
            for form in ("different-from", "different-across"):
                if form == "different-from":
                    marked = (
                        f"Instruction: each reviewer must select a {noun}, "
                        f"different-from(Baseline-{domain_index + 1}, by={key_marker})."
                    )
                    careful = (
                        f"Instruction: each reviewer's selected {noun} must have a {key} unequal "
                        f"to Baseline-{domain_index + 1}'s {key}; different reviewers may select "
                        f"{plural} with the same {key}."
                    )
                    answer = OPTIONS[0] if ref_differs and across_differs else (
                        OPTIONS[1] if ref_differs else OPTIONS[2]
                    )
                else:
                    marked = (
                        f"Instruction: each reviewer must select a {noun}, "
                        f"different-across(reviewers, by={key_marker})."
                    )
                    careful = (
                        f"Instruction: every pair of distinct reviewers must select {plural} with "
                        f"unequal {key} values; a selected {noun} may have the same {key} as "
                        f"Baseline-{domain_index + 1}."
                    )
                    answer = OPTIONS[0] if across_differs and ref_differs else (
                        OPTIONS[1] if across_differs else OPTIONS[3]
                    )
                row += 1
                items.append({
                    "id": f"different-fresh-{row:03d}",
                    "english": facts + " " + careful,
                    "ainglish": facts + " " + marked,
                    "question": "Which is the exact evaluation required by the instruction?",
                    "options": rotated(OPTIONS, row),
                    "answer": answer,
                    "settlement_stratum": form,
                    "strata": {
                        "form": form,
                        "profile": profile,
                        "domain": noun,
                        "key": key,
                        "reference_difference": ref_differs,
                        "across_group_difference": across_differs,
                        "repeat_position": None if across_differs else ("first-second" if domain_index % 2 == 0 else "second-third"),
                        "reference_position": None if ref_differs else (domain_index % 3),
                    },
                })
    return items


def calibration_items() -> list[dict]:
    rows = [
        ("ownership", "Either Pella or Quon owns the rollback.", "The record says Pella, not Quon, owns the rollback.", "Who owns the rollback?", ["Quon", "cannot tell", "Pella"], "Pella"),
        ("colour", "The status light is either amber or teal.", "The status light is teal, not amber.", "What colour is the status light?", ["amber", "teal", "cannot tell"], "teal"),
        ("region", "The active shard is in either Oslo or Lima.", "The active shard is in Lima, not Oslo.", "Where is the active shard?", ["cannot tell", "Oslo", "Lima"], "Lima"),
        ("approval", "Either Suri or Tovan approved the patch.", "The record says Tovan, not Suri, approved the patch.", "Who approved the patch?", ["Suri", "Tovan", "cannot tell"], "Tovan"),
        ("sequence", "The violet job ran either before or after the silver job.", "The violet job ran before, not after, the silver job.", "When did the violet job run relative to the silver job?", ["after", "cannot tell", "before"], "before"),
        ("count", "The batch contains either four or nine records.", "The batch contains nine records, not four.", "How many records are in the batch?", ["cannot tell", "nine", "four"], "nine"),
        ("cause", "Either a stale lease or a full queue caused the delay.", "A full queue, not a stale lease, caused the delay.", "What caused the delay?", ["a stale lease", "a full queue", "cannot tell"], "a full queue"),
        ("state", "The certificate is either current or expired.", "The certificate is expired, not current.", "What is the certificate state?", ["current", "cannot tell", "expired"], "expired"),
    ]
    return [{
        "id": f"different-cal-{i:02d}",
        "english": cold,
        "ainglish": planted,
        "question": question,
        "options": options,
        "answer": answer,
        "calibration": True,
        "calibration_scope": "target-independent",
        "strata": {"control": control},
    } for i, (control, cold, planted, question, options, answer) in enumerate(rows, 1)]


def main() -> None:
    scientific = scientific_items()
    calibration = calibration_items()
    assert len(scientific) == 160 and len(calibration) == 8
    assert len({item["id"] for item in scientific + calibration}) == 168
    assert {item["settlement_stratum"] for item in scientific} == {"different-from", "different-across"}
    assert all(sum(item["settlement_stratum"] == form for item in scientific) == 80 for form in ("different-from", "different-across"))
    assert all(sum(item["strata"]["profile"] == profile for item in scientific) == 40 for profile, _, _ in PROFILES)
    items = scientific + calibration
    digest = hashlib.sha256(canonical(items)).hexdigest()
    artifact = {
        "kind": "dexagon.ainglish.different-comprehension-replication-carrier.v1",
        "proposal_revision": SLUG,
        "seed": SEED,
        "sha256": digest,
        "population": "160 fresh allocation-compliance items: 80 per form, 20 operational domains and four crossed reference/across truth profiles, plus eight target-independent controls",
        "aggregation": "equal-weight mean of separately reported different-from and different-across accuracy deltas; marked form versus complete careful-English mapping",
        "reader_calls": 0,
        "items": items,
    }
    (ROOT / "items.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "scientific": len(scientific), "calibration": len(calibration), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
