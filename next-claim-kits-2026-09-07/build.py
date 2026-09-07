"""Unspent answer-bearing claim kits with explicit finite-world entailment keys.

No tokenizer is loaded and no model or governance endpoint is called here.
"""
from itertools import product
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
STATES = ['yes', 'no', 'not determined']
VECTORS = list(product(STATES, repeat=2))
REGENERATE = '--regenerate-unpublished' in sys.argv

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w' if REGENERATE else 'x') as out:
        json.dump(value, out, ensure_ascii=False, indent=2); out.write('\n')

def entail(worlds, index):
    values = {w[index] for w in worlds}
    assert values
    return 'yes' if values == {True} else 'no' if values == {False} else 'not determined'

def options(gold, ordinal):
    vectors = VECTORS[ordinal % 9:] + VECTORS[:ordinal % 9]
    meanings = {chr(65+i): list(v) for i,v in enumerate(vectors)}
    answer = next(k for k,v in meanings.items() if v == gold)
    prose = ' '.join(f'{k}=first {v[0]}, second {v[1]}.' for k,v in meanings.items())
    return list(meanings), meanings, answer, prose

def replied():
    source = ROOT.parent / 'overnight-progression-2026-09-06/replied-token'
    cells = json.loads((source/'cells.json').read_text())
    token_pairs = json.loads((source/'prepared.json').read_text())['manifest']['test_set']
    items, audit = [], []
    for n, (c, pair) in enumerate(zip(cells, token_pairs)):
        # World axes: a responsive answer exists somewhere, it expresses no,
        # and a responsive answer was observed in the named email/cutoff record.
        # Observed answers must exist. A negative answer must exist. Delivery
        # receipts alone add no answer; the hidden scenario cannot constrain gold.
        worlds = [w for w in product([False,True],repeat=3) if (not w[1] or w[0]) and (not w[2] or w[0])]
        if c['form'] == 'replied-no':
            worlds = [w for w in worlds if w[0] and w[1]]
        else:
            worlds = [w for w in worlds if not w[2]]
        gold = [entail(worlds,0),entail(worlds,1)]
        opts, meaning, answer, prose = options(gold,n)
        arms = {lang:c['shared_context']+c[lang+'_claim'] for lang in ['english','ainglish']}
        assert all(arms[lang] == pair[lang] for lang in arms), 'Never change the already-frozen token arms'
        question = ('First: does an attributable answer to the exact named request exist in any channel? '
            'Second: has an attributable answer expressed a negative stance toward that exact request? '
            'A fact not established either way is not determined, rather than no. '+prose)
        items.append({'id':c['id'],**arms,'question':question,'options':opts,'answer':answer,
            'settlement_stratum':c['form'],'strata':{'domain':c['domain'],'latent_scenario':c['scenario'],'delivery_known':int(c['delivery_known'])}})
        audit.append({'id':c['id'],'form':c['form'],'visible_gold':gold,'choice_meanings':meaning,
            'compatible_worlds':worlds,'hidden_world_used_for_gold':False,
            'hidden_scenario_note':c['hidden_world_for_later_gold_review']})
    assert len(items)==256 and len({(r['english'],r['ainglish']) for r in items})==256
    assert all(r['visible_gold']==(['yes','yes'] if r['form']=='replied-no' else ['not determined','not determined']) for r in audit)
    save(ROOT/'replied/items.json',items);save(ROOT/'replied/gold-audit.json',audit)
    save(ROOT/'replied/PLAN.json',{'kind':'ainglish.replied-visible-facts-kit.v1','source_cells_sha256':sha(source/'cells.json'),
        'source_prepared_sha256':sha(source/'prepared.json'),'semantic_cells':256,
        'primary':'Exact two-axis recovery of what the visible record establishes about global responsive answer existence and its negative stance, equally weighted between the two forms.',
        'token_bridge':'Every English/Ainglish arm byte-matches the corresponding previously frozen 256-pair token packet. No tokenizer or reader calls have been made on this kit.',
        'gate':'Do not run until the exact token packet has been preregistered, executed, independently assessed and the live declared prerequisite is satisfied; then freeze exact reader/settings/qualification/calibration and SDK preflight/mint before any target call.',
        'limitations':['A focused scoped-entailment kit, not the whole predicted comprehension study.',
            'The old eight scenario labels contain hidden facts that are NOT visible to readers. This kit does not pretend to test reasoning about an unshown later answer, other channel, qualified reply or current revision.',
            'Under visible scoped absence, global response and global refusal are UNKNOWN, not false. Under an attributable exact-request no, both are established.',
            'Policies are present identically but policy-routing accuracy is not scored. No bare-status gain, future permanence, edit robustness or delivery understanding is established.',
            'Two gold classes and sixteen domains with identifier variants are not256 independent hard-negative templates. Do not infer broad efficacy from a ceiling here.'],
        'next_full_claim_design':'A new prospectively frozen full-world kit must put relevant timing/channel/revision facts into BOTH arms, use the corresponding complete token-cost cells, and keep bare ambiguity scored by semantic compatibility rather than an invisible author intention.'})

