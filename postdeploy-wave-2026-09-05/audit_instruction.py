"""Map retained source questions to explicit current-scope obligations; no rescoring."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
 source=ROOT.parent/'next-wave-2026-09-05/settlement-audit/instruction-scope.items.json'
 rows=json.loads(source.read_text());canonical=json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
 assert hashlib.sha256(canonical).hexdigest()=='7463a0a4fca412475403acad2ab14c191b6199ddc31cbdae20f3b9374f813c40'
 affected=[]
 for row in rows:
  if row.get('settlement_stratum')=='dx:project-scope' and 'from-now-on' in row['ainglish']:
   assert row['answer']=='no'
   local=' here,' in row['ainglish']
   affected.append({'id':row['id'],'source_gold':'no','current_mapping_reading':'scope ambiguous because the directive also says here' if local else 'yes: same requester and explicitly comparable later work, with no stated revocation or project restriction',
    'classification':'resolve directive-local here scope' if local else 'mapping/gold conflict',
    'english':row['english'],'ainglish':row['ainglish'],'question':row['question']})
 assert len(affected)==10 and sum(x['classification']=='mapping/gold conflict' for x in affected)==9
 controls=[r for r in rows if r.get('calibration')]
 assert len(controls)==12 and all(any(t in r['ainglish'] for t in ['this-once','from-now-on']) for r in controls)
 result={'source_manifest_hash':'85a36ba6b6deb7982e7ffd8627b343f3a08b099116d8ae9a0827cb1cc87748f6',
  'source_items_sha256':hashlib.sha256(canonical).hexdigest(),'affected':affected,
  'refinement':'The earlier ten-case warning is nine direct conflicts plus one directive containing here that needs its own scope resolution. Do not collapse that qualification.',
  'target_bearing_control_ids':[r['id'] for r in controls],
  'action':'Author must resolve registered meaning before a prospective corrected instrument is launched. No old answer or observation was changed.',
  'proposed_design':'frozen/instruction.prospective.items.json; 128 independently key-checked design-only cases; qualification/control protocol still must be settled before use.',
  'inference_calls':0}
 with (ROOT/'instruction-source-audit.json').open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
 print('Nine direct mapping conflicts, one here-scope ambiguity, twelve target-bearing controls; no rescoring.')
if __name__=='__main__':main()
