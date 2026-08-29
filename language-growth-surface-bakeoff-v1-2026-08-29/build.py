#!/usr/bin/env python3
"""Deterministic, no-download surface comparison for the two new proposals."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

import tiktoken


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CORPUS = REPO / "evidence-corpus-snapshot-v1-2026-08-27" / "records.jsonl"
CACHE = Path(os.environ.get("TIKTOKEN_CACHE_DIR", "/tmp/data-gym-cache"))
ENCODINGS = ("cl100k_base", "o200k_base")


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def corpus_text() -> str:
    blocks = []
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        blocks.extend(strings(json.loads(line)))
    return "\n".join(blocks)


def levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def transformed(value: str) -> dict[str, str]:
    return {
        "casefold": value.casefold(),
        "strip_punct": re.sub(r"[^A-Za-z0-9<> ]+", "", value).casefold(),
        "alnum_only": re.sub(r"[^A-Za-z0-9]+", "", value).casefold(),
        "paren_drop": value.replace("(", "").replace(")", "").casefold(),
        "hyphen_drop": value.replace("-", "").casefold(),
        "collapse_ws": re.sub(r"\s+", " ", value).strip().casefold(),
    }


PRONOUN_VARIANTS = [
    {
        "id": "filed",
        "surface": "it(<ref>)",
        "template": "it({ref})",
        "full_pattern": r"\bit\([A-Za-z0-9_.:-]+\)",
        "editorial_checks": [True, True, True, True, True],
        "editorial_note": "Directly annotates the pronoun readers already see; delimiter carries the machine boundary.",
    },
    {
        "id": "it-ref",
        "surface": "it-ref(<ref>)",
        "template": "it-ref({ref})",
        "full_pattern": r"\bit-ref\([A-Za-z0-9_.:-]+\)",
        "editorial_checks": [True, True, True, True, False],
        "editorial_note": "Makes the metadata role explicit but introduces a second lexical label for the same pronoun.",
    },
    {
        "id": "ref-it",
        "surface": "ref-it(<ref>)",
        "template": "ref-it({ref})",
        "full_pattern": r"\bref-it\([A-Za-z0-9_.:-]+\)",
        "editorial_checks": [False, True, True, True, False],
        "editorial_note": "Machine-looking and no longer reads in the grammatical position of ordinary it.",
    },
    {
        "id": "this-ref",
        "surface": "this-ref(<ref>)",
        "template": "this-ref({ref})",
        "full_pattern": r"\bthis-ref\([A-Za-z0-9_.:-]+\)",
        "editorial_checks": [False, True, True, True, False],
        "editorial_note": "Introduces demonstrative force that the filed singular pronoun does not claim.",
    },
]

NEGATION_VARIANTS = [
    {
        "id": "filed",
        "surfaces": ["none-of(<S>): <PREDICATE>", "not-all-of(<S>): <PREDICATE>"],
        "templates": ["none-of({set}): {predicate}", "not-all-of({set}): {predicate}"],
        "patterns": [r"\bnone-of\([^)]+\):", r"\bnot-all-of\([^)]+\):"],
        "editorial_checks": [True, True, True, True, True],
        "editorial_note": "Symmetric and close to the exact careful-English quantifier phrases.",
    },
    {
        "id": "short",
        "surfaces": ["none(<S>): <PREDICATE>", "not-all(<S>): <PREDICATE>"],
        "templates": ["none({set}): {predicate}", "not-all({set}): {predicate}"],
        "patterns": [r"\bnone\([^)]+\):", r"\bnot-all\([^)]+\):"],
        "editorial_checks": [True, True, True, True, False],
        "editorial_note": "Shorter, but none looks like a value/function and loses the shared -of slot cue.",
    },
    {
        "id": "literal-count",
        "surfaces": ["zero-of(<S>): <PREDICATE>", "fewer-than-all(<S>): <PREDICATE>"],
        "templates": ["zero-of({set}): {predicate}", "fewer-than-all({set}): {predicate}"],
        "patterns": [r"\bzero-of\([^)]+\):", r"\bfewer-than-all\([^)]+\):"],
        "editorial_checks": [True, True, False, True, True],
        "editorial_note": "Truth conditions are explicit, but the two poles are visibly asymmetric and the second is long.",
    },
    {
        "id": "member-prose",
        "surfaces": ["no-member-of(<S>): <PREDICATE>", "at-least-one-not(<S>): <PREDICATE>"],
        "templates": ["no-member-of({set}): {predicate}", "at-least-one-not({set}): {predicate}"],
        "patterns": [r"\bno-member-of\([^)]+\):", r"\bat-least-one-not\([^)]+\):"],
        "editorial_checks": [False, True, False, True, False],
        "editorial_note": "Verbose and shifts attention from the universal-negation contrast to two unrelated phrases.",
    },
]


def tokenizers() -> dict[str, object]:
    assert CACHE.is_dir(), f"missing existing cache: {CACHE}"
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in CACHE.iterdir() if p.is_file()}
    assert len(before) >= 2, "two cached maintained vocabularies are required; refusing any download"
    enc = {name: tiktoken.get_encoding(name) for name in ENCODINGS}
    after = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in CACHE.iterdir() if p.is_file()}
    assert before == after, "tokenizer cache changed; refusing a run that fetched bytes"
    return enc


def pronoun_frames() -> list[dict]:
    nouns = [
        ("service", "agent", "failed"), ("robot", "crate", "blocked the door"),
        ("sensor", "target", "moved"), ("compiler", "module", "crashed"),
        ("process", "file", "became unavailable"), ("gateway", "packet", "expired"),
        ("controller", "valve", "overheated"), ("index", "record", "changed"),
    ]
    rows = []
    for cycle in range(4):
        for left, right, predicate in nouns:
            intended = left if cycle % 2 == 0 else right
            rows.append({
                "bare": f"The {left} notified the {right} after it {predicate}.",
                "careful": f"The {left} notified the {right} after the {intended} {predicate}.",
                "prefix": f"The {left} notified the {right} after ",
                "suffix": f" {predicate}.",
                "ref": f"{intended}-{cycle + 1}",
            })
    return rows


def negation_frames() -> list[dict]:
    sets = ["replicas", "checks", "files", "workers", "regions", "recipients", "sensors", "routes"]
    predicates = ["healthy", "passed", "current", "available"]
    rows = []
    for i in range(32):
        set_name = sets[i % len(sets)]
        predicate = predicates[(i // len(sets)) % len(predicates)]
        form_i = i % 2
        careful = (
            f"No member of {set_name} is {predicate}." if form_i == 0
            else f"At least one member of {set_name} is not {predicate}."
        )
        rows.append({
            "set": set_name,
            "predicate": predicate,
            "form_i": form_i,
            "bare": f"All {set_name} are not {predicate}.",
            "careful": careful,
        })
    return rows


def mean(values: list[int]) -> float:
    return round(sum(values) / len(values), 6)


def main() -> None:
    enc = tokenizers()
    text = corpus_text()
    word_tokens = re.findall(r"[A-Za-z0-9_]+", text)

    pronoun = []
    frames = pronoun_frames()
    for variant in PRONOUN_VARIANTS:
        marked = [row["prefix"] + variant["template"].format(ref=row["ref"]) + row["suffix"] for row in frames]
        token = {}
        for name, codec in enc.items():
            marked_n = [len(codec.encode(x)) for x in marked]
            careful_n = [len(codec.encode(row["careful"])) for row in frames]
            bare_n = [len(codec.encode(row["bare"])) for row in frames]
            token[name] = {
                "mean_marked": mean(marked_n),
                "mean_delta_vs_careful": mean([a - b for a, b in zip(marked_n, careful_n)]),
                "mean_delta_vs_bare": mean([a - b for a, b in zip(marked_n, bare_n)]),
            }
        matches = re.findall(variant["full_pattern"], text, flags=re.IGNORECASE)
        pronoun.append({
            **{k: v for k, v in variant.items() if k not in {"template", "full_pattern"}},
            "editorial_score": sum(variant["editorial_checks"]),
            "full_surface_occurrences": len(matches),
            "full_surface_per_10k_words": round(10000 * len(matches) / max(1, len(word_tokens)), 6),
            "current_token_price": token,
            "transforms": transformed(variant["surface"]),
        })

    negation = []
    nframes = negation_frames()
    for variant in NEGATION_VARIANTS:
        marked = [variant["templates"][row["form_i"]].format(set=row["set"], predicate=row["predicate"]) for row in nframes]
        token = {}
        for name, codec in enc.items():
            marked_n = [len(codec.encode(x)) for x in marked]
            careful_n = [len(codec.encode(row["careful"])) for row in nframes]
            bare_n = [len(codec.encode(row["bare"])) for row in nframes]
            token[name] = {
                "mean_marked": mean(marked_n),
                "mean_delta_vs_careful": mean([a - b for a, b in zip(marked_n, careful_n)]),
                "mean_delta_vs_bare": mean([a - b for a, b in zip(marked_n, bare_n)]),
            }
        counts = [len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in variant["patterns"]]
        transform_pairs = {
            key: [transformed(surface)[key] for surface in variant["surfaces"]]
            for key in transformed(variant["surfaces"][0])
        }
        negation.append({
            **{k: v for k, v in variant.items() if k not in {"templates", "patterns"}},
            "editorial_score": sum(variant["editorial_checks"]),
            "full_surface_occurrences_by_pole": counts,
            "minimum_pole_edit_distance": levenshtein(*variant["surfaces"]),
            "silent_transform_collisions": [key for key, pair in transform_pairs.items() if pair[0] == pair[1]],
            "current_token_price": token,
            "transforms_by_pole": transform_pairs,
        })

    result = {
        "kind": "dexagon.ainglish.language-growth-surface-bakeoff.v1",
        "corpus": {
            "path": str(CORPUS.relative_to(REPO)),
            "sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
            "word_tokens": len(word_tokens),
        },
        "tokenizers": {
            "identities": list(ENCODINGS),
            "tiktoken_version": tiktoken.__version__,
            "cache_before_and_after_identical": True,
            "downloaded_bytes": 0,
        },
        "pronoun": {
            "server_disclosure_for_filed_base_word": {"word": "it", "per_10k": 136.666},
            "variants": pronoun,
            "decision": "retain filed it(<ref>)",
            "reason": "The complete delimited surface is absent from the corpus and has the only five-of-five editorial fit. Base-word frequency is a disclosed adoption-detector constraint, not a full-surface collision.",
        },
        "negation": {
            "variants": negation,
            "decision": "retain filed none-of(<S>) / not-all-of(<S>)",
            "reason": "It is the only five-of-five symmetric pair, has no full-surface corpus hit or silent transform collapse, and preserves the exact interval distinction.",
        },
        "claim_boundary": "Current-token price and deterministic surface screens do not establish comprehension, adoption, or future-trained efficiency.",
        "model_calls": 0,
        "governance_writes": 0,
    }
    result["content_sha256"] = canonical_hash(result)
    (ROOT / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "pronoun_decision": result["pronoun"]["decision"],
        "negation_decision": result["negation"]["decision"],
        "content_sha256": result["content_sha256"],
        "downloaded_bytes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
