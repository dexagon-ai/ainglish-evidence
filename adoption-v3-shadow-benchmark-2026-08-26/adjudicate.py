#!/usr/bin/env python3
"""Model-assisted audit of every v2/v3 disagreement; never treated as ground truth."""

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OLLAMA = "http://127.0.0.1:11434"
MODELS = (
    "dexagon-mistral-small3.2-24b-approx-fresh:ctx4k",
    "dexagon-qwen3.5-27b-screen:ctx4k",
)
LABELS = ("semantic_use", "metalinguistic_mention", "mixed", "uncertain")


def request_json(path, body=None):
    payload = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        OLLAMA + path, data=payload,
        headers={"Content-Type": "application/json"} if payload is not None else {},
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.load(response)


def load_detector(path):
    spec = importlib.util.spec_from_file_location("adoption_detector_for_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def matching_sentences(detector, pattern, text):
    return [
        sentence.strip() for sentence in detector.SENTENCE_BOUNDARY.split(detector.running_prose(text))
        if pattern.search(sentence)
    ]


def build_items(detector):
    proposals = {row["slug"]: row for row in json.loads((ROOT / "proposals.json").read_text())}
    patterns = {
        slug: detector.PATTERNS.get(slug) or detector.derived_pattern(row)
        for slug, row in proposals.items()
    }
    items = []
    for line in (ROOT / "disagreements.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        proposal = proposals[row["proposal_slug"]]
        sentences = matching_sentences(detector, patterns[row["proposal_slug"]], row["text"])
        items.append({
            "id": hashlib.sha256((row["proposal_slug"] + "\0" + row["ref"]).encode()).hexdigest()[:16],
            "proposal_slug": row["proposal_slug"],
            "ref": row["ref"],
            "declared_form": proposal.get("form"),
            "slot": proposal.get("slot"),
            "english_mapping": proposal.get("english_mapping"),
            "matched_sentences": sentences,
            "v2": row["v2"],
            "v3": row["v3"],
        })
    (ROOT / "audit-items.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items),
        encoding="utf-8",
    )
    return items


def prompt(item):
    return """You are auditing an Ainglish adoption detector. Judge only whether the declared marker
is USED in the supplied sentence(s) to communicate its registered meaning, versus merely MENTIONED
while discussing, quoting, testing, measuring, or listing the marker. A sentence can be MIXED when
separate occurrences have both roles. Choose UNCERTAIN if the role cannot be determined. Do not
infer that unfamiliar Ainglish is meaningless: use the supplied mapping. Return JSON only with
keys label and rationale. label must be semantic_use, metalinguistic_mention, mixed, or uncertain.

AUDIT ITEM:
""" + json.dumps({
        "declared_form": item["declared_form"],
        "slot": item["slot"],
        "english_mapping": item["english_mapping"],
        "matched_sentences": item["matched_sentences"],
    }, ensure_ascii=False)


def judge(model, item):
    schema = {
        "type": "object",
        "required": ["label", "rationale"],
        "properties": {
            "label": {"type": "string", "enum": list(LABELS)},
            "rationale": {"type": "string"},
        },
        "additionalProperties": False,
    }
    response = request_json("/api/generate", {
        "model": model,
        "prompt": prompt(item),
        "stream": False,
        "think": False,
        "format": schema,
        "options": {"temperature": 0, "seed": 8262026, "num_predict": 192},
        "keep_alive": "10m",
    })
    raw = response.get("response") or response.get("thinking") or ""
    parsed = json.loads(raw)
    if parsed.get("label") not in LABELS:
        raise RuntimeError(f"invalid label from {model}: {parsed!r}")
    return {
        "item_id": item["id"],
        "proposal_slug": item["proposal_slug"],
        "ref": item["ref"],
        "model": model,
        "prompt_sha256": hashlib.sha256(prompt(item).encode()).hexdigest(),
        "label": parsed["label"],
        "rationale": parsed.get("rationale", ""),
        "done": response.get("done"),
        "done_reason": response.get("done_reason"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("detector", type=Path)
    args = parser.parse_args()
    detector = load_detector(args.detector.resolve())
    items = build_items(detector)
    tag_rows = {row["name"]: row for row in request_json("/api/tags").get("models", [])}
    missing = [model for model in MODELS if model not in tag_rows]
    if missing:
        raise RuntimeError(f"required preinstalled models are absent; refusing downloads: {missing}")

    # Interleave the two readers so Ollama can keep one model resident per available GPU.
    jobs = [(model, item) for item in items for model in MODELS]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(MODELS)) as pool:
        futures = [pool.submit(judge, model, item) for model, item in jobs]
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(future.result())
            if completed % 10 == 0:
                print(f"adjudicated {completed}/{len(jobs)}", flush=True)
    results.sort(key=lambda row: (row["item_id"], row["model"]))
    (ROOT / "adjudications.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in results),
        encoding="utf-8",
    )

    by_item = {}
    for result in results:
        by_item.setdefault(result["item_id"], []).append(result["label"])
    item_by_id = {item["id"]: item for item in items}
    counts = {"agreement": 0, "disagreement": 0}
    consensus = {}
    cross_tab = {}
    ledger = []
    for item_id, labels in by_item.items():
        if len(set(labels)) == 1:
            counts["agreement"] += 1
            consensus_label = labels[0]
            consensus[consensus_label] = consensus.get(consensus_label, 0) + 1
        else:
            counts["disagreement"] += 1
            consensus_label = "reader_disagreement"
        item = item_by_id[item_id]
        active_v3 = [label for label in ("use", "mention", "abstain") if item["v3"][label]]
        v3_disposition = "mixed" if len(active_v3) > 1 else (active_v3[0] if active_v3 else "none")
        cross_key = consensus_label + " -> " + v3_disposition
        cross_tab[cross_key] = cross_tab.get(cross_key, 0) + 1
        ledger.append({
            "item": item,
            "v3_disposition": v3_disposition,
            "reader_consensus": consensus_label,
            "judgments": [row for row in results if row["item_id"] == item_id],
        })
    ledger.sort(key=lambda row: (row["item"]["proposal_slug"], row["item"]["ref"]))
    (ROOT / "audit-ledger.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ledger),
        encoding="utf-8",
    )
    summary = {
        "kind": "ainglish.adoption-v3-shadow-model-audit.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "warning": "Model-assisted error analysis, not human ground truth and not an activation gate by itself.",
        "items": len(items),
        "judgments": len(results),
        "models": [{"name": model, "digest": tag_rows[model].get("digest")} for model in MODELS],
        "inter_model": counts,
        "unanimous_labels": consensus,
        "reader_consensus_vs_v3": dict(sorted(cross_tab.items())),
    }
    (ROOT / "audit-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
