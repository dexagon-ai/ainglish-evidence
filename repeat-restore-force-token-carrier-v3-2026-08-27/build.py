#!/usr/bin/env python3
"""Build a fresh affirmative token population for repeat/restore successor -4."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "repeat-event-restore-state-did-again-repeat-the-action-or-on-4"
ACTORS = ("Anika", "Belen", "Cyrus", "Dev", "Elian", "Fiona", "Gita", "Hugo")
EVENTS = (
    ("energize", "energized", "energized", "inspection circuit"),
    ("disarm", "disarmed", "disarmed", "alarm channel"),
    ("archive", "archived", "archived", "incident record"),
    ("publish", "published", "published", "release notice"),
    ("encrypt", "encrypted", "encrypted", "audit bundle"),
    ("decrypt", "decrypted", "decrypted", "review packet"),
    ("isolate", "isolated", "isolated", "worker process"),
    ("reconnect", "reconnected", "connected", "backup link"),
)
QUALIFIERS = ("alpha", "bravo", "cedar", "delta", "ember", "fjord", "grove", "harbour")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    rows = []
    for family_index, (lemma, past, state, noun) in enumerate(EVENTS):
        for item_index, (actor, qualifier) in enumerate(zip(ACTORS, QUALIFIERS, strict=True)):
            object_name = f"{qualifier} {noun}"
            object_key = object_name.replace(" ", "-")
            clause = f"{actor} {past} the {object_name}"
            form = "repeat-event" if (family_index + item_index) % 2 == 0 else "restore-state"
            if form == "repeat-event":
                ainglish = f"repeat-event: {clause}."
                english = (
                    f"{clause}; before this event's reference time, {actor} had performed an earlier "
                    f"{lemma} event on that same {object_name}."
                )
            else:
                state_argument = f"{state}({object_key})"
                ainglish = f"restore-state({state_argument}): {clause}."
                english = (
                    f"The {object_name} had been {state} during an earlier interval; {clause}, and this "
                    f"asserted transition entails that it is now {state}; no earlier matching {lemma} "
                    f"event or earlier same-actor cause is claimed."
                )
            rows.append({
                "item_id": f"v3-{family_index + 1:02d}-{item_index + 1:02d}",
                "form": form,
                "predicate_family": lemma,
                "event_clause": clause,
                "result_state": f"{state}({object_key})",
                "english": english,
                "ainglish": ainglish,
            })

    form_counts = {
        form: sum(row["form"] == form for row in rows)
        for form in ("repeat-event", "restore-state")
    }
    family_counts = {
        lemma: {
            form: sum(
                row["predicate_family"] == lemma and row["form"] == form
                for row in rows
            )
            for form in form_counts
        }
        for lemma, *_ in EVENTS
    }
    assert len(rows) == 64 and form_counts == {"repeat-event": 32, "restore-state": 32}
    assert all(
        counts == {"repeat-event": 4, "restore-state": 4}
        for counts in family_counts.values()
    )

    packet = {
        "kind": "dexagon.ainglish.repeat-restore-force-token-carrier.v3",
        "proposal_slug": SLUG,
        "metric": "token_delta",
        "test_set": rows,
        "forms": list(form_counts),
        "form_counts": form_counts,
        "predicate_family_counts": family_counts,
        "comparison": "registered affirmative marker versus its complete current force-matched careful-English mapping",
        "acceptance": {"least_favourable_form_balanced_mean_at_most": 0},
        "evidentiary_limit": "deterministic price prerequisite only; not comprehension, actor-attribution, directive, execution, or adoption evidence",
        "tokenizer_calls": 0,
        "model_calls": 0,
        "governance_writes": 0,
    }
    packet["items_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    (ROOT / "token-items.json").write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    index = {
        "kind": "dexagon.ainglish.repeat-restore-force-token-freeze.v3",
        "proposal_slug": SLUG,
        "items_path": "token-items.json",
        "items_sha256": packet["items_sha256"],
        "pairs": 64,
        "form_counts": form_counts,
        "tokenizer_calls": 0,
        "model_calls": 0,
        "governance_writes": 0,
        "execution_gate": "fresh successor stage is seconded or measured and token_delta state is submit_original",
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "pairs": 64,
        "form_counts": form_counts,
        "items_sha256": packet["items_sha256"],
        "content_sha256": index["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()

