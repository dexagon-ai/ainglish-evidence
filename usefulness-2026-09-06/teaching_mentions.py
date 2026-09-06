"""Report literal marked-form mentions in ratified mappings; not semantic dependencies."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent
MARKER=re.compile(r'\b[a-z][a-z0-9_]*(?:-[a-z0-9_]+)+\b|\b[a-z][a-z0-9_]*(?=\(|:)')


def main():
    c=ainglish_client(); register=c.register(); proposals=list(c.iter_proposals(page_size=200))
    index=defaultdict(list)
    for p in proposals:
        markers=set(MARKER.findall(p['form']))
        markers.update(k for k in (p.get('slot') or {}) if isinstance(k,str) and MARKER.fullmatch(k))
        for marker in markers:index[marker].append({'id':p['public_id'],'slug':p['slug'],'stage':p['stage'],'form':p['form']})
    findings=[]
    for entry in register['entries']:
        if entry['kind']=='protocol':continue
        for marker in sorted(set(MARKER.findall(entry['english_mapping']))):
            matches=[p for p in index.get(marker,[]) if p['slug']!=entry['slug']]
            if matches:
                findings.append({'source_slug':entry['slug'],'marker':marker,'has_ratified_target':any(p['stage']=='ratified' for p in matches),'targets':matches})
    value={'at':datetime.now(timezone.utc).isoformat(),'kind':'ainglish.marked-mention-audit.v1','register':register,'index_records':len(proposals),'findings':findings,
           'boundary':'Literal spelling match only, including negative examples and contrasts. Not a parser, semantic dependency graph, conformance certificate or proof that a whole sentence is invalid. Bare English remains legal. No mappings rewritten.'}
    with (ROOT/'TEACHING-MENTIONS.json').open('x') as h:json.dump(value,h,indent=2,ensure_ascii=False);h.write('\n')
    print(json.dumps({'register_count':register['count'],'mention_edges':len(findings),'without_current_ratified_target':[r for r in findings if not r['has_ratified_target']]}))


if __name__=='__main__':main()
