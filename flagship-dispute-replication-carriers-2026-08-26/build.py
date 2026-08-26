#!/usr/bin/env python3
"""Build fresh dispute-replication inputs without model or governance calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082641
PREFERENCE_FORMS = {
    "rather-not": (", rather-not.", ", but I'd rather you didn't."),
    "fine-either-way": (", fine-either-way.", ", either way is fine."),
    "would-welcome": (", would-welcome.", ", but I'd welcome it."),
}
POWER = ("peer", "superior", "subordinate")
ACTIONS = (
    "add another regression test", "update the changelog", "review the generated files",
    "attend the planning call", "send a separate status note", "bring a printed copy",
    "reorder the replacement cable", "polish the draft diagrams",
)
DIRECTIVES = (
    "Use sentence case for headings", "Keep the diagnostics flag enabled",
    "Send the summary in the task channel", "Run the formatter before returning work",
    "Preserve source comments", "Use UTC in exported reports", "Attach the completion receipt",
    "Exclude temporary files", "Use British spelling", "Sort imports alphabetically",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def placed(answer: str, alternatives: list[str], position: int) -> list[str]:
    assert answer not in alternatives and len(set(alternatives)) == 2
    values = list(alternatives)
    values.insert(position % 3, answer)
    return values


def preference_items() -> list[dict]:
    rows = []
    form_index = 0
    for form, (marked_suffix, careful_suffix) in PREFERENCE_FORMS.items():
        omit_wanted = form in ("rather-not", "fine-either-way")
        do_wanted = form in ("fine-either-way", "would-welcome")
        for frame in range(24):
            power = POWER[frame % 3]
            action = ACTIONS[(frame + form_index * 3) % len(ACTIONS)]
            case = 1600 + form_index * 100 + frame
            relationship = {
                "peer": "A peer writes to a peer",
                "superior": "A supervisor writes to a team member",
                "subordinate": "A team member writes to a supervisor",
            }[power]
            base = f"{relationship} for case {case}: You don't need to {action}"
            english = base + careful_suffix
            ainglish = base + marked_suffix
            probes = [
                ("The receiver omits the optional action. Has the sender got the outcome they preferred?", "yes" if omit_wanted else "no", "preference-omit"),
                ("The receiver performs the optional action. Has the sender got the outcome they preferred?", "yes" if do_wanted else "no", "preference-do"),
                ("Would performing the optional action violate the instruction?", "no", "false-prohibition"),
                ("Would omitting the optional action itself be a failure to satisfy an obligation?", "no", "false-obligation"),
            ]
            for probe_index, (question, answer, outcome) in enumerate(probes):
                rows.append({
                    "id": f"pref-{form}-{frame + 1:02d}-{probe_index + 1}",
                    "english": english,
                    "ainglish": ainglish,
                    "question": question,
                    "options": placed(answer, ["yes" if answer == "no" else "no", "cannot tell"], (frame * 4 + probe_index) % 3),
                    "answer": answer,
                    "form": form,
                    "frame": frame + 1,
                    "power_stratum": power,
                    "outcome": "preference_recovery" if outcome.startswith("preference") else "false_obligation",
                    "probe": outcome,
                })
        form_index += 1
    assert len(rows) == 288
    return rows


def persistence_item(form: str, index: int, stratum: str, attachment: str,
                     directive: str, later: str, applies: bool) -> dict:
    marked = ", this-once." if form == "this-once" else ", from-now-on."
    careful = ", just this once." if form == "this-once" else ", from now on."
    case = 2100 + index
    prefix = f"Instruction {case}: {directive}"
    context = f" Later, {later}"
    answer = "yes" if applies else "no"
    return {
        "id": f"persist-{form}-{index + 1:03d}",
        "english": prefix + careful + context,
        "ainglish": prefix + marked + context,
        "question": "Must the later work follow the earlier directive?",
        "options": placed(answer, ["no" if applies else "yes", "cannot tell"], index % 3),
        "answer": answer,
        "form": form,
        "stratum": stratum,
        "attachment": attachment,
        "scored_probe": "applicability",
    }


def persistence_items() -> list[dict]:
    rows = []
    ordinal = 0
    for form in ("this-once", "from-now-on"):
        standing = form == "from-now-on"
        attachments = (
            ("current-retry", "the same task is retried after a transient failure.", True),
            ("same-item-next-action", "another step on the same item begins.", True),
            ("later-comparable-task", "a new task of the same kind begins.", standing),
            ("later-noncomparable-task", "an unrelated task of a different kind begins.", False),
        )
        for attachment, later, applies in attachments:
            for offset in range(10):
                directive = DIRECTIVES[(ordinal + offset) % len(DIRECTIVES)]
                rows.append(persistence_item(form, ordinal, "core", attachment, directive, later, applies))
                ordinal += 1
        discordant = (
            ("storage-forbidden", "later-comparable-task", "persistent storage is unavailable, and then a new task of the same kind begins.", standing),
            ("audit-required", "later-comparable-task", "an audit log stores every directive, and then a new task of the same kind begins.", standing),
            ("project-scope", "later-comparable-task", "a later comparable task in the same named project begins.", standing),
        )
        for stratum, attachment, later, applies in discordant:
            for offset in range(10):
                directive = DIRECTIVES[(ordinal + offset) % len(DIRECTIVES)]
                rows.append(persistence_item(form, ordinal, stratum, attachment, directive, later, applies))
                ordinal += 1
    assert len(rows) == 140
    return rows


def calibration_items(prefix: str) -> list[dict]:
    rows = []
    objects = ("amber pass", "bronze seal", "coral key", "dune card", "elm disk", "flint badge", "jade token", "linen tag")
    for index, obj in enumerate(objects):
        bay = 71 + index
        answer = f"bay {bay}"
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "calibration_scope": "target-independent",
            "english": f"The note labels the {obj} rov({bay}), but supplies no definition of rov.",
            "ainglish": f"Control entry: rov(<N>) means the labelled object is stored in bay N.\n\nThe note labels the {obj} rov({bay}).",
            "question": f"Where does the control place the {obj}?",
            "options": placed(answer, [f"bay {bay + 1}", "not inferable"], index % 3),
            "answer": answer,
        })
    return rows


def main() -> None:
    snapshots = json.loads((ROOT / "proposal-snapshots.json").read_text(encoding="utf-8"))
    campaigns = {
        "preference": {
            "items": preference_items() + calibration_items("preference"),
            "scientific_items": 288,
            "calibration_items": 8,
        },
        "persistence": {
            "items": persistence_items() + calibration_items("persistence"),
            "scientific_items": 140,
            "calibration_items": 8,
        },
    }
    index = {"kind": "dexagon.ainglish.flagship-dispute-replication-freeze.v1", "seed": SEED, "model_calls": 0, "governance_writes": 0, "campaigns": {}}
    for name, campaign in campaigns.items():
        record = snapshots["proposals"][name]
        rows = campaign["items"]
        digest = hashlib.sha256(canonical(rows)).hexdigest()
        packet = {
            "kind": "dexagon.ainglish.flagship-dispute-replication-items.v1",
            "campaign": name,
            "slug": record["surface"]["slug"],
            "replicates_hash": record["target_original"]["replicates_hash"],
            "seed": SEED,
            "sha256": digest,
            **campaign,
        }
        path = ROOT / f"items-{name}.json"
        path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index["campaigns"][name] = {
            "slug": packet["slug"], "replicates_hash": packet["replicates_hash"],
            "items_path": path.name, "items_sha256": digest,
            "scientific_items": campaign["scientific_items"], "calibration_items": 8,
            "surface_sha256": record["surface_sha256"],
        }
    index["proposal_snapshot_sha256"] = snapshots["content_sha256"]
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"campaigns": 2, "scientific_items": 428, "content_sha256": index["content_sha256"]}))


if __name__ == "__main__":
    main()
