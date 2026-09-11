"""Prospective semantic reference renderer, NOT the current shortest-English contract.

No tokenizer or inference. A longer reference cannot silently replace the current
comparison. The author must decide the semantic/comparator question first.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Meaning:
    action: str
    state: str # no_path_known, path_known, unknown
    path: str | None = None
    holder: str = 'the writer'
    exclusive_holder: bool = False
    window: str | None = None
    cost: str | None = None
    restores: str = 'immediately preceding state'
    path_evidence: str | None = None # same disclosed anchor in both arms


def render(m):
    if not m.action.strip() or any(ch in m.action for ch in '\n\r'):
        raise ValueError('One exact action clause is required')
    if m.state=='unknown':
        raise ValueError('Unknown reversibility cannot be rendered as no-undo')
    if m.state=='no_path_known':
        if m.path or m.window or m.cost or m.exclusive_holder or m.holder!='the writer':
            raise ValueError('Do not silently drop positive path/holder/constraint fields')
        return m.action+'; the writer knows no way back to the state immediately before this action.'
    if m.state!='path_known' or not m.path or not m.path.strip() or not m.path_evidence:
        raise ValueError('A named, evidenced path is required, not guessed folklore')
    if m.restores!='immediately preceding state':
        raise ValueError('Recovery to a different prior state is not this can-undo claim')
    if not m.holder.strip():raise ValueError('Holder must resolve; the only default is the writer')
    for value in [m.path,m.holder,m.window,m.cost]:
        if value is not None and (not value.strip() or any(ch in value for ch in '\n\r;')):
            raise ValueError('Ambiguous slot delimiter or empty slot; clarify the input')
    clause='the state immediately before this action can be restored via '+m.path+' by '+m.holder
    if m.exclusive_holder:clause+=' only'
    if m.window:clause+=' within '+m.window
    if m.cost:clause+='; cost: '+m.cost
    return m.action+'; '+clause+'.'
