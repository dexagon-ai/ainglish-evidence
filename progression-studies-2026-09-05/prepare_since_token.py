"""Prepare a faithful, separate cost prerequisite with the canonical SDK runner; no counts."""
import json
from pathlib import Path
from ainglish import estimand,token_measurement
ROOT=Path(__file__).resolve().parent
DOMAINS=[('incident-response','the relay reset','the alarms have stayed quiet'),
 ('deployments','the route patch landed','the service has answered successfully'),
 ('access-policy','the access rule changed','the account has remained locked'),
 ('payments','the bank link reopened','payments have cleared each evening'),
 ('health-monitoring','the monitor was recalibrated','the readings have stayed within range'),
 ('logistics','the depot reopened','deliveries have arrived each morning'),
 ('scheduling','the new rota began','the desk has remained staffed'),
 ('research-reporting','the sensor was replaced','the lab has logged readings daily'),
 ('coordination','the meeting moved online','the team has met weekly')]
def save(name,value):
    with (ROOT/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2)

if __name__=='__main__':
    rows=[]
    for i in range(32):
        domain,event,main=DOMAINS[i%9]
        prefix=f'For journal T{12100+i}, at the reference date, '
        rows.append({'english':prefix+f'{event} explains why {main}.',
            'ainglish':prefix+f'Because {event}, {main}.','stratum':'reason:'+domain})
        rows.append({'english':prefix+f'{main} throughout the interval from when {event} through the reference date.',
            'ainglish':prefix+f'Ever since {event}, {main}.','stratum':'interval:'+domain})
    assert len(rows)==64 and len({(x['english'],x['ainglish']) for x in rows})==64
    declaration=estimand.declaration(unit_span='one complete reason or through-reference interval claim',
        contrast='Registered ordinary Because/Ever since wording minus concise complete English with the same reason or interval assertion; no invented marker syntax, bare-since comparison or explicit no-cause padding',
        population='Prospective 64-pair operational journal population: 32 per form, all nine declared domains; 3 or 4 fresh contexts per form-domain cell, with equal domain and form weights',
        reducer='least_favourable',aggregation_rule='For each tokenizer, equal-weight mean of the 18 form-domain cell means; report maximum tokenizer mean (least-favourable), with exact member-span bounds')
    spec={'manifest':{'metric':'token_delta','models':['cl100k_base','o200k_base'],'test_set':rows,
        'seed':2026090521,'estimand_contract':declaration,
        'settlement_strata':[{'id':form+':'+domain,'weight':1} for form in ['reason','interval'] for domain,_,_ in DOMAINS],
        'legacy_contract_repair_of':'03f86227-8d19-4f54-b7b2-47408e36711f',
        'method':'New original under the registered surfaces; not a replication of the invalid invented-wrapper source. Canonical SDK token_measurement prepare -> mint -> run_prepared -> verify -> measure. No encoding before mint.',
        'scope':'Current reference tokenizer cost only. This result does not measure comprehension or establish future-trained efficiency.'}}
    save('since-token.spec.json',spec)
    plan=token_measurement.prepare(spec)
    plan['mint']['admissibility_gates'] += ['live proposal active and token prerequisite unresolved',
        'use existing cached encodings only; no network downloads','every finite result filed once, including a positive cost',
        'unchanged exact form/domain corpus and weights; current costs do not predict future tokenizer training']
    save('since-token.plan.json',plan)
    print(plan['manifest_commitment'],plan['pair_count'],'prepared; zero counts')
