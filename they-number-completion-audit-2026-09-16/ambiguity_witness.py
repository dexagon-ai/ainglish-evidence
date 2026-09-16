"""Check contradictory semantic golds in the pinned bare-English task bank.

No model is called and no measured result is recomputed. Option order is explicitly
kept separate from semantic task identity.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / "longcat-linked-items.json").read_text())
pin = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode()).hexdigest()
assert pin == "8417e8bf936eb47ebf3c6d2869aa50da32bdc4ad80b6c3f9dde309157a926160"
semantic = defaultdict(list)
ordered = defaultdict(list)
for item in rows:
    if item.get("calibration"):
        continue
    semantic[(item["english"], item["question"], tuple(sorted(item["options"])))].append(item)
    ordered[(item["english"], item["question"], tuple(item["options"]))].append(item)
conflicts = [group for group in semantic.values() if len({i["answer"] for i in group}) > 1]
ordered_conflicts = [group for group in ordered.values() if len({i["answer"] for i in group}) > 1]
assert len(conflicts) == 96
assert sum(map(len, conflicts)) == 192
assert len(ordered_conflicts) == 0
out = {
    "kind": "they-number-ambiguity-witness.v1",
    "source_pin": pin,
    "real_items": 192,
    "unique_text_question_choice_set_tasks": len(semantic),
    "tasks_with_conflicting_gold_answers": len(conflicts),
    "affected_items": sum(map(len, conflicts)),
    "exact_ordered_prompt_conflicts": len(ordered_conflicts),
    "witness": [{
        "id": i["id"], "english": i["english"], "question": i["question"],
        "options": i["options"], "answer": i["answer"], "intended_number": i["number"],
    } for i in conflicts[0]],
    "interpretation": (
        "For every semantic bare task, two intended-number labels demand different answers "
        "without changing the English text, question or available answer meanings. Option "
        "order differs in every pair: this is not a claim of byte-identical full prompts, "
        "nor a score bound for models that exploit presentation cues. Position cannot make "
        "one of two distinct semantic consequences follow from the same ambiguous message. "
        "These rows measure intended-information recovery, not solely correct interpretation. "
        "Do not claim 192 independent semantic worlds."
    ),
}
(ROOT / "ambiguity-witness.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in out.items() if k not in {"witness", "interpretation"}}))
