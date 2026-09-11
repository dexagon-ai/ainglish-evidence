"""Offline admission/packet checks. No inferred author approval or target spend."""
from collections import Counter
import argparse,copy,hashlib,json,re,subprocess
from pathlib import Path
from ainglish.experiment_audit import audit_items

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
REF='1c4a58a'
MAY='completion-followthrough-2026-09-08/may-not-review/'
STOCK='integrity-and-progression-2026-09-08/stock-flow/'

def prior(path):
    return json.loads(subprocess.check_output(['git','-C',str(REPO),'show',REF+':'+path],text=True))
def digest(v):
    return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(path,v):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2)


def admission(decisions,mapping,*,author_count_unit=None,prior_answer_exposure=None):
    if author_count_unit!='contextual_primary_rows':
        raise ValueError('Author must resolve the counting unit; never substitute rows for independent clauses')
    if prior_answer_exposure is not False:
        raise ValueError('Do not call exposed or undisclosed review blinded')
    ids=[r['review_id'] for r in decisions]
    if len(ids)!=len(set(ids)) or set(ids)!=set(mapping):
        raise ValueError('The frozen review must address each distinct bare clause exactly once')
    admitted=[];excluded=[]
    for row in decisions:
        fields=['binding_prohibition_is_a_plausible_reading','epistemic_nonoccurrence_is_a_plausible_reading']
        if any(type(row.get(k)) is not bool for k in fields) or not str(row.get('reason_or_lexical_prior_concern') or '').strip():
            raise ValueError('Every clause needs two explicit judgements and a reason')
        (admitted if all(row[k] for k in fields) else excluded).extend(mapping[row['review_id']])
    if len(set(admitted+excluded)) != len(admitted+excluded):
        raise ValueError('One contextual row was counted more than once')
    return {'admitted_primary_rows':len(admitted),'excluded_primary_rows':len(excluded),
        'minimum_128_rows_met':len(admitted)>=128,'admitted_ids':sorted(admitted),
        'independent_bare_clauses':sum(all(row[k] for k in fields) for row in decisions),
        'gate_status':'Conditional arithmetic only: independently verify the author receipt and review chronology',
        'remaining':'Contextual unique-gold review, all other prediction checks, qualification and preregistration'}


def improve_stock_grammar(items):
    """Pre-exposure repair of ordinary noun/verb agreement, no marker inflection."""
    singular={'workers':'worker','visitors':'visitor','responders':'responder','jobs':'job',
              'packages':'package','replicas':'replica','subscriptions':'subscription','sensors':'sensor'}
    out=copy.deepcopy(items);changes=[]
    for row in out:
        if row.get('calibration'):continue
        for arm in ['english','ainglish']:
            old=row[arm];new=old
            for plural,one in singular.items():
                new=re.sub(r'(?i)(exactly 1 (?:distinct )?)'+plural+r'\b',r'\g<1>'+one,new)
                new=re.sub(r'(?i)(exactly 1 distinct '+one+r') are\b',r'\g<1> is',new)
            if new!=old:row[arm]=new;changes.append({'id':row['id'],'arm':arm,'before':old,'after':new})
    return out,changes


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    out=args.out
    blind=prior(MAY+'blind-clauses.json');mapping=prior(MAY+'unblinded-item-map.json')
    primary=[r for r in prior('completion-campaign-2026-09-08/may-not-draft/careful.items.json') if r.get('probe')=='two-bit']
    secondary=prior(MAY+'careful.balanced-probes.json')
    assert len(primary)==160 and len(secondary)==1280 and len(blind)==20
    assert set(sum(mapping.values(),[]))=={r['id'] for r in primary}
    save(out/'may-not-blind-review.json',blind)
    save(out/'may-not-admission-plan.json',{'state':'awaiting_author_decision_not_run','measurement':False,
        'blind_input_sha256':digest(blind),'primary_items_sha256':digest(primary),
        'secondary_items_sha256':digest(secondary),'distinct_bare_clauses':20,'primary_rows':160,
        'secondary_rows':1280,'old_unbalanced_secondary_rows_excluded':True,
        'author_decision_required':['Both-readings-live assessed before disambiguating context, unique gold checked afterwards?',
            'Does 128 mean contextual primary rows or independent clause/scenario units? Twenty clauses are not 160 independent sentences.'],
        'qualified_readers':[],'attempt_id':None,'target_calls':0,
        'do_not_pool':['primary two-bit recovery','false inference rates','positive sensitivity'],
        'no_blinding_claim':'The builder already knows the gold; needs an unexposed reviewer and frozen decisions before unblinding.'})
    original=prior(STOCK+'items.json');items,changes=improve_stock_grammar(original)
    audit=audit_items(items);assert audit['ok'],audit
    save(out/'stock-flow-items-v2.json',items)
    save(out/'stock-flow-grammar-changes.json',changes)
    save(out/'stock-flow-audit.json',audit)
    save(out/'stock-flow-plan.json',{'state':'held_semantic_review_and_integrity_decision','measurement':False,
        'source_items_sha256':digest(original),'items_sha256':digest(items),'worlds_sha256':digest(prior(STOCK+'worlds.json')),
        'target_items':512,'worlds':128,'controls':12,'form_domain_strata':16,'changed_arm_texts':len(changes),
        'unchanged':['All worlds, gold answers, options, questions, marker forms, count semantics and controls'],
        'component_only':'Careful-English comparison, not the full bare-left gain, robustness or human-comprehension claim',
        'token_state':'Existing +2 original/confirmation remains server-valid. Copied nested items hash awaits public author/integrity resolution; not silently declared a failed API gate.',
        'reviewed_example':'Exactly 1 distinct workers are inside S -> Exactly 1 distinct worker is inside S',
        'qualified_readers':[],'attempt_id':None,'target_calls':0,
        'holds':['Author/integrity decision about the retained cost metadata',
            'Review the v2 texts, boundary probes and meaning, including grammatical N=1 operator use',
            'An actually available eligible original/replication roster and fresh qualifications',
            'New immutable items pin, official runspec/preflight, mint before any reader call']})
    print(json.dumps({'may_not_primary':160,'may_not_secondary':1280,'stock_targets':512,'stock_grammar_arm_edits':len(changes),'reader_calls':0}))

if __name__=='__main__':main()
