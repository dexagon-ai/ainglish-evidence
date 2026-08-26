#!/usr/bin/env python3
"""Build two deterministic, form-balanced token packets without network or model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def pair(form: str, base: str, english_suffix: str, ainglish_suffix: str) -> dict:
    return {
        "form": form,
        "english": base + english_suffix,
        "ainglish": base + ainglish_suffix,
    }


def build_among() -> list[dict]:
    bases = (
        "The retryable responses are 408 and 429",
        "The accepted image formats are PNG and WebP",
        "The approved hosts are api-east and api-west",
        "The deployment roles are reviewer and operator",
        "The direct dependencies are parser and serializer",
        "The recognized evidence labels are observed and inferred",
        "The billable service tiers are standard and priority",
        "The enabled export targets are JSON and CSV",
        "The permitted login factors are passkey and security key",
        "The monitored regions are north and central",
        "The supported archive types are tar and zip",
        "The allowed notification channels are email and webhook",
        "The indexed document classes are report and invoice",
        "The scheduled maintenance windows are Tuesday and Thursday",
        "The accepted checksum families are SHA-256 and SHA-512",
        "The active worker pools are ingest and publish",
    )
    rows = []
    for base in bases:
        rows.append(pair("among-others", base, ", among others.", ", among-others."))
        rows.append(pair("and-no-others", base, ", and nothing else.", ", and-no-others."))
    return rows


def build_scope() -> list[dict]:
    bases = (
        "Use sentence case for the generated heading",
        "Keep the diagnostics flag enabled",
        "Send the summary in the task channel",
        "Run the formatter before returning the patch",
        "Preserve source comments during the rewrite",
        "Use UTC timestamps in the exported report",
        "Attach the receipt to the completion message",
        "Exclude temporary files from the archive",
    )
    rows = []
    for base in bases:
        rows.append(pair("this-once", base, ", just this once.", ", this-once."))
        rows.append(pair("from-now-on", base, ", from now on.", ", from-now-on."))
    return rows


def campaign(slug: str, forms: list[str], rows: list[dict], acceptance: dict) -> dict:
    assert len(rows) and not (len(rows) & (len(rows) - 1))
    assert len({(row["english"], row["ainglish"]) for row in rows}) == len(rows)
    assert {row["form"] for row in rows} == set(forms)
    assert len({sum(row["form"] == form for row in rows) for form in forms}) == 1
    return {
        "slug": slug,
        "forms": forms,
        "acceptance": acceptance,
        "test_set": rows,
        "items_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
    }


def main() -> None:
    campaigns = {
        "among": campaign(
            "among-others-and-no-others-is-the-list-the-whole-list-2",
            ["among-others", "and-no-others"],
            build_among(),
            {"metric": "token_delta", "at_most": 2},
        ),
        "scope": campaign(
            "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
            ["this-once", "from-now-on"],
            build_scope(),
            {"metric": "token_delta", "at_most": 2},
        ),
    }
    packet = {
        "kind": "ainglish.flagship-token-prerequisites.v1",
        "seed": "none - deterministic authored minimal pairs",
        "model_calls": 0,
        "campaigns": campaigns,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    (ROOT / "items.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        name: {"pairs": len(row["test_set"]), "items_sha256": row["items_sha256"]}
        for name, row in campaigns.items()
    }, indent=2))


if __name__ == "__main__":
    main()
