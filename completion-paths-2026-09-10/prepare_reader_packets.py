"""Prepare held study materials without readers, tokenizers, qualifications or mints.

Reuse the immutable 041943d repair assets in this repository's Git history.
The files produced here are review packets, NOT executable panel manifests.
"""
import argparse
import copy
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from ainglish.experiment_audit import audit_items
from ainglish.panel import _validate_learnability_v2

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SLUGS = {
    'rent': 'rent-borrow-rent-lend-active-bare-verbs-s-will-rent-borrow',
    'resume': 'action-resume-from-checkpoint-action-redo-from-start-retain',
    'sanction': 'sanction-allow-authority-clause-sanction-penalize-authority',
}


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def prior(relative):
    return json.loads(subprocess.check_output(
        ['git','-C',str(REPO),'show','041943d:completion-followthrough-2026-09-09/'+relative],
        text=True))


def snapshot(c, name):
    p = c.proposal(SLUGS[name], authenticated=True)
    return {k: p[k] for k in ['public_id','slug','form','english_mapping',
                              'predicted_measurement','evidence_contract','colony_thread_url']}


def entry_for(p):
    text = 'Registered form: ' + p['form'] + '\n\n' + p['english_mapping']
    return {'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'source_url':'https://ainglish.org/api/v1/proposals/'+p['slug'],
            'proposal_revision':p['slug']}


def position_report(items):
    groups = defaultdict(list)
    for row in items:
        if row.get('calibration'): continue
        groups['all'].append(row)
        for key in ['form','domain','block','force']:
            if key in row.get('strata',{}): groups[key+'='+str(row['strata'][key])].append(row)
    result = {}
    for key, rows in groups.items():
        answers = Counter(r['answer'] for r in rows)
        positions = Counter(r['options'].index(r['answer']) for r in rows)
        result[key] = {'count':len(rows),'answer_counts':dict(answers),
                       'position_counts':dict(positions),
                       'constant_answer_baseline':max(answers.values())/len(rows),
                       'constant_position_baseline':max(positions.values())/len(rows)}
    return result


def learning(out, p, name, controls):
    if name == 'rent':
        items = prior('rent-v2/items.json')
        assert digest(items) == '5a0a30da1ae884a88c805a7cce52c2491f4590dc37c9206d7fa866a5981c3de4'
        real = [r for r in items if not r.get('calibration')]
        scope = ('64 unexposed supporting-learnability targets plus eight repaired controls. '
                 'Not the separate 96-item comprehension/cost matrix. Old calibration abort remains visible.')
        holds = ['Spark independent semantic review of the repaired controls',
                 'Do not treat this 64-item learning set as the separate 96-item CAD/cost set']
    else:
        real = prior('resume-v2/learning-items.json')
        assert digest(real) == '5a3317c7149ad9a046e1b91834ef6df91618b5512084e467818dec1ad498cecd'
        items = real + copy.deepcopy(controls)
        scope = ('64 core items plus 32 separately scored boundaries and eight generic controls. '
                 'Same scenarios as the unrun careful-English packet, not independent evidence from it.')
        holds = ['Excelsior semantic, canonical-comparator and boundary-scope review',
                 'Required comprehension prerequisite is unresolved; refresh eligible work before learning spend']
    calib = [r for r in items if r.get('calibration')]
    assert all(r['english'] == r['ainglish'] for r in real)
    entry = entry_for(p)
    partial = {'slug':p['slug'],'form':p['form'],'construct':p['form'],'entry':entry}
    assert _validate_learnability_v2(partial, real, calib)
    audit = audit_items(items)
    assert audit['ok'], audit
    plan = {
        'kind':'ainglish.prospective-review-packet.v1', 'state':'held_not_run',
        'not_an_executable_runspec':True, 'public_id':p['public_id'], 'slug':p['slug'],
        'metric':'learnability','entry':entry,'items_sha256':digest(items),
        'scope':scope, 'core_targets':len(real) if name=='rent' else 64,
        'boundary_targets':0 if name=='rent' else 32, 'controls':len(calib),
        'entry_binding_check':'SDK 0.2.59 structural v2 entry/arm/control checks passed only',
        'reader_instruments':[], 'reader_qualifications':[], 'scientific_attempt_id':None,
        'target_reader_calls':0, 'calibration_reader_calls':0,
        'exposure': {
            'cold':'Byte-identical marked text, no entry supplied; diagnostic arm',
            'entry_loaded':'Same marked text; only the official harness supplies the one exact entry snapshot',
            'state':'Fresh stateless session for each cell; no other targets, examples or answer keys in context',
            'not_claimed':['training the weights','changing a tokenizer','independent evidence from the paired comparator study']},
        'success_criteria': {
            'entry_accuracy_per_pole':0.90,
            'boundary_accuracy':0.90 if name=='resume' else None,
            'uncertainty':'Report intervals; do not make threshold-crossing point estimates conclusive',
            'reporting':'Every reader and pole separately; resume boundaries never pooled into the core score'},
        'remaining_holds':holds+[
            'Named original measurer and independent replicator must verify access to the exact same provider/model/digest/settings roster',
            'At least two distinct base-model lineages qualified on frozen target-independent controls before exposure',
            'Complete official runspec, seed, strata, call ledger, manifests and server preflight before mint',
            'Fresh proposal, source and full discussion review immediately before spending',
            'Safe local resources: unchanged Windows >=22 GiB start and <15 GiB stop, or independently verified remote capacity'],
        'not_evidence_of':'Human validation, ratification readiness, future training gain or current token savings',
    }
    base = out/(name+'-learning')
    for file,obj in [('proposal-snapshot.json',p),('items.json',items),('review-plan.json',plan),
                     ('offline-audit.json',audit),('positions.json',position_report(items))]:
        save(base/file,obj)


