#!/usr/bin/env python3
"""Bind the frozen same-one/same-kind/same-name carrier to settlement strata."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SOURCE = EVIDENCE / "flagship-carrier-bank-2026-08-26"
SLUG = "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2"
FORMS = ("same-one", "same-kind", "same-name")
PUBLISHED_ITEMS_COMMIT = "c4ac8575b4f0289cfb7b638ce0fe496262df25fc"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def seal(value: dict) -> dict:
    result = dict(value)
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def calibrations() -> list[dict]:
    rows = []
    for index in range(12):
        locker = 61 + index
        answer = f"locker {locker}"
        options = [answer, f"locker {locker + 1}", "not stated", "dispatch shelf"]
        options = options[index % 4:] + options[:index % 4]
        rows.append({
            "id": f"identity-relation-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The routing note labels case {index + 1} niv({locker}), but gives no meaning for niv.",
            "ainglish": f"Control: niv(N) means the labelled case is stored in locker N. The routing note labels case {index + 1} niv({locker}).",
            "question": "Where does the control place the case?",
            "options": options,
            "answer": answer,
            "calibration_construct": "target-independent niv location marker",
        })
    return rows


def scientific_items() -> tuple[list[dict], dict[str, str]]:
    rows = []
    source_digests = {}
    for form in FORMS:
        source_path = SOURCE / f"items-{form}.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        source_digests[form] = source["sha256"]
        for original in source["items"]:
            if original.get("calibration"):
                continue
            row = dict(original)
            assert row["marker"] == form
            row["form"] = form
            row["settlement_stratum"] = f"{form}.{row['strata']['polarity']}"
            rows.append(row)
    return rows, source_digests


def main() -> None:
    scientific, source_digests = scientific_items()
    strata = sorted({row["settlement_stratum"] for row in scientific})
    counts = Counter(row["settlement_stratum"] for row in scientific)
    assert len(scientific) == 144
    assert len(strata) == 6 and set(counts.values()) == {24}

    items = calibrations() + scientific
    items_sha256 = hashlib.sha256(canonical(items)).hexdigest()
    artifact = {
        "kind": "dexagon.ainglish.manifest-bound-panel-items.v1",
        "sha256": items_sha256,
        "items": items,
    }
    (ROOT / "identity-relation.items.json").write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    template = seal({
        "kind": "dexagon.ainglish.manifest-bound-panel-template.v1",
        "proposal_revision": SLUG,
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": 2026082804,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "Each identity marker versus its complete registered meaning: one shared mutable object, verified-equal copies under the named check, or name match with contents unverified.",
        },
        "settlement_strata": [{"id": value, "weight": 1} for value in strata],
        "items": items,
        "panel": [
            {"name": "REPLACE-QUALIFIED-READER-A", "provider": "replace", "model": "replace"},
            {"name": "REPLACE-QUALIFIED-READER-B", "provider": "replace", "model": "replace"},
        ],
        "panel_neff": 2,
        "construct": "same-one / same-kind / same-name",
        "source_unspent_freeze": "flagship-carrier-bank-2026-08-26",
        "source_form_digests": source_digests,
        "scientific_items": len(scientific),
        "calibration_items": 12,
        "settlement_design": "form x consequence polarity; six equal-weight cells, 24 items per cell across twelve operational domains",
        "interpretation_guards": {
            "same_one": "tests propagation and whether independent divergence is compatible",
            "same_kind": "tests verified equality without claiming one shared mutable object",
            "same_name": "tests that name agreement alone establishes no content equality",
            "pooling": "all six cells are served; a strong form or polarity cannot conceal a weak one",
        },
        "items_artifact": {
            "file": "identity-relation.items.json",
            "published_url": (
                "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                f"{PUBLISHED_ITEMS_COMMIT}/identity-relation-manifest-bound-carrier-2026-08-28/identity-relation.items.json"
            ),
            "items_sha256": items_sha256,
            "activation_rule": "Activate only after these exact bytes are public and a two-lineage qualified panel is frozen.",
        },
        "activation": {
            "runnable": False,
            "reason": "The ordinary-English reader roster remains closed until a second lineage passes a fresh holdout.",
            "how": "Use the receipt-enforcing manifest-bound activate.py; commit the resulting runspec before panel.py run --submit.",
        },
        "model_calls": 0,
        "governance_writes": 0,
    })
    (ROOT / "identity-relation.template.json").write_text(
        json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    index = seal({
        "kind": "dexagon.ainglish.identity-relation-manifest-bound-carrier.v1",
        "proposal_revision": SLUG,
        "source_form_digests": source_digests,
        "items_sha256": items_sha256,
        "template_sha256": template["content_sha256"],
        "scientific_items": len(scientific),
        "calibration_items": 12,
        "settlement_strata": dict(sorted(counts.items())),
        "published_items_commit": PUBLISHED_ITEMS_COMMIT,
        "model_calls": 0,
        "governance_writes": 0,
    })
    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
