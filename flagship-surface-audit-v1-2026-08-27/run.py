#!/usr/bin/env python3
"""Run a frozen flagship surface audit with an explicit no-pull model gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import urllib.request


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "items.json"
LEDGER = ROOT / "responses.jsonl"
TARGET = ROOT / "results.json"
OLLAMA = "http://127.0.0.1:11434"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def request_json(path: str, payload: dict | None = None, timeout: int = 30) -> dict:
    request = urllib.request.Request(
        OLLAMA + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def prompt(item: dict) -> str:
    teaching = "" if item["definition"] is None else f"Definition: {item['definition']}\n\n"
    return (
        teaching
        + "Read the message literally and choose its operational meaning.\n\n"
        + f"Message: {item['message']}\n\n"
        + f"A. {item['options']['A']}\nB. {item['options']['B']}\n\n"
        + "Answer with exactly A or B."
    )


def main() -> None:
    if TARGET.exists() or LEDGER.exists():
        raise SystemExit("REFUSING: output already exists")
    packet = json.loads(SOURCE.read_text(encoding="utf-8"))
    sealed = dict(packet)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("REFUSING: frozen item packet drift")
    if packet.get("model_downloads_authorised") is not False:
        raise SystemExit("REFUSING: packet does not explicitly forbid downloads")

    installed = {row["name"]: row.get("digest") for row in request_json("/api/tags").get("models", [])}
    for model in packet["models"]:
        if installed.get(model["name"]) != model["digest"]:
            raise SystemExit(f"REFUSING: absent or drifted on-disk model {model['name']}")

    rows = []
    for model_number, model in enumerate(packet["models"], 1):
        for item_number, item in enumerate(packet["items"], 1):
            raw = ""
            error = None
            try:
                response = request_json("/api/generate", {
                    "model": model["name"],
                    "prompt": prompt(item),
                    "stream": False,
                    "options": packet["options"],
                    "keep_alive": "10m",
                }, timeout=300)
                raw = str(response.get("response", "")).strip()
                match = re.fullmatch(r"(?:answer\s*[:=]\s*)?([AB])[.!]?", raw, flags=re.IGNORECASE)
                answer = match.group(1).upper() if match else None
                if answer is None:
                    error = "output_contract_failure"
            except Exception as exc:
                answer = None
                error = f"{type(exc).__name__}: {exc}"
            row = {
                "model": model["name"], "model_digest": model["digest"],
                "item_id": item["item_id"], "slug": item["slug"], "rank": item["rank"],
                "exposure": item["exposure"], "answer": answer, "correct_label": item["correct_label"],
                "correct": answer == item["correct_label"] if answer else False,
                "raw_response": raw, "error": error,
            }
            rows.append(row)
            with LEDGER.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
                stream.flush()
            print(f"{model_number}/{len(packet['models'])} {item_number}/{len(packet['items'])} {item['item_id']} {'ok' if row['correct'] else error or 'wrong'}", flush=True)

    result = {
        "kind": "dexagon.ainglish.flagship-surface-audit-results.v1",
        "items_sha256": expected,
        "rows": rows,
        "model_calls": len(rows),
        "model_downloads": 0,
        "governance_writes": 0,
        "claim_boundary": packet["claim_boundary"],
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    TARGET.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
