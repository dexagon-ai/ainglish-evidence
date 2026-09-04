#!/usr/bin/env python3
"""Bind the public timing carrier to two qualified local reader lineages."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SOURCE_COMMIT = "f4d8875f93eac1a7c280c080bde7ad9d818724a9"
SDK_VERSION = "0.2.53"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    reference = json.loads(
        (EVIDENCE / "same-identity-comprehension-replication-v1-2026-09-04" / "runspec.json")
        .read_text(encoding="utf-8")
    )
    seed = 2026090421
    readers = [{**reader, "seed": seed} for reader in reference["panel"]]
    qualifications = reference["reader_qualifications"]
    strata = [{"id": "parallel", "weight": 1}, {"id": "sequence", "weight": 1}]
    spec = {
        "kind": "dexagon.ainglish.parallel-sequence-comprehension-runspec.v1",
        "construct": "in-parallel / in-sequence — explicit wait edge",
        "public_id": "a-t4np309pbatx0mfh",
        "slug": "in-parallel-in-sequence-say-whether-listed-actions-may-overl-2",
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": readers,
        "models": [f"{reader['name']}@{reader['precision']}" for reader in readers],
        "reader_qualifications": qualifications,
        "comparator": {
            "kind": "full-careful-english-wait-edge-v1",
            "description": (
                "The same fresh workflow with an explicit full sentence stating whether later actions may begin "
                "before earlier actions reach a terminal outcome. Bare coordination is not scored as incorrect."
            ),
        },
        "comparison_identity": {
            "comparator_genre": "full-careful-english-wait-edge-v1",
            "pair_rendering": "same workflow and wait-edge fact; trailing marker versus full careful-English mapping",
            "reader_roster": [f"{reader['name']}@{reader['precision']}" for reader in readers],
            "forms": ["in-parallel", "in-sequence"],
            "domains": ["operational", "social", "governance", "scheduling"],
            "render_styles": ["semicolon", "and", "bullets", "ordinal-prose", "three-action"],
            "target_estimand": (
                "equal-weight two-stratum marked-minus-careful exact wait-edge recovery; each polarity is load-bearing"
            ),
        },
        "settlement_strata": strata,
        "settlement_item_field": "settlement_stratum",
        "settlement_rule": "manifest-weighted arms and value; parallel and sequence are separately load-bearing",
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{SOURCE_COMMIT}/parallel-sequence-comprehension-original-v1-2026-09-04/items.json"
        ),
        "items_sha256": index["items_sha256"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": SOURCE_COMMIT,
            "path": "parallel-sequence-comprehension-original-v1-2026-09-04/items.json",
        },
        "concurrency": {
            "max_in_flight": 2,
            "per_reader_max_in_flight": {reader["name"]: 1 for reader in readers},
        },
        "training_asymmetry": (
            "The reader artifacts were trained primarily on ordinary English and are not assumed to have seen "
            "Ainglish. This estimates current zero-shot transparency, not performance after future Ainglish training."
        ),
        "attempt": {
            "proposal_revision": "in-parallel-in-sequence-say-whether-listed-actions-may-overl-2",
            "estimand": (
                "Percentage-point exact wait-edge recovery difference, registered trailing marker minus the full "
                "same-workflow careful-English mapping, over 200 frozen items: 100 in-parallel and 100 in-sequence. "
                "The scalar is the equal-weight mean of those two separately reported polarity strata over two "
                "qualified reader lineages. The prediction is non-inferiority with a -5 percentage-point margin, "
                "which requires the interval lower bound above -5pp and neither polarity below the protocol floor. "
                "Retain absolute arms, interval, calibration, yield, per-reader, downsample, and both strata."
            ),
            "admissibility_gates": [
                "fresh authenticated suggestions and proposal detail still request an original comprehension_accuracy_delta immediately before mint",
                "the proposal remains the current seconded revision with no prior comprehension original or open attempt",
                f"the public carrier hashes to {index['items_sha256']} and contains exactly 200 scientific plus 16 target-independent calibration items",
                "each of 100 workflows appears once under in-parallel and once under in-sequence with the same actions",
                "both settlement strata contain exactly 100 items and carry equal weight; neither polarity may be hidden by pooling",
                "each polarity contains exactly 25 operational, social, governance, and scheduling workflows",
                "semicolon, ordinary-and, bullet, ordinal-prose, and three-action renderings remain balanced within every domain",
                "the primary comparator is the full careful-English mapping; bare coordination is not scored as inaccurate",
                "both exact local reader configurations retain passing target-independent qualification receipts at mint time",
                "both reader artifacts still match their declared Ollama sha256 digests and run at temperature zero with the frozen seed",
                "construct-free calibration executes first and each reader must show explicit-minus-unresolved gap at least 0.5",
                "no reader receives repository access, retrieval, conversation history, or a register definition beyond the presented cell",
                "zero response-bound truncations and full cell yield are required; any transport or format fault produces a typed abort without retry",
                "every finite supportive, adverse, or null outcome is filed exactly once without item, threshold, prompt, or reader tuning",
                "causal-conflict, mutual-exclusion, bare-ambiguity, independence-overread, and hyphen-loss checks remain separate diagnostics and do not enter this scalar",
            ],
            "planned_sample": {
                "comparison": "registered timing marker versus full same-workflow careful-English wait-edge mapping",
                "scientific_items": 200,
                "calibration_items": 16,
                "shared_workflows": 100,
                "forms": {"in-parallel": 100, "in-sequence": 100},
                "domains_per_form": {"operational": 25, "social": 25, "governance": 25, "scheduling": 25},
                "settlement_strata": {"parallel": 100, "sequence": 100},
                "readers": 2,
                "reader_lineages": [q["lineage"]["key"] for q in qualifications],
                "panel_neff": 2,
                "real_cells": 400,
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
