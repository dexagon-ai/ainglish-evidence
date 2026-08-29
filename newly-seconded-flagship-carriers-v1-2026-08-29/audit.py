#!/usr/bin/env python3
"""Offline structural, semantic, freshness, and manifest-size audit."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
FORMS = {
    "average": ("mean-of", "median-of"),
    "deletion": ("removed-from", "erased-from"),
}
COMPARATORS = ("bare", "careful", "practical")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if "content_sha256" in value:
        sealed = dict(value)
        expected = sealed.pop("content_sha256")
        assert sha(sealed) == expected
    return value


def prior_answer_triples() -> set[tuple[str, str, str]]:
    found = set()
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if all(isinstance(current.get(key), str) for key in ("ainglish", "question", "answer")):
                    found.add((current["ainglish"], current["question"], current["answer"]))
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
    return found


def audit_comprehension(name: str, forms: tuple[str, str], prior: set[tuple[str, str, str]]) -> dict:
    packet = json.loads((ROOT / f"{name}-comprehension-items.json").read_text(encoding="utf-8"))
    rows = packet["items"]
    assert sha(rows) == packet["items_sha256"]
    assert len(rows) == 160 and len({row["id"] for row in rows}) == 160
    assert {form: sum(row["form"] == form for row in rows) for form in forms} == {form: 80 for form in forms}
    assert set(packet["comparators"]) == set(COMPARATORS)
    assert all(all(row[field] for field in ("ainglish", *COMPARATORS, "question", "answer")) for row in rows)
    assert all(row["answer"] in row["options"] and len(row["options"]) == 3 for row in rows)
    assert [sum(row["options"].index(row["answer"]) == pos for row in rows) for pos in range(3)] in (
        [54, 53, 53], [53, 54, 53], [53, 53, 54]
    )
    pairs = {}
    for row in rows:
        pairs.setdefault(row["scenario_id"], []).append(row)
    assert len(pairs) == 80 and all(len(pair) == 2 for pair in pairs.values())
    assert all({row["form"] for row in pair} == set(forms) for pair in pairs.values())
    if name == "average":
        assert all(len({row["population_ref"] for row in pair}) == 1 for pair in pairs.values())
        assert all(len({row["unit"] for row in pair}) == 1 for pair in pairs.values())
    else:
        assert all(pair[0]["bare"] == pair[1]["bare"] for pair in pairs.values())
    hard_counts = {cell: sum(row["hard_cell"] == cell for row in rows) for cell in sorted({row["hard_cell"] for row in rows})}
    assert min(hard_counts.values()) >= (16 if name == "average" else 12)
    current = {(row["ainglish"], row["question"], row["answer"]) for row in rows}
    assert not current & prior
    if name == "average":
        for row in rows:
            values = row["hidden_values"]
            mean_value = Fraction(sum(values), len(values))
            median_value = Fraction(median(values))
            render = lambda value: str(value.numerator) if value.denominator == 1 else f"{value.numerator / value.denominator:.2f}"
            assert row["derived_mean"] == render(mean_value)
            assert row["derived_median"] == render(median_value)
            assert row["hidden_values_exposed_to_reader"] is False
            assert row["population_ref"] in row["ainglish"] and row["population_ref"] in row["careful"]
            assert row["population_ref"] in row["answer"]
            assert row["answer"].startswith(row["primary_statistic_population"])
    else:
        for row in rows:
            ref = row["surface_ref"] if row["form"] == "removed-from" else row["inventory_ref"]
            assert row["object_ref"] in row["ainglish"] and ref in row["ainglish"]
            assert row["epoch"] in row["ainglish"] and ref in row["careful"]
            assert ref in row["answer"] and row["epoch"] in row["answer"]
            assert row["answer"].startswith(row["primary_scope_epoch"])
    templates = json.loads((ROOT / f"{name}-comprehension-templates.json").read_text(encoding="utf-8"))
    assert sha(templates["templates"]) == templates["templates_sha256"]
    assert len(templates["templates"]) == 6
    assert {(row["form"], row["comparator"]) for row in templates["templates"]} == {
        (form, comparator) for form in forms for comparator in COMPARATORS
    }
    assert all(row["items"] == 80 and row["activation"]["required_distinct_base_lineages"] == 2 for row in templates["templates"])
    return {"items": 160, "forms": {form: 80 for form in forms}, "hard_cells": hard_counts, "templates": 6}


def audit_token(name: str, forms: tuple[str, str]) -> dict:
    packet = checked(ROOT / f"{name}-token-items.json")
    rows = packet["test_set"]
    assert sha(rows) == packet["items_sha256"]
    assert len(rows) == 32 and len({row["item_id"] for row in rows}) == 32
    assert packet["form_counts"] == {form: sum(row["form"] == form for row in rows) for form in forms} == {form: 16 for form in forms}
    comprehension = json.loads((ROOT / f"{name}-comprehension-items.json").read_text(encoding="utf-8"))["items"]
    source_pairs = {(row["id"], row["ainglish"], row["careful"]) for row in comprehension}
    assert all((row["item_id"], row["ainglish"], row["english"]) in source_pairs for row in rows)
    assert all(row["ainglish"] != row["english"] for row in rows)
    manifest_probe = {
        "metric": "token_delta", "formula_version": 1,
        "construct": name, "models": ["tiktoken/cl100k_base", "tiktoken/o200k_base", "tiktoken/p50k_base"],
        "test_set": rows, "items_sha256": packet["items_sha256"], "test_set_note": packet["comparison"],
        "estimand": {"population": "32 frozen pairs", "acceptance": packet["acceptance"]},
        "evidentiary_limit": packet["evidentiary_limit"],
    }
    assert len(canonical(manifest_probe)) < 20_000
    return {"pairs": 32, "forms": packet["form_counts"], "manifest_probe_bytes": len(canonical(manifest_probe))}


def main() -> None:
    snapshot = checked(ROOT / "proposal-snapshots.json")
    index = checked(ROOT / "index.json")
    assert index["proposal_snapshot_sha256"] == snapshot["content_sha256"]
    for name, digest in index["artifacts"].items():
        assert sha(json.loads((ROOT / name).read_text(encoding="utf-8"))) == digest
    prior = prior_answer_triples()
    result = {
        "status": "ok",
        "average_comprehension": audit_comprehension("average", FORMS["average"], prior),
        "average_token": audit_token("average", FORMS["average"]),
        "deletion_comprehension": audit_comprehension("deletion", FORMS["deletion"], prior),
        "deletion_token": audit_token("deletion", FORMS["deletion"]),
        "prior_exact_answer_triple_overlap": 0,
        "model_calls": 0,
        "tokenizer_calls": 0,
        "governance_writes": 0,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
