"""Freeze the complete public input population before the retirement regression run."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re,subprocess
from pathlib import Path
from ainglish.client import AinglishClient

ROOT=Path(__file__).resolve().parent/'retirement'
WEB=Path('/home/dexagon/codex/worktrees/web-retirement-audit-20260909')
DEPLOY='ddaeda4728bb96587a8e672641163d08d4049fdb'
IMPLEMENTATION='dcccabf25a7fcc3c2161ba1e1ba47c50ed1efdb3'

def save(name,value):
    ROOT.mkdir(exist_ok=True)
    with (ROOT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False)

def git(*args):return subprocess.check_output(['git',*args],cwd=WEB,text=True).strip()
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def assess(text):
    return re.search(r'(?ms)^    public function assess\(Proposal \$p\): void\n.*?(?=^    /\*\*)',text).group()

def main():
    c=AinglishClient(use_env=False)
    assert c.health()['deployment']['commit']==DEPLOY
    records=[r for page in c.proposal_pages(page_size=200) for r in page['proposals']]
    assert len({r['public_id'] for r in records})==len(records)
    # Details are needed only where the changed guard can alter execution.
    # All other rows remain in the domain and are discharged by exact source
    # equivalence of the unchanged branch, not silently omitted from the count.
    withdrawn={r['public_id']:c.proposal(r['slug']) for r in records if r['stage']=='withdrawn'}
    before=git('show',IMPLEMENTATION+'^1:src/Service/MeasurementService.php')
    after=git('show',IMPLEMENTATION+':src/Service/MeasurementService.php')
    deployed=git('show',DEPLOY+':src/Service/MeasurementService.php')
    old_guard="if (!$p->isPublished()) {"
    new_guard="if (!$p->isPublished() || $p->stage === 'withdrawn') {"
    # This checks causal identity, not any population's scientific outcome.
    assert assess(before).replace(old_guard,new_guard)==assess(after)==assess(deployed)
    save('input-census.json',{'captured_at':datetime.now(timezone.utc).isoformat(),
        'domain':'complete public all-stage proposal sweep, including language and protocols',
        'records':records,'withdrawn_details':withdrawn,
        'row_class_counts':dict(Counter(('protocol' if r['kind']=='protocol' else 'language')+'/'+r['stage'] for r in records))})
    paths=git('diff','--name-only',IMPLEMENTATION+'^1',IMPLEMENTATION).splitlines()
    save('source-boundary.json',{'repository':'ai-nglish/ainglish-symfony',
        'implementation':IMPLEMENTATION,'parent':git('rev-parse',IMPLEMENTATION+'^1'),
        'initial_deployment':'5c3b487f39087f1de0738ffd6b7f3492b688e40e','current_deployment':DEPLOY,
        'changed_paths':paths,'before_assess_sha256':sha(assess(before)),
        'after_assess_sha256':sha(assess(after)),'current_measurement_service_sha256':sha(deployed+'\n'),
        'difference':{'before':old_guard,'after':new_guard},
        'unchanged_non_withdrawn_branch':'Exact byte equality after substituting only the guard; evaluated over every census row.',
        'scope':'Causal live effect of the deployed reassessment guard. No fake pre-deploy census is reconstructed. Activation/authorisation tests are a separate supplementary local test surface.'})
    print('Frozen',len(records),'public records and',len(withdrawn),'withdrawn details; no regression outcome computed.')

if __name__=='__main__':main()
