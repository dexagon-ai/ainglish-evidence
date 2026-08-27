#!/usr/bin/env python3
"""Build zero-model manifest-bound flagship carrier templates from unspent frozen items."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
REPEAT_SLUG = "repeat-event-restore-state-did-again-repeat-the-action-or-on-4"
PUBLISHED_ITEMS_COMMIT = "069790cb0efd9dbb25a667c613e5bc0bcfd8ce0f"
PUBLISHED_ITEMS_BASE = (
    "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
    f"{PUBLISHED_ITEMS_COMMIT}/manifest-bound-flagship-carriers-v1-2026-08-27"
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load(relative: str) -> dict:
    return json.loads((EVIDENCE / relative).read_text(encoding="utf-8"))


def seal(value: dict) -> dict:
    value = dict(value)
    value["content_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    return value


def write(name: str, value: dict) -> dict:
    value = seal(value)
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"file": name, "content_sha256": value["content_sha256"]}


def attach_item_artifact(template: dict, name: str) -> dict:
    items = template["items"]
    digest = hashlib.sha256(canonical(items)).hexdigest()
    artifact = {
        "kind": "dexagon.ainglish.manifest-bound-panel-items.v1",
        "sha256": digest,
        "items": items,
    }
    (ROOT / name).write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    template["items_artifact"] = {
        "file": name,
        "published_url": f"{PUBLISHED_ITEMS_BASE}/{name}",
        "items_sha256": digest,
        "activation_rule": "Publish these exact bytes, then activate with their HTTPS URL; the runnable manifest carries URL plus digest instead of exceeding the 20 KB commitment cap.",
    }
    return template


def contract(ids: list[str]) -> list[dict]:
    return [{"id": ident, "weight": 1} for ident in ids]


def template_base(slug: str, seed: int, items: list[dict], strata: list[str], comparator: dict) -> dict:
    return {
        "kind": "dexagon.ainglish.manifest-bound-panel-template.v1",
        "proposal_revision": slug,
        "slug": slug,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "comparator": comparator,
        "settlement_strata": contract(strata),
        "items": items,
        "panel": [
            {"name": "REPLACE-QUALIFIED-READER-A", "provider": "replace", "model": "replace"},
            {"name": "REPLACE-QUALIFIED-READER-B", "provider": "replace", "model": "replace"},
        ],
        "panel_neff": 2,
        "activation": {
            "runnable": False,
            "reason": "The independently qualified two-lineage roster remains closed at 1/2.",
            "how": "Use activate.py with an exact two-reader panel JSON after both lineages qualify; commit and push its output before the first reader call.",
        },
        "model_calls": 0,
        "governance_writes": 0,
    }


def repeat_restore() -> tuple[dict, dict]:
    source = load("repeat-restore-force-comprehension-carrier-v1-2026-08-26/items.json")
    scientific = []
    for original in source["scientific_rows"]:
        row = dict(original)
        row["settlement_stratum"] = ".".join((row["form"], row["force"], row["probe"]))
        scientific.append(row)
    ids = sorted({row["settlement_stratum"] for row in scientific})
    counts = Counter(row["settlement_stratum"] for row in scientific)
    assert len(ids) == 16 and set(counts.values()) == {16}
    items = [dict(row) for row in source["calibration_rows"]] + scientific
    result = template_base(
        REPEAT_SLUG,
        2026082701,
        items,
        ids,
        {
            "kind": "complete-careful-english-v1",
            "description": "The force-matched full current mapping for repeat-event or restore-state, including its projected background condition.",
        },
    )
    result.update({
        "construct": "repeat-event / restore-state",
        "source_unspent_freeze": "repeat-restore-force-comprehension-carrier-v1-2026-08-26/items.json",
        "scientific_items": len(scientific),
        "calibration_items": len(source["calibration_rows"]),
        "settlement_design": "form x at-issue force x independently scored probe; every one of 16 cells is load-bearing",
        "validity_fixture_sidecar": {
            "source": "repeat-restore-force-comprehension-carrier-v1-2026-08-26/items.json#validity_rows",
            "status": "retained diagnostic, not mixed into the paired accuracy estimand",
            "reason": "Its English rows are licence-check instructions rather than complete paired controls; pooling them would manufacture an easy English arm.",
        },
    })
    return result, {"strata": len(ids), "per_stratum": 16, "scientific": len(scientific)}


def planted_calibrations() -> list[dict]:
    rows = []
    for index in range(12):
        bay = 41 + index
        answer = f"bay {bay}"
        options = [answer, f"bay {bay + 1}", "not stated", "dispatch desk"]
        options = options[index % 4:] + options[:index % 4]
        rows.append({
            "id": f"role-cardinality-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The routing note labels parcel {index + 1} zof({bay}), but gives no meaning for zof.",
            "ainglish": f"Control: zof(N) means the labelled parcel is stored in bay N. The routing note labels parcel {index + 1} zof({bay}).",
            "question": "Where does the control place the parcel?",
            "options": options,
            "answer": answer,
            "calibration_construct": "target-independent zof location marker",
        })
    return rows


def role_cardinality() -> tuple[dict, dict]:
    source_dir = "one-or-more-exactly-one-comprehension-carrier-2026-08-26"
    scientific = []
    for form in ("one-or-more", "exactly-one"):
        for comparison in ("careful", "bare"):
            source = load(f"{source_dir}/items-{form}-{comparison}.json")
            for original in source["items"]:
                if original.get("calibration"):
                    continue
                row = dict(original)
                cell = int(row["strata"]["cell"])
                row["settlement_stratum"] = f"{form}.{comparison}.cell-{cell:02d}"
                scientific.append(row)
    ids = sorted({row["settlement_stratum"] for row in scientific})
    counts = Counter(row["settlement_stratum"] for row in scientific)
    assert len(ids) == 48 and set(counts.values()) == {10}
    result = template_base(
        "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
        2026082702,
        planted_calibrations() + scientific,
        ids,
        {
            "kind": "role-cardinality-dual-comparator-v1",
            "description": "Every form is separately compared with both its full careful mapping and a byte-identical bare indefinite-singular instruction; all twelve semantic cells remain separate.",
        },
    )
    result.update({
        "construct": "one-or-more(<role>) / exactly-one(<role>)",
        "source_unspent_freeze": source_dir,
        "scientific_items": len(scientific),
        "calibration_items": 12,
        "settlement_design": "form x comparator x semantic cell; 48 equal-weight load-bearing cells, ten operational roles per cell",
        "role_scope_seams": {
            "named_role_only": "cell-06",
            "independence_nonclaim": "cell-09",
            "delegation_nonclaim": "cell-10",
            "cross_role_eligibility_nonclaim": "cell-11",
            "rule": "A cardinality marker counts distinct principals only inside the named role. It does not imply independence, delegation rights, or eligibility for another role.",
        },
    })
    return result, {"strata": len(ids), "per_stratum": 10, "scientific": len(scientific)}


def replacement_original(name: str, source_path: str, comparator: dict) -> tuple[dict, dict]:
    source = load(source_path)
    scientific = []
    for original in source["items"]:
        row = dict(original)
        if not row.get("calibration"):
            row["settlement_stratum"] = row["form"]
            scientific.append(row)
    ids = sorted({row["settlement_stratum"] for row in scientific})
    items = [dict(row) for row in source["items"]]
    science_by_id = {row["id"]: row for row in scientific}
    items = [science_by_id.get(row["id"], row) for row in items]
    result = template_base(source["slug"], int(source["seed"]) + 1000, items, ids, comparator)
    result.update({
        "construct": name,
        "source_unspent_freeze": source_path,
        "scientific_items": len(scientific),
        "calibration_items": sum(bool(row.get("calibration")) for row in items),
        "legacy_original_hash": source["replicates_hash"],
        "replicates_hash": None,
        "filing_mode": "new stratified original, not a replication of the legacy pooled row",
        "reason": "A legacy pooled original cannot acquire post-hoc strata. This fresh unspent population must start a manifest-bound original, then await a different principal's fresh stratified replication.",
    })
    return result, {"strata": len(ids), "counts": dict(Counter(row["settlement_stratum"] for row in scientific))}


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    outputs = {}
    repeat, repeat_audit = repeat_restore()
    repeat = attach_item_artifact(repeat, "repeat-restore.items.json")
    outputs["repeat_restore"] = {**write("repeat-restore.template.json", repeat), **repeat_audit}
    role, role_audit = role_cardinality()
    role = attach_item_artifact(role, "role-cardinality.items.json")
    outputs["role_cardinality"] = {**write("role-cardinality.template.json", role), **role_audit}
    replacements = (
        ("preference", "preference valence", "flagship-dispute-replication-carriers-2026-08-26/items-preference.json", {"kind": "complete-careful-english-v1", "description": "Each preference marker versus its full registered mapping."}),
        ("persistence", "directive persistence", "flagship-dispute-replication-carriers-2026-08-26/items-persistence.json", {"kind": "shortest-adequate-careful-control-v1", "description": "this-once/from-now-on versus its shortest adequate careful control."}),
        ("may", "may force", "may-modal-settlement-replication-2026-08-26/items.json", {"kind": "shortest-adequate-careful-control-v1", "description": "permission/possibility marker versus is-permitted-to/might."}),
    )
    for key, title, path, comparator in replacements:
        result, audit = replacement_original(title, path, comparator)
        result = attach_item_artifact(result, f"{key}-replacement-original.items.json")
        outputs[key] = {**write(f"{key}-replacement-original.template.json", result), **audit}
    index = {
        "kind": "dexagon.ainglish.manifest-bound-flagship-carrier-index.v1",
        "generated_from_unspent_frozen_items": True,
        "outputs": outputs,
        "model_calls": 0,
        "tokenizer_calls": 0,
        "governance_writes": 0,
        "external_gate": "Symfony PR 297 and SDK PR 98 merged/deployed, then a second independently qualified reader lineage",
    }
    write("index.json", index)
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
