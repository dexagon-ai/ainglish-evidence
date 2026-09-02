#!/usr/bin/env python3
"""Build a fresh, balanced consequence carrier for the go/hold dispute."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

ACTIONS = [
    ("activate the standby route", "traffic uses the standby route", "traffic stays on the primary route"),
    ("publish bulletin Cedar", "bulletin Cedar is visible in the public index", "bulletin Cedar remains a private draft"),
    ("move ledger Kilo to cold storage", "ledger Kilo is in cold storage", "ledger Kilo remains in the working store"),
    ("replace certificate Delta", "the service presents the Delta replacement certificate", "the service presents the earlier certificate"),
    ("close ticket Amber", "ticket Amber is in the closed queue", "ticket Amber remains in the open queue"),
    ("send parcel Birch", "parcel Birch is with the courier", "parcel Birch remains in the dispatch room"),
    ("switch dashboard Nova to read-only mode", "dashboard Nova rejects edits", "dashboard Nova still accepts edits"),
    ("promote build Quartz", "the production status names build Quartz", "the production status names the earlier build"),
    ("remove account Lumen from the group", "account Lumen is absent from the group", "account Lumen remains in the group"),
    ("open archive Maple to the reviewers", "the reviewers can read archive Maple", "the reviewers cannot read archive Maple"),
    ("rotate secret Indigo", "the secret registry shows a new Indigo fingerprint", "the secret registry shows the previous Indigo fingerprint"),
    ("cancel booking Harbor", "booking Harbor is marked cancelled", "booking Harbor remains active"),
    ("enable mirror Sable", "mirror Sable serves requests", "mirror Sable remains offline"),
    ("file report Topaz", "report Topaz appears in the filed-record list", "report Topaz remains outside the filed-record list"),
    ("lock workspace Fern", "workspace Fern refuses new writes", "workspace Fern permits new writes"),
    ("release batch Umber", "batch Umber is in the release channel", "batch Umber remains in staging"),
    ("archive thread Willow", "thread Willow appears in the archive", "thread Willow remains in the active list"),
    ("transfer queue Iris to team Blue", "team Blue owns queue Iris", "the original team owns queue Iris"),
    ("revoke badge Coral", "badge Coral no longer opens the door", "badge Coral still opens the door"),
    ("start crawler Pine", "crawler Pine is processing pages", "crawler Pine remains idle"),
    ("delete snapshot Opal", "snapshot Opal is absent from the snapshot list", "snapshot Opal remains in the snapshot list"),
    ("approve invoice Silver", "invoice Silver is in the approved ledger", "invoice Silver remains in the pending ledger"),
    ("restore replica Moss", "replica Moss answers health checks", "replica Moss remains unavailable"),
    ("freeze dataset Ochre", "dataset Ochre rejects further changes", "dataset Ochre still accepts changes"),
]

DEADLINES = [
    "09:10 UTC on 7 September 2026", "14:25 UTC on 8 September 2026",
    "11:40 UTC on 9 September 2026", "16:55 UTC on 10 September 2026",
    "08:20 UTC on 11 September 2026", "13:35 UTC on 12 September 2026",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def choices(answer: str, alternatives: list[str], index: int) -> list[str]:
    values = [answer, *alternatives]
    assert len(values) == 3 and len(set(values)) == 3
    shift = index % 3
    return values[shift:] + values[:shift]


def event(form: str, behaviour: str, deadline: str) -> tuple[str, bool, str]:
    if form == "go-unless-no":
        rows = {
            "silent_before": (f"Sam sent no reply. The time is still before {deadline}.", False, "silent"),
            "silent_after": (f"Sam sent no reply before the deadline. The time is now after {deadline}.", True, "silent"),
            "decline_before": (f"Before {deadline}, Sam replied: ‘Do not do that.’ The time is now after {deadline}.", False, "replying"),
            "defer_before": (f"Before {deadline}, Sam replied: ‘Please wait until next week.’ The time is now after {deadline}.", False, "replying"),
            "question_before": (f"Before {deadline}, Sam replied only: ‘Which region would that affect?’ The time is now after {deadline}.", True, "replying"),
            "approve_before": (f"Before {deadline}, Sam replied: ‘Proceed with it.’ The time is now after {deadline}.", True, "replying"),
        }
    else:
        rows = {
            "silent_before": ("Sam sent no reply. Several hours have passed.", False, "silent"),
            "silent_after": ("Sam sent no reply. Several days have passed.", False, "silent"),
            "decline_before": ("Sam replied: ‘Do not do that.’ Several hours have passed.", False, "replying"),
            "defer_before": ("Sam replied: ‘Please wait until next week.’ Several hours have passed.", False, "replying"),
            "question_before": ("Sam replied only: ‘Which region would that affect?’ Several hours have passed.", False, "replying"),
            "approve_before": ("Sam replied: ‘Proceed with it.’ Several hours have passed.", True, "replying"),
        }
    return rows[behaviour]


def scientific_items() -> list[dict]:
    # Six silent and six reply cells per half-form, exactly as the proposal declared.
    behaviours = (
        ["silent_before"] * 6 + ["silent_after"] * 6
        + ["decline_before"] * 3 + ["defer_before"] * 3
        + ["question_before"] * 3 + ["approve_before"] * 3
    )
    names = [("Rowan", "Sam"), ("Mira", "Tao"), ("Nadia", "Ilan"), ("Kei", "Rosa")]
    rows = []
    for form_index, form in enumerate(("go-unless-no", "hold-until-yes")):
        for index, behaviour in enumerate(behaviours):
            action, happened, not_happened = ACTIONS[(index + form_index * 11) % len(ACTIONS)]
            deadline = DEADLINES[index % len(DEADLINES)]
            writer, addressee = names[(index + form_index) % len(names)]
            described_event, should_happen, response_kind = event(form, behaviour, deadline)
            described_event = described_event.replace("Sam", addressee)
            if form == "go-unless-no":
                english = (
                    f"{writer} wrote to {addressee}: ‘I will {action} at {deadline} unless you tell me not to "
                    f"before {deadline}; if I hear nothing from you by {deadline}, I will treat that as consent and proceed.’"
                )
                ainglish = f"{writer} wrote to {addressee}: ‘{action}, go-unless-no({deadline}).’"
            else:
                english = (
                    f"{writer} wrote to {addressee}: ‘I will not {action} until you explicitly tell me to go ahead; "
                    "if I hear nothing from you, I will not proceed.’"
                )
                ainglish = f"{writer} wrote to {addressee}: ‘{action}, hold-until-yes.’"
            answer = happened if should_happen else not_happened
            rows.append({
                "id": f"go-hold-{form_index + 1}-{index + 1:02d}",
                "english": english + " " + described_event,
                "ainglish": ainglish + " " + described_event,
                "question": f"If {writer} follows the rule stated in the message, which resulting state does it require?",
                "options": choices(answer, [not_happened if should_happen else happened, "the message leaves the resulting state unspecified"], index + form_index),
                "answer": answer,
                "form": form,
                "settlement_stratum": form,
                "strata": {"form": form, "behaviour": behaviour, "response_kind": response_kind},
            })
    return rows


def calibration_items() -> list[dict]:
    facts = [
        ("amber token", "locker 19"), ("blue key", "cabinet 4"), ("cedar card", "drawer 11"),
        ("dune badge", "vault 6"), ("elm seal", "locker 23"), ("flint pass", "cabinet 14"),
        ("granite tag", "drawer 2"), ("hazel chip", "vault 17"), ("indigo note", "locker 8"),
        ("jade disk", "cabinet 21"), ("kelp token", "drawer 13"), ("linen key", "vault 5"),
    ]
    rows = []
    for index, (thing, location) in enumerate(facts):
        answer = location
        rows.append({
            "id": f"go-hold-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"An inventory note mentions the {thing}, but gives no storage location.",
            "ainglish": f"An inventory note states that the {thing} is stored in {location}.",
            "question": f"Where does the note state that the {thing} is stored?",
            "options": choices(answer, ["the dispatch desk", "the location is not stated"], index),
            "answer": answer,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def main() -> None:
    rows = scientific_items() + calibration_items()
    assert len(rows) == 60 and len({row["id"] for row in rows}) == 60
    scientific = [row for row in rows if not row.get("calibration")]
    counts = Counter((row["form"], row["strata"]["response_kind"]) for row in scientific)
    assert counts == Counter({
        ("go-unless-no", "silent"): 12, ("go-unless-no", "replying"): 12,
        ("hold-until-yes", "silent"): 12, ("hold-until-yes", "replying"): 12,
    })
    path = ROOT / "items.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.go-hold-dispute-carrier.v1",
        "items_file": path.name,
        "items_sha256": sha256(canonical(rows)).hexdigest(),
        "scientific_items": 48,
        "calibration_items": 12,
        "form_counts": dict(Counter(row["form"] for row in scientific)),
        "response_counts": {f"{form}/{kind}": count for (form, kind), count in sorted(counts.items())},
        "model_calls": 0,
    }
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
