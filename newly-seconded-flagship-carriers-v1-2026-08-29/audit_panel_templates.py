#!/usr/bin/env python3
"""Verify template seals, immutable bindings, receipt gates, and manifest size."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
ACTIVATE_PATH = REPO / "manifest-bound-flagship-carriers-v1-2026-08-27" / "activate.py"
SPEC = importlib.util.spec_from_file_location("shared_activate", ACTIVATE_PATH)
assert SPEC and SPEC.loader
ACTIVATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ACTIVATE)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def reader(name: str, lineage: str, char: str) -> dict:
    model = f"audit-model-{name}"
    digest = char * 64
    receipt = {
        "kind": "ainglish.panel.reader-qualification-receipt.v1",
        "qualified": True, "lineage": lineage, "model": model,
        "model_digest": f"sha256:{digest}", "holdout_sha256": "f" * 64,
    }
    receipt["content_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    return {
        "name": name, "model": model, "model_digest": f"sha256:{digest}",
        "provider": "offline-audit-placeholder", "lineage": lineage,
        "qualification_receipt": receipt,
    }


def active_size(template: dict) -> tuple[int, int]:
    panel = ACTIVATE.validate_panel([reader("a", "Audit Lineage A", "a"), reader("b", "Audit Lineage B", "b")])
    seed = int(template["seed"])
    while not ACTIVATE.complete(template, panel, seed):
        seed += 1
        assert seed - int(template["seed"]) < 100_000
    active = {
        key: value for key, value in template.items()
        if key not in {"content_sha256", "kind", "activation", "model_calls", "governance_writes", "items", "items_artifact"}
    }
    active.update({
        "kind": "ainglish.panel.runspec.v1", "seed": seed, "panel": panel,
        "items_url": template["items_artifact"]["published_url"],
        "items_sha256": template["items_artifact"]["items_sha256"],
        "attempt": ACTIVATE.attempt_block(template, panel, seed),
    })
    return len(canonical(active)), seed - int(template["seed"])


def main() -> None:
    results = {}
    for name, expected_strata in (("average", 60), ("deletion", 78)):
        template = json.loads((ROOT / f"{name}-panel.template.json").read_text(encoding="utf-8"))
        unsigned = dict(template)
        seal = unsigned.pop("content_sha256")
        assert hashlib.sha256(canonical(unsigned)).hexdigest() == seal
        artifact = template["items_artifact"]
        packet = json.loads((ROOT / artifact["file"]).read_text(encoding="utf-8"))
        assert packet["items"] == template["items"]
        assert hashlib.sha256(canonical(template["items"])).hexdigest() == artifact["items_sha256"] == packet["sha256"]
        assert "/5eb3824f3e7805cdb8488615a5a8ae3f705ef911/" in artifact["published_url"]
        assert len(template["settlement_strata"]) == expected_strata
        assert len({row["id"] for row in template["settlement_strata"]}) == expected_strata
        assert all(row["weight"] == 1 for row in template["settlement_strata"])
        assert template["prerequisite_receipt"]["value"] <= 0
        size, seed_offset = active_size(template)
        assert size <= 20_000
        results[name] = {
            "template_sha256": seal, "items_sha256": artifact["items_sha256"],
            "settlement_strata": expected_strata, "activated_manifest_bytes": size,
            "audit_seed_offset": seed_offset, "published_item_binding": True,
        }
    print(json.dumps({
        "status": "ready_when_two_lineage_panel_qualifies", "targets": results,
        "fake_panel_scope": "offline activation and size audit only; never a scientific roster",
        "model_calls": 0, "api_calls": 0, "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
