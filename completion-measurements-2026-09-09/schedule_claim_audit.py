"""Arithmetic-only audit of manually verified operative claims, never a reader-label quiz."""
from datetime import datetime,timezone
import re,unittest

def audit(row):
 """The human/agent auditor must verify the source bytes and assertion scope first."""
 if row.get('use_kind')!='operative_assertion':
  return {'state':'excluded','reason':'example, quotation, question or non-operative mention'}
 if row.get('source_verification')!='auditor-verified':
  return {'state':'unreviewed','reason':'source bytes, claim scope and event identity need independent inspection'}
 if row.get('tag') not in ('moved-earlier','moved-later'):
  return {'state':'unreviewed','reason':'not one unambiguous registered direction claim'}
 for key in ('claim','before','after'):
  source=row.get(key+'_source')
  if not isinstance(source,dict) or not isinstance(source.get('url'),str) or not source['url'].startswith('https://') \
    or not re.fullmatch('[0-9a-f]{64}',source.get('sha256','')):
   return {'state':'unreviewed','reason':'missing pinned '+key+' source'}
 if not row.get('event_id') or row.get('before_event_id')!=row['event_id'] or row.get('after_event_id')!=row['event_id']:
  return {'state':'unreviewed','reason':'before and after must belong to the same resolved event'}
 if row.get('before_time') is None:
  return {'state':'excluded','reason':'prior scheduled time is unrecoverable; never guess it'}
 def instant(value):
  time=datetime.fromisoformat(value.replace('Z','+00:00'))
  if time.tzinfo is None or time.utcoffset() is None:raise ValueError('explicit timezone required')
  return time.astimezone(timezone.utc)
 try:before,after=instant(row['before_time']),instant(row['after_time'])
 except (TypeError,ValueError,KeyError,AttributeError):
  return {'state':'unreviewed','reason':'invalid or unanchored schedule time'}
 correct=after<before if row['tag']=='moved-earlier' else after>before
 return {'state':'audited','faithful':correct,'tag':row['tag'],
  'before_utc':before.isoformat(),'after_utc':after.isoformat(),
  'boundary':'Arithmetic on supplied auditor-verified sources; this function did not fetch or authenticate them. No inference about notice, finality, adoption or English comprehension.'}

def summarize(rows):
 results=[audit(r) for r in rows];scored=[r for r in results if r['state']=='audited']
 return {'audited_claims':len(scored),'faithful_claims':sum(r['faithful'] for r in scored),
  'excluded':sum(r['state']=='excluded' for r in results),'unreviewed':sum(r['state']=='unreviewed' for r in results),
  'fraction':sum(r['faithful'] for r in scored)/len(scored) if scored else None,
  'results':results,'boundary':'A descriptive audit only. Mint a frozen, eligible real-use sample before auditing it scientifically. Fixtures and prior exploratory reviews cannot become prospective evidence.'}

class AuditTests(unittest.TestCase):
 def row(self,**changes):
  r=dict(use_kind='operative_assertion',source_verification='auditor-verified',tag='moved-earlier',
   event_id='unit-test-only',before_event_id='unit-test-only',after_event_id='unit-test-only',
   before_time='2026-09-12T09:00:00Z',after_time='2026-09-12T08:00:00Z')
  for key in ('claim','before','after'):r[key+'_source']={'url':'https://example.invalid/test-only/'+key,'sha256':'a'*64}
  return r|changes
 def test_direction_strict_and_timezone_aware(self):
  for tag,after,expected in [('moved-earlier','2026-09-12T08:59:59Z',True),
    ('moved-later','2026-09-12T09:00:01Z',True),('moved-earlier','2026-09-12T09:00:00Z',False),
    ('moved-later','2026-09-12T10:00:00+01:00',False),('moved-later','2026-09-12T11:00:00+01:00',True),
    ('moved-earlier','2026-09-12T08:30:00-01:00',False)]:
   self.assertEqual(audit(self.row(tag=tag,after_time=after))['faithful'],expected)
 def test_unknown_examples_and_unverified_sources_never_count_as_true(self):
  for change,state in [({'before_time':None},'excluded'),({'use_kind':'example'},'excluded'),
   ({'source_verification':None},'unreviewed'),({'after_event_id':'other'},'unreviewed'),
   ({'before_time':'2026-09-12T09:00:00'},'unreviewed'),({'after_time':'bad'},'unreviewed'),
   ({'claim_source':None},'unreviewed'),({'tag':'moved-forward'},'unreviewed')]:
   self.assertEqual(audit(self.row(**change))['state'],state)
 def test_empty_is_not_perfect_or_zero_fidelity(self):
  self.assertIsNone(summarize([])['fraction'])
  self.assertIsNone(summarize([self.row(use_kind='example')])['fraction'])
 def test_false_claim_is_in_denominator(self):
  result=summarize([self.row(),self.row(after_time='2026-09-13T09:00:00Z')])
  self.assertEqual((result['audited_claims'],result['faithful_claims'],result['fraction']),(2,1,.5))

if __name__=='__main__':unittest.main()
