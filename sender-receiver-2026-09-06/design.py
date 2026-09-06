"""Prospective free-form sender/receiver task; every communication token is counted."""
from itertools import product
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ['include_recipient', 'finish_deadline', 'collective', 'both_allowed', 'old_A_active']
COMMON = ('You are planning a safe simulation, not executing actions. The sender addresses Mira; '
          'the named team is Noor, Ivo and Mira. There is one named check per episode. The clock '
          'deadline is today at 18:00 UTC; the same-day date and UTC are known to everyone. '
          'Existing authorized, uncompleted instructions A and B are uniquely named and active. '
          'The sender is authorized to issue C and change A. No action has started. '
          'Evaluate the active instructions once C is accepted at the authoritative instruction-ledger '
          'commit event. All requested checks are compatible. Option red and option blue are equally '
          'available. No other constraints apply.')
GUIDES = {
 'ainglish': ('Use these five ratified families when relevant, preserving all referents: '
    'we-including-you includes the addressee; we-excluding-you excludes the addressee. '
    'start-by(t) bounds the start; complete-by(t) bounds successful completion, not mere termination. '
    'as-one is one collective named act; each-alone is one named act per member. '
    'In "red or blue, or-both", either option or both are permitted; "red or blue, not-both" requires exactly one. '
    '"C: supplements(A): <new action>" keeps A and adds C; "C: supersedes(A): <new action>" replaces A with C at that commit event. '
    'Both update forms leave separately named B unchanged. No form grants authority.'),
 'english': ('Use explicit ordinary English, preserving all referents: say whether the team '
    'includes the addressee or excludes the addressee. Say whether the action must start '
    'by the deadline or successfully finish by it; mere termination is not successful completion. '
    'Say whether the group performs one collective named act or each member performs their own '
    'named act. Say whether either option or both are allowed, or exactly one is required. '
    'Say whether C is added while A remains active, or C replaces A. '
    'Both update choices leave separately named B unchanged. No wording grants authority.')}
SENDER_SYSTEM = ('Write a short operational instruction in prose, not JSON, a checklist of booleans, '
    'or an answer key. Communicate all five choices precisely. Do not execute anything. '
    'Do not include analysis or mention this benchmark. Use only the language requested.')
RECEIVER_SYSTEM = ('Interpret the sender instruction as a proposed plan, not authority to execute. '
    'Reply with exactly one JSON object, no markdown or explanation. It must have exactly these '
    'five fields, each a JSON boolean or null if the sender did not determine it: '
    'include_recipient (is Mira in the acting team), finish_deadline (deadline bounds successful '
    'completion rather than start), collective (one collective check rather than one per member), '
    'both_allowed (may both red and blue be used), old_A_active (does A remain after C). '
    'Never fill an unspecified choice from probability or common practice.')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def build():
    cases=[]
    for i, bits in enumerate(product([False, True], repeat=5)):
        brief=dict(zip(FIELDS,bits))
        cases.append({'id':f'episode-{i:02d}', 'brief':brief, 'common':COMMON,
            'semantic_brief': {
                'acting_team': ['Noor','Ivo','Mira'] if brief['include_recipient'] else ['Noor','Ivo'],
                'deadline_event': 'successful completion' if brief['finish_deadline'] else 'start',
                'number_of_checks': 1 if brief['collective'] else (3 if brief['include_recipient'] else 2),
                'permitted_choices': ['red','blue','red and blue'] if brief['both_allowed'] else ['red','blue'],
                'active_instructions_after_C': ['A','B','C'] if brief['old_A_active'] else ['B','C']}})
    save(ROOT/'cases.json',cases)
    source=json.loads((ROOT.parent/'learning-transfer-2026-09-06/source-constructs.json').read_text())
    source['entries']={k:v for k,v in source['entries'].items() if k in ['participants','deadline','multiplicity','alternatives','update']}
    save(ROOT/'source-constructs.json',source)
    plan={'kind':'ainglish.sender-receiver-prose.v1','date':'2026-09-06','governance_evidence':False,
        'conditions':['base','ainglish-17','english-17'],'arms':['ainglish','english'],
        'seeds_selection':'Training seed17 selected prospectively, never the best holdout seed.',
        'episodes_per_condition_arm':32,'stages':['sender','receiver','clarification','receiver-final'],
        'design':'Full 2^5 factorial, one synthetic operational context.32 combinations are not32 independently authored reasoning templates. Both arms receive an explicit matched meaning guide. No cold-reader claim.',
        'clarification':'Every episode gets exactly one clarification opportunity, regardless of first-pass correctness. Sender sees the receiver interpretation, but no oracle score or corrective gold beyond its original brief.',
        'primary':'Exact five-field first-pass and final plan accuracy; all five marginal accuracies; malformed/truncated receiver results wrong; first-pass-to-final changes retained. Separately report format-adherent success requiring complete non-JSON prose from the sender and clarification; do not hide sender noncompliance behind a correct plan.',
        'costs':'Sum actual tokenizer input/output counts across all four calls, including both guides, instructions and clarification; report guide-only token counts separately but do not subtract them from total cost. These are logical per-request tokens, not cache-billing or wall-clock charges.',
        'limits':['One base model, one preselected training seed, single-author synthetic instructions.',
                  'Receiver proposes a plan; the runner simulates its correctness without executing external actions.',
                  'Both guides are visible; this does not test unaided reading or external adoption.',
                  'Tokenizers are fixed; learned weights cannot change segmentation.'],
        'qualification':{'control_items':8,'minimum_correct':7,'invalid_allowed':0,'target_dependent':False},
        'max_tokens':{'sender':192,'clarification':192,'receiver':128,'receiver-final':128},
        'max_prompt_tokens':2048,'target_retries':0,'physical_gpu':0,'downloads':0,
        'adapter_seal':'aae532c','source_release':'ainglish-core-v3',
        'source_public_ids':['a-bwfjwj7fe6zp3wda','a-kajnp96t7eq33704','a-4m4fsz9pd71m5w6b','a-vw5486vepv0dvay2'],
        'additional_update_source':'See source-constructs.json in the pinned learning-transfer corpus for the supplements/supersedes ratified entry.'}
    save(ROOT/'PLAN.json',plan)
    files=['design.py','run.py','analyse.py','test_design.py','cases.json','PLAN.json','source-constructs.json']
    save(ROOT/'FROZEN.json',{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files})


if __name__=='__main__':build()
