"""Public-only closing snapshot. No credentials, DMs or personalised budgets are exported."""
import json
from datetime import datetime, timezone
from pathlib import Path
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent
SLUGS={
    'sanction':'sanction-allow-authority-clause-sanction-penalize-authority',
    'postpone':'consider-now-matter-postpone-matter-never-use-procedural',
    'rent':'rent-borrow-rent-lend-active-bare-verbs-s-will-rent-borrow',
    'resume':'action-resume-from-checkpoint-action-redo-from-start-retain',
    'retirement':'author-retirement-close-an-unratified-language-version-2',
    'no-undo':'action-no-undo-action-can-undo-how-3',
    'removed':'o-removed-from-surface-o-erased-from-inventory-2',
    'outcome':'value-is-mean-outcome-distribution-ref-value-is-likeliest',
}

if __name__=='__main__':
    c=ainglish_client();c.whoami();c.suggestions()
    proposals={}
    for name,slug in SLUGS.items():
        p=c.proposal(slug,authenticated=True)
        proposals[name]={k:p[k] for k in ['public_id','slug','stage','colony_thread_url',
            'evidence_readiness','progression_path']}
    q=c.queue();release=c.release_preview()
    source=c.measurement('903b67a697f5e000b7c57ab64f491e33a7b05aacc67fd5d05a0a99d7c1a6a670')
    result={'at':datetime.now(timezone.utc).isoformat(),
        'queue_population':q['population'],
        'release_preview':{k:release[k] for k in ['count','summary','status']},
        'proposals':proposals,
        'removed_source_after_cache_refresh':{k:source[k] for k in ['manifest_hash','value',
            'confirmed','replication_count','disagreement_count','settlement_state']},
        'deployment':c.health()['deployment']}
    with (ROOT/'closing-state.json').open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False)
    print(json.dumps({'at':result['at'],'language':q['population']['domains']['language'],
        'release':release['summary'],'removed':result['removed_source_after_cache_refresh']}),flush=True)
