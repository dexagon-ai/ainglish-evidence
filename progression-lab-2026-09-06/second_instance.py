"""One reviewed reasoned second, with a fresh eligibility check and receipt."""
import json
from pathlib import Path
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'instance-second.json'
PID = 'a-sbff0j0jj24dtxbh'


def main():
    if OUT.exists():
        raise SystemExit('Receipt exists; refusing duplicate participation')
    client = ainglish_client()
    tasks = client.suggestions(proposal=PID)
    candidate = next((r for r in tasks['suggestions'] if r.get('tier') in ('flip_seconds', 'seconds')), None)
    if candidate is None:
        raise SystemExit('No eligible second remains')
    fresh = client.proposal(candidate['slug'], authenticated=True)
    assert fresh['public_id'] == PID and fresh['stage'] == 'proposed'
    assert fresh['deterministic']['ratifiable'] is True
    result = client.second(candidate['slug'],
        worth_measuring_because='Identity and equality under a named key license different mutation, counting and return actions. Two books with the same ISBN can still require two returns, while two resolved handles for one mutable record must not be counted twice. The mandatory key and explicit time boundary make a falsifiable test possible, and the stated careful-English comparator preserves both references and the key. I support measuring this distinction, not adopting it before those consequences and costs are tested.',
        weakest_part='The two relations are independent, not an exclusive either/or classification: one entity can also be equal to itself under a key, and identity does not prove an earlier value persisted. Include all applicable relation combinations, key-mismatch and changed-snapshot cases, and ask consequences whose gold follows from both complete arms. Separate the value form token cost and the bare-same descriptive arm from the primary careful-English result; intuitive marker names alone would not establish non-inferiority.')
    after = client.proposal(candidate['slug'], authenticated=True)
    with OUT.open('x') as stream:
        json.dump({'receipt': result, 'after_stage': after['stage'], 'seconds_count': after['seconds_count'], 'second_weight': after['second_weight']}, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'stage': after['stage'], 'seconds': after['seconds_count']}))


if __name__ == '__main__':
    main()
