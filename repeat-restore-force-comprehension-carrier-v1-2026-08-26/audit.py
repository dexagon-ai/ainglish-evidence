#!/usr/bin/env python3
"""Audit the force-aware carrier without model, tokenizer, or governance calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ("repeat-event", "restore-state")
FORCES = ("affirmative", "negated", "question", "directive")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8")); index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    sealed_packet = dict(packet); packet_digest = sealed_packet.pop("content_sha256"); sealed_index = dict(index); index_digest = sealed_index.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed_packet)).hexdigest() == packet_digest == index["items_content_sha256"]
    assert hashlib.sha256(canonical(sealed_index)).hexdigest() == index_digest
    frames, rows, validity, calibration = packet["frames"], packet["scientific_rows"], packet["validity_rows"], packet["calibration_rows"]
    assert len(frames) == 128 and len(rows) == 256 and len(validity) == 32 and len(calibration) == 8
    assert hashlib.sha256(canonical(frames)).hexdigest() == packet["frames_sha256"]
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["scientific_rows_sha256"]
    assert hashlib.sha256(canonical(validity)).hexdigest() == packet["validity_rows_sha256"]
    assert hashlib.sha256(canonical(calibration)).hexdigest() == packet["calibration_rows_sha256"]
    assert Counter((row["form"], row["force"], row["probe"]) for row in rows) == Counter({(form, force, probe): 16 for form in FORMS for force in FORCES for probe in ("background_condition", "at_issue_force")})
    assert Counter(row["options"].index(row["answer"]) for row in rows) == Counter({0: 64, 1: 64, 2: 64, 3: 64})
    assert Counter(row["fixture_kind"] for row in validity) == Counter({"valid": 8, "missing-state": 8, "non-entailed-state": 8, "ambiguous-state": 4, "multi-result": 4})
    assert sum(row["valid"] for row in validity) == 8
    assert all(row["answer"] in row["options"] and len(set(row["options"])) == len(row["options"]) for row in rows + validity + calibration)
    assert all(row["english"] != row["ainglish"] for row in rows + validity + calibration)
    directive = [row for row in rows if row["force"] == "directive" and row["probe"] == "background_condition"]
    assert len(directive) == 32 and all("does not say whether" in row["answer"] if row["form"] == "repeat-event" else "no earlier matching event" in row["answer"] for row in directive)
    print(json.dumps({"status": "ok", "frames": 128, "scientific_rows": 256, "validity_rows": 32, "calibration_rows": 8, "form_force_probe_cells": 16, "answer_positions": {str(k): v for k, v in sorted(Counter(row["options"].index(row["answer"]) for row in rows).items())}, "model_calls": 0, "tokenizers_loaded": 0, "governance_writes": 0, "content_sha256": index["content_sha256"]}, indent=2))


if __name__ == "__main__": main()

