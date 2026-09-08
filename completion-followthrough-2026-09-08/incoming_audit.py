"""Read-only public evidence checks, never new independent measurement voices.

Example: python incoming_audit.py 158383ee7346428911d758236b395697ee0afc9ee74db2b9f692b97cb83a72a1
Requires the public ainglish SDK only for normalising qualification-screen data.
No inference, tokenizer run, authentication, mint, submission or moderation call.
"""
import hashlib,json,sys,urllib.request
from collections import Counter
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from ainglish.reader_qualification import validate_screen,SCREEN_KIND


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def read(url):
    with urllib.request.urlopen(url,timeout=40) as response:
        body=response.read(3_000_001)
    if len(body)>3_000_000:raise ValueError('Unexpected large public artifact')
    return json.loads(body)


def item_list(bundle):
    return bundle['items'] if isinstance(bundle,dict) else bundle


def gold_check(row):
    data=row['strata'];kind=row['settlement_stratum']
    gold=data['answer_options'][row['answer']]
    if kind in ['utc','civil','fold','gap']:
        local=datetime.fromisoformat(data['date']+'T'+data['clock'])
        # A Z spelling fixes UTC even if metadata names the event's geographical venue.
        zone=ZoneInfo('UTC' if kind=='utc' else data['zone'])
        instants=[]
        for fold in [0,1]:
            utc=local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc)
            if utc.astimezone(zone).replace(tzinfo=None)==local and utc not in instants:instants.append(utc)
        expected=(instants[0].strftime('%Y-%m-%d %H:%M UTC') if len(instants)==1 else 'not determined') if kind in ['utc','civil'] else {0:'no matching instant',1:'one matching instant',2:'two matching instants'}[len(instants)]
    elif kind.startswith('missing-date'):
        # A hidden metadata date is NOT visible dating context for the reader.
        expected='no unique dated instant'
    elif kind=='recurring-utc':expected='the UTC clock reading stays fixed'
    elif kind=='recurring-civil':
        dates=data.get('dates',data.get('recurrence_dates'))
        offsets={datetime.fromisoformat(day+'T'+data['clock']).replace(tzinfo=ZoneInfo(data['zone'])).utcoffset() for day in dates}
        if len(offsets)!=2:return {'id':row['id'],'issue':'supplied dates do not exhibit differing offsets'}
        names=['the '+data['zone']+' civil clock reading stays fixed']
        if data['zone']=='Europe/London':names.append('the London clock reading stays fixed')
        expected=gold if gold in names else names[0]
    else:return {'id':row['id'],'issue':'unhandled condition'}
    return None if gold==expected else {'id':row['id'],'gold':gold,'expected':expected}


def clock_audit(source,replica,bundle,source_bundle):
    rows=item_list(bundle);old=item_list(source_bundle)
    targets=[r for r in rows if not r.get('calibration')]
    complete=lambda r:digest({k:r.get(k) for k in ['english','ainglish','question','options','answer']})
    failures=[issue for r in targets if (issue:=gold_check(r)) is not None]
    screens=[]
    available=bundle.get('qualification_screens',[]) if isinstance(bundle,dict) else []
    for raw,q in zip(available,replica['manifest'].get('reader_qualifications',[])):
        screen=validate_screen(raw)
        actual=digest({'kind':SCREEN_KIND,'controls':screen['controls'],
            'ordering':'control order; detectable then other; one call per cell; no retry'})
        screens.append({'reader':q['roster_id'],'fingerprint_matches':actual==q['screen_sha256'],
            'qualified_before_mint':q['qualified_at']<replica['attempt']['created_at']})
    originals={r['name']:r for r in source['manifest']['readers']}
    keys=['model','precision','model_digest','answer_protocol','max_tokens','timeout_s','temperature','seed','top_p','top_k','num_ctx','reasoning_effort']
    roster=[{'reader':r['name'],'changed_fields':[k for k in keys if r.get(k)!=originals.get(r['name'],{}).get(k)]} for r in replica['manifest']['readers']]
    return {'checked_at':datetime.now(timezone.utc).isoformat(),'source':source['url'],'replication':replica['url'],
        'source_items_digest_matches':digest(old)==source['manifest']['items_sha256'],
        'replication_items_digest_matches':digest(rows)==replica['manifest']['items_sha256'],
        'complete_input_overlap':sorted({complete(r) for r in old}&{complete(r) for r in rows}),
        'targets':len(targets),'controls':len(rows)-len(targets),
        'strata_counts':dict(Counter(r['settlement_stratum'] for r in targets)),
        'gold_failures':failures,'qualification_screen_checks':screens,'reader_setting_checks':roster,
        'execution_journal_verified':False,
        'scope':'Deterministic input/gold/declaration audit using installed zoneinfo rules. Not a model rerun, independent settlement vote, proof of execution chronology, or guarantee of future civil-time legislation. Complete journals and actual allocation procedure still require review.'}


if __name__=='__main__':
    h=sys.argv[1]
    if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise SystemExit('Pass an exact lowercase manifest hash')
    replica=read('https://ainglish.org/api/v1/measurements/'+h)
    source=read('https://ainglish.org/api/v1/measurements/'+replica['replicates_hash'])
    print(json.dumps(clock_audit(source,replica,read(replica['manifest']['items_url']),read(source['manifest']['items_url'])),indent=2))
