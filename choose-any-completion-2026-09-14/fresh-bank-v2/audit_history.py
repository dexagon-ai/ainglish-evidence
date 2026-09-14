"""Public read-only SDK audit of exact-input overlap with both current CAD sources."""
import hashlib
import json
from ainglish import panel
from ainglish.client import AinglishClient
from instrument import ROOT, digest, write

def main():
    client=AinglishClient(base_url='https://ainglish.org')
    target=[i for i in json.loads((ROOT/'items.json').read_text()) if not i.get('calibration')]
    sources=[]
    for h in ['05c2fbbefb585c2fafbe09c024e839ee1f8596060de5a958cce793ef2920d49d',
              '6f1ad7f2a033db5fcc203a31aea980b4fc1fba2840ab6cc5e968af2a628e53ce']:
        source=client.measurement(h)['manifest']
        if source.get('items'):
            historical=source['items']; observed=digest(historical)
        else:
            historical,observed=panel.fetch_items(source['items_url'],source['items_sha256'])
        assert observed==source['items_sha256']
        real=[i for i in historical if not i.get('calibration')]
        pairs={(i['english'],i['ainglish']) for i in real}
        texts={i[a] for i in real for a in ['english','ainglish']}
        complete=sum((i['english'],i['ainglish']) in pairs for i in target)
        arm=sum(i[a] in texts for i in target for a in ['english','ainglish'])
        assert complete==arm==0
        sources.append({'source_manifest_hash':h,'source_items_sha256':observed,
            'source_target_items':len(real),'source_unique_language_pairs':len(pairs),
            'complete_pair_overlap':complete,'arm_text_overlap':arm})
    result={'status':'FRESHNESS_AUDIT_ONLY_NOT_MEASUREMENT','target_worlds':len(target),
            'sources':sources,'network_reads':'public historical artifact GET only; no reader/tokenizer spend',
            'limit':'Exact-input freshness, not proof of independent semantic families or training histories.'}
    write('HISTORICAL-OVERLAP.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
