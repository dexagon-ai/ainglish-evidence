#!/usr/bin/env python3
"""Render the live gate matrix, semantic atlas, and handoff work orders."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    snapshot = json.loads((ROOT / "live-snapshot.json").read_text(encoding="utf-8"))
    candidates = json.loads((ROOT / "semantic-candidates.json").read_text(encoding="utf-8"))
    results = json.loads((ROOT / "semantic-results.json").read_text(encoding="utf-8"))
    by_id = {row["pair_id"]: row for row in results["results"]}
    lines = [
        "# Flagship pipeline control plane", "",
        f"Live snapshot: `{snapshot['suggestions_generated_at']}`. Snapshot digest: `{snapshot['content_sha256']}`.", "",
        "This is an execution gate, not a quality ranking. `carrier_ready` is the only state that authorizes a claim-carrier GPU run; no row currently has it.", "",
        "## Live gate matrix", "",
        "| Group | Proposal | Stage | Pipeline state | Next action |", "|---|---|---|---|---|",
    ]
    for row in snapshot["rows"]:
        lines.append(f"| {row['group']} | `{row['slug']}` | {row['stage']} | `{row['pipeline_state']}` | {row['next_action']} |")
    lines += [
        "", "## Concrete handoffs", "",
        "- **Saturnia — may positive:** amend the prerequisite from generic `token_delta` to the proposal's declared bounded `at_most 4` comparison, then independently settle the exact 120-item `+2.5` lineage. The frozen carrier still also requires two fresh qualified reader families.",
        "- **Saturnia — may-not:** its prose accepts `<=+2`, but its machine contract is generic `token_delta`; amend to a bounded prerequisite before token or reader spend.",
        "- **Reticuli — moved direction:** amend the generic prerequisite to the declared `at_most 2`; the confirmed `+1.5` result then becomes interpretable rather than opposing. Build the 100-item-per-form consequence carrier only after the new lifecycle is seconded.",
        "- **Reticuli — preference triad successor:** obtain two more independent seconds. The old lifecycle's `-1.3333` token result was explicitly not carried and must not satisfy the successor.",
        "- **Independent token measurers:** use fresh complete mappings for `must`, `should`, `will`, and `all-or-nothing`; do not start their reader carriers until each prerequisite settles.",
        "- **Maintainers — legacy rows:** `able-to / allowed-to`, `attempt / ensure`, and `in-parallel / in-sequence` need explicit evidence contracts. The in-parallel original also has legacy version-suffixed tokenizer identities that current writes reject and therefore cannot gain shared-member settlement without migration.",
        "- **Independent seconder:** `this-once / from-now-on` is at 2/3 and needs one more reasoned second before measurements.",
        "- **Biweekly adjudication:** do not add another original. Existing comprehension and token families are disputed, with material adverse and discordant rows; resolve the estimands or amend rather than averaging them into a flagship claim.",
        "", "## Targeted semantic consolidation", "",
        "Every row remains `review_required: true` and `asserted_relation: null`. Agreement routes attention; it does not create a register edge.", "",
        "| Review focus | Left | Right | Model result |", "|---|---|---|---|",
    ]
    for candidate in candidates["candidates"]:
        result = by_id[candidate["pair_id"]]
        label = result["agreed_label"] or "disagreement/error"
        lines.append(f"| {candidate['review_question']} | `{candidate['left']['slug']}` | `{candidate['right']['slug']}` | `{label}` |")
    lines += [
        "", "## Execution outcomes in this round", "",
        "- Preference triad old lifecycle: token original `a833ee7e...` filed at `-1.3333`, then superseded without evidence carry.",
        "- Evidential tags: fresh token replication `3e1b01c0...` filed at `-5.875`; strict tolerance says eligible disagreement, although the aggregate prerequisite is now supportive.",
        "- Proposal-by: attempt `9f7e47e2...` aborted at calibration (`0.125` gap versus `0.5`); zero scientific cells and no measurement.",
        "- In-parallel replication: not attempted because legacy versioned roster identity cannot be submitted under the current tokenizer identity contract.",
        "- May and moved claim carriers: not run because their prerequisite states are opposing, not sound.",
        "", "## Reproduce", "", "```bash", "python build.py", "ollama create dexagon-gemma3-12b-flagship-atlas:ctx4k -f Modelfile.gemma3-12b", "ollama create dexagon-mistral-small3.2-24b-flagship-atlas:ctx4k -f Modelfile.mistral-small3.2-24b", "python run_classifiers.py", "python summarize.py", "```", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
