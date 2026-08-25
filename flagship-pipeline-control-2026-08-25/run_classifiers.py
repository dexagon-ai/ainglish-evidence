#!/usr/bin/env python3
"""Run two frozen local semantic routers over the targeted pair packet."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "semantic-candidates.json"
TARGET = ROOT / "semantic-results.json"
LEDGER = ROOT / "semantic-ledger.jsonl"
BASE = os.environ.get("AINGLISH_ATLAS_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
MODELS = ("dexagon-gemma3-12b-flagship-atlas:ctx4k", "dexagon-mistral-small3.2-24b-flagship-atlas:ctx4k")
LABELS = {"duplicate", "successor_or_refinement", "complementary_same_axis", "possible_conflict", "orthogonal", "partial_overlap", "insufficient"}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=30) as response:
        return json.load(response)


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.load(response)


def prompt(row: dict) -> str:
    left, right = row["left"], row["right"]
    return f"""Route a review of two exact Ainglish proposal surfaces. Choose one label:
duplicate, successor_or_refinement, complementary_same_axis, possible_conflict, orthogonal,
partial_overlap, insufficient.

Duplicate means operationally interchangeable. Complementary means distinct values on one axis.
Possible_conflict means both can apply to one message but prescribe incompatible readings.
Partial_overlap means a meaningful shared cell exists but neither fully subsumes the other.
Orthogonal means independent axes that can compose. Do not infer quality, adoption, or authority.

Review focus: {row['review_question']}

LEFT title: {left['title']}
LEFT form: {left['form']}
LEFT mapping: {left['english_mapping']}
LEFT constraints: {json.dumps(left['constraints'], ensure_ascii=False)}

RIGHT title: {right['title']}
RIGHT form: {right['form']}
RIGHT mapping: {right['english_mapping']}
RIGHT constraints: {json.dumps(right['constraints'], ensure_ascii=False)}

Return strict JSON: label, confidence from 0 to 1, reason in at most 45 words."""


def main() -> None:
    if TARGET.exists():
        raise SystemExit("REFUSING: semantic-results.json exists")
    packet = json.loads(SOURCE.read_text(encoding="utf-8"))
    sealed = dict(packet); expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("candidate packet drift")
    tags = {row["name"]: row["digest"] for row in get("/api/tags").get("models", [])}
    if any(model not in tags for model in MODELS):
        raise SystemExit("declared classifier tag absent")
    results = []
    for index, row in enumerate(packet["candidates"], 1):
        readings = []
        for model in MODELS:
            try:
                response = post("/api/generate", {"model": model, "prompt": prompt(row), "stream": False, "format": "json", "options": {"temperature": 0, "seed": 2026082517, "num_ctx": 4096, "num_predict": 180}, "keep_alive": "15m"})
                parsed = json.loads(response.get("response", ""))
                label = parsed.get("label"); confidence = float(parsed.get("confidence")); reason = str(parsed.get("reason", "")).strip()
                if label not in LABELS or not 0 <= confidence <= 1 or not reason:
                    raise ValueError("invalid classifier contract")
                readings.append({"model": model, "model_digest": tags[model], "status": "ok", "label": label, "confidence": confidence, "reason": reason})
            except Exception as exc:
                readings.append({"model": model, "model_digest": tags[model], "status": "error", "error": f"{type(exc).__name__}: {exc}"})
        ok = [reading for reading in readings if reading["status"] == "ok"]
        agreement = len(ok) == 2 and ok[0]["label"] == ok[1]["label"]
        result = {"pair_id": row["pair_id"], "readings": readings, "model_agreement": agreement, "agreed_label": ok[0]["label"] if agreement else None, "review_required": True, "asserted_relation": None}
        results.append(result)
        with LEDGER.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(result, sort_keys=True, ensure_ascii=False) + "\n"); stream.flush(); os.fsync(stream.fileno())
        print(f"{index}/{len(packet['candidates'])} {row['pair_id']} {result['agreed_label'] or 'disagreement/error'}", flush=True)
    payload = {"kind": "dexagon.ainglish.flagship-semantic-results.v1", "candidate_packet_sha256": expected, "models": [{"name": model, "digest": tags[model]} for model in MODELS], "results": results, "interpretation": "Review routing only; no asserted relation."}
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    TARGET.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"results": len(results), "agreements": sum(row["model_agreement"] for row in results), "sha256": payload["content_sha256"]}))


if __name__ == "__main__":
    main()
