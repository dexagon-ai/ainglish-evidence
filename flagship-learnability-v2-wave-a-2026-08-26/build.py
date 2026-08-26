#!/usr/bin/env python3
"""Build fresh learnability-v2 entry snapshots and answer-bearing item sets offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
N = 48
SEED = 2026082617
CAMPAIGNS = {
    "each-alone": ("each-alone-as-one", "each-alone", "groups"),
    "as-one": ("each-alone-as-one", "as-one", "groups"),
    "you-one": ("you-one-you-all", "you-one", "address"),
    "you-all": ("you-one-you-all", "you-all", "address"),
    "or-both": ("or-both-not-both", "or-both", "disjunction"),
    "not-both": ("or-both-not-both", "not-both", "disjunction"),
}
GROUP_SCENARIOS = [
    ("reviewers", "approved the release", "approval"),
    ("auditors", "verified the ledger", "verification"),
    ("operators", "restarted the worker", "restart"),
    ("editors", "signed the notice", "signature"),
    ("maintainers", "closed the incident", "closure"),
    ("inspectors", "checked the archive", "inspection"),
    ("stewards", "sealed the package", "seal"),
    ("analysts", "scored the application", "score"),
]
ADDRESS_SCENARIOS = [
    ("Amina", "Bram", "Chen", "approve ticket"),
    ("Dev", "Esme", "Fionn", "inspect archive"),
    ("Gia", "Hugo", "Ines", "verify digest"),
    ("Joon", "Kira", "Liam", "sign receipt"),
    ("Mina", "Niko", "Ola", "review incident"),
    ("Priya", "Rui", "Sol", "rotate key"),
    ("Tess", "Umar", "Vale", "publish anchor"),
    ("Wynn", "Xavi", "Yuki", "close ballot"),
]
DISJUNCTION_SCENARIOS = [
    ("enable caching", "enable tracing"),
    ("retry the job", "escalate the incident"),
    ("grant read access", "grant write access"),
    ("archive the file", "retain the file"),
    ("notify the owner", "notify the reviewer"),
    ("use mirror A", "use mirror B"),
    ("run the audit", "run the simulation"),
    ("publish the summary", "publish the appendix"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def placed_options(answer: str, alternatives: list[str], position: int) -> list[str]:
    if answer in alternatives or len(set(alternatives)) != len(alternatives):
        raise AssertionError((answer, alternatives))
    options = list(alternatives)
    options.insert(position % (len(alternatives) + 1), answer)
    return options


def real_row(campaign: str, index: int, message: str, question: str,
             answer: str, alternatives: list[str], probe: str) -> dict:
    return {
        "id": f"learn-{campaign}-{index + 1:03d}",
        "english": message,
        "ainglish": message,
        "question": question,
        "options": placed_options(answer, alternatives, index % 3),
        "answer": answer,
        "marker": campaign,
        "probe": probe,
        "scenario_id": f"learnability-wave-a-{campaign}-{index + 1:03d}",
    }


def group_rows(marker: str) -> list[dict]:
    distributive = marker == "each-alone"
    rows = []
    for index in range(N):
        group, action, noun = GROUP_SCENARIOS[index % len(GROUP_SCENARIOS)]
        count = 2 + ((index // 6 + index % 6) % 4)
        message = f"For round {700 + index}, the {count} {group} {action}, {marker}."
        probe = index % 6
        if probe == 0:
            q = "Does the marked statement assert one separate instance for every member?"
            answer = "yes" if distributive else "no"
            alternatives = ["no" if distributive else "yes", "not stated"]
        elif probe == 1:
            q = "Does the marked statement assert exactly one collective instance?"
            answer = "no" if distributive else "yes"
            alternatives = ["yes" if distributive else "no", "not stated"]
        elif probe == 2:
            q = (f"Would {count} separate {noun} instances satisfy the stated multiplicity?"
                 if distributive else f"Would one joint {noun} instance satisfy the stated multiplicity?")
            answer, alternatives = "yes", ["no", "not stated"]
        elif probe == 3:
            q = "Does the marker state that all members acted simultaneously?"
            answer, alternatives = "not stated", ["yes", "no"]
        elif probe == 4:
            q = "Does the marker identify which member acted first?"
            answer, alternatives = "not stated", ["yes", "no"]
        else:
            q = "How many instances does the marked statement assert?"
            answer = f"{count} separate instances" if distributive else "one collective instance"
            alternatives = (["one collective instance", "not stated"] if distributive
                            else [f"{count} separate instances", "not stated"])
        rows.append(real_row(marker, index, message, q, answer, alternatives, f"group-{probe}"))
    return rows


def address_rows(marker: str) -> list[dict]:
    singular = marker == "you-one"
    rows = []
    for index in range(N):
        one, two, three, action = ADDRESS_SCENARIOS[index % len(ADDRESS_SCENARIOS)]
        ticket = 300 + index
        envelope = (f"Private message addressed only to {one}." if singular
                    else f"Group message addressed to {one}, {two}, and {three}.")
        message = f"{envelope} {marker} must {action} {ticket}."
        probe = index % 6
        if probe == 0:
            q = "Does the marked clause address exactly one recipient?"
            answer = "yes" if singular else "no"
            alternatives = ["no" if singular else "yes", "not stated"]
        elif probe == 1:
            q = "Does the marked clause address every member of the established group?"
            answer = "no" if singular else "yes"
            alternatives = ["yes" if singular else "no", "not stated"]
        elif probe == 2:
            q = f"Is {three} included in the marked recipient set?"
            answer = "no" if singular else "yes"
            alternatives = ["yes" if singular else "no", "not stated"]
        elif probe == 3:
            q = "Does the marker say whether the work happens jointly or once per recipient?"
            answer, alternatives = "not stated", ["jointly", "once per recipient"]
        elif probe == 4:
            if singular:
                q = "Does merely forwarding the message later preserve the original one-person addressee boundary?"
                answer, alternatives = "yes", ["no", "not stated"]
            else:
                q = "Would forwarding the message later automatically add a new addressee?"
                answer, alternatives = "no", ["yes", "not stated"]
        else:
            q = "Does the recipient-number marker itself establish that the request is authorized?"
            answer, alternatives = "not stated", ["yes", "no"]
        rows.append(real_row(marker, index, message, q, answer, alternatives, f"address-{probe}"))
    return rows


def disjunction_rows(marker: str) -> list[dict]:
    inclusive = marker == "or-both"
    rows = []
    for index in range(N):
        left, right = DISJUNCTION_SCENARIOS[index % len(DISJUNCTION_SCENARIOS)]
        message = f"For case {500 + index}, {left} or {right}, {marker}."
        probe = index % 6
        if probe == 0:
            q = "Does the marked disjunction permit taking both listed options?"
            answer = "yes" if inclusive else "no"
            alternatives = ["no" if inclusive else "yes", "not stated"]
        elif probe == 1:
            q = "Must at least one listed option be taken?"
            answer, alternatives = "yes", ["no", "not stated"]
        elif probe == 2:
            q = "Does the marked disjunction permit taking neither option?"
            answer, alternatives = "no", ["yes", "not stated"]
        elif probe == 3:
            q = "Does the marked disjunction require exactly one option?"
            answer = "no" if inclusive else "yes"
            alternatives = ["yes" if inclusive else "no", "not stated"]
        elif probe == 4:
            q = "Does the marker say which listed option should be attempted first?"
            answer, alternatives = "not stated", [left, right]
        else:
            q = "Which particular listed option must be taken?"
            answer, alternatives = "not stated", [left, right]
        rows.append(real_row(marker, index, message, q, answer, alternatives, f"disjunction-{probe}"))
    return rows


BUILDERS = {"groups": group_rows, "address": address_rows, "disjunction": disjunction_rows}


def calibration_rows(campaign: str) -> list[dict]:
    objects = ["amber token", "bronze seal", "coral disk", "flint key",
               "jade card", "linen badge", "opal pass", "silver tag"]
    rows = []
    for index, obj in enumerate(objects):
        bay = 17 + index
        answer = f"bay {bay}"
        rows.append({
            "id": f"learn-{campaign}-cal-{index + 1:02d}",
            "calibration": True,
            "calibration_scope": "target-independent",
            "calibration_construct": "miv-location-control-v1",
            "english": f"The routing note labels the {obj} miv({bay}), but supplies no definition of miv.",
            "ainglish": (f"Control entry: miv(<N>) means the labelled object is stored in bay N.\n\n"
                         f"The routing note labels the {obj} miv({bay})."),
            "question": f"Where does the control place the {obj}?",
            "options": placed_options(answer, [f"bay {bay + 1}", "not inferable"], index % 3),
            "answer": answer,
            "set": "target-independent novel-marker positive control",
        })
    return rows


def entry_text(surface: dict) -> str:
    return (
        "Ainglish register entry\n"
        f"Title: {surface['title']}\n"
        f"Form: {surface['form']}\n\n"
        "Standard-English mapping:\n"
        f"{surface['english_mapping']}\n\n"
        "Registered Ainglish examples:\n"
        f"{surface['example_ainglish']}\n\n"
        "Registered standard-English examples:\n"
        f"{surface['example_english']}\n"
    )


def main() -> None:
    snapshots = json.loads((ROOT / "proposal-snapshots.json").read_text(encoding="utf-8"))
    index = {
        "kind": "dexagon.ainglish.flagship-learnability-wave-a-freeze.v1",
        "seed": SEED,
        "model_calls": 0,
        "governance_writes": 0,
        "campaigns": {},
    }
    entry_meta = {}
    for proposal_key, record in snapshots["proposals"].items():
        surface = record["surface"]
        text = entry_text(surface)
        path = ROOT / f"entry-{proposal_key}.txt"
        path.write_text(text, encoding="utf-8")
        entry_meta[proposal_key] = {
            "path": path.name,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "proposal_slug": surface["slug"],
            "proposal_form": surface["form"],
            "surface_sha256": record["surface_sha256"],
        }

    all_real = set()
    for campaign, (proposal_key, marker, builder_name) in CAMPAIGNS.items():
        scientific = BUILDERS[builder_name](marker)
        calibration = calibration_rows(campaign)
        rows = scientific + calibration
        assert len(scientific) == N and len(calibration) == 8
        assert all(row["english"] == row["ainglish"] for row in scientific)
        assert all(row["english"] != row["ainglish"] for row in calibration)
        pairs = {(row["english"], row["ainglish"], row["question"]) for row in scientific}
        assert len(pairs) == N and not (pairs & all_real)
        all_real |= pairs
        positions = [row["options"].index(row["answer"]) for row in scientific]
        assert {position: positions.count(position) for position in range(3)} == {0: 16, 1: 16, 2: 16}
        digest = hashlib.sha256(canonical(rows)).hexdigest()
        payload = {
            "kind": "dexagon.ainglish.flagship-learnability-items.v2",
            "campaign": campaign,
            "proposal_key": proposal_key,
            "marker": marker,
            "seed": SEED,
            "sha256": digest,
            "design": "48 fresh byte-identical marked real arms plus eight target-independent novel-marker calibrations",
            "items": rows,
        }
        path = ROOT / f"items-{campaign}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        index["campaigns"][campaign] = {
            "proposal_key": proposal_key,
            "marker": marker,
            "items_path": path.name,
            "items_sha256": digest,
            "scientific_items": N,
            "calibration_items": 8,
            "entry": entry_meta[proposal_key],
        }
    index["proposal_snapshot_sha256"] = snapshots["content_sha256"]
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"campaigns": len(CAMPAIGNS), "content_sha256": index["content_sha256"]}))


if __name__ == "__main__":
    main()
