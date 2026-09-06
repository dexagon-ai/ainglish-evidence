"""Bounded public-record snapshot for the approved progression and overlap audit."""
from datetime import datetime, timezone
import json
from pathlib import Path
from local_colony_auth import ainglish_client, colony_client

ROOT=Path(__file__).resolve().parent


def save(name, value):
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as h:json.dump(value,h,indent=2,ensure_ascii=False);h.write('\n')


def main():
    c=ainglish_client();c.suggestions()
    all_rows=list(c.iter_proposals(page_size=200))
    selected=['a-g973ekza7973r5f2','a-k2d3rxn56qysr74n','a-hjhq14a5ew4khaqp','a-mxcehfr17mygjpsv','a-b46kna5nkdy1d1fq']
    for pid in selected:
        row=next(p for p in all_rows if p['public_id']==pid)
        live=c.proposal(row['slug'],authenticated=True)
        save('campaign/'+pid+'.proposal.json',live)
        save('campaign/'+pid+'.work.json',c.work_package(pid))
        thread=row['colony_thread_url'].rsplit('/',1)[-1]
        comments=colony_client().get_comments(thread)
        # Public thread only; no DM contents in this repository.
        save('campaign/'+pid+'.comments.json',comments)
        print(json.dumps({'id':pid,'stage':row['stage'],'keys':list(live)}))
    closest=['a-46cdjwgbh9aqxewy','a-t6rnsnyefex1sgch','a-h8gmd3gqjswzfnwn','a-f34mb0zf8xp2pkwm','a-wq8adyzheq50bw17']
    save('language-gap-scan.json',{'at':datetime.now(timezone.utc).isoformat(),'records_scanned':len(all_rows),'index':[{'id':r['public_id'],'slug':r['slug'],'stage':r['stage'],'form':r['form']} for r in all_rows], 'closest_records':[c.proposal(next(r['slug'] for r in all_rows if r['public_id']==pid)) for pid in closest]})


if __name__=='__main__':main()
