#!/usr/bin/env python3
"""Freeze the live-register collision review for the cardinality proposal."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


NEAREST = {
    "you-one-you-all-say-whether-you-addresses-one-recipient-or-t": "addressee cardinality, not actor-count requirement",
    "they-one-they-many-say-whether-they-is-one-actor-or-several": "pronoun-reference cardinality, not actor-count requirement",
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2": "subset quantification over a bounded population, not exactly-one",
    "each-alone-as-one-distributive-vs-collective-does-the-plural": "distribution of an already plural action set, not membership count",
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet": "reported-set completeness, not a prospective role constraint",
    "among-others-and-no-others-is-the-list-the-whole-list-2": "enumeration closure, not a participant-count constraint",
    "no-delegation-one-hop-delegation-allowed-state-whether-a-tas": "handoff depth, not the number of principals satisfying a role",
    "or-both-not-both-english-or-never-says-whether-both-is-allow": "choice-set conjunction, not existential versus exact-one cardinality",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    register = [{key: row.get(key) for key in ("slug", "stage", "title", "form")} for row in client.iter_proposals(page_size=200)]
    rows = []
    by_slug = {row["slug"]: row for row in register}
    for slug, distinction in NEAREST.items():
        row = by_slug.get(slug)
        if row is None:
            raise SystemExit(f"REFUSING: nearest candidate absent from live register: {slug}")
        rows.append({**row, "distinction": distinction})
    snapshot = {
        "kind": "ainglish.register-collision-review.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "candidate_form": "one-or-more(<role>): <ACTION-CLAUSE> | exactly-one(<role>): <ACTION-CLAUSE>",
        "register_rows": len(register),
        "register_digest": hashlib.sha256(canonical(register)).hexdigest(),
        "exact_surface_matches": [
            row for row in register
            if "one-or-more(" in (row.get("form") or "") or "exactly-one(" in (row.get("form") or "")
        ],
        "nearest": rows,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target = ROOT / "collision-snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: collision-snapshot.json already exists")
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "register_rows": len(register),
        "exact_surface_matches": len(snapshot["exact_surface_matches"]),
        "nearest": len(rows),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
