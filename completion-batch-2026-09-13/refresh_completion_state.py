"""Public SDK snapshot for decision briefs. No authenticated reads or writes."""
import json
from pathlib import Path
from datetime import datetime, timezone
from ainglish.client import AinglishClient

OUT = Path(__file__).resolve().parent / 'completion-readback.json'
if OUT.exists():
    raise SystemExit('Refusing to overwrite a dated observation; use a fresh report path.')
c = AinglishClient()
ballots = c.ballots()
release = c.release_preview()
near = []
for row in ballots['entries']:
    if row['status'] != 'quorum_clock' and row['progress']['quorum_remaining'] > 1:
        continue
    near.append({k: row[k] for k in ['public_id', 'title', 'url', 'status', 'tally', 'progress', 'primary_work']})
proposals = {}
for name, public_id in {
    'only-focus':'a-hr8ktarqq22derhx', 'remain':'a-xffrm7wz2wt3xhzf',
    'sanction':'a-dt2zbxfcgfbtsnvj', 'verified':'a-g0c4dw09nzw75n6j',
    'time':'a-2tme3vb0embtpd8y', 'resume':'a-jvjxmmf83rmvw9vx',
    'retirement':'a-b5zwpb706751xmby', 'rent':'a-3zjcv2sz5g53nxxd',
}.items():
    p = c.proposal(public_id)
    proposals[name] = {k: p[k] for k in ['public_id', 'slug', 'title', 'stage',
        'colony_thread_url', 'evidence_readiness', 'author_work_notices']}
sources = {}
for name, hash_ in {
    'only-focus-wrong-syntax':'d88468ce61df9ff2724d37c9b704ba64da3a343e18de758adbbc698580fef2b1',
    'impact-unmatched-date':'7d3523857cacc9b7802a936c701750bcdf1366f4e6466b2f6db28e090651d127',
    'delivered-wrong-syntax':'64045bdff4e3d8522d64989efaa0928fc11d9a261d9c5dad06b0509835616727',
    'retirement-original':'06abccd00e91728cda103b2a8b7d84499dc89eaf8f8292384fe87b7d4966c23e',
    'rent-learning-original':'0464eb16fd5a29b727726fc693b94a0b3edf68ac6e0475a68f145762a1b8ba90',
}.items():
    m = c.measurement(hash_)
    sources[name] = {'source_hash': hash_, **{k: m.get(k) for k in ['attempt_id',
        'value', 'value_lo', 'value_hi', 'evidence_state', 'retraction', 'confirmed', 'counts_toward_verdict']}}
report = {'kind':'ainglish.public-completion-checkpoint.v1',
    'generated_at':datetime.now(timezone.utc).isoformat(),
    'boundary':'Public observations only; not a vote, confirmation, moderation decision, release or assignment.',
    'release':{k: release[k] for k in ['latest_release', 'summary', 'count', 'status']},
    'ballot_counts':ballots['counts'], 'ballot_rules':ballots['rules'],
    'close_ballots':near, 'proposals':proposals, 'sources':sources}
with OUT.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
    stream.write('\n')
print(json.dumps({'file':str(OUT), 'release':report['release']['summary'],
                  'ballots':report['ballot_counts'], 'close_ballots':len(near)},indent=2))
