#!/usr/bin/env python3
"""Bind the public bare-same carrier to two qualified local reader lineages."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SOURCE_COMMIT = "bdcbe4f55a576cd6d227391ea167d536fad28ecf"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    reference = json.loads(
        (EVIDENCE / "same-identity-comprehension-replication-v1-2026-09-04" / "runspec.json")
        .read_text(encoding="utf-8")
    )
    seed = 2026090419
    readers = [{**reader, "seed": seed} for reader in reference["panel"]]
    qualifications = reference["reader_qualifications"]
    strata = [{"id": form, "weight": 1} for form in ("same-one", "same-kind", "same-name")]
    spec = {
        "kind": "dexagon.ainglish.same-identity-bare-comprehension-runspec.v1",
        "construct": "same-one / same-kind / same-name — resolving bare same",
        "public_id": "a-ptwhg57dq4w4fas4",
        "slug": "same-one-same-kind-same-name",
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": readers,
        "models": [f"{reader['name']}@{reader['precision']}" for reader in readers],
        "reader_qualifications": qualifications,
        "comparator": {
            "kind": "bare-same-ambiguous-english-v1",
            "description": "The same fresh frame using bare same, scored against the hidden intended one/kind/name relation.",
        },
        "comparison_identity": {
            "comparator_genre": "bare-same-ambiguous-english-v1",
            "pair_rendering": "same frame; marked identity relation versus bare same; held-out consequence or relation-basis choice",
            "reader_roster": [f"{reader['name']}@{reader['precision']}" for reader in readers],
            "form_balance": {form: 32 for form in ("same-one", "same-kind", "same-name")},
            "target_estimand": "equal-weight three-form marked-minus-bare exact-answer accuracy",
        },
        "settlement_strata": strata,
        "settlement_item_field": "settlement_stratum",
        "settlement_rule": "manifest-weighted arms and value; every identity form is load-bearing",
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{SOURCE_COMMIT}/same-identity-bare-comprehension-original-v1-2026-09-04/items.json"
        ),
        "items_sha256": index["items_sha256"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": SOURCE_COMMIT,
            "path": "same-identity-bare-comprehension-original-v1-2026-09-04/items.json",
        },
        "concurrency": {
            "max_in_flight": 2,
            "per_reader_max_in_flight": {reader["name"]: 1 for reader in readers},
        },
        "training_asymmetry": (
            "The reader artifacts were trained on ordinary English and are not assumed to have seen Ainglish. "
            "This estimates current zero-shot transparency over bare same, not future post-training performance."
        ),
        "attempt": {
            "proposal_revision": "same-one-same-kind-same-name",
            "estimand": (
                "Percentage-point exact-answer accuracy difference, marked same-one/same-kind/same-name minus "
                "same-frame bare same, over 96 wholly fresh frozen questions; equal-weight mean of three separately "
                "reported 32-item form strata. Probes cover change propagation, exact relation basis, content-equality "
                "non-claims and four same-kind relation-laundering negatives. Retain absolute arms, interval, "
                "calibration, yield, per-reader results and every form stratum."
            ),
            "admissibility_gates": [
                "fresh authenticated suggestions and proposal detail still request strengthening comprehension evidence immediately before mint",
                "the proposal remains current at measured stage and the executing principal is not the proposer",
                f"the public answer-bearing array hashes to {index['items_sha256']} and contains exactly 96 scientific plus 16 target-independent calibration items",
                "all 48 complete marked/bare frame pairs are absent from prior proposal measurement manifests",
                "same-one, same-kind and same-name each contribute exactly 32 load-bearing questions",
                "every same-kind carrier names both the comparison relation and observation moment",
                "four same-kind relation-laundering fixtures require the named relation not to be promoted to byte equality",
                "both exact local reader configurations retain passing target-independent qualification receipts at mint time",
                "both reader artifacts match their declared Ollama sha256 digests and run at temperature zero with the frozen seed",
                "construct-free calibration executes first and each reader must show explicit-minus-unresolved gap at least 0.5",
                "no reader receives repository access, retrieval, conversation history or a register definition beyond the presented cell",
                "zero response-bound truncations and full cell yield are required; any transport or format fault produces a typed abort without retry",
                "every finite supportive, adverse or null outcome is filed exactly once without item or prompt tuning",
                "this resolving original does not rewrite or suppress the existing neutral careful-English original and its agreement",
            ],
            "planned_sample": {
                "comparison": "marked identity form versus same-frame bare same",
                "scientific_items": 96,
                "calibration_items": 16,
                "forms": {form: 32 for form in ("same-one", "same-kind", "same-name")},
                "readers": 2,
                "reader_lineages": [q["lineage"]["key"] for q in qualifications],
                "panel_neff": 2,
                "real_cells": 192,
                "calibration_cells": 64,
                "sdk_version": "0.2.53",
                "source_commit": SOURCE_COMMIT,
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"content_sha256": spec["content_sha256"], "items_sha256": spec["items_sha256"], "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
