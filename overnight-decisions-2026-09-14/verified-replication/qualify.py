"""Run each frozen exact source configuration on neutral controls once, never targets."""
import json,sys
from pathlib import Path
from ainglish.reader_qualification import run_screen,_canonical
import hashlib,urllib.request
from build import ROOT,write
pin=sys.argv[1]
for label in ['gemma','mistral']:
 result=ROOT/(label+'.qualification.json')
 flag=ROOT/(label+'.execution-started.json')
 if result.exists() or flag.exists():raise SystemExit('Already started; inspect existing qualification, no rerun.')
 raw=urllib.request.urlopen(f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{pin}/overnight-decisions-2026-09-14/verified-replication/{label}.screen.json',timeout=30).read()
 screen=json.loads(raw);assert screen==json.loads((ROOT/(label+'.screen.json')).read_text())
 write(label+'.execution-started.json',{'screen_file_sha256':hashlib.sha256(raw).hexdigest(),'target_calls':0})
 observed=run_screen(screen)
 write(label+'.qualification.json',observed)
 print(label,observed['status'],observed['receipt']['settings_sha256'],flush=True)
 if observed['status']!='passed':raise SystemExit('Qualification failed; no target launch or replacement reader.')
