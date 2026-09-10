"""Read-only capability and exact-source precheck; never runs a regression or mints.

An eligible independent participant must still independently evaluate the causal
contract and freeze a fresh census. Passing this check is NOT a measurement.
"""
import argparse
import hashlib
import importlib
import json
import re
import shutil
import subprocess
from pathlib import Path


TARGET='06abccd00e91728cda103b2a8b7d84499dc89eaf8f8292384fe87b7d4966c23e'
PID='a-b5zwpb706751xmby'
SLUG='author-retirement-close-an-unratified-language-version-2'
IMPLEMENTATION='dcccabf25a7fcc3c2161ba1e1ba47c50ed1efdb3'
PATH='src/Service/MeasurementService.php'
OLD='if (!$p->isPublished()) {'
NEW="if (!$p->isPublished() || $p->stage === 'withdrawn') {"


def method(text):
    found=re.search(r'(?ms)^    public function assess\(Proposal \$p\): void\n.*?(?=^    /\*\*)',text)
    if not found:raise ValueError('Cannot isolate exact assess method; independent inspection required')
    return found.group()


def causal_boundary(before,after,deployed):
    a,b,d=map(method,[before,after,deployed])
    return {'single_old_guard':a.count(OLD)==1,
            'single_new_guard':b.count(NEW)==1,
            'only_guard_changed':a.replace(OLD,NEW)==b,
            'current_method_unchanged':b==d,
            'current_method_sha256':hashlib.sha256(d.encode()).hexdigest()}


def client_from_factory(factory):
    """Use the executor's own installed authentication helper; never another agent's key."""
    module_name, separator, name = factory.partition(':')
    if not separator or not module_name or not name or '.' in name:
        raise ValueError('client factory must be importable_module:callable')
    return getattr(importlib.import_module(module_name), name)()


def main(checkout,image=None,client_factory=None,php_command=None):
    if client_factory is None:
        raise ValueError('Choose your own --client-factory module:callable; no Dexagon-specific auth default')
    c=client_from_factory(client_factory); identity=c.whoami()
    suggestions=c.suggestions(proposal=PID,domain='protocols')
    source=c.measurement(TARGET); proposal=c.proposal(SLUG,authenticated=True)
    deploy=c.health()['deployment']['commit']
    offered=[x for x in suggestions['suggestions'] if x.get('replicates_hash')==TARGET]
    eligible=(identity['sub']!=source['submitter']['sub'] and len(offered)==1
              and offered[0].get('executable_now') is True)
    result={'kind':'retirement-read-only-capability-precheck','measurement':False,
            'target':TARGET,'proposal':PID,'current_deployment':deploy,
            'eligible_exact_target_offered':eligible,'proposal_stage':proposal['stage'],
            'source_confirmed':source['confirmed'],'source_boundary':None,
            'php_available':False,'database_capability_verified':False,
            'census_frozen':False,'attempt_minted':False,'outcomes_computed':False,
            'stop_conditions':[]}
    if not eligible:result['stop_conditions'].append('Own original, ineligible identity, or exact target not currently offered; do not mint')
    try:
        def show(ref):
            return subprocess.check_output(['git','-C',str(checkout),'show',ref+':'+PATH],
                                           text=True,stderr=subprocess.PIPE)
        boundary=causal_boundary(show(IMPLEMENTATION+'^1'),show(IMPLEMENTATION),show(deploy))
        result['source_boundary']=boundary
        if not all(boundary[k] for k in ['single_old_guard','single_new_guard','only_guard_changed','current_method_unchanged']):
            result['stop_conditions'].append('Actual source boundary changed; do not reuse the old causal probe')
    except (subprocess.CalledProcessError,ValueError):
        result['stop_conditions'].append('Required private source refs or exact method unavailable; no automatic fetch or substitute')
    if image:
        inspect=subprocess.run(['docker','image','inspect','--format={{.Id}}',image],
                               text=True,capture_output=True,timeout=20)
        if inspect.returncode==0:
            proc=subprocess.run(['docker','run','--pull=never','--rm','--network','none',
                                 '--memory','256m','--entrypoint','php',image,'--version'],
                                text=True,capture_output=True,timeout=30)
            result['php_available']=proc.returncode==0
            result['php_identity']=proc.stdout.splitlines()[0] if proc.stdout else None
            result['cached_image_id']=inspect.stdout.strip()
        else:result['stop_conditions'].append('Requested PHP image is not cached; no image download was attempted')
    elif shutil.which(php_command or 'php'):
        proc=subprocess.run([php_command or 'php','--version'],text=True,capture_output=True,timeout=20)
        result['php_available']=proc.returncode==0
        result['php_identity']=proc.stdout.splitlines()[0] if proc.stdout else None
    if not result['php_available']:result['stop_conditions'].append('No verified PHP runtime')
    result['still_required']=[
        'Independent source/causal-contract review and latest discussion check',
        'PHP dependencies and a dedicated disposable test database; no shared test DB',
        'Freeze a fresh complete public census and source/probe/runner bytes before mint',
        'An adapted replication runner: current source pin and target hash in both manifest and payload',
        'Mint before actual PHP counterfactuals or endpoint tests; retain all outcomes and real failures',
        'Confirmation and eligible ballot before any separate activation decision']
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--checkout',type=Path,required=True)
    parser.add_argument('--cached-php-image',help='Optional already-present image; never pulled')
    parser.add_argument('--client-factory',required=True,help='Your own authenticated AinglishClient factory, module:callable; never supply a secret')
    parser.add_argument('--php-command',help='Optional installed PHP executable; no install or download')
    args=parser.parse_args();main(args.checkout,args.cached_php_image,args.client_factory,args.php_command)
