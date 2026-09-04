#!/usr/bin/env python3
"""Freeze three fresh legacy token replication manifests without loading a tokenizer."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODELS = ["cl100k_base", "o200k_base", "p50k_base"]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def consider_pairs() -> list[dict]:
    nouns = ["budget note", "safety report", "route change", "appeal", "draft standard"]
    rows = []
    for index, noun in enumerate(nouns):
        ref = f"{noun.replace(' ', '-')}-{index + 41}"
        rows.append({"id": f"consider-{index + 1:02d}", "english": f"Please table the {noun} identified as {ref} for this meeting.", "ainglish": f"consider-now({ref})."})
        rows.append({"id": f"postpone-{index + 1:02d}", "english": f"Please table the {noun} identified as {ref} until a later meeting.", "ainglish": f"postpone({ref})."})
    return rows


def since_pairs() -> list[dict]:
    events = [
        ("the mirror lost quorum", "publication is blocked", "publication has required manual approval"),
        ("the sensor was replaced", "the readings are stable", "the readings have stayed stable"),
        ("the contract expired", "purchasing is paused", "purchasing has remained paused"),
        ("the index was rebuilt", "search is faster", "search has stayed faster"),
        ("the archive moved", "retrieval is slower", "retrieval has remained slower"),
    ]
    rows = []
    for index, (event, causal, temporal) in enumerate(events):
        rows.append({"id": f"because-{index + 1:02d}", "english": f"Since {event}, {causal} in case {index + 61}.", "ainglish": f"Because {event}, {causal} in case {index + 61}."})
        rows.append({"id": f"ever-since-{index + 1:02d}", "english": f"Since {event}, {temporal} in case {index + 71}.", "ainglish": f"Ever since {event}, {temporal} in case {index + 71}."})
    return rows


def replace_pairs() -> list[dict]:
    nouns = ["relay", "certificate", "worker", "schema", "mirror", "queue", "policy", "adapter", "dataset", "gateway"]
    rows = []
    for index, noun in enumerate(nouns):
        old = f"{noun}-legacy-{index + 81}"
        new = f"{noun}-current-{index + 91}"
        rows.append({"id": f"replace-{index + 1:02d}", "english": f"Replace departing {old} with incoming {new} in the active slot.", "ainglish": f"replace(old={old}, new={new})."})
    return rows


def write(name: str, public_id: str, slug: str, construct: str, target: str, pairs: list[dict]) -> dict:
    assert len(pairs) == 10 and len({(row["english"], row["ainglish"]) for row in pairs}) == 10
    manifest = {
        "metric": "token_delta", "construct": construct, "models": MODELS,
        "replicates_hash": target, "test_set": pairs,
        "seed": "deterministic-no-randomness-20260904",
        "method": "tiktoken encode count difference between Ainglish and English for every complete pair; equal pair mean per tokenizer; headline is the maximum tokenizer mean",
        "environment": {"library": "tiktoken", "version": "0.14.0"},
    }
    path = ROOT / f"{name}.manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "name": name, "public_id": public_id, "slug": slug, "construct": construct,
        "replicates_hash": target, "file": path.name, "pair_count": len(pairs),
        "manifest_sha256": sha256(canonical(manifest)).hexdigest(),
        "pairs_sha256": sha256(canonical(pairs)).hexdigest(),
    }


def main() -> None:
    campaigns = [
        write("consider-postpone", "a-ge8tz4ejhpknbghe", "consider-now-matter-postpone-matter-never-use-procedural", "consider-now / postpone", "055e4849c715c9c7ef7db0e3180096c0d86a8ac4fd89d8cf634eb0fe6408c404", consider_pairs()),
        write("because-ever-since", "a-hjhq14a5ew4khaqp", "because-clause-ever-since-time-or-event-interval-compatible", "because / ever since", "fc4685f26b41e8b97cf85660cc4139d103e8ca9de63b2d73b1ff0c24426e6f7f", since_pairs()),
        write("replacement-roles", "a-f34mb0zf8xp2pkwm", "replace-old-departing-ref-new-incoming-ref", "replace(old, new)", "dcc44e99b046b16139a87497c0ffe036d3d32f310407b8f6e8cf721f1ef7f5c8", replace_pairs()),
    ]
    all_pairs = []
    for row in campaigns:
        all_pairs.extend(json.loads((ROOT / row["file"]).read_text(encoding="utf-8"))["test_set"])
    assert len({(row["english"], row["ainglish"]) for row in all_pairs}) == 30
    output = {
        "kind": "dexagon.ainglish.legacy-token-settlement-wave.v1", "model_calls": 0,
        "tokenizer_calls": 0, "tiktoken_version": "0.14.0", "campaigns": {row["name"]: row for row in campaigns},
    }
    output["content_sha256"] = sha256(canonical(output)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