DOMAINS = [
    ('library-books','ISBN-edition','binding-colour'),('physical-copies','printed-content','owner'),
    ('files-and-paths','content-checksum','file-mode'),('data-records','name-and-address','row-owner'),
    ('accounts','account-balance','account-holder'),('configurations','declared-config-fields','comment'),
    ('model-artifacts','model-digest','file-location'),('running-workers','image-digest','process-id'),
    ('devices','firmware-version','serial-number'),('measured-quantities','measured-length','material'),
    ('versioned-documents','document-content','storage-location'),('image-assets','pixel-checksum','licence-tag'),
    ('tickets','route-and-fare','ticket-number'),('inventory','part-specification','stock-tag'),
    ('certificates','public-key','certificate-serial'),('datasets','record-checksum','custodian'),
]

def instance():
    items, tokens, audit = [], [], []
    ordinal = 0
    for domain,key,other_key in DOMAINS:
        for form in ['same-instance-as','value-equal-to']:
            for scenario in range(4):
                for similar_names in [False,True]:
                    x=f'X{ordinal:03d}';y=('X' if similar_names else 'Y')+f'{ordinal+1:03d}'
                    epoch='2026-09-07T12:00Z';past='2026-09-06T12:00Z'
                    # Boolean world axes: references co-refer, K values equal,
                    # unmentioned J values equal, X.K unchanged from prior snapshot.
                    worlds=[w for w in product([False,True],repeat=4) if not w[0] or (w[1] and w[2])]
                    worlds=[w for w in worlds if w[0 if form=='same-instance-as' else 1]]
                    context=(f'Domain {domain}. At {epoch}, {x} and {y} are resolved references in one identity system. '
                        f'The keys {key} and {other_key} resolve to deterministic record projections at that instant; no historical invariance of either projection is assumed. '
                        f'Lettering is not identity evidence. An earlier snapshot is at {past}. ')
                    if scenario==1:
                        context+=f'The recorded {key} value of {x} differs from its earlier snapshot. '
                        worlds=[w for w in worlds if not w[3]]
                    elif scenario==2:
                        if form=='same-instance-as':
                            context+=f'The recorded {key} value of {x} equals its earlier snapshot value. '
                            worlds=[w for w in worlds if w[3]]
                        else:
                            context+=f'The identity ledger resolves {x} and {y} to different individuals. '
                            worlds=[w for w in worlds if not w[0]]
                    elif scenario==3:
                        if form=='same-instance-as':
                            context+='No future reference binding or future property value is specified. '
                        else:
                            context+=f'The recorded {other_key} values of {x} and {y} differ at that instant. '
                            worlds=[w for w in worlds if not w[2]]
                    assert worlds, 'Do not create a contradictory marker/context pair'
                    if form=='same-instance-as':
                        a=f'{x} same-instance-as({y}) as_of({epoch}).'
                        e=f'{x} and {y} denote the same individual at {epoch}.'
                    else:
                        a=f'{x} value-equal-to({y}, by={key}) as_of({epoch}).'
                        e=f'{x} and {y} have equal {key} values at {epoch}.'
                    gold=[entail(worlds,0),entail(worlds,3)]
                    opts,meanings,answer,prose=options(gold,ordinal)
                    question=(f'First: do {x} and {y} designate just one individual at the stated comparison instant? '
                        f'Second: has the {key} value of {x} stayed unchanged from the earlier snapshot to that instant? '
                        'Use only what the record establishes; unsupported alternatives remain not determined. '+prose)
                    ident=f'{domain}/{form}/{scenario}/{int(similar_names)}'
                    items.append({'id':ident,'english':context+e,'ainglish':context+a,'question':question,
                        'options':opts,'answer':answer,'settlement_stratum':form,
                        'strata':{'domain':domain,'key':key,'scenario':scenario,'similar_reference_names':int(similar_names)}})
                    # The prerequisite explicitly compares complete marked claims
                    # with the same two references and key; shared context is held
                    # outside this declared claim-span count in BOTH arms.
                    tokens.append({'id':ident,'english':e,'ainglish':a,'stratum':form})
                    audit.append({'id':ident,'visible_gold':gold,'choice_meanings':meanings,'compatible_worlds':worlds,
                        'asserted_relation':form,'key':key,'other_key':other_key,
                        'complete_claim_arms':{'english':e,'ainglish':a},'shared_context':context})
                    ordinal+=1
    assert len(items)==len(tokens)==256 and len({(r['english'],r['ainglish']) for r in tokens})==256
    for item,row in zip(items,audit):
        assert all(item[arm]==row['shared_context']+row['complete_claim_arms'][arm] for arm in ['english','ainglish'])
        assert row['compatible_worlds']
    save(ROOT/'instance/items.json',items);save(ROOT/'instance/token-pairs.json',tokens);save(ROOT/'instance/gold-audit.json',audit)
    save(ROOT/'instance/PLAN.json',{'kind':'ainglish.instance-history-joint-kit.v1','semantic_cells':256,
        'domains':16,'forms':2,'scenarios_per_form':4,'reference_name_patterns':2,
        'primary':'Joint current co-reference and same-key historical stability recovery versus complete careful English; equal form weights. Same semantic cases underlie the separate claim-span token prerequisite.',
        'gold':'Enumerate all finite Boolean worlds consistent with current identity implying equality of deterministic current properties; value equality alone imposes no identity constraint. History is independent unless explicitly stated. Infer yes/no only when every remaining world agrees.',
        'token_comparator':'Complete marked claim and shortest adequate careful-English claim; identical resolved X/Y, named key for equality and comparison epoch. Shared vignette context and the consequence question are excluded from BOTH claim-span counts, explicitly; this is not a whole-prompt efficiency estimate.',
        'gate':'Before encoding: exact prepared SDK token manifest, live bounded capacity, source/mapping freshness, preregistration and server recount. Before any comprehension: token prerequisite satisfied and exact panel/settings/neutral qualification/calibration/manifest publicly frozen and preregistered.',
        'limits':['This focused joint identity/history test does not complete all192-vignette action-routing, bare-same gain or corruption predictions.',
            'A current identity claim is not proof of historical immutability. Named equal values do not prove a shared identity; different other-key values disprove it under the declared deterministic identity system.',
            'Scope is only at the stated instant. No persistent synchronization, future bindings, actual mutation execution or authority is inferred.',
            'All keys resolve here. Missing/unresolved/nonunique identity keys require a separate invalid-input clarification study, not silently manufactured valid relations.',
            'Sixteen domain frames and controlled variants are not256 independently authored contexts. Model and token counts remain unspent.']})

def main():
    if REGENERATE:
        assert not subprocess.check_output(['git','ls-files','--',ROOT.name],cwd=ROOT.parent), 'Never regenerate a published or tracked kit'
        assert not (ROOT/'execution').exists(), 'Never regenerate an executed kit'
    replied();instance()
    paths=[p for p in ROOT.rglob('*') if p.is_file() and p.name!='FROZEN.json' and p.suffix in ['.py','.json','.md']]
    save(ROOT/'FROZEN.json',{str(p.relative_to(ROOT)):sha(p) for p in paths})
    print('Prepared two256-cell unspent focused kits; finite-world gold and exact token/comprehension bridges audited.')

if __name__=='__main__': main()
