#!/usr/bin/env python3
"""Build fresh matched population-coverage items for whole(S) / part(S)."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FRAMES = [
    (17, "audit packets", "a forged signature"),
    (23, "staging deployments", "a rollback alarm"),
    (31, "warehouse scans", "a damaged seal"),
    (14, "permission reviews", "an excessive grant"),
    (28, "billing records", "a duplicated charge"),
    (19, "regional probes", "a routing failure"),
    (26, "dependency reports", "an unpatched library"),
    (33, "training shards", "a malformed example"),
    (21, "support transcripts", "an unresolved complaint"),
    (16, "certificate checks", "an expired certificate"),
    (29, "sensor batches", "an out-of-range reading"),
    (18, "release candidates", "a blocking regression"),
    (37, "inventory entries", "an unknown owner"),
    (24, "access logs", "a denied request"),
    (13, "backup snapshots", "a checksum mismatch"),
    (32, "message deliveries", "an unacknowledged recipient"),
    (22, "replica health reports", "an unavailable replica"),
    (27, "moderation decisions", "an unexplained reversal"),
    (34, "migration rows", "a failed conversion"),
    (12, "research summaries", "an unsupported conclusion"),
    (36, "job executions", "an incomplete task"),
    (15, "translated notices", "a changed instruction"),
    (25, "api responses", "an undocumented field"),
    (38, "review ballots", "an ineligible vote"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def options(answer: str, alternatives: list[str], index: int) -> list[str]:
    values = [answer, *alternatives]
    shift = index % len(values)
    return values[shift:] + values[:shift]


def scientific_items() -> list[dict]:
    rows = []
    for index, (count, population, event) in enumerate(FRAMES):
        selected = f"the {count} {population}"
        probe = index % 3
        for form in ("part", "whole"):
            if form == "part":
                english = (
                    f"{selected.capitalize()} are a subset of the population covered by this report; "
                    f"additional in-scope {population} were not inspected. {event.capitalize()} "
                    f"appeared in none of {selected}."
                )
                ainglish = f"part({selected}): no {event} appeared."
                answers = ("yes", "no", "no")
            else:
                english = (
                    f"{selected.capitalize()} are the entire population covered by this report; "
                    f"there are no other in-scope {population}. {event.capitalize()} appeared in "
                    f"none of {selected}."
                )
                ainglish = f"whole({selected}): no {event} appeared."
                answers = ("no", "yes", "yes")
            if probe == 0:
                question = (
                    f"Could another in-scope member of the {population} population exist beyond "
                    f"{selected} without contradicting the report?"
                )
                answer = answers[0]
            elif probe == 1:
                question = (
                    f"Would finding {event} in an additional in-scope member contradict the "
                    "report's population-coverage claim?"
                )
                answer = answers[1]
            else:
                question = (
                    f"Does the report say that {selected} exhaust the in-scope population?"
                )
                answer = answers[2]
            rows.append({
                "id": f"whole-part-{form}-{index + 1:02d}",
                "english": english,
                "ainglish": ainglish,
                "question": question,
                "options": options(answer, [x for x in ("yes", "no", "cannot tell") if x != answer], index),
                "answer": answer,
                "form": form,
                "strata": {"form": form, "probe": f"coverage-{probe + 1}"},
            })
    return rows


def calibration_items() -> list[dict]:
    facts = [
        ("amber pass", "shelf 14"),
        ("cedar card", "drawer 23"),
        ("indigo key", "cabinet 6"),
        ("granite tag", "locker 31"),
        ("pearl token", "vault 11"),
        ("crimson badge", "shelf 28"),
        ("hemp seal", "drawer 15"),
        ("basalt disk", "cabinet 20"),
    ]
    rows = []
    for index, (thing, location) in enumerate(facts):
        rows.append({
            "id": f"whole-part-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"A dispatch note mentions the {thing}, but states no storage location.",
            "ainglish": f"A dispatch note says the {thing} is stored on {location}.",
            "question": f"Where does the note say the {thing} is stored?",
            "options": options(location, ["at the dispatch desk", "the location is not stated"], index),
            "answer": location,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def main() -> None:
    rows = scientific_items() + calibration_items()
    real = [row for row in rows if not row.get("calibration")]
    assert len(rows) == 56 and len(real) == 48
    assert len({row["id"] for row in rows}) == len(rows)
    counts = Counter(row["form"] for row in real)
    assert counts == {"part": 24, "whole": 24}
    path = ROOT / "items.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.whole-part-fresh-carrier.v1",
        "items_file": path.name,
        "items_sha256": sha256(canonical(rows)).hexdigest(),
        "scientific_items": len(real),
        "calibration_items": len(rows) - len(real),
        "form_counts": dict(counts),
        "probe_counts": dict(Counter(row["strata"]["probe"] for row in real)),
        "model_calls": 0,
    }
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
