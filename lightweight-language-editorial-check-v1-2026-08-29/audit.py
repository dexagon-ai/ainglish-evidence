#!/usr/bin/env python3
"""Check counts and claim boundaries in the lightweight editorial cards."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    data = json.loads((ROOT / "cards.json").read_text(encoding="utf-8"))
    cards = data["cards"]
    assert len(cards) == 8
    assert len({card["form"] for card in cards}) == 8
    assert all(len(card["checks"]) == 5 for card in cards)
    assert all(card["score"] == sum(card["checks"]) for card in cards)
    assert sum(card["score"] == 5 for card in cards) == 7
    assert sum(card["score"] == 4 for card in cards) == 1
    assert data["summary"]["native_speaker_observations"] == 0
    assert data["summary"]["model_calls"] == 0
    assert data["summary"]["governance_writes"] == 0
    print(json.dumps({"status": "passed", "cards": 8, "five_of_five": 7, "four_of_five": 1}, indent=2))


if __name__ == "__main__":
    main()
