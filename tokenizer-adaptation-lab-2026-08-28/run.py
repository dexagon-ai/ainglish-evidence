#!/usr/bin/env python3
"""Train matched-budget control/Ainglish tokenizers from local public data only."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import statistics

from tokenizers import Tokenizer, models, pre_tokenizers, trainers


ROOT = Path(__file__).resolve().parent
SYMFONY = ROOT.parent.parent / "ainglish-symfony"
RELEASE = ROOT.parent.parent / "ainglish-releases" / "ainglish-training-v0.35.0"
CORPUS = SYMFONY / "public" / "corpus" / "slice-cfb0f4433028.json"
REPETITIONS = 32
CORE_TRAIN_BYTES = 8_000_000
CORE_EVAL_BYTES = 2_000_000
SUPPLEMENT_BYTES = 2_000_000
VOCAB_SIZES = (8_000, 16_000)
PRETOKENIZERS = ("punctuation_split", "whitespace_only")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clip_utf8(value: str, budget: int) -> str:
    return value.encode()[:budget].decode("utf-8", errors="ignore")


def take_documents(rows: list[str], budget: int) -> tuple[list[str], list[str]]:
    chosen, used = [], 0
    for index, row in enumerate(rows):
        candidate = row + "\n"
        size = len(candidate.encode())
        if used + size > budget:
            remaining = budget - used
            if remaining:
                chosen.append(clip_utf8(candidate, remaining))
            return chosen, rows[index + 1 :]
        chosen.append(candidate)
        used += size
        if used == budget:
            return chosen, rows[index + 1 :]
    raise SystemExit("REFUSING: public corpus is smaller than the fixed byte budget")


def supplement(values: list[str], neutral: list[str]) -> str:
    exposed = "".join((value + "\n") for _ in range(REPETITIONS) for value in values)
    exposed_bytes = len(exposed.encode())
    if exposed_bytes >= SUPPLEMENT_BYTES:
        raise SystemExit("REFUSING: matched exposure rows exceed supplement budget")
    filler = "".join(neutral)
    return exposed + clip_utf8(filler, SUPPLEMENT_BYTES - exposed_bytes)


def make_tokenizer(pretokenizer: str, vocab_size: int, iterator: list[str]) -> Tokenizer:
    tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
    if pretokenizer == "punctuation_split":
        tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
    elif pretokenizer == "whitespace_only":
        tokenizer.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
    else:
        raise AssertionError(pretokenizer)
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=2,
        special_tokens=["[UNK]", "[PAD]", "[BOS]", "[EOS]"],
        show_progress=False,
    )
    tokenizer.train_from_iterator(iterator, trainer=trainer, length=len(iterator))
    return tokenizer


def count(tokenizer: Tokenizer, values: list[str]) -> int:
    return sum(len(tokenizer.encode(value).ids) for value in values)


def main() -> None:
    version = importlib.metadata.version("tokenizers")
    if version != "0.22.2":
        raise SystemExit("REFUSING: tokenizers version drift")
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    parallel_path = RELEASE / "data" / "parallel.jsonl"
    register_path = RELEASE / "data" / "register.jsonl"
    parallel = [json.loads(line) for line in parallel_path.read_text(encoding="utf-8").splitlines() if line]
    register = [json.loads(line) for line in register_path.read_text(encoding="utf-8").splitlines() if line]
    marker_words = sorted({
        marker.lower()
        for row in register
        for marker in re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)+", row["form"])
    })
    marker_pattern = re.compile("|".join(re.escape(marker) for marker in marker_words), re.I)
    documents = []
    for row in corpus["records"]:
        text = "\n".join(str(row.get(key) or "") for key in ("title", "body")).strip()
        if len(text) >= 80 and "ainglish" not in text.lower() and not marker_pattern.search(text):
            documents.append(text)
    core_train, remaining = take_documents(documents, CORE_TRAIN_BYTES)
    core_eval, neutral = take_documents(remaining, CORE_EVAL_BYTES)
    control_supplement = supplement([row["english"] for row in parallel], neutral)
    ainglish_supplement = supplement([row["ainglish"] for row in parallel], neutral)
    if len(control_supplement.encode()) != SUPPLEMENT_BYTES or len(ainglish_supplement.encode()) != SUPPLEMENT_BYTES:
        raise SystemExit("REFUSING: supplement byte budget drift")

    marker_surfaces = sorted({
        match
        for row in register
        for match in re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)+", row["form"])
    })
    results = []
    models_by_cell: dict[tuple[int, str, str], Tokenizer] = {}
    for vocab_size in VOCAB_SIZES:
        for pretokenizer in PRETOKENIZERS:
            for exposure, extra in (("control_english", control_supplement), ("ainglish", ainglish_supplement)):
                tokenizer = make_tokenizer(pretokenizer, vocab_size, [*core_train, extra])
                path = ROOT / f"tokenizer-{vocab_size}-{pretokenizer}-{exposure}.json"
                tokenizer.save(str(path))
                vocab = tokenizer.get_vocab()
                row = {
                    "vocab_size_requested": vocab_size,
                    "vocab_size_observed": tokenizer.get_vocab_size(),
                    "pretokenizer": pretokenizer,
                    "exposure": exposure,
                    "tokenizer_sha256": sha(path),
                    "ordinary_eval": {
                        "bytes": sum(len(value.encode()) for value in core_eval),
                        "tokens": count(tokenizer, core_eval),
                    },
                    "release": {
                        "english_tokens": count(tokenizer, [pair["english"] for pair in parallel]),
                        "ainglish_tokens": count(tokenizer, [pair["ainglish"] for pair in parallel]),
                    },
                    "markers": {
                        "surfaces": len(marker_surfaces),
                        "tokens": count(tokenizer, marker_surfaces),
                        "single_token": sum(len(tokenizer.encode(value).ids) == 1 for value in marker_surfaces),
                        "per_surface": {value: len(tokenizer.encode(value).ids) for value in marker_surfaces},
                    },
                }
                row["release"]["delta"] = row["release"]["ainglish_tokens"] - row["release"]["english_tokens"]
                results.append(row)
                models_by_cell[(vocab_size, pretokenizer, exposure)] = tokenizer

    comparisons = []
    for vocab_size in VOCAB_SIZES:
        for pretokenizer in PRETOKENIZERS:
            control = next(row for row in results if row["vocab_size_requested"] == vocab_size and row["pretokenizer"] == pretokenizer and row["exposure"] == "control_english")
            adapted = next(row for row in results if row["vocab_size_requested"] == vocab_size and row["pretokenizer"] == pretokenizer and row["exposure"] == "ainglish")
            comparisons.append({
                "vocab_size": vocab_size,
                "pretokenizer": pretokenizer,
                "ainglish_release_token_change": adapted["release"]["ainglish_tokens"] - control["release"]["ainglish_tokens"],
                "careful_english_release_token_change": adapted["release"]["english_tokens"] - control["release"]["english_tokens"],
                "ordinary_eval_token_change": adapted["ordinary_eval"]["tokens"] - control["ordinary_eval"]["tokens"],
                "marker_token_change": adapted["markers"]["tokens"] - control["markers"]["tokens"],
                "single_token_marker_change": adapted["markers"]["single_token"] - control["markers"]["single_token"],
            })
    report = {
        "kind": "dexagon.ainglish.tokenizer-adaptation-lab.v1",
        "design": {
            "tokenizers_version": version,
            "core_training_bytes": CORE_TRAIN_BYTES,
            "ordinary_evaluation_bytes": CORE_EVAL_BYTES,
            "supplement_bytes_each": SUPPLEMENT_BYTES,
            "reviewed_pairs": len(parallel),
            "repetitions_per_pair": REPETITIONS,
            "control": "32 repeats of each careful-English reviewed pair, then neutral corpus filler to the fixed supplement byte budget",
            "ainglish": "32 repeats of each paired Ainglish rendering, then neutral corpus filler to the same fixed supplement byte budget",
            "pretokenizers": {
                "punctuation_split": "Whitespace: isolates punctuation, including hyphens",
                "whitespace_only": "WhitespaceSplit: keeps hyphenated whitespace-delimited forms together during BPE learning",
            },
            "boundary": "A small tokenizer-training simulation, not a production-tokenizer forecast. Exposure frequency is intentionally high enough to test whether vocabulary allocation can respond. Ordinary-corpus filtering is lexical and cannot prove absence of every Ainglish concept.",
        },
        "inputs": {
            "corpus_sha256": sha(CORPUS),
            "corpus_records": corpus["records_count"],
            "eligible_non_ainglish_documents": len(documents),
            "parallel_sha256": sha(parallel_path),
            "register_sha256": sha(register_path),
            "marker_surfaces": marker_surfaces,
        },
        "cells": results,
        "comparisons": comparisons,
        "model_calls": 0,
        "governance_evidence": False,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Tokenizer adaptation lab",
        "",
        "This matched-budget experiment asks a narrow question: if a tokenizer is actually trained with",
        "Ainglish surfaces, can it allocate vocabulary differently without changing the model weights?",
        "It crosses two vocabulary sizes, two pre-tokenization policies, and careful-English versus",
        "Ainglish exposure. Every cell receives 8 MB of the same filtered public English corpus plus a",
        "2 MB supplement; both supplements repeat each of the 57 semantic pairs exactly 32 times and use",
        "neutral filler to equalize bytes.",
        "",
        "| Vocab | Hyphen policy | Ainglish-token change | English-token change | Ordinary-eval change | Marker-token change | Single-token markers |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in comparisons:
        lines.append(
            f"| {row['vocab_size']} | `{row['pretokenizer']}` | {row['ainglish_release_token_change']:+d} | "
            f"{row['careful_english_release_token_change']:+d} | {row['ordinary_eval_token_change']:+d} | "
            f"{row['marker_token_change']:+d} | {row['single_token_marker_change']:+d} |"
        )
    lines += [
        "",
        "Negative token changes mean the Ainglish-exposed tokenizer used fewer tokens than its matched",
        "careful-English control. The ordinary-evaluation column is the corresponding cost or benefit on",
        "2 MB of held-out public English. The two hyphen policies are deliberately reported separately:",
        "vocabulary exposure cannot create a whole-marker token when the pre-tokenizer forbids merges",
        "across hyphens.",
        "",
        "This is not a claim about any laboratory's eventual production tokenizer. It demonstrates a",
        "mechanism and its trade-off under small, reproducible tokenizers. Model exposure and tokenizer",
        "adaptation remain different interventions.",
        "",
        f"Frozen report digest: `{report['content_sha256']}`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "report_sha256": report["content_sha256"], "comparisons": comparisons}, indent=2))


if __name__ == "__main__":
    main()
