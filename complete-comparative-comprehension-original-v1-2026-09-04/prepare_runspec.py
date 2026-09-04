#!/usr/bin/env python3
"""Bind the public role carrier to two currently qualified local reader lineages."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SOURCE_COMMIT = "924d1462de24b7a2e1bc0c0ebf3aba3d5115b6cd"
SDK_VERSION = "0.2.53"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    reference = json.loads(
        (EVIDENCE / "same-identity-comprehension-replication-v1-2026-09-04" / "runspec.json")
        .read_text(encoding="utf-8")
    )
    seed = 2026090417
    readers = [{**reader, "seed": seed} for reader in reference["panel"]]
    qualifications = reference["reader_qualifications"]
    strata = [
        {"id": "doer-live", "weight": 1},
        {"id": "doer-clash", "weight": 1},
        {"id": "done-to-live", "weight": 1},
        {"id": "done-to-clash", "weight": 1},
        {"id": "full-live", "weight": 1},
        {"id": "full-clash", "weight": 1},
    ]
    spec = {
        "kind": "dexagon.ainglish.complete-comparative-comprehension-runspec.v1",
        "construct": "complete-the-comparative — explicit rival grammatical role",
        "public_id": "a-xswxcqjeh8ad5gv3",
        "slug": "complete-the-comparative-when-the-clause-before-a-degree",
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": readers,
        "models": [f"{reader['name']}@{reader['precision']}" for reader in readers],
        "reader_qualifications": qualifications,
        "comparator": {
            "kind": "bare-role-ambiguous-english-v1",
            "description": "The same fresh frame with the role-completing words removed. The hidden ledger fixes the intended role; exact recovery is scored against that intent.",
        },
        "comparison_identity": {
            "comparator_genre": "bare-role-ambiguous-english-v1",
            "pair_rendering": "same frame; completed rival role versus bare rival; held-out three-way exact role choice",
            "reader_roster": [f"{reader['name']}@{reader['precision']}" for reader in readers],
            "forms": ["doer-completed", "done-to-completed", "full-rival-clause"],
            "context_types": ["type-live", "type-clash"],
            "role_sites": ["direct-object", "kept-preposition", "adjective-complement"],
            "target_estimand": "equal-weight six-stratum completed-minus-bare exact role-recovery accuracy",
        },
        "settlement_strata": strata,
        "settlement_item_field": "settlement_stratum",
        "settlement_rule": "manifest-weighted arms and value; every form-by-context stratum is load-bearing",
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{SOURCE_COMMIT}/complete-comparative-comprehension-original-v1-2026-09-04/role-items.json"
        ),
        "items_sha256": index["role_items_sha256"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": SOURCE_COMMIT,
            "path": "complete-comparative-comprehension-original-v1-2026-09-04/role-items.json",
        },
        "concurrency": {
            "max_in_flight": 2,
            "per_reader_max_in_flight": {reader["name"]: 1 for reader in readers},
        },
        "training_asymmetry": (
            "The reader artifacts were trained on ordinary English and are not assumed to have seen Ainglish. "
            "This estimates current zero-shot role transparency, not performance after future Ainglish training."
        ),
        "attempt": {
            "proposal_revision": "complete-the-comparative-when-the-clause-before-a-degree",
            "estimand": (
                "Percentage-point exact role-recovery accuracy difference, role-completed comparative minus its "
                "same-frame bare-rival comparator, over 96 frozen fresh items; equal-weight mean of six separately "
                "reported form-by-context strata (doer/done-to/full crossed with type-live/type-clash), two qualified "
                "reader lineages. Rival absolute-level over-reading is a separately frozen diagnostic and is not "
                "pooled into this scalar. Retain absolute arms, interval, calibration, yield, per-reader and every stratum."
            ),
            "admissibility_gates": [
                "fresh authenticated suggestions and proposal detail still request an original comprehension_accuracy_delta immediately before mint",
                "the proposal remains current at measured stage and the executing principal is not the proposer",
                f"the public role carrier hashes to {index['role_items_sha256']} and contains exactly 96 scientific plus 16 target-independent calibration items",
                "the six settlement strata each contain exactly 16 role-recovery items and carry equal weight",
                "doer, done-to and full-clause forms are crossed with type-live and type-clash contexts; all three live role sites remain represented",
                "the separately frozen rival-level over-reading probe is excluded from this scalar rather than diluting role recovery",
                "both exact local reader configurations retain passing target-independent qualification receipts at mint time",
                "both reader artifacts still match their declared Ollama sha256 digests and run at temperature zero with the frozen seed",
                "construct-free calibration executes first and each reader must show explicit-minus-unresolved gap at least 0.5",
                "no reader receives repository access, retrieval, conversation history or a register definition beyond the presented cell",
                "zero response-bound truncations and full cell yield are required; any transport or format fault produces a typed abort without retry",
                "every finite supportive, adverse or null outcome is filed exactly once without item or prompt tuning",
                "the already satisfied token prerequisite is retained and not represented as a comprehension result",
            ],
            "planned_sample": {
                "comparison": "role-completed comparative versus same-frame bare rival",
                "scientific_items": 96,
                "calibration_items": 16,
                "forms": {"doer-completed": 32, "done-to-completed": 32, "full-rival-clause": 32},
                "contexts": {"type-live": 48, "type-clash": 48},
                "settlement_strata": {row["id"]: 16 for row in strata},
                "readers": 2,
                "reader_lineages": [q["lineage"]["key"] for q in qualifications],
                "panel_neff": 2,
                "real_cells": 192,
                "calibration_cells": 64,
                "sdk_version": SDK_VERSION,
                "source_commit": SOURCE_COMMIT,
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "content_sha256": spec["content_sha256"],
        "items_sha256": spec["items_sha256"],
        "reader_count": len(readers),
        "model_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
