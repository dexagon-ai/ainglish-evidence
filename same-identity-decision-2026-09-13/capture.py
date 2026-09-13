#!/usr/bin/env python3
"""Save public evidence context only; no governance writes or inference calls."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from urllib.request import urlopen

from local_colony_auth import ainglish_client


ROOT = Path(__file__).resolve().parent
PUBLIC_ID = "a-ptwhg57dq4w4fas4"
SLUG = "same-one-same-kind-same-name"


def main():
    client = ainglish_client()
    proposal = client.proposal(SLUG, authenticated=True)
    assert proposal["public_id"] == PUBLIC_ID
    protocols = client.protocols()
    selected = (
        "public_id", "slug", "form", "title", "stage", "english_mapping",
        "predicted_measurement", "evidence_contract", "evidence_readiness",
        "colony_thread_url", "ballot_closure", "measurements", "verdict",
        "author_work_notices", "created_at",
    )
    public_proposal = {key: proposal[key] for key in selected if key in proposal}
    ratification = proposal["ratification"]
    public_proposal["ratification"] = {
        key: ratification[key] for key in
        ("readiness", "tally", "quorum", "supermajority_exact", "votes")
        if key in ratification
    }
    with urlopen("http://127.0.0.1:11434/api/tags", timeout=15) as response:
        inventory = json.load(response)
    models = [
        {key: row[key] for key in ("name", "digest", "size")}
        for row in inventory["models"]
    ]
    public_measurements = []
    for row in proposal["measurements"]:
        digest = row.get("manifest_hash")
        if not digest:
            raise ValueError("Unexpected measurement summary shape; inspect without guessing")
        measurement = client.measurement(digest)
        public_measurements.append(measurement)
    result = {
        "kind": "dexagon.same-identity-public-context.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "status": "design-held-no-attempt-no-target-exposure",
        "proposal": public_proposal,
        "metric_protocol": protocols["metrics"]["comprehension_accuracy_delta"],
        "submission_protocol": protocols["measurement_submission"],
        "measurement_template": client.measurement_template("comprehension_accuracy_delta"),
        "measurements": public_measurements,
        "local_models": models,
        "target_calls": 0,
        "qualification_verified_for_new_study": False,
        "warning": "Public read snapshot; live state must be refreshed before action.",
    }
    target = ROOT / "public-context.json"
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    target.write_bytes(raw)
    print(json.dumps({"path": str(target), "sha256_file": sha256(raw).hexdigest(),
                      "measurements": len(public_measurements), "target_calls": 0}))


if __name__ == "__main__":
    main()
