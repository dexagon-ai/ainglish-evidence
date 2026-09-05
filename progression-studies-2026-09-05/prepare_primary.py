"""Bind reviewed fixed items to existing qualified readers. No inference or mutation."""
import hashlib
import json
from pathlib import Path
import sys
from ainglish import estimand
from ainglish.reader_qualification import attach
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent
SOURCES={'regime':'bf6a6e1c-f6c0-458d-bf8b-0cf33ef80b95','some':'245ed98c-7e94-4f3c-ba88-80982fc71f3a'}
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()

def main(commit):
    assert len(commit)==40 and all(c in '0123456789abcdef' for c in commit)
    qualified=ROOT.parent/'reader-qualification-local-v1-2026-09-04'
    readers,receipts=[],[]
    for key in ['mistral','gemma']:
        screen=json.loads((qualified/(key+'-screen.json')).read_text())
        qualification=json.loads((qualified/(key+'-qualification.json')).read_text())
        assert qualification['status']=='passed'
        readers.append(screen['reader']);receipts.append(qualification['receipt'])
    c=ainglish_client()
    for offset,name in enumerate(['regime','some'],1):
        data=json.loads((ROOT/(name+'.items-v2.json')).read_text())
        p=json.loads((ROOT/(name+'.proposal.json')).read_text())
        real=[x for x in data if not x.get('calibration')]
        strata=list(dict.fromkeys(x['settlement_stratum'] for x in real))
        description=('exact joint possibility/counterexample-consequence recovery on standing-property claims' if name=='regime'
                     else 'exact joint lower/upper quantifier-bound recovery on bounded populations with at least two members')
        spec={
            'construct':p['form'],'slug':p['slug'],'metric':'comprehension_accuracy_delta',
            'seed':2026090510+offset,'panel':readers,'panel_neff':2,
            'models':[x['roster_id'] for x in receipts],
            'planted_arm':'ainglish','calibration_min_gap':0.5,
            'comparator':{'kind':'complete-careful-english-v1','description':description+'; no bare English in primary'},
            'comparison_identity':{'comparator_genre':'complete-careful-English-v1','pair_rendering':description,
                'form_strata':strata,'reader_class':'two qualified cold local Q4 reader lineages; no definition exposure'},
            'settlement_strata':[{'id':x,'weight':1} for x in strata],
            'items_url':f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/{name}.items-v2.json',
            'items_sha256':hashlib.sha256(canonical(data)).hexdigest(),
            'estimand_contract':estimand.declaration_v2(
                population=description+'; the fixed eight-domain template population, not arbitrary natural-language messages',
                item_set_construction={'design':'prospective complete-careful primary v2','items':len(real),
                    'strata':strata,'weighting':'equal per form','gold':'joint consequence profile; exact whole-answer scoring',
                    'balance':'rotated opaque answer positions; some also balances question order and polarity'},
                reader_class='Two qualified stateless Q4 local lineages, Mistral Small 3.2 24B and Gemma 3 12B; exact digest/settings elsewhere in manifest',
                window='one fixed preregistered cold-reading study; no definition exposure, retraining, extensions or outcome-conditioned selection',
                selection_rules={'before_spend':'exact items, gold, sampler, target-independent controls frozen',
                    'calibration':'both readers pass planted gap at least 0.5 before real cells',
                    'faults':'zero transport, truncation, empty or off-option outcomes; abort with retained receipts, no retry',
                    'publication':'every finite direction filed; old adverse/null results retained'}),
            'training_asymmetry':'Current English-trained readers and current tokenizers have prior English exposure. This tests present cold readability, not performance after future Ainglish training.',
            'attempt':{'proposal_revision':p['slug'],
                'estimand':f'New full-careful original: {description}. {len(real)} items, two fixed readers, equal-weight form strata. Percentage-point accuracy difference Ainglish minus English. Not a replication of the linked earlier instrument. Primary NI interpretation uses -5 pp per form, not a new threshold replacing the proposal claim.',
                'admissibility_gates':[
                    'fresh live proposal remains active and token prerequisite satisfied; current missing comprehension and non-duplicate estimand justify this new original',
                    'all complete answer-bearing inputs publicly commit-pinned before reader calls; semantic gold checks pass',
                    'reader settings and digests match both unexpired qualification receipts',
                    'target-independent calibration first; each reader passes the fixed 0.5 planted effect gap',
                    'zero faults/truncations/empty/unparsed answers; any instrument failure means a retained typed abort, not another try',
                    'fixed sample and exact per-form results; every finite result filed once',
                    'bare, robustness, broader boundary and future-trained claims remain unmeasured by this primary; no automatic retirement of earlier evidence'],
                'planned_sample':{'scientific_items':len(real),'calibration_items':8,'readers':2,'real_cells':2*len(real),
                    'calibration_cells':32,'per_form_ni_margin_pp':-5,'source_commit':commit,
                    'limitations':'Template/domain repetition limits generalization. Item-bootstrap is conditional on these fixed frames/readers, not human validation or a population of all models.'}}
        }
        spec=c.legacy_repair_manifest(SOURCES[name],'comprehension_accuracy_delta',spec,author_path=False)
        spec=attach(spec,receipts)
        with (ROOT/(name+'.runspec.json')).open('x') as f:json.dump(spec,f,ensure_ascii=False,indent=2)
        print(name,spec['items_sha256'])

if __name__=='__main__':main(sys.argv[1])