def sanction(out,p):
    """One narrower careful-English/force component; no scored ambiguous English arm."""
    items=[]; ledger=[]
    targets=[('person','Mira joining the field exercise'),
             ('company','Larch Ltd expanding the service'),
             ('transaction','the transfer of parcel ownership'),
             ('deployment','deployment of the audit service'),
             ('product','distribution of the Cedar instrument'),
             ('state','the territory operating the satellite link'),
             ('company','Nacre Ltd running the review desk'),
             ('person','Tarin participating in the restricted session')]
    states=['asserted-now','asserted-expired','quoted-not-endorsed','uncertain-or-denied']
    penalties=['a fixed fine','a temporary restriction','a suspension of one permit','a freeze on one account']
    for pi,pole in enumerate(['allow','penalize']):
        for si,state in enumerate(states):
            for k,(domain,target) in enumerate(targets):
                iid='S-'+hashlib.sha256(f'sanction-careful-20260910-{pi}-{si}-{k}'.encode()).hexdigest()[:10]
                authority='Board-'+hashlib.sha256((iid+'authority').encode()).hexdigest()[:6]
                context=(f'Fictional record {iid}. {authority} is the uniquely named issuing body for this record; '
                         'a separate body called North Desk has made no decision here. ')
                if k%2: context=(f'The target is {target}. '+context)
                if state=='asserted-expired':
                    context+='The recorded measure took effect last week and expired yesterday. The archive sorts historical formal acts, not present permissions. '
                else:
                    context+='The archive sorts reported formal acts, not execution, lawful authority or current permission. '
                allow_colour,pen_colour = (('Blue','Amber') if k%2==0 else ('Amber','Blue'))
                context+=(f'Its explicit routing rule sends a record asserting that {authority} formally permitted its target to the {allow_colour} tray, '
                          f'and a record asserting that {authority} formally imposed a penalty on its target to the {pen_colour} tray. '
                          'If neither formal act is asserted, neither tray is licensed. ')
                if pole=='allow':
                    marked=f'sanction-allow({authority}): {target}.'
                    english=(f'{authority} formally permitted {target}.' if k%2==0
                             else f'{target.capitalize()} was formally permitted by {authority}.')
                else:
                    penalty=penalties[k%len(penalties)]
                    marked=f'sanction-penalize({authority}): {target}, {penalty}.'
                    english=(f'{authority} formally imposed a penalty on {target}: {penalty}.' if k%2==0
                             else f'A penalty was formally imposed by {authority} on {target}: {penalty}.')
                asserted=state.startswith('asserted')
                if state=='quoted-not-endorsed':
                    marked='force-suspended The following is an unendorsed quotation, not this writer\'s assertion: “'+marked+'”'
                    english='The following is an unendorsed quotation, not this writer\'s assertion: “'+english+'”'
                elif state=='uncertain-or-denied':
                    if k%2:
                        marked='The writer denies the complete following claim: “'+marked+'”'
                        english='The writer denies the complete following claim: “'+english+'”'
                    else:
                        marked='The writer does not know whether the following claim is true: “'+marked+'”'
                        english='The writer does not know whether the following claim is true: “'+english+'”'
                gold=(allow_colour if pole=='allow' else pen_colour) if asserted else 'Neither tray is licensed'
                options=['Blue','Amber','Neither tray is licensed']
                # Position varies independently of label and form; the harness also remaps opaque codes.
                wanted=(k+si+pi)%3
                options.remove(gold); options.insert(wanted,gold)
                items.append({'id':iid,'english':context+english,'ainglish':context+marked,
                    'question':'Which archive tray does this writer\'s asserted record license under the stated routing rule?',
                    'options':options,'answer':gold,
                    'strata':{'form':pole,'domain':domain,'force':state,'block':'careful-english-component'},
                    'settlement_stratum':pole})
                ledger.append({'id':iid,'asserted_formal_act':asserted,'polarity':pole,
                               'allow_tray':allow_colour,'penalty_tray':pen_colour,'gold':gold})
    assert len(items)==64
    assert Counter(r['strata']['form'] for r in items)=={'allow':32,'penalize':32}
    audit=audit_items(items,require_balanced=True)
    assert audit['ok'],audit
    # Answer-bearing text/golds are frozen for review, not sent to readers.
    base=out/'sanction-careful'
    plan={'kind':'ainglish.prospective-review-packet.v1','state':'held_not_run',
          'not_an_executable_runspec':True,'metric':'comprehension_accuracy_delta',
          'public_id':p['public_id'],'slug':p['slug'],'items_sha256':digest(items),
          'targets':64,'forms':{'allow':32,'penalize':32},
          'threshold':'Marked non-inferior to complete careful English within 5 percentage points, separately by form',
          'scope':'One prospective careful-English and assertion-force component with held-out routing consequences. Not the complete declared evidence programme.',
          'remaining_components':['Bare-sanction ambiguity/intent recovery needs its own explicit estimand; do not score a truthful unknown as misunderstanding',
               'Practical authorized/penalized competitor comparison',
               'Noise, summary and translation robustness',
               'Real-use fidelity and eventual adoption',
               'Separate validity and scope-overreading tests beyond this archive task'],
          'remaining_holds':['Independent semantic review of the full answer-bearing packet',
               'Decide whether routing adds too much task complexity; review against the simple stated claim',
               'Frozen target-independent calibration, seed, named qualified readers and independently accessible roster',
               'Official complete runspec/preflight and safe resources before mint'],
          'reader_instruments':[],'reader_qualifications':[],'scientific_attempt_id':None,
          'target_reader_calls':0,'calibration_reader_calls':0}
    for file,obj in [('proposal-snapshot.json',p),('items.json',items),('gold-ledger.json',ledger),
                     ('offline-audit.json',audit),('positions.json',position_report(items)),
                     ('review-plan.json',plan)]:save(base/file,obj)


def main(out, snapshots=None):
    if snapshots is None:
        from local_colony_auth import ainglish_client
        c=ainglish_client(); c.whoami(); c.suggestions()
        snapshots={name:snapshot(c,name) for name in SLUGS}
    rent_items=prior('rent-v2/items.json')
    controls=[r for r in rent_items if r.get('calibration')]
    for name in ['rent','resume']:learning(out,snapshots[name],name,controls)
    sanction(out,snapshots['sanction'])
    print('Prepared three held review packets; zero model/tokenizer calls, no attempts',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=ROOT/'reader-packets')
    parser.add_argument('--from-snapshots',type=Path,help='Reproduce from this packet tree without refreshing live content')
    args=parser.parse_args()
    snaps=None if args.from_snapshots is None else {
        name:json.loads((args.from_snapshots/(name+'-careful' if name=='sanction' else name+'-learning')/'proposal-snapshot.json').read_text()) for name in SLUGS}
    main(args.out,snaps)
