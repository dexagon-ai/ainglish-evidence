#!/usr/bin/env python3
"""Build balanced controlled-use moved-direction fidelity cases offline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082647
EVENTS = ("review", "maintenance", "scheduled job", "ballot close", "deadline", "delivery slot", "audit", "release call")
ANSWERS = ("moved-earlier", "moved-later", "neither tag is warranted")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def placed(answer: str, position: int) -> list[str]:
    values = [value for value in ANSWERS if value != answer]
    values.insert(position % 3, answer)
    return values


def main() -> None:
    snapshot = json.loads((ROOT / "proposal-snapshot.json").read_text(encoding="utf-8"))
    rows = []
    base = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    for index in range(96):
        event = EVENTS[index % len(EVENTS)]
        old = base + timedelta(days=index, hours=index % 5)
        class_index = index % 3
        if class_index == 0:
            new = old - timedelta(hours=1 + index % 7)
            answer = "moved-earlier"
            source = f"The {event} was scheduled for {old.isoformat()} and is now rescheduled to {new.isoformat()}."
        elif class_index == 1:
            new = old + timedelta(hours=1 + index % 7)
            answer = "moved-later"
            source = f"The {event} was scheduled for {old.isoformat()} and is now rescheduled to {new.isoformat()}."
        else:
            answer = "neither tag is warranted"
            variant = (index // 3) % 3
            if variant == 0:
                source = f"The {event} remains scheduled for {old.isoformat()}; no schedule change occurred."
            elif variant == 1:
                source = f"The {event} now has time {old.isoformat()}, but its previous schedule is unavailable."
            else:
                new = old + timedelta(hours=2)
                source = f"One signed notice moves the {event} from {old.isoformat()} to {new.isoformat()}, while another equally current signed notice moves it to {(old - timedelta(hours=2)).isoformat()}; no notice supersedes the other."
        rows.append({
            "id": f"moved-fidelity-{index + 1:03d}",
            "event_domain": event,
            "source_event": source,
            "proposition": "Apply exactly one registered moved-direction tag only when the current schedule and replacement schedule determine it.",
            "instruction": "Which exact registered tag is warranted by the source event?",
            "options": placed(answer, index % 3),
            "answer": answer,
            "class": ("earlier", "later", "neither")[class_index],
        })
    assert len(rows) == 96
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    packet = {
        "kind": "dexagon.ainglish.moved-direction-controlled-fidelity-items.v1",
        "slug": snapshot["surface"]["slug"],
        "surface_sha256": snapshot["surface_sha256"],
        "seed": SEED,
        "sha256": digest,
        "population": "96 controlled schedule-change classifications across eight operational event domains",
        "aggregation": "least-favourable exact warranted-tag fraction across qualified reader lineages",
        "items": rows,
    }
    (ROOT / "fidelity-cases.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.moved-direction-fidelity-freeze.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "items_path": "fidelity-cases.json",
        "items_sha256": digest,
        "cases": 96,
        "classes": {name: 32 for name in ("earlier", "later", "neither")},
        "model_calls": 0,
        "governance_writes": 0,
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"cases": 96, "items_sha256": digest, "content_sha256": index["content_sha256"]}))


if __name__ == "__main__":
    main()
