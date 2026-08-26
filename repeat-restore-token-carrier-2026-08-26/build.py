#!/usr/bin/env python3
"""Build the repeat-event / restore-state same-item token prerequisite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ACTORS = ["Mara", "Ivo", "Nadia", "Soren", "Priya", "Tomas", "Amina", "Jonas", "Mei", "Luka", "Zara", "Owen"]
EVENTS = [
    ("open", "opened", "open", ["north gate", "side hatch", "intake valve", "bay shutter", "lab window", "review channel", "release tunnel", "audit port", "storage locker", "access panel", "control room", "dispatch lane"]),
    ("close", "closed", "closed", ["south gate", "service hatch", "outlet valve", "loading shutter", "office window", "incident channel", "transfer tunnel", "debug port", "media locker", "inspection panel", "briefing room", "intake lane"]),
    ("lock", "locked", "locked", ["primary vault", "backup archive", "admin console", "signing key", "release branch", "ballot box", "evidence cabinet", "operator account", "build queue", "review record", "dispatch case", "source mirror"]),
    ("unlock", "unlocked", "unlocked", ["secondary vault", "cold archive", "staging console", "recovery key", "hotfix branch", "appeal box", "sample cabinet", "service account", "deploy queue", "audit record", "support case", "artifact mirror"]),
    ("start", "started", "running", ["api service", "batch worker", "coolant pump", "indexing job", "replica node", "alert daemon", "backup task", "render process", "ingest pipeline", "status monitor", "build agent", "message relay"]),
    ("stop", "stopped", "not-running", ["web service", "mail worker", "transfer pump", "cleanup job", "leader node", "watch daemon", "export task", "merge process", "training pipeline", "health monitor", "test agent", "event relay"]),
    ("connect", "connected", "connected", ["temperature sensor", "read replica", "network bridge", "backup cable", "worker socket", "control terminal", "storage volume", "telemetry feed", "message bus", "power adapter", "audit stream", "release client"]),
    ("disconnect", "disconnected", "not-connected", ["pressure sensor", "write replica", "service bridge", "uplink cable", "admin socket", "debug terminal", "archive volume", "metrics feed", "event bus", "charging adapter", "report stream", "staging client"]),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def state_phrase(state: str) -> str:
    return {"not-running": "not running", "not-connected": "not connected"}.get(state, state)


def state_argument(state: str, object_key: str) -> str:
    return f"{state}({object_key.replace(' ', '-')})"


def main() -> None:
    rows = []
    for event_index, (lemma, past, state, objects) in enumerate(EVENTS):
        for item_index, (actor, object_name) in enumerate(zip(ACTORS, objects, strict=True)):
            form = "repeat-event" if (event_index + item_index) % 2 == 0 else "restore-state"
            clause = f"{actor} {past} the {object_name}"
            if form == "repeat-event":
                ainglish = f"repeat-event: {clause}."
                english = f"{clause}; {actor} had previously {past} that same {object_name}."
            else:
                state_text = state_phrase(state)
                ainglish = f"restore-state({state_argument(state, object_name)}): {clause}."
                english = (
                    f"{clause}; the {object_name} had earlier been {state_text}, then ceased to be {state_text} "
                    f"before this event, and this event restored that state; no earlier {lemma} event by {actor} is claimed."
                )
            rows.append({
                "item_id": f"{event_index + 1:02d}-{item_index + 1:02d}",
                "form": form,
                "predicate_family": lemma,
                "event_clause": clause,
                "result_state": state_argument(state, object_name),
                "ainglish": ainglish,
                "english": english,
            })

    counts = {form: sum(row["form"] == form for row in rows) for form in ("repeat-event", "restore-state")}
    family_counts = {
        family: {form: sum(row["predicate_family"] == family and row["form"] == form for row in rows) for form in counts}
        for family, *_ in EVENTS
    }
    if len(rows) != 96 or counts != {"repeat-event": 48, "restore-state": 48}:
        raise SystemExit("REFUSING: item-count or form-balance gate")
    if any(values != {"repeat-event": 6, "restore-state": 6} for values in family_counts.values()):
        raise SystemExit("REFUSING: predicate-family balance gate")
    if len({row["event_clause"] for row in rows}) != 96:
        raise SystemExit("REFUSING: event clauses are not unique")
    if any("again" in row["event_clause"].lower() for row in rows):
        raise SystemExit("REFUSING: bare event clause contains again")

    packet = {
        "kind": "dexagon.ainglish.repeat-restore-token-carrier.v1",
        "proposal_slug": "repeat-event-restore-state-did-again-repeat-the-action-or-on-2",
        "metric": "token_delta",
        "forms": list(counts),
        "form_counts": counts,
        "predicate_family_counts": family_counts,
        "comparison": "registered marker versus the complete careful-English mapping on the same 96 events reserved for the form-separated comprehension population",
        "acceptance": {"least_favourable_form_balanced_mean_at_most": 0},
        "evidentiary_limit": "deterministic price prerequisite only; it cannot establish comprehension, actor attribution, force projection, or adoption",
        "test_set": rows,
        "model_calls": 0,
        "tokenizer_calls": 0,
        "governance_writes": 0,
    }
    packet["items_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "token-items.json"
    if target.exists():
        raise SystemExit("REFUSING: token-items.json already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "items": len(rows),
        "form_counts": counts,
        "items_sha256": packet["items_sha256"],
        "content_sha256": packet["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
