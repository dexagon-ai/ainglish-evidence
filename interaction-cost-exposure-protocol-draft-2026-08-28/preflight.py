#!/usr/bin/env python3
"""Run the public authoritative preflight on the sealed protocol draft."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    package = json.loads((ROOT / "draft.json").read_text(encoding="utf-8"))
    sealed = dict(package)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("REFUSING: draft digest drift")
    result = AinglishClient().preflight(package["proposal"])
    receipt = {
        "kind": "dexagon.ainglish.interaction-cost-protocol-preflight.v1",
        "draft_sha256": package["content_sha256"],
        "result": result,
    }
    receipt["content_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    (ROOT / "preflight.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"valid": result.get("valid"), "filing_allowed": result.get("filing_allowed"), "warnings": result.get("warnings"), "content_sha256": receipt["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
