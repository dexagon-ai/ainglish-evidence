"""Capture only public decision/audit fields; never suggestions, DMs or admin logs."""
import json
from pathlib import Path
from ainglish.client import AinglishClient


def main():
    client = AinglishClient(use_env=False)
    root = Path(__file__).parent
    audit = client.evidence_contract_audit()
    preview = client.release_preview()
    ballots = client.ballots()
    captured = {
        "kind": "ainglish.public.decision-completion-snapshot.v1",
        "generated_at": audit["generated_at"],
        "audit": audit,
        "release_preview": preview,
        "ballot_counts": ballots["counts"],
        "boundary": "Public read-only snapshot. Review flags are not invalidity findings or retrospective permissions. No suggestion observations, private feedback or DMs are included.",
    }
    (root / 'public-snapshot.json').write_text(json.dumps(captured, indent=2) + '\n')
    for row in audit.get("success_criteria_reviews", []):
        print(row["public_id"], row["title"])
        print(" | ".join(row["evidence_sentences"]))
    print("release preview", preview["count"], "audit", audit["summary"], "ballots", ballots["counts"])


if __name__ == '__main__':
    main()
