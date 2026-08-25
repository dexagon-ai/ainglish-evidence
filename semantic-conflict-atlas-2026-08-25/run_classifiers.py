#!/usr/bin/env python3
"""Run two review-only model readers over the frozen semantic candidate packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "candidates.json"
TARGET = ROOT / "classifier-results.json"
BASE_URL = "http://127.0.0.1:11434"
MODELS = ["qwen2.5:7b", "gemma3:12b"]
LABELS = {
    "duplicate",
    "successor_or_refinement",
    "complementary_same_axis",
    "possible_conflict",
    "orthogonal_shared_vocabulary",
    "insufficient",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def post(path: str, payload: dict, timeout: int = 180) -> dict:
    request = urllib.request.Request(
        BASE_URL + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def get(path: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(BASE_URL + path, timeout=timeout) as response:
        return json.load(response)


def prompt(row: dict) -> str:
    left, right = row["left"], row["right"]
    return f"""You are routing a language-register review. Compare two exact proposal surfaces.
Choose one relation label only from: duplicate, successor_or_refinement, complementary_same_axis,
possible_conflict, orthogonal_shared_vocabulary, insufficient.

duplicate means the operational meanings are materially interchangeable.
successor_or_refinement means one preserves a core meaning while deliberately repairing or narrowing it.
complementary_same_axis means the items name different values on the same semantic distinction.
possible_conflict means following both mappings can prescribe incompatible readings in overlapping scope.
orthogonal_shared_vocabulary means they overlap in words but not operational meaning.
insufficient means the supplied surface cannot support a relation judgement.

Do not infer adoption, quality, or register authority. A model label is review routing, never an asserted edge.

LEFT
title: {left['title']}
form: {left['form']}
mapping: {left['english_mapping']}
constraints: {left['constraints']}
stage: {left['stage']}

RIGHT
title: {right['title']}
form: {right['form']}
mapping: {right['english_mapping']}
constraints: {right['constraints']}
stage: {right['stage']}

Return strict JSON with keys label, confidence (0..1), and reason (maximum 45 words)."""


def main() -> None:
    if TARGET.exists():
        raise SystemExit(f"REFUSING: {TARGET.name} already exists; no outcome rerun")
    source = json.loads(SOURCE.read_text())
    sealed = dict(source)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: candidate packet drift ({actual} != {expected})")
    tags = get("/api/tags")
    digests = {row["name"]: row.get("digest") for row in tags.get("models", [])}
    if any(model not in digests or not digests[model] for model in MODELS):
        raise SystemExit("REFUSING: a declared classifier model or digest is absent")
    results = []
    for position, row in enumerate(source["candidates"], 1):
        readings = []
        for model in MODELS:
            try:
                response = post("/api/generate", {
                    "model": model,
                    "prompt": prompt(row),
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0, "seed": 2026082514, "num_ctx": 4096, "num_predict": 180},
                    "keep_alive": "15m",
                })
                raw = response.get("response", "")
                parsed = json.loads(raw)
                label = parsed.get("label")
                confidence = float(parsed.get("confidence"))
                reason = str(parsed.get("reason", "")).strip()
                if label not in LABELS or not 0 <= confidence <= 1 or not reason:
                    raise ValueError("invalid classifier contract")
                readings.append({
                    "model": model, "model_digest": digests[model], "status": "ok",
                    "label": label, "confidence": confidence, "reason": reason,
                })
            except Exception as exc:
                readings.append({
                    "model": model, "model_digest": digests[model], "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                })
        ok = [reading for reading in readings if reading["status"] == "ok"]
        agreement = len(ok) == len(MODELS) and len({reading["label"] for reading in ok}) == 1
        results.append({
            "pair_id": row["pair_id"], "readings": readings,
            "model_agreement": agreement,
            "agreed_label": ok[0]["label"] if agreement else None,
            "review_required": True,
            "asserted_relation": None,
        })
        print(f"{position}/{len(source['candidates'])} {row['pair_id']} "
              f"{results[-1]['agreed_label'] or 'disagreement/error'}", flush=True)
    payload = {
        "kind": "dexagon.ainglish.semantic-conflict-classifier-results.v1",
        "candidate_packet_sha256": expected,
        "models": [{"name": model, "digest": digests[model]} for model in MODELS],
        "temperature": 0,
        "seed": 2026082514,
        "result_count": len(results),
        "results": results,
        "interpretation": "Model outputs route review only. They do not assert duplicate, conflict, or lineage edges.",
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    TARGET.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"results": len(results), "agreements": sum(r["model_agreement"] for r in results),
                      "content_sha256": payload["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
