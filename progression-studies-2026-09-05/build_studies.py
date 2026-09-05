"""Freeze complete-careful-English studies before readers; no inference or governance writes."""
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()

def save(name, value):
    with (ROOT / name).open("x") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")

def choice(options, index):
    shift = index % len(options)
    return options[shift:] + options[:shift]

def calibration(prefix):
    rows = []
    for i, (a, b) in enumerate([("Davin", "Sela"), ("Orin", "Tova"), ("Mika", "Ruel"),
                               ("Anya", "Leif"), ("Imra", "Bryn"), ("Zora", "Huw"),
                               ("Fenn", "Nala"), ("Avra", "Tari")]):
        ref = f"{prefix.upper()}-{400 + i}"
        rows.append({"id": f"{prefix}-cal-{i}", "calibration": True,
            "english": f"The sealed bag {ref} is with either {a} or {b}.",
            "ainglish": f"The sealed bag {ref} is with {a}, not {b}.",
            "question": f"Who has the sealed bag {ref}?",
            "options": choice([a, b, "the information does not determine who", "neither person"], i), "answer": a})
    return rows

def regime():
    domains = [
        ("download replies", "valid JSON", "a reply that is not valid JSON"),
        ("submitted receipts", "signed", "an unsigned submitted receipt"),
        ("archive entries", "readable", "an unreadable archive entry"),
        ("export bundles", "encrypted", "an unencrypted export bundle"),
        ("payment notices", "dated", "an undated payment notice"),
        ("sample labels", "machine-readable", "a sample label that a machine cannot read"),
        ("delivery records", "uniquely numbered", "two delivery records with the same number"),
        ("inventory summaries", "free of duplicate lines", "an inventory summary with a duplicate line"),
    ]
    profiles = [
        "1: no; 2: the claim about the mechanism was false",
        "1: yes; 2: a responsible person owes a remedy or explanation",
        "1: yes; 2: a new observation, with no duty created by this claim",
        "1: yes; 2: the claim about the mechanism was false",
        "1: no; 2: a responsible person owes a remedy or explanation",
        "1: no; 2: a new observation, with no duty created by this claim",
    ]
    rows = []
    for i in range(64):
        subject, property_, exception = domains[i % len(domains)]
        scope = f"service region R{2100+i}"
        for j, form in enumerate(["by-construction", "by-rule", "in-practice"]):
            claim = f"In {scope}, {subject} are {property_}"
            english = {
                "by-construction": claim + ": how the system is built makes an exception impossible while the system remains unchanged.",
                "by-rule": f"A standing rule requires {subject} in {scope} to be {property_}; exceptions are possible and a responsible person owes repair or explanation for each violation.",
                "in-practice": f"Everything observed so far has shown {subject} in {scope} to be {property_}; nothing in this statement prevents or forbids an exception.",
            }[form]
            # Neither arm names a detected exception or supplies its observed consequence.
            question = (f"Take the statement literally, without assuming it is warranted. "
                f"1. Could there be {exception} in {scope} while the system remains unchanged? "
                f"2. If that is then observed in the same unchanged system, what follows under this statement? "
                "Choose the complete pair of answers.")
            rows.append({"id": f"regime-{j}-{i:02}", "english": english,
                "ainglish": claim + " " + form + ".", "question": question,
                "options": choice(profiles, j - ((i*3+j) % 6)), "answer": profiles[j],
                "settlement_stratum": form, "strata": {"form":form, "domain":i % 8}})
    return rows

def some():
    domains = [("tests", "failed"), ("replicas", "responded"), ("permission checks", "passed"),
               ("recipients", "replied"), ("alerts", "fired"), ("stock items", "sold"),
               ("guests", "arrived"), ("applications", "qualified")]
    options = ["1: yes; 2: yes", "1: yes; 2: no", "1: no; 2: yes", "1: no; 2: no"]
    rows = []
    for i in range(128):
        noun, predicate = domains[i % 8]
        n = [2, 4, 7, 12][(i // 8) % 4]
        scope = f"batch Q{5100+i}"
        context = f"The bounded set for {scope} consists of exactly {n} {noun}. "
        for j, form in enumerate(["some-or-all", "some-but-not-all"]):
            english = (f"At least one of those {noun} {predicate}, and every one may have {predicate}."
                       if j == 0 else f"At least one but fewer than all of those {noun} {predicate}.")
            lower_positive = (i // 4) % 2 == 0
            upper_positive = (i // 2) % 2 == 0
            lower = (f"An audit finds that 0 of those {noun} {predicate}. Does that contradict the statement?"
                     if lower_positive else f"Could an audit find that 0 of those {noun} {predicate} without contradicting the statement?")
            upper = (f"An audit finds that all {n} of those {noun} {predicate}. Is that compatible with the statement?"
                     if upper_positive else f"An audit finds that all {n} of those {noun} {predicate}. Does that contradict the statement?")
            answers = [lower_positive, (j == 0) if upper_positive else (j != 0)]
            questions = [lower, upper]
            if i % 2:
                answers.reverse(); questions.reverse()
            answer = f"1: {'yes' if answers[0] else 'no'}; 2: {'yes' if answers[1] else 'no'}"
            rows.append({"id":f"some-{j}-{i:03}", "english":context+english,
                "ainglish":context+f"{form} {noun} {predicate}.",
                "question":"1. "+questions[0]+" 2. "+questions[1]+" Choose the complete pair of answers.",
                "options":choice(options, options.index(answer) - ((i*2+j) % 4)), "answer":answer, "settlement_stratum":form,
                "strata":{"form":form,"domain":i%8,"population":n,"lower_first":not bool(i%2)}})
    return rows

if __name__ == "__main__":
    summary = {}
    for name, builder in [("regime", regime), ("some", some)]:
        rows = builder()
        pairs = {(r["english"],r["ainglish"]) for r in rows}
        assert len(pairs) == len(rows)
        assert all(r["answer"] in r["options"] and len(set(r["options"])) == len(r["options"]) for r in rows)
        data = rows + calibration(name)
        digest = hashlib.sha256(canonical(data)).hexdigest()
        save(name + ".items-v2.json", data)
        summary[name] = {"real_items":len(rows), "calibration_items":8,
            "settlement_strata":dict(Counter(r["settlement_stratum"] for r in rows)),
            "answer_positions":dict(Counter(r["options"].index(r["answer"]) for r in rows)),
            "items_sha256":digest, "reader_calls":0,
            "scope":"A new full-careful, joint-consequence original; not a replication of the older aggregate or terse-code study. Secondary/bare/robustness claims are not established by this primary panel."}
    save("primary-design-audit-v2.json", summary)
    print(json.dumps(summary, indent=2))
