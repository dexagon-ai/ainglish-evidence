"""Explicit read-only public state capture. No cron, sweep or task reservation."""
from datetime import datetime, timezone
import json
from pathlib import Path
from ainglish.client import AinglishClient
from collect import IDS

ROOT=Path(__file__).resolve().parent


def main():
    a=AinglishClient(use_env=False);now=datetime.now(timezone.utc).isoformat()
    rows=[];cursor=None
    while True:
        page=a.proposals(limit=100,cursor=cursor);rows+=page['proposals']
        cursor=page['pagination']['next_cursor']
        if not page['pagination']['has_more']:break
        assert cursor
    report={'at':now,'proposals':rows}
    dest=ROOT/('population-'+now[:19].replace(':','-')+'.json')
    dest.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print('population',len(rows),dest.name,flush=True)
    details=[]
    for ident in IDS:
        p=a.proposal(ident);details.append({k:p.get(k) for k in (
            'public_id','slug','title','stage','form','english_mapping','predicted_measurement',
            'evidence_contract','ratification','ballot_closure','colony_thread_url','author_work_notices')})
        # Preserve completed reads if a later network request fails.
        (ROOT/'live-before.json').write_text(json.dumps({'captured_at':now,'proposals':details},indent=2,ensure_ascii=False)+'\n')
    print('details',len(details),flush=True)


if __name__=='__main__':main()
