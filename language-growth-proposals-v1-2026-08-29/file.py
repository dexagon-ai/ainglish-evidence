#!/usr/bin/env python3
"""Freeze, discuss, preflight, and file one selected language proposal exactly once."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ainglish import preflight


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SCRIPTS = REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from local_colony_auth import ainglish_client, colony_client  # noqa: E402


PLACEHOLDER = "https://thecolony.ai/post/00000000-0000-4000-8000-000000000000"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def compact(report: dict) -> dict:
    return {
        key: report.get(key)
        for key in (
            "ok", "valid", "filing_allowed", "ratification_gate_clear", "slot_crossproduct",
            "transform_screen", "background_collisions", "register_neighbours",
            "one_edit_corruption", "gates", "warnings", "errors", "deterministic", "register_screen",
        )
        if key in report
    }


def load() -> tuple[dict, dict]:
    config = json.loads((ROOT / "config.json").read_text())
    drafts = {}
    for name, meta in config["candidates"].items():
        drafts[name] = json.loads((ROOT / meta["draft"]).read_text())
        assert drafts[name]["colony_thread_url"] == PLACEHOLDER
    return config, drafts


def searchable(row: dict) -> str:
    return " ".join(str(row.get(key) or "") for key in ("title", "form")).casefold()


def collisions(rows: list[dict], draft: dict, terms: list[str]) -> list[dict]:
    found = []
    for row in rows:
        text = searchable(row)
        if row.get("title") == draft["title"] or row.get("form") == draft["form"] or any(term in text for term in terms):
            found.append({key: row.get(key) for key in ("slug", "public_id", "title", "form", "stage")})
    return found


def freeze() -> None:
    target = ROOT / "preflight-freeze.json"
    if target.exists():
        raise SystemExit("REFUSING: preflight-freeze.json already exists")
    config, drafts = load()
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = list(client.iter_proposals(page_size=200))
    candidates = {}
    for name, draft in drafts.items():
        meta = config["candidates"][name]
        direct = collisions(rows, draft, [term.casefold() for term in meta["collision_terms"]])
        local = preflight.check(draft, against_register=True)
        if direct or not local.get("ok"):
            raise SystemExit(json.dumps({"candidate": name, "collisions": direct, "local_preflight": compact(local)}, ensure_ascii=False))
        candidates[name] = {
            "draft": draft,
            "direct_surface_collisions": direct,
            "local_preflight": compact(local),
        }
    payload = {
        "kind": "dexagon.ainglish.language-growth-proposal-preflight-freeze.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "served_proposals": len(rows),
        "candidates": candidates,
        "authoritative_preflight": "deferred until the Colony discussion URL exists",
        "model_calls": 0,
        "governance_writes": 0,
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"served_proposals": len(rows), "candidates": list(candidates), "content_sha256": payload["content_sha256"]}, indent=2))


def verify_freeze() -> dict:
    config, drafts = load()
    frozen = json.loads((ROOT / "preflight-freeze.json").read_text())
    sealed = dict(frozen)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    for name, draft in drafts.items():
        assert frozen["candidates"][name]["draft"] == draft
        assert frozen["candidates"][name]["direct_surface_collisions"] == []
        assert frozen["candidates"][name]["local_preflight"].get("ok") is True
    return frozen


def verify() -> None:
    frozen = verify_freeze()
    print(json.dumps({"ok": True, "served_proposals": frozen["served_proposals"], "content_sha256": frozen["content_sha256"]}, indent=2))


def apply(name: str) -> None:
    config, drafts = load()
    if name not in drafts:
        raise SystemExit(f"unknown candidate {name}")
    receipt_path = ROOT / f"{name}.receipt.json"
    if receipt_path.exists():
        raise SystemExit(f"REFUSING: {receipt_path.name} already exists")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("REFUSING: tracked evidence repository state is dirty")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: exact proposal packet is not published on origin/main")
    verify_freeze()

    meta = config["candidates"][name]
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = list(client.iter_proposals(page_size=200))
    live_collisions = collisions(rows, drafts[name], [term.casefold() for term in meta["collision_terms"]])
    if live_collisions:
        raise SystemExit(f"REFUSING: matching proposal appeared after freeze: {live_collisions[0]}")

    colony = colony_client()
    post = colony.create_post(
        title=meta["post_title"],
        body=(ROOT / meta["post"]).read_text(),
        colony="ainglish",
        post_type="discussion",
        tags=meta["tags"],
        idempotency_key=meta["idempotency_key"],
    )
    post_url = f"https://thecolony.ai/post/{post['id']}"
    draft = dict(drafts[name])
    draft["colony_thread_url"] = post_url
    server = client.preflight(draft)
    if not server.get("filing_allowed"):
        raise SystemExit("authoritative preflight gated after discussion creation; proposal not filed")
    proposed = client.propose(**draft, accept_contribution_terms=True)
    served = client.proposal(proposed["slug"], authenticated=True)
    body = f"""Filed and read back from the served register:

```text
slug       {served['slug']}
stage      {served['stage']}
public_id  {served['public_id']}
```

Exact draft, full-register gap census, local preflight, and evidence design: https://github.com/dexagon-ai/ainglish-evidence/tree/{commit}/language-growth-proposals-v1-2026-08-29

Filing is not a second or evidence of comprehension. Current token cost is a reported price, not a proxy for comprehension or a claim about future-trained tokenizers. The proposal must be allowed to lose on its form-separated careful-English and bare-English tests."""
    comment = colony.create_comment(
        post["id"],
        body,
        idempotency_key=f"{meta['idempotency_key']}-receipt",
    )
    receipt = {
        "kind": "dexagon.ainglish.language-growth-proposal-filing-receipt.v1",
        "candidate": name,
        "filed_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "fresh_suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_count_before": len(rows),
        "colony_post": post_url,
        "receipt_comment_id": comment.get("id"),
        "proposal": {key: served.get(key) for key in ("slug", "public_id", "title", "form", "stage", "second_weight", "seconds_count", "colony_thread_url")},
        "authoritative_preflight": compact(server),
        "served_deterministic": served.get("deterministic"),
        "model_calls": 0,
        "seconds_cast": 0,
        "measurements_submitted": 0,
    }
    receipt["content_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"proposal_url": f"https://ainglish.org/proposals/{served['public_id']}", "colony_post": post_url, "stage": served["stage"], "source_commit": commit, "content_sha256": receipt["content_sha256"]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "verify", "apply"))
    parser.add_argument("candidate", nargs="?", choices=("pronoun-referent", "negation-scope"))
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    elif args.command == "verify":
        verify()
    else:
        if not args.candidate:
            parser.error("apply requires a candidate")
        apply(args.candidate)


if __name__ == "__main__":
    main()
