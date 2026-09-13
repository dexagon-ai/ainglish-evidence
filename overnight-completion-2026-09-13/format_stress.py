"""Frozen English-only answer-format diagnostic; not Ainglish proposal evidence.

One call per reader/control, no retries, no parser changes. Never imports an
Ainglish client or mints/submits an attempt. Run the freeze command and publish
the design before run. A started directory cannot be run again.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from ainglish import panel

ROOT = Path(__file__).resolve().parent / "format-stress"


def save(path, value, mode="w"):
    with path.open(mode) as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")


def design():
    controls = []
    for style in ["short", "compound", "punctuated", "long"]:
        for i in range(32):
            labels = ["red", "blue", "green", "unknown"]
            if style == "compound":
                labels = ["cedar: 3; violet: unknown", "cedar: unknown; violet: 3",
                          "cedar: 0; violet: 0", "cedar: 3; violet: 3"]
            elif style == "punctuated":
                labels = ['status = "ready" (revision 4)', 'status = "waiting" (revision 4)',
                          'status = "ready" (revision 5)', 'status = "unknown" (revision 5)']
            elif style == "long":
                labels = [f"The {color} folder contains the signed record; the other folders contain only unsigned copies."
                          for color in ["copper", "indigo", "silver", "violet"]]
            gold = labels[i % 4]
            controls.append({"id": f"format-{style}-{i:02d}", "style": style,
                "text": f"Record C{i + 700}: its complete stored value is [{gold}]. Copy the stored value exactly; the brackets delimit the value and are not part of it.",
                "question": "Which option is exactly the complete stored value?",
                "options": labels, "answer": gold})
    configs = []
    for short, model, digest in [
        ("gemma", "dexagon-gemma3-12b-pp-task:ctx4k", "de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f"),
        ("mistral", "dexagon-mistral-small3.2-24b-pp-task:ctx4k", "6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de"),
    ]:
        configs.append({"name": f"format-stress-{short}", "provider": "ollama", "model": model,
            "base_url": "http://127.0.0.1:11434/v1", "model_digest": "sha256:" + digest,
            "precision": "Q4_K_M-ollama0333-vulkan", "temperature": 0,
            "max_tokens": 512, "timeout_s": 120, "seed": 13, "top_p": 1.0})
    assert len(controls) == 128 and len({c['id'] for c in controls}) == 128
    assert all(c['answer'] in c['options'] and len(set(c['options'])) == 4 for c in controls)
    return {"kind": "dexagon.reader-format-stress.v1", "panel": configs, "controls": controls,
        "inference_calls_planned": 256, "ordering": "reader, then frozen control order",
        "analysis": "Count exact accepted options, exact gold, absent and off-option per reader and style. No inferential confidence or model selection. Format failures remain recorded; continue this diagnostic, but stop all further calls on transport exception or wall budget.",
        "wall_budget_seconds": 7200, "retries": 0,
        "boundary": "English-only copy-retrieval controls, not target items, qualification, comprehension evidence, replication or a revised scoring rule. No result can revive the aborted remain/departed attempt."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["freeze", "run"])
    args = parser.parse_args()
    ROOT.mkdir(exist_ok=True)
    path = ROOT / "design.json"
    if args.operation == "freeze":
        save(path, design(), "x")
        print(hashlib.sha256(path.read_bytes()).hexdigest())
        return
    data = json.loads(path.read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if data != design():
        raise SystemExit("Frozen design differs from the inspected source; do not run.")
    panel.prepare_reader_instruments(data)
    save(ROOT / "start.json", {"at": datetime.now(timezone.utc).isoformat(),
         "design_sha256": digest, "instruments": [panel.reader_receipt(r) for r in data['panel']]}, "x")
    started = time.monotonic()
    cells, stop = [], None
    try:
        for reader in data["panel"]:
            for c in data["controls"]:
                if time.monotonic() - started > data["wall_budget_seconds"]:
                    stop = "wall_budget_exhausted"
                    break
                record = {"reader": reader["name"], "control_id": c["id"], "style": c["style"]}
                try:
                    answer = panel.ask(reader, c['text'], c['question'], c['options'])
                    absent = panel.is_absent(answer)
                    normalized = str(answer).strip().casefold() if not absent else None
                    record.update(answer=str(answer), absent=absent,
                        accepted=normalized in [x.casefold() for x in c['options']],
                        correct=normalized == c['answer'].casefold())
                except Exception as exc:
                    record.update(error_type=type(exc).__name__, accepted=False, correct=False)
                    stop = "transport_or_harness_exception"
                cells.append(record)
                save(ROOT / "cells.json", cells)
                if len(cells) % 16 == 0:
                    print(json.dumps({"completed": len(cells), "reader": reader['name'],
                        "off_option_so_far": sum(not r.get('accepted', False) for r in cells)}), flush=True)
                if stop:
                    break
            if stop:
                break
    finally:
        summary = {}
        for r in cells:
            key = r['reader'] + '/' + r['style']
            acc = summary.setdefault(key, {"started": 0, "accepted": 0, "correct": 0, "absent": 0, "errors": 0})
            acc['started'] += 1
            for flag in ['accepted', 'correct', 'absent']:
                acc[flag] += int(r.get(flag, False))
            acc['errors'] += int('error_type' in r)
        save(ROOT / "result.json", {"finished_at": datetime.now(timezone.utc).isoformat(),
            "design_sha256": digest, "started": len(cells), "planned": 256,
            "stop": stop, "by_reader_and_style": summary, "usage": panel.usage_report(),
            "boundary": data['boundary']})
    print(json.dumps({"started": len(cells), "stop": stop, "summary": summary}), flush=True)


if __name__ == "__main__":
    main()
