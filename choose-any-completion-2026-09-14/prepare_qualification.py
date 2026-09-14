"""Build frozen target-independent control screens from READ-ONLY local model metadata.

Does not call a reader, load a model, download weights, mint, or submit. Run the separate official
qualification CLI only after these exact screens have been published and read back.
"""
import hashlib
import json
from pathlib import Path
import urllib.request
from ainglish.reader_qualification import validate_screen

ROOT = Path(__file__).resolve().parent
MODELS = (
    ("gemma", "dexagon-gemma3-12b-pp-task:ctx4k", "gemma3-12b-opaque-choice-q4_k_m", "google/gemma3-12b"),
    ("mistral", "dexagon-mistral-small3.2-24b-pp-task:ctx4k", "mistral-small3.2-24b-opaque-choice-q4_k_m", "mistral/mistral-small3.2-24b"),
)

def controls():
    result = []
    for i in range(32):
        owner, other = f"Desk-Beryl-{i+201}", f"Desk-Vesper-{i+401}"
        zone, alternative = f"Store-Azure-{i+301}", f"Store-Copper-{i+501}"
        record = f"Control-record-{i+701}"
        choices = [f"{owner} / {zone}", f"{other} / {zone}", f"{owner} / {alternative}",
                   "The complete assignment is not established."]
        offset = i % 4
        choices = choices[-offset:] + choices[:-offset] if offset else choices
        result.append({
            "id": f"joint-facts-control-{i+1:02d}",
            "detectable": f"{record}: the responsible desk is {owner}, not {other}. The destination is {zone}, not {alternative}.",
            "other": f"{record}: the responsible desk has not been resolved between {other} and {owner}. The destination has not been resolved between {alternative} and {zone}.",
            "question": "Which desk/destination assignment is fully established and can be copied into the completed record?",
            "options": choices, "answer": f"{owner} / {zone}",
        })
    return result

def main():
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10) as response:
        rows = json.load(response)["models"]
    by_name = {m["name"]: m for m in rows}
    out = ROOT / "qualification"
    out.mkdir(exist_ok=True)
    summary = []
    for short, model, name, lineage in MODELS:
        if model not in by_name:
            raise SystemExit(f"Required cached model is absent: {model}; do not download a substitute")
        row = by_name[model]
        raw_digest = row["digest"].removeprefix("sha256:")
        reader = {"name": name, "provider": "ollama", "api": "openai",
                  "base_url": "http://127.0.0.1:11434/v1", "model": model,
                  "model_digest": "sha256:" + raw_digest,
                  "digest_source": "local Ollama /api/tags metadata; cached model, no download",
                  "precision": "q4_k_m", "max_tokens": 128, "temperature": 0,
                  "seed": 2026091451, "timeout_s": 120}
        screen = {"kind": "ainglish.reader-qualification-screen.v1",
                  "roster_id": name + "@q4_k_m", "reader": reader,
                  "lineage": {"key": lineage,
                              "basis": "Named cached base-model family and local content digest. Distinct vendor/family is a declared reader-axis basis, not proof of independent error or training data."},
                  "validity_days": 7, "min_gap_bps": 5000, "min_recovered_bps": 8750,
                  "controls": controls()}
        validate_screen(screen)
        payload = (json.dumps(screen, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        (out / f"{short}-screen.json").write_bytes(payload)
        summary.append({"reader": short, "roster_id": screen["roster_id"],
                        "model_digest": reader["model_digest"], "raw_screen_sha256": hashlib.sha256(payload).hexdigest(),
                        "control_count": 32, "planned_cells": 64, "reader_calls_so_far": 0})
    (out / "PRE-SPEND.json").write_text(json.dumps({"kind":"qualification-preparation-only", "screens":summary,
                "boundary":"This qualifies positive-control sensitivity only. It does not approve the target draft, certify NI, or independently replicate a proposal measurement."}, indent=2) + "\n")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
