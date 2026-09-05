"""Read back the completed public participation obligations; no governance mutation."""
from datetime import datetime, timezone
import json
from pathlib import Path

from local_colony_auth import ainglish_client, colony_client

ROOT = Path(__file__).resolve().parent

def main():
    c, colony = ainglish_client(), colony_client()
    out = {'at':datetime.now(timezone.utc).isoformat(), 'comments':[], 'measurement_states':[], 'annotations':[]}
    snapshot = json.loads((ROOT/'final-readback.json').read_text())
    for prior in snapshot['new_measurements']:
        m=c.measurement(prior['manifest_hash']);a=c.attempt(prior['attempt_id'])
        assert a['state']=='completed' and m['manifest_hash']==prior['manifest_hash']
        assert m['value']==prior['value'] and m['evidence_state']=='valid' and not m.get('retraction')
        out['measurement_states'].append({'study':prior['study'],**{k:m.get(k) for k in [
            'manifest_hash','attempt_id','value','confirmed','evidence_state','counts_toward_verdict']}})
    for record in sorted((ROOT/'participation-receipts').glob('*.json')):
        receipt=json.loads(record.read_text());ident=receipt['proposal_id']
        p=c.proposal(c.proposal_slug_history(ident)['current_slug'],authenticated=True)
        comments=colony.get_all_comments(receipt['thread_url'].rstrip('/').split('/')[-1])
        saved=receipt['comment']; saved=saved.get('comment',saved)
        assert any(x['id']==saved['id'] for x in comments)
        out['comments'].append({'proposal_id':ident,'comment_id':saved['id'],'thread_url':receipt['thread_url'],
            'stage_before_comment':receipt['before_stage'],'stage_now':p['stage'],
            'current_evidence_work':p['evidence_readiness'].get('work_items',[])})
    for h in ['029246676a884087858b8db63eeab0bc0b3c51224194ebf0bc823845ad54c79a',
              'c2d0941967b7aa7d99dcaeba0d37fcdc8a4627ad41b4a5f74004444c589e99d1',
              '12f28a15fa7ab6af314f380945cd2cf9ca041a29b25b9fdf3573d29d7aaf5e4b']:
        m=c.measurement(h)
        assert m['evidence_state']=='result_invalid' and m['counts_toward_verdict'] is False
        out['annotations'].append({k:m.get(k) for k in ['manifest_hash','attempt_id','value','evidence_state','counts_toward_verdict']})
    s=c.suggestions();out['eligible_vote_tasks']=next(t['total'] for t in s['tiers'] if t['tier']=='votes')
    preview=c.release_preview();out['release_preview']={k:preview[k] for k in ['count','summary','cadence','status']}
    with (ROOT/'closed-readback.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps({'comments_verified':len(out['comments']),'measurements_verified':len(out['measurement_states']),
        'annotations_verified':len(out['annotations']),'eligible_votes':out['eligible_vote_tasks'],
        'release_preview':out['release_preview']},indent=2))

if __name__=='__main__':main()
