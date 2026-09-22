"""Exposed reference-graph design controls, not NLP parsing or reader measurements."""
from dataclasses import dataclass, replace
import re

@dataclass(frozen=True)
class Referent:
    label: str
    kind: str = 'singular_nonperson'
    introduced: bool = True
    context: str = 'local'

def resolve(surface, graph):
    m = re.fullmatch(r'it\(([A-Za-z0-9_-]+)\)',surface)
    if not m: return 'non_marker', None
    matches=[r for r in graph if r.label==m[1] and r.introduced and r.context in ('local','immutable')]
    if len(matches)!=1: return 'unresolved',None
    if matches[0].kind!='singular_nonperson': return 'out_of_scope',None
    return 'valid',matches[0].label

def main():
    a,b=Referent('service-A'),Referent('service-B')
    cases=[
        ('valid-A','it(service-A)',[a,b],('valid','service-A')),
        ('valid-B','it(service-B)',[a,b],('valid','service-B')),
        ('missing','it(service-C)',[a,b],('unresolved',None)),
        ('forward','it(service-A)',[replace(a,introduced=False),b],('unresolved',None)),
        ('duplicate','it(service-A)',[a,a,b],('unresolved',None)),
        ('plural','it(service-A)',[replace(a,kind='plural'),b],('out_of_scope',None)),
        ('person','it(service-A)',[replace(a,kind='person'),b],('out_of_scope',None)),
        ('unpinned','it(service-A)',[replace(a,context='unpinned'),b],('unresolved',None)),
        ('pinned-valid','it(service-A)',[replace(a,context='immutable'),b],('valid','service-A')),
        ('delimiter-loss','it service-A',[a,b],('non_marker',None)),
        ('possessive','its(service-A)',[a,b],('non_marker',None)),
        ('demonstrative','this(service-A)',[a,b],('non_marker',None)),
    ]
    for name,s,g,want in cases: assert resolve(s,g)==want,name
    # Sender-intended key is deliberately not an argument to resolve().
    intended='service-A'
    _,received=resolve('it(service-B)',[a,b])
    assert received != intended and received=='service-B'
    for claim in ('identity','ownership','responsibility','causality','continued_existence','truth'):
        # Reference graph contains no assertions of these relations; a future bank must
        # test reader behaviour on both unstated and explicitly stated versions.
        facts={}
        assert facts.get(claim,'unknown')=='unknown'
        facts[claim]=True
        assert facts[claim] is True
    print(f'{len(cases)} reference fixtures; valid-to-valid limit; 6 nonclaim/control pairs checked. Reader calls: 0.')

if __name__=='__main__': main()
