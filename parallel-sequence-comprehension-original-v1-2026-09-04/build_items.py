#!/usr/bin/env python3
"""Build a fresh 200-item matched timing panel without making model calls."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

DOMAINS = {
    "operational": [
        ("fetch the primary manifest", "fetch the mirror manifest", "compare both digests"),
        ("scan the east shard", "scan the west shard", "merge both reports"),
        ("compile the API service", "compile the worker service", "assemble the release"),
        ("copy the audit ledger", "rotate the ledger key", "verify the restored copy"),
        ("probe the public endpoint", "probe the private endpoint", "summarize the responses"),
        ("render the desktop page", "render the mobile page", "compare both screenshots"),
        ("validate the schema", "validate the fixtures", "publish the validation report"),
        ("index the document archive", "index the image archive", "join the search catalogs"),
        ("rebuild the cache", "restart the queue", "run the smoke check"),
        ("export the billing table", "export the usage table", "reconcile their totals"),
        ("download the north replica", "download the south replica", "select the newest record"),
        ("inspect the ingress rules", "inspect the egress rules", "file the security note"),
        ("compress the event log", "compress the trace log", "upload both archives"),
        ("test the JSON parser", "test the YAML parser", "publish the compatibility matrix"),
        ("warm the catalog cache", "warm the profile cache", "measure the combined hit rate"),
        ("snapshot database Cedar", "snapshot database Flint", "record both checksums"),
        ("lint the templates", "lint the stylesheets", "package the static assets"),
        ("query sensor Amber", "query sensor Violet", "calculate the joint reading"),
        ("replay queue Alpha", "replay queue Beta", "compare their failure sets"),
        ("sign the source bundle", "sign the data bundle", "publish both signatures"),
        ("drain worker pool Red", "drain worker pool Blue", "replace their instances"),
        ("measure route Aspen", "measure route Birch", "choose the lower-latency path"),
        ("check the primary certificate", "check the backup certificate", "update the trust report"),
        ("read the first ledger partition", "read the second ledger partition", "compute the full balance"),
        ("verify agent Lin's digest independently", "verify agent Rao's digest independently", "compare the two receipts"),
    ],
    "social": [
        ("send Mira the invitation", "send Jonah the invitation", "collect both replies"),
        ("brief the design group", "brief the operations group", "record their questions"),
        ("interview candidate A", "interview candidate B", "write the comparison note"),
        ("notify the authors", "notify the reviewers", "open the shared discussion"),
        ("ask Leila for consent", "ask Anton for consent", "record both answers"),
        ("translate the announcement for team East", "translate it for team West", "publish both versions"),
        ("thank the incident responders", "thank the support volunteers", "archive the acknowledgements"),
        ("introduce analyst Noor to editor Emil", "introduce analyst Sana to editor Theo", "schedule their follow-ups"),
        ("collect feedback from the readers", "collect feedback from the writers", "compare the themes"),
        ("send the accessibility survey", "send the clarity survey", "combine the anonymous totals"),
        ("moderate the first forum session", "moderate the second forum session", "publish the session notes"),
        ("call the venue manager", "call the equipment manager", "confirm both arrangements"),
        ("invite the local researchers", "invite the remote researchers", "prepare the attendee list"),
        ("ask the first witness for a statement", "ask the second witness for a statement", "compare the accounts"),
        ("brief the morning facilitator", "brief the evening facilitator", "share the common checklist"),
        ("send the draft to Priya", "send the draft to Malik", "collect their independent reviews"),
        ("consult the language group", "consult the safety group", "write the joint summary"),
        ("record Hana's oral history", "record Dario's oral history", "catalog both recordings"),
        ("teach cohort Cedar the protocol", "teach cohort Delta the protocol", "compare their quiz results"),
        ("ask the users about navigation", "ask the editors about navigation", "rank the reported obstacles"),
        ("welcome the new moderators", "welcome the new measurers", "introduce the two groups"),
        ("send agent Kaia the first prompt", "send agent Pavel the first prompt", "compare their independent answers"),
        ("debrief the field team", "debrief the laboratory team", "merge the action lists"),
        ("confirm Rosa's attendance", "confirm Yara's attendance", "release unused seats"),
        ("explain the change to the press desk", "explain it to the research desk", "answer their follow-up questions"),
    ],
    "governance": [
        ("publish the draft rule", "open the comment window", "summarize the submissions"),
        ("verify the quorum", "count the ballots", "certify the outcome"),
        ("record the proposal", "record the objection", "place both in the docket"),
        ("audit the first evidence packet", "audit the second evidence packet", "issue the joint finding"),
        ("notify the eligible voters", "freeze the voter roll", "open the ballot"),
        ("review the moderation report", "review the author's response", "publish the disposition"),
        ("check the release manifest", "check the rights statement", "authorize publication"),
        ("collect the supporting reasons", "collect the opposing reasons", "prepare the neutral brief"),
        ("appoint the first panel member", "appoint the second panel member", "declare the completed panel"),
        ("archive the superseded rule", "activate the successor rule", "record the effective instant"),
        ("inspect the public minutes", "inspect the private audit trail", "resolve any discrepancy"),
        ("validate the nomination", "validate the seconder list", "place the item on the agenda"),
        ("open the appeal", "appoint the appeal reviewer", "serve the final decision"),
        ("publish the conflict disclosure", "publish the recusal notice", "assign a replacement reviewer"),
        ("compare the two policy drafts", "compare their evidence tables", "recommend one text"),
        ("invite written objections", "invite written endorsements", "count each class separately"),
        ("review the spending request", "review the risk assessment", "release or refuse the funds"),
        ("check the candidate's eligibility", "check the sponsor's standing", "accept or reject the filing"),
        ("read the majority report", "read the minority report", "publish both without alteration"),
        ("record the temporary order", "record the expiry condition", "schedule the mandatory review"),
        ("verify the public-domain dedication", "verify the dataset checksums", "sign the release receipt"),
        ("inspect moderator Lin's finding independently", "inspect moderator Rao's finding independently", "compare the two conclusions"),
        ("close the evidence window", "seal the submitted artifacts", "begin the adjudication"),
        ("announce the proposed amendment", "announce its impact analysis", "start the consultation"),
        ("test the rule against case Amber", "test it against case Violet", "publish the precedential analysis"),
    ],
    "scheduling": [
        ("reserve room Aspen", "reserve room Birch", "send the final venue notice"),
        ("book the morning train", "book the evening hotel", "share the itinerary"),
        ("schedule the design review", "schedule the security review", "publish the combined calendar"),
        ("open registration for workshop A", "open registration for workshop B", "allocate the remaining places"),
        ("confirm the speaker's slot", "confirm the moderator's slot", "release the programme"),
        ("start the east maintenance window", "start the west maintenance window", "announce service restoration"),
        ("reserve the recording studio", "reserve the editing suite", "notify the production team"),
        ("assign the morning shift", "assign the night shift", "publish the rota"),
        ("schedule agent Lin's run", "schedule agent Rao's run", "compare their independent receipts"),
        ("open the first office hour", "open the second office hour", "collate the questions"),
        ("set the submission deadline", "set the response deadline", "publish the full timetable"),
        ("start the blue deployment", "start the green deployment", "close the change window"),
        ("reserve the primary test rig", "reserve the backup test rig", "confirm the allocation"),
        ("schedule the data freeze", "schedule the code freeze", "announce the release candidate"),
        ("plan the field survey", "plan the laboratory survey", "merge their collection calendar"),
        ("open nominations", "open endorsement filing", "close both intake windows"),
        ("set Mira's interview", "set Jonah's interview", "send the panel's agenda"),
        ("start the first batch", "start the second batch", "publish the completion forecast"),
        ("reserve bandwidth for backup A", "reserve bandwidth for backup B", "confirm the transfer plan"),
        ("schedule the accessibility audit", "schedule the language audit", "prepare the joint readout"),
        ("open the morning ballot", "open the evening ballot", "combine the certified counts"),
        ("begin the north-region drill", "begin the south-region drill", "issue the national report"),
        ("set the archive migration", "set the index rebuild", "announce the search outage"),
        ("book the first rehearsal", "book the second rehearsal", "confirm the performance time"),
        ("schedule the initial review", "schedule the follow-up review", "publish both appointments"),
    ],
}


def rotate(options: list[str], amount: int) -> list[str]:
    amount %= len(options)
    return options[amount:] + options[:amount]


def render_marked(actions: tuple[str, str, str], marker: str, style: int) -> str:
    a, b, c = actions
    if style == 0:
        return f"req: {a}; {b}, {marker}."
    if style == 1:
        return f"req: {a} and {b}, {marker}."
    if style == 2:
        return f"req:\n- {a}\n- {b}\n{marker}."
    if style == 3:
        return f"req: first, {a}; second, {b}, {marker}."
    return f"req: {a}; {b}; {c}, {marker}."


def render_careful(actions: tuple[str, str, str], polarity: str, style: int) -> str:
    a, b, c = actions
    listed = f"{a}; {b}" + (f"; {c}" if style == 4 else "")
    if polarity == "parallel":
        return (
            "Requirement: begin the listed actions without waiting for any earlier-listed action "
            f"to reach a terminal outcome: {listed}. Their execution intervals are intended to overlap, "
            "and the written order creates no precedence requirement."
        )
    return (
        f"Requirement: first, {a}. Wait until that action reaches a terminal outcome, whether success or failure. "
        f"Only after that may the second listed action begin: {b}." +
        (f" After the second action reaches a terminal outcome, perform the third: {c}." if style == 4 else "")
    )


def scientific_items() -> list[dict]:
    rows = []
    global_index = 0
    for domain, workflows in DOMAINS.items():
        assert len(workflows) == 25
        for local_index, actions in enumerate(workflows):
            style = local_index % 5
            for polarity, marker, answer in [
                ("parallel", "in-parallel", "yes"),
                ("sequence", "in-sequence", "no"),
            ]:
                options = rotate(["yes", "no", "cannot determine"], global_index + (polarity == "sequence"))
                rows.append({
                    "id": f"{polarity}-{domain}-{local_index + 1:02d}",
                    "english": render_careful(actions, polarity, style),
                    "ainglish": render_marked(actions, marker, style),
                    "question": "May the second listed action begin before the first has reached a terminal outcome?",
                    "options": options,
                    "answer": answer,
                    "settlement_stratum": polarity,
                    "polarity": polarity,
                    "domain": domain,
                    "render_style": ["semicolon", "and", "bullets", "ordinal-prose", "three-action"][style],
                    "shared_workflow_id": f"{domain}-{local_index + 1:02d}",
                    "terminal_outcome_includes_failure": True,
                })
            global_index += 1
    return rows


def calibration_items() -> list[dict]:
    subjects = [
        ("cedar gate", "amber gate"), ("north lamp", "south lamp"),
        ("first ledger", "second ledger"), ("red sensor", "blue sensor"),
        ("archive A", "archive B"), ("route Pine", "route Oak"),
        ("worker Mira", "worker Jonah"), ("queue East", "queue West"),
        ("room Aspen", "room Birch"), ("model Jade", "model Quartz"),
        ("report 17", "report 18"), ("adapter K", "adapter L"),
        ("service Dawn", "service Dusk"), ("table Alpha", "table Beta"),
        ("agent Noor", "agent Emil"), ("build 41", "build 42"),
    ]
    rows = []
    for index, (answer, other) in enumerate(subjects, 1):
        rows.append({
            "id": f"control-{index:02d}",
            "english": f"The note mentions the {answer} and the {other}, but does not say which one passed inspection.",
            "ainglish": f"The {answer} passed inspection; the {other} did not.",
            "question": "Which named item passed inspection?",
            "options": rotate([answer, other, "cannot determine"], index),
            "answer": answer,
            "calibration": True,
            "calibration_scope": "target-independent",
        })
    return rows


def main() -> None:
    scientific = scientific_items()
    calibration = calibration_items()
    rows = scientific + calibration
    assert len(scientific) == 200 and len(calibration) == 16
    assert len({row["id"] for row in rows}) == len(rows)
    assert sum(row["polarity"] == "parallel" for row in scientific) == 100
    assert sum(row["polarity"] == "sequence" for row in scientific) == 100
    for workflow_id in {row["shared_workflow_id"] for row in scientific}:
        pair = [row for row in scientific if row["shared_workflow_id"] == workflow_id]
        assert {row["polarity"] for row in pair} == {"parallel", "sequence"}
    (ROOT / "items.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    index = {
        "kind": "dexagon.ainglish.parallel-sequence-carrier-index.v1",
        "scientific_items": 200,
        "shared_workflows": 100,
        "calibration_items": 16,
        "settlement_strata": {"parallel": 100, "sequence": 100},
        "domain_counts_per_polarity": {domain: 25 for domain in DOMAINS},
        "items_sha256": digest,
        "model_calls": 0,
    }
    index["content_sha256"] = sha256(json.dumps(index, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
