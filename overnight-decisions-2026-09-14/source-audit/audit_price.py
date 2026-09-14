"""Post-outcome structural audit, not a new experiment or settlement computation."""
from collections import Counter,defaultdict
import hashlib,json,re,sys
from pathlib import Path
from ainglish.panel import fetch_items
ROOT=Path(__file__).resolve().parent
SRC='53387330268be4a9721563f2e5693f11562419343aef1ecedffe4fe79a805827'
REP='d300b285cd7d639215d31031585f9aed2c983bed5dc86569ecc2cb7b4c50ca14'

def normal(value):
 if isinstance(value,str):
  # Only explicitly changed resource/invoice/pool identifiers and observation
  # timestamps. Do not strip semantic prices/counts, wording, labels or answers.
  value=re.sub(r'(?<=-)\b[78]30([0-7])\b',r'ID30\1',value)
  return value.replace('2026-09-07 at12:00 UTC','OBSERVATION_TIME').replace('2026-09-13 at15:00 UTC','OBSERVATION_TIME')
 if isinstance(value,list):return [normal(v) for v in value]
 if isinstance(value,dict):return {k:normal(v) for k,v in value.items()}
 return value

def key(row):
 return json.dumps(normal({k:row[k] for k in ['english','ainglish','question','options','answer','settlement_stratum','strata']}),sort_keys=True,separators=(',',':'))

def main():
 s=json.loads((ROOT/(SRC+'.json')).read_text());r=json.loads((ROOT/(REP+'.json')).read_text())
 original,_=fetch_items(str(ROOT.parents[1]/'price-allocation-original-2026-09-07/items.json'),s['manifest']['items_sha256'])
 replica,digest=fetch_items(sys.argv[1],r['manifest']['items_sha256'])
 (ROOT/'saturnia-price-items-mirror.json').write_text(json.dumps(replica,ensure_ascii=False,indent=2)+'\n')
 scientific=lambda rows:[v for v in rows if not v.get('calibration')]
 a=scientific(original);b=scientific(replica)
 lookup=defaultdict(list)
 for row in a:lookup[key(row)].append(row['id'])
 matches=[{'replica_id':row['id'],'source_ids':lookup.get(key(row),[])} for row in b]
 counts=defaultdict(lambda:[0,0])
 for cell in r['interval_provenance_attestation']['cells']:
  pair=counts[(cell['reader'],cell['arm'])];pair[0]+=cell['correct'];pair[1]+=1
 report={'kind':'post-outcome-structural-audit','source':SRC,'replication':REP,
  'replica_item_digest_verified':digest,'source_scientific_items':len(a),'replica_scientific_items':len(b),
  'same_normalized_complete_case':sum(bool(v['source_ids']) for v in matches),'matches':matches,
  'normalization':'Only item/invoice/pool 730x versus 830x identifiers and the two declared observation timestamps; all sentences, questions, options, keys and strata retained. Metadata item IDs omitted.',
  'replica_reader_counts':[{'reader':k[0],'arm':k[1],'correct':v[0],'total':v[1]} for k,v in sorted(counts.items())],
  'boundary':'This does not recalculate or override the server settlement result, prove misconduct, establish the cause of reader heterogeneity, or claim the rows have literally identical bytes. Identifier/date changes are not new semantic scenarios. Raw answer/wire journals would be needed for a fuller instrument audit.'}
 (ROOT/'price-audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['same_normalized_complete_case','source_scientific_items','replica_scientific_items','replica_reader_counts']},indent=2))

if __name__=='__main__':main()
