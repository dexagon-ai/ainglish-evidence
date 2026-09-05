"""Public source recovery for a new prospective campaign; no inference or governance writes."""
from datetime import datetime, timezone
import json
from pathlib import Path
from local_colony_auth import ainglish_client, colony_client

ROOT=Path(__file__).resolve().parent
IDS={'mean':'a-4r2ytyygh560hxre','quantity':'a-k2d3rxn56qysr74n','choice':'a-g973ekza7973r5f2',
     'probability':'a-b46kna5nkdy1d1fq','instruction':'a-pfneg523cg48ny0c',
     'they':'a-6tp9dcwend2vx7yn','replace':'a-f34mb0zf8xp2pkwm','clock':'a-9zr8dzy0b5r5zcyp',
     'coverage':'a-c845tav0kqgzs0be','free':'a-yc4193gwc2e87zkn'}

def save(name,obj):
    with (ROOT/name).open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')

def main():
    c,forum=ainglish_client(),colony_client()
    save('selection.json',c.suggestions())
    for name,ident in IDS.items():
        history=c.proposal_slug_history(ident)
        p=c.proposal(history['current_slug'],authenticated=True)
        save(name+'.proposal.json',p)
        save(name+'.work.json',c.suggestions(proposal=ident))
        comments=forum.get_all_comments(p['colony_thread_url'].rsplit('/',1)[-1])
        save(name+'.comments.json',[{'id':r.get('id'),'parent_id':r.get('parent_id'),
            'author':r.get('author',{}).get('username'),'body':r.get('body'),'created_at':r.get('created_at')}
            for r in comments])
        print(name,p['stage'],p.get('form'),flush=True)
    save('snapshot-time.json',{'at':datetime.now(timezone.utc).isoformat(),'new_model_downloads':0,'reader_calls':0})

if __name__=='__main__':main()
