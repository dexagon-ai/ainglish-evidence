#!/usr/bin/env python3
"""Freeze a small, exploratory cold-surface/one-line-teaching flagship audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
LEDGER = ROOT.parent / "flagship-census-v7-2026-08-27" / "ledger.json"
TARGET = ROOT / "items.json"
OLLAMA = "http://127.0.0.1:11434"
MODELS = (
    "qwen2.5:7b",
    "gemma3:12b",
    "mistral-small3.2:24b-instruct-2506-q4_K_M",
)


CASES = {
    "we-including-you-we-excluding-you-clusivity-mark-whether-we--4": [
        ("we-including-you will review the draft at noon.", "The addressee is part of the reviewing group.", "The addressee is outside the reviewing group."),
        ("we-excluding-you will review the draft at noon.", "The addressee is outside the reviewing group.", "The addressee is part of the reviewing group."),
    ],
    "you-one-you-all-say-whether-you-addresses-one-recipient-or-t": [
        ("you-one should approve the change.", "One recipient is being addressed.", "Every recipient is being addressed."),
        ("you-all should approve the change.", "Every recipient is being addressed.", "Only one recipient is being addressed."),
    ],
    "fact-not-known-choice-not-made-distinguish-missing-evidence-": [
        ("fact-not-known — whether the backup completed.", "An answer may exist, but it is not known.", "No one has chosen an answer yet."),
        ("choice-not-made — which region to use.", "The authorised choice is still pending.", "A settled fact exists but has not been found."),
    ],
    "no-delegation-one-hop-delegation-allowed-state-whether-a-tas": [
        ("Complete the audit, no-delegation.", "The recipient must not hand the task onward.", "The recipient may hand the task to one direct delegate."),
        ("Complete the audit, one-hop-delegation-allowed.", "A direct delegate is allowed, but that delegate may not pass it on.", "Delegation is forbidden at every level."),
    ],
    "each-alone-as-one-distributive-vs-collective-does-the-plural": [
        ("The agents each-alone signed the report.", "Every agent signed separately.", "The group supplied one collective signature."),
        ("The agents as-one signed the report.", "The group supplied one collective signature.", "Every agent supplied a separate signature."),
    ],
    "by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3": [
        ("The delay happened by-unknown.", "The cause has not been identified.", "The cause is known but deliberately undisclosed."),
        ("The delay happened by-withheld.", "The cause is known but deliberately undisclosed.", "The cause has not been identified."),
    ],
    "start-by-complete-by-say-which-task-event-a-deadline-constra": [
        ("Migrate the database start-by(14:00).", "The migration must begin by 14:00.", "The migration must finish by 14:00."),
        ("Migrate the database complete-by(14:00).", "The migration must finish by 14:00.", "The migration only needs to begin by 14:00."),
    ],
    "or-both-not-both-english-or-never-says-whether-both-is-allow": [
        ("Use the cache or-both the index.", "Either resource or both resources may be used.", "Exactly one resource may be used."),
        ("Use the cache not-both the index.", "Exactly one of the two resources may be used.", "Using both resources is allowed."),
    ],
    "true-as-worded-false-as-worded-unambiguous-answers-to-negati": [
        ("true-as-worded — all four checks passed.", "The exact following statement is asserted true.", "Only a rough paraphrase is asserted true."),
        ("false-as-worded — all four checks passed.", "The exact following statement is asserted false.", "The exact following statement is asserted true."),
    ],
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2": [
        ("The review moved-earlier from Friday to Wednesday.", "The review now happens sooner.", "The review now happens later."),
        ("The review moved-later from Wednesday to Friday.", "The review now happens later.", "The review now happens sooner."),
    ],
    "among-others-and-no-others-is-the-list-the-whole-list-2": [
        ("Notify Mina and Jules, among-others.", "Mina and Jules are examples; additional people may be included.", "The list is exhaustive."),
        ("Notify Mina and Jules, and-no-others.", "Only Mina and Jules are included.", "Mina and Jules are merely examples."),
    ],
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2": [
        ("some-or-all services may restart.", "At least one service may restart, possibly every service.", "At least one but not every service may restart."),
        ("some-but-not-all services may restart.", "At least one service may restart, but not every service.", "Every service may restart."),
    ],
    "may-as-permission-may-as-possibility-does-may-authorize-an-a": [
        ("The worker may-as-permission delete the cache.", "Deleting the cache is authorised.", "Deleting the cache is merely considered possible."),
        ("The worker may-as-possibility delete the cache.", "Deletion is a possible outcome, not an authorisation.", "The worker is authorised to delete the cache."),
    ],
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet": [
        ("whole(report): verified.", "The verification covers the entire report.", "The verification covers an unspecified portion only."),
        ("part(report): verified.", "The verification covers only a portion of the report.", "The verification necessarily covers the entire report."),
    ],
    "proposal-by-p-decision-by-a-say-whether-an-option-is-offered": [
        ("proposal-by(Mina): deploy on Friday.", "Mina suggested Friday; this does not itself say Mina made the decision.", "Mina made the binding decision to deploy Friday."),
        ("decision-by(Mina): deploy on Friday.", "Mina made the stated decision.", "Mina merely suggested the stated option."),
    ],
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at": [
        ("one-or-more(reviewer): approve the release.", "At least one reviewer must approve; several may do so.", "Exactly one reviewer must approve."),
        ("exactly-one(reviewer): approve the release.", "One and only one reviewer must approve.", "Any positive number of reviewers may approve."),
    ],
    "repeat-event-restore-state-did-again-repeat-the-action-or-on-4": [
        ("repeat-event: send the notification.", "Perform another notification-sending event.", "Restore the system to a previous state without necessarily sending again."),
        ("restore-state(ready): reset the worker.", "Return the worker to the named ready state.", "Repeat the previous reset event regardless of resulting state."),
    ],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get_tags() -> dict[str, str]:
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=20) as response:
        payload = json.load(response)
    return {row["name"]: row.get("digest", "") for row in payload.get("models", [])}


def main() -> None:
    if TARGET.exists():
        raise SystemExit("REFUSING: items.json already exists")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = ledger["rows"]
    if {row["slug"] for row in rows} != set(CASES):
        missing = {row["slug"] for row in rows} - set(CASES)
        extra = set(CASES) - {row["slug"] for row in rows}
        raise SystemExit(f"case/catalog mismatch: missing={sorted(missing)} extra={sorted(extra)}")

    tags = get_tags()
    absent = [name for name in MODELS if not tags.get(name)]
    if absent:
        raise SystemExit(f"REFUSING: declared on-disk models absent: {absent}")

    items = []
    for row in rows:
        for case_number, (message, correct, foil) in enumerate(CASES[row["slug"]], 1):
            for exposure in ("surface_only", "one_line_definition"):
                item_number = len(items)
                correct_label = "A" if item_number % 2 == 0 else "B"
                options = {correct_label: correct, "B" if correct_label == "A" else "A": foil}
                items.append({
                    "item_id": f"f{row['rank']:02d}-c{case_number}-{exposure}",
                    "rank": row["rank"],
                    "slug": row["slug"],
                    "form": row["form"],
                    "exposure": exposure,
                    "definition": row["safe_caption"] if exposure == "one_line_definition" else None,
                    "message": message,
                    "options": options,
                    "correct_label": correct_label,
                })

    packet = {
        "kind": "dexagon.ainglish.flagship-surface-audit-items.v1",
        "source_ledger_sha256": ledger["content_sha256"],
        "purpose": "exploratory model-only triage of cold surface transparency and one-line teaching transfer",
        "models": [{"name": name, "digest": tags[name]} for name in MODELS],
        "options": {"temperature": 0, "seed": 2026082702, "num_ctx": 4096, "num_predict": 20},
        "items": items,
        "claim_boundary": "Not human validation, not governance evidence, not reader qualification, and not a comprehension-effect estimate.",
        "model_downloads_authorised": False,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    TARGET.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "models": len(MODELS), "sha256": packet["content_sha256"]}))


if __name__ == "__main__":
    main()
