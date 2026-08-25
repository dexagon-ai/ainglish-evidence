#!/usr/bin/env python3
"""Build a rights-pinned Ainglish learning and held-out transfer corpus."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
SYSTEM = (
    "You are using the ratified Ainglish register. Expand and apply only the supplied registered "
    "meaning. Preserve scope, constraints, uncertainty, and actor boundaries; do not invent effects."
)
TRANSFER_HOLDOUT = {
    "we-including-you-we-excluding-you-clusivity-mark-whether-we--4",
    "no-delegation-one-hop-delegation-allowed-state-whether-a-tas",
    "start-by-complete-by-say-which-task-event-a-deadline-constra",
    "true-as-worded-false-as-worded-unambiguous-answers-to-negati",
}
TRANSFER_MARKERS = (
    "we-including-you",
    "we-excluding-you",
    "no-delegation",
    "one-hop-delegation-allowed",
    "start-by",
    "complete-by",
    "true-as-worded",
    "false-as-worded",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def record(slug: str, task: str, user: str, assistant: str, split: str) -> dict:
    return {
        "id": hashlib.sha256(f"{slug}\n{task}\n{user}".encode()).hexdigest()[:24],
        "source_slug": slug,
        "task": task,
        "split": split,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
    }


def rows_for(proposal: dict, split: str) -> list[dict]:
    slug = proposal["slug"]
    title = proposal["title"]
    form = proposal["form"]
    mapping = proposal["english_mapping"]
    constraints = proposal.get("form_constraints") or "No separate form-constraints field is registered; obey the complete mapping."
    example_a = proposal.get("example_ainglish")
    example_e = proposal.get("example_english")
    rows = [
        record(slug, "definition",
               f"What does the ratified Ainglish form `{form}` mean? Give its careful-English mapping without adding effects.",
               mapping, split),
        record(slug, "lossless-expansion",
               f"Expand this registered Ainglish surface into careful English: `{form}`",
               mapping, split),
        record(slug, "form-retrieval",
               f"Which exact ratified Ainglish form has this registered meaning?\n\n{mapping}",
               form, split),
        record(slug, "scope-and-constraints",
               f"State the scope and use constraints for `{form}`. Preserve the register boundary and do not infer adoption.",
               f"Registered mapping:\n{mapping}\n\nForm constraints:\n{constraints}", split),
        record(slug, "distinction-summary",
               f"Summarize the operational distinction named by this ratified entry: {title}",
               f"Form: {form}\nMeaning: {mapping}", split),
    ]
    if example_a and example_e:
        rows.extend([
            record(slug, "example-expand", f"Expand this Ainglish example carefully:\n{example_a}", example_e, split),
            record(slug, "example-encode", f"Rewrite this careful-English example using the registered form:\n{example_e}", example_a, split),
        ])
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> str:
    encoded = b"".join(canonical(row) + b"\n" for row in rows)
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def marker_hits(row: dict) -> list[str]:
    content = "\n".join(message["content"] for message in row["messages"]).casefold()
    return [marker for marker in TRANSFER_MARKERS if marker in content]


def main() -> None:
    client = AinglishClient(use_env=False)
    proposals = [
        row for row in client.iter_proposals(page_size=200)
        if row.get("kind") != "protocol" and row.get("stage") == "ratified" and not row.get("superseded_by")
    ]
    proposals.sort(key=lambda row: row["slug"])
    if len(proposals) < 15:
        raise SystemExit("REFUSING: unexpectedly small ratified population")
    actual_slugs = {row["slug"] for row in proposals}
    if not TRANSFER_HOLDOUT <= actual_slugs:
        raise SystemExit(f"REFUSING: held-out construct missing: {sorted(TRANSFER_HOLDOUT - actual_slugs)}")
    terms = client.contribution_terms()
    snapshot = {
        "kind": "dexagon.ainglish.ratified-training-source.v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "https://ainglish.org/api/v1/proposals",
        "contribution_terms": {
            key: terms.get(key) for key in ("version", "digest", "license", "dedication") if terms.get(key) is not None
        },
        "proposals": [
            {key: row.get(key) for key in (
                "slug", "public_id", "title", "form", "english_mapping", "form_constraints",
                "example_ainglish", "example_english", "ratified_at", "ratified_version",
            )}
            for row in proposals
        ],
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "register-snapshot.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")

    train_dev, validation_seen, transfer, release = [], [], [], []
    excluded_cross_references = []
    for proposal in proposals:
        held_out = proposal["slug"] in TRANSFER_HOLDOUT
        all_rows = rows_for(proposal, "release-train")
        release.extend(all_rows)
        if held_out:
            transfer.extend(rows_for(proposal, "transfer-holdout"))
            continue
        development = rows_for(proposal, "development")
        validation_task = "distinction-summary"
        for row in development:
            hits = marker_hits(row)
            if hits:
                excluded_cross_references.append(
                    {"id": row["id"], "source_slug": row["source_slug"], "task": row["task"], "markers": hits}
                )
                continue
            if row["task"] == validation_task:
                row["split"] = "validation-seen"
                validation_seen.append(row)
            else:
                row["split"] = "train-dev"
                train_dev.append(row)
    contamination = [
        {"id": row["id"], "markers": marker_hits(row)}
        for row in train_dev + validation_seen if marker_hits(row)
    ]
    if contamination:
        raise SystemExit(f"REFUSING: exact holdout markers leaked after filtering: {contamination}")
    outputs = {}
    for filename, rows in (
        ("train-dev.jsonl", train_dev),
        ("validation-seen.jsonl", validation_seen),
        ("transfer-holdout.jsonl", transfer),
        ("train-release.jsonl", release),
    ):
        outputs[filename] = {"rows": len(rows), "sha256": write_jsonl(ROOT / filename, rows)}
    manifest = {
        "kind": "dexagon.ainglish.learning-corpus-manifest.v1",
        "source_snapshot_sha256": snapshot["content_sha256"],
        "ratified_constructs": len(proposals),
        "development_train_constructs": len(proposals) - len(TRANSFER_HOLDOUT),
        "transfer_holdout_constructs": sorted(TRANSFER_HOLDOUT),
        "transfer_holdout_markers": list(TRANSFER_MARKERS),
        "excluded_cross_reference_rows": excluded_cross_references,
        "outputs": outputs,
        "contamination_boundary": (
            "The development adapter sees neither source rows from transfer-holdout constructs nor "
            "any row containing their exact registered marker strings. This is not a claim that all "
            "ordinary-English concepts related to those meanings are absent. A later release adapter "
            "may use train-release only after development evaluation is frozen."
        ),
        "governance_boundary": (
            "Trained adapters and their evaluations are product/research artifacts, never independent Ainglish measurement principals or replication evidence."
        ),
    }
    manifest["content_sha256"] = hashlib.sha256(canonical(manifest)).hexdigest()
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
