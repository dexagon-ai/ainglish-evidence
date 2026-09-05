"""Run the two prepublished, target-independent reader screens once; retain failures."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import urllib.request
from ainglish.reader_qualification import run_screen

ROOT=Path(__file__).resolve().parent

def main():
    q=ROOT/'qualification'
    screens=[json.loads((q/f'{name}-screen.json').read_text()) for name in ['mistral','gemma']]
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps',timeout=10) as r:loaded=json.load(r)['models']
    allowed={s['reader']['model'] for s in screens}
    assert all(m.get('name',m.get('model')) in allowed for m in loaded),'Unrelated loaded inference workload'
    gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],check=True,capture_output=True,text=True).stdout
    assert sum(int(x) for x in gpu.splitlines())>40000
    with (q/'started.json').open('x') as f:json.dump({'at':datetime.now(timezone.utc).isoformat(),'source_commit':'74c633f','gpu_free_mib':gpu.splitlines(),'retry_count':0},f)
    for name,screen in zip(['mistral','gemma'],screens):
        result=run_screen(screen)
        with (q/f'{name}-qualification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        print(name,result['status'],flush=True)

if __name__=='__main__':main()
