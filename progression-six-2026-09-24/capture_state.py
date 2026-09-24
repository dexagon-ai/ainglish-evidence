"""Explicit public snapshot/readback, never writes to Ainglish or Colony."""
from datetime import datetime, timezone
import json
from pathlib import Path

from ainglish.client import AinglishClient

ROOT=Path(__file__).resolve().parent
IDS=['a-hvrcz8j6qcp8amvr','a-mbxazvtshv2excx5','a-gsp0xkxk1sq5pgn5','a-hz2zrrjkjfjvjgdb',
     'a-mv841prke9x9e5cm','a-ppyzdf5qk6z67aty','a-twt7mcv776hnrz2f','a-ef4rsdm2ksnkdz2r']
SOURCE='f8b68a42ab8bef927b7f5d6161b17bd066b7a7dad8c6daf95e874afda13e9daa'


def capture():
    a=AinglishClient(use_env=False)
    now=datetime.now(timezone.utc).isoformat(); rows=[]
    for ident in IDS:
        p=a.proposal(ident)
        row={k:p.get(k) for k in ('public_id','slug','title','stage','form','english_mapping','predicted_measurement',
            'evidence_contract','ratification','ballot_closure','author_work_notices')}
        row['measurement_count']=len(p.get('measurements',[]));rows.append(row)
        print(ident,p.get('stage'),json.dumps({k:p.get(k) for k in ('ratification','ballot_closure')})[:2000],flush=True)
    source=a.measurement(SOURCE)
    # Store the exact public test_set and typed identity, not unrelated session URLs.
    selected={k:source.get(k) for k in ('manifest_hash','attempt_id','value','value_lo','value_hi','confirmed','settlement_state','evidence_state','retraction')}
    selected['manifest_fields']={k:source['manifest'].get(k) for k in ('test_set','items_sha256','comparison_identity','estimand_contract','settlement_strata','tokenizer_provenance')}
    report={'captured_at':now,'public_read_only':True,'proposals':rows,'stat_token_source':selected}
    name='live-'+now[:19].replace(':','-')+'.json'
    (ROOT/name).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print('saved',name,flush=True)
    return report


if __name__=='__main__':capture()
