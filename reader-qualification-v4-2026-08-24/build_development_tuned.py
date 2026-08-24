#!/usr/bin/env python3
"""Freeze the single construct-blind transport revision after development."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    spec = json.loads((ROOT / "development.json").read_text())
    spec["kind"] = "ainglish.panel.reader-qualification-development-tuned.v4"
    spec["result_kind"] = "ainglish.panel.reader-qualification-development-tuned-result.v4"
    spec["purpose"] = "Check the one allowed construct-blind transport revision: disable hidden reasoning so a fixed-choice instrument cannot exhaust its bound before emitting a code."
    spec["transport"] = {"adapter": "ollama-native-chat-v1", "think": False}
    spec["development_predecessor"] = "development-result.json: all 19 visible codes were correct; five cells exhausted the 1024-token thinking bound before any visible code"
    spec["panel"][0]["max_tokens"] = 16
    spec["panel"][0]["name"] = "qwen3.5-9b-literal-nothink-q4_k_m"
    out = ROOT / "development-tuned.json"
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(out), "items": len(spec["items"]), "reader_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
