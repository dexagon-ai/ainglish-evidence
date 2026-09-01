"""Frozen token-cost cells for cause-question / justification-question.

The eighty bounded occurrence references are crossed with both forms.  This keeps
the argument bytes identical across the relation split and yields the filing's
declared 160 form-balanced cells without using tokenizer output to select text.
"""

DOMAINS = {
    "incident": [f"incident-{i:02d}@evt-{100+i}" for i in range(1, 11)],
    "file": [f"file-change-{i:02d}@evt-{200+i}" for i in range(1, 11)],
    "deploy": [f"deploy-{i:02d}@evt-{300+i}" for i in range(1, 11)],
    "moderation": [f"moderation-{i:02d}@evt-{400+i}" for i in range(1, 11)],
    "payment": [f"payment-{i:02d}@evt-{500+i}" for i in range(1, 11)],
    "schedule": [f"schedule-{i:02d}@evt-{600+i}" for i in range(1, 11)],
    "access": [f"access-{i:02d}@evt-{700+i}" for i in range(1, 11)],
    "shutdown": [f"shutdown-{i:02d}@evt-{800+i}" for i in range(1, 11)],
}


def build_test_set():
    rows = []
    for domain, refs in DOMAINS.items():
        for ref in refs:
            rows.append({
                "item_id": f"{domain}-cause-{ref}",
                "domain": domain,
                "occurrence_ref": ref,
                "form": "cause-question",
                "english": (
                    f"What trigger, input, state transition, decision, fault, or other antecedent "
                    f"produced {ref}? This asks for its descriptive causal or process chain, not "
                    "whether it was permitted, desirable, reasonable, excusable, or justified."
                ),
                "ainglish": f"cause-question({ref})?",
            })
            rows.append({
                "item_id": f"{domain}-justification-{ref}",
                "domain": domain,
                "occurrence_ref": ref,
                "form": "justification-question",
                "english": (
                    f"What rule, authority, obligation, goal, value, or explicit trade-off, if any, "
                    f"made {ref} warranted? No valid justification or not an attributable choice "
                    "is a responsive answer. This asks for normative basis, not the mechanism that "
                    "produced it."
                ),
                "ainglish": f"justification-question({ref})?",
            })
    return rows


TEST_SET = build_test_set()

