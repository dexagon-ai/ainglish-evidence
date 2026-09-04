#!/usr/bin/env python3
"""Submit the retained, locally replay-verified result without further reader calls."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

SLUG = "in-parallel-in-sequence-say-whether-listed-actions-may-overl-2"
ATTEMPT_ID = "7137bb19-9869-486e-bb5c-b1b4f5d42b93"
REQUEST = ROOT / f"runspec.attempt-{ATTEMPT_ID}.measurement.php-rounding.json"


def main() -> None:
    if (ROOT / "result.json").exists():
        raise SystemExit("REFUSING: retained result was already submitted")
    payload = json.loads(REQUEST.read_text(encoding="utf-8"))
    if payload.get("attempt_id") != ATTEMPT_ID:
        raise SystemExit("REFUSING: corrected request does not name the frozen attempt")
    client = ainglish_client()
    attempt = client.attempt(ATTEMPT_ID)
    if attempt.get("state") != "open" or attempt.get("measurement_ref") is not None:
        raise SystemExit("REFUSING: attempt is no longer open and unfiled")
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "seconded" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal lifecycle changed before retained-result submission")
    if any(
        row.get("metric") == "comprehension_accuracy_delta" and not row.get("replicates_hash")
        for row in proposal.get("measurements") or []
    ):
        raise SystemExit("REFUSING: a comprehension original appeared before retained-result submission")
    result = client.measure(SLUG, payload)
    (ROOT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "kind": result.get("kind"),
        "manifest_hash": (result.get("measurement") or result).get("manifest_hash"),
        "attempt_id": ATTEMPT_ID,
        "value": (result.get("measurement") or result).get("value"),
    }, indent=2))


if __name__ == "__main__":
    main()
