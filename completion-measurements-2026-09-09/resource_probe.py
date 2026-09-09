"""Prompt-free load/unload probes of explicit cached models; no scientific calls."""
import argparse,json,shutil,time,urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE='http://127.0.0.1:11434'
FLOOR=15*1024**3
START=22*1024**3
def request(path,data=None,timeout=180):
 req=urllib.request.Request(BASE+path,data=None if data is None else json.dumps(data).encode(),
   headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as f:return json.load(f)
def main(name,filename):
 output=ROOT/filename;assert not output.exists(),'Probe receipts are never overwritten'
 assert not request('/api/ps')['models'],'Another model is loaded; do not disturb shared work'
 tags=request('/api/tags')['models'];match=[x for x in tags if x['name']==name]
 assert len(match)==1,'Model must already be cached; no downloads'
 assert shutil.disk_usage('/mnt/c').free>=START,'Insufficient initial host-disk headroom'
 report={'kind':'ainglish.prompt-free-resource-probe.v1','model':name,'digest':match[0]['digest'],
  'scope':'Model load/unload only, no prompt, qualification or target inference; no files deleted.',
  'started_at':datetime.now(timezone.utc).isoformat(),'stop_floor_bytes':FLOOR,'samples':[]}
 minimum=shutil.disk_usage('/mnt/c').free
 try:
  with ThreadPoolExecutor(max_workers=1) as ex:
   job=ex.submit(request,'/api/generate',{'model':name,'keep_alive':600,'stream':False})
   while not job.done():
    free=shutil.disk_usage('/mnt/c').free;minimum=min(minimum,free)
    row={'time':datetime.now(timezone.utc).isoformat(),'host_free_bytes':free}
    report['samples'].append(row);print('LOAD',name,'host_free_GiB',round(free/1024**3,2),flush=True)
    time.sleep(3)
   result=job.result();report['load']={k:v for k,v in result.items() if k!='context'}
  report['loaded_models']=request('/api/ps')['models']
  for _ in range(3):
   free=shutil.disk_usage('/mnt/c').free;minimum=min(minimum,free)
   report['samples'].append({'time':datetime.now(timezone.utc).isoformat(),'host_free_bytes':free})
   time.sleep(2)
  report['minimum_host_free_bytes']=minimum
  report['safe_for_single_model_probe']=minimum>=FLOOR
 finally:
  # Only the explicit model this probe loaded is released; no service or other job is stopped.
  report['unload']=request('/api/generate',{'model':name,'keep_alive':0,'stream':False})
  report['host_free_after_release_bytes']=shutil.disk_usage('/mnt/c').free
  with output.open('x') as f:json.dump(report,f,indent=2)
 print('PROBE',name,report.get('safe_for_single_model_probe'),'minimum_GiB',round(minimum/1024**3,2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('receipt');a=p.parse_args();main(a.model,a.receipt)
