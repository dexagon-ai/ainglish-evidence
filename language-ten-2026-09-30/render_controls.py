"""Render prospective language-review examples, not a measured or approved bank."""
from pathlib import Path
from collections import Counter
import json, hashlib
ROOT = Path(__file__).parent
OLD = ROOT / 'operational-design-v2.json'
if not OLD.exists():
    OLD = Path('/home/dexagon/ainglish-participation.fxkss3p3/operational-design-v2.json')
old = json.loads(OLD.read_text())
# Each tuple is question, shared premise, affirmative record, non-establishing record.
specs = {
'stat': [
("Is a posterior probability supplied for Alden-42's zero-average-change null?", "The null is zero average change in Alden-42.", "Bayesian report B42 assigns posterior probability 0.03 to this null.", "Test report T42 gives a p-value of 0.03 for this null."),
("Does the evidence establish that the exact protocol used for Alden-42 was registered before its results were first observed?", "Alden-42 used protocol digest A42; Birch-11 used distinct digest B11, with no alias. Results were first observed at 12:00 UTC on 24 September 2026. The registration service retained an immutable complete protocol at 09:00 UTC that day.", "The 09:00 registration contains protocol digest A42.", "The 09:00 registration contains protocol digest B11."),
("Is a causal conclusion supplied for North-42's intervention and outcome?", "North-42 and Birch-11 concern distinct interventions and outcomes, with no equivalence claim.", "Report C42 concludes that North-42's intervention caused its outcome change under assumptions A42.", "Report C11 concludes that Birch-11's intervention caused its outcome change under assumptions A11."),
("Does the record say implementation of North-42's change was judged worthwhile?", "North-42 and Birch-11 are distinct proposed changes, not aliases.", "Decision D42 weighs costs and benefits and recommends implementing North-42.", "Decision D11 weighs costs and benefits and recommends implementing Birch-11."),
("Does the record establish reproduction of North-42's effect by an independent team on fresh units?", "Cedar conducted the original study on N1; Pine has no shared members or delegated role. N2 is disjoint from N1.", "Pine reproduced North-42's effect on N2.", "Pine reproduced North-42's effect by reanalysing N1."),
("Does supplied validation report North-42's effect meeting Material-8 in South?", "North and South are disjoint populations; Material-8 and its unit are identical in both.", "V42 applies North-42's intervention to South and reports its effect meets Material-8 there.", "V42 applies North-42's intervention to North and reports its effect meets Material-8 there."),
("Does the evidence establish that Alden-42 applied both predeclared corrections C1 and C2?", "The complete predeclared correction set is {C1,C2}. C1,C2,C3 are distinct. This execution ledger is complete for Alden-42.", "The ledger records C1 and C2 as applied.", "The ledger records C1 and C3 as applied."),
("Does the evidence record ethics approval of the project that produced North-42?", "North-42 belongs to P42; Birch-11 belongs to distinct P11. Approval does not transfer between them.", "Committee E approved P42 before its start.", "Committee E approved P11 before its start."),
("Does the evidence establish that every required cell in Alden-42's frozen input table has a recorded value?", "D42 has expected rows R1 through R100 and required fields latency_before and latency_after. The audit inspected all 200 required cells. An empty cell is a missing value even when its row exists.", "All 100 expected rows are present; the complete audit reports 200 populated and 0 empty required cells.", "All 100 expected rows are present; the complete audit reports 199 populated and 1 empty required cells."),
("Is a power calculation supplied for Alden-42's named test and sampling design?", "Alden-42 uses MeanShift-42 with S42; Birch-11 uses distinct MeanShift-11 with S11.", "W42 supplies a power calculation for MeanShift-42 under S42 at its declared target effect.", "W11 supplies a power calculation for MeanShift-11 under S11 at its declared target effect.")],
'assignment': [
("Does the evidence establish exactly one editable source that can affect max_workers on the next Cedar-42 resolution?", "This question counts editable sources, not individual edits or alternative values. A and Z are distinct sources.", "The exhaustive next-resolution dependency record names only A as editable and able to affect max_workers.", "The exhaustive next-resolution dependency record names A and Z as editable and able to affect max_workers."),
("Does the evidence establish that a human typed candidate input A?", "A and Z are distinct input events, with no shared authorship inference.", "The provenance log records a human typing A.", "The provenance log records a human typing Z."),
("Does the operator guide recommend value 8 for max_workers at Cedar-42's resolution boundary?", "The guide explicitly scopes recommendations to this setting and boundary.", "The guide recommends max_workers value 8 for Cedar-42.", "The guide recommends max_workers value 12 for Cedar-42."),
("Does the supplied review judge Cedar-42's configuration secure under threat model M?", "Cedar-42 and Birch-11 are distinct configurations; conclusions do not transfer. This asks what the review says, not absolute security.", "Review S42 judges Cedar-42 secure under M.", "Review S11 judges Birch-11 secure under M."),
("Does the evidence guarantee the next resolution will produce max_workers value 8?", "The current resolution produced 8. A guarantee here must constrain all inputs and the resolver that determine the next value.", "The case stipulates unchanged complete inputs, resolver and boundary, with deterministic execution next time.", "The case stipulates an unchanged resolver and boundary next time, but leaves the candidate input for max_workers unspecified."),
("Does the evidence establish that source A has a globally unique identifier with retained immutable content for the registry's declared retention period?", "A and Z are distinct events. Registry G owns an exclusively reserved global namespace. Uniqueness alone does not establish retention or resolvability.", "Registry G assigns A identifier G:A and guarantees unique resolution to its retained immutable content for the declared retention period.", "Registry G assigns Z identifier G:Z and guarantees unique resolution to its retained immutable content for the declared retention period."),
("Does the evidence give the receiving agent permission to change Cedar-42's configuration?", "Cedar-42 and Birch-11 have distinct permission scopes; grants do not transfer.", "The administrator grants this receiving agent permission to change Cedar-42's configuration.", "The administrator grants this receiving agent permission to change Birch-11's configuration."),
("Does the evidence establish that resolved max_workers differs from its default at this boundary?", "The handoff resolves max_workers to 8 by assignment. Rule R is the fallback rule at that exact boundary.", "R's default is 12.", "R's default is 8."),
("Does the evidence establish that Cedar-42's resolved max_workers value was written successfully to disk?", "A successful resolution is not a disk-write receipt; Cedar-42 and Birch-11 are different runs.", "Commit log L42 records Cedar-42's resolved max_workers value written successfully to disk.", "Commit log L11 records Birch-11's resolved max_workers value written successfully to disk."),
("Does the evidence establish successful completion of every Cedar-42 stage after configuration resolution?", "Resolution and later execution stages are separate. Cedar-42 and Birch-11 are distinct runs.", "Execution report E42 records successful completion of all Cedar-42 stages after resolution.", "Execution report E11 records successful completion of all Birch-11 stages after resolution.")],
'latest': [
("Does the record establish that release line Other was closed at 10:00?", "Cedar, Other and Birch are distinct sequences; closures do not transfer.", "Signed record C closes Other at 10:00 UTC on 25 September 2026.", "Signed record C closes Birch at 10:00 UTC on 25 September 2026."),
("Does the case guarantee that Cedar can never be reopened after closure?", "Closure and permission to reopen are separate. Assume the explicit rule is authoritative within this hypothetical system.", "Cedar's immutable charter prohibits every future reopening and cannot be overridden or amended.", "Cedar's charter prohibits reopening until 1 October 2026, without restricting later reopening."),
("Does the record establish D10 as an admitted member of Cedar?", "D10 is a draft identifier; Cedar and Birch are distinct sequences.", "Admission receipt A admits D10 to Cedar.", "Admission receipt A admits D10 to Birch."),
("Does the evidence establish that R7 passed safety check S?", "R7 and R8 are distinct items; S is a named bounded check, not a general safety guarantee.", "Review V records R7 passing S.", "Review V records R8 passing S."),
("Does the evidence establish that R7 arrived by its delivery deadline?", "R7's inclusive deadline was 12:00 UTC on 25 September 2026. The clock and arrival receipt use that time standard.", "Receipt D records R7 arriving at 11:59 UTC that day.", "Receipt D records R7 arriving at 12:01 UTC that day."),
("Does the record grant the receiving agent permission to publish R7?", "R7 and R8 are different items; this permission is item-specific.", "The release authority grants this agent permission to publish R7.", "The release authority grants this agent permission to publish R8."),
("Does the record establish a maximum of twenty admitted members for Cedar?", "Cedar and Birch are different sequences. The stated charter limit is exhaustive and operative.", "The charter caps Cedar at twenty admitted members.", "The charter caps Birch at twenty admitted members."),
("Does the record establish that branches East and West belong to the same sequence?", "East, West and North are distinct branch identifiers; no implicit merge or alias is assumed.", "The charter explicitly places East and West in one sequence.", "The charter explicitly places East and North in one sequence."),
("Does separate evidence establish that no member of finite candidate set F has higher quality than R7 under criterion Q?", "F, Q and R7 are fixed; Q orders quality. This asks about the comparison proof, not whether sequence closure proves quality.", "A complete comparison proof records R7 as maximal under Q over F.", "A complete comparison proof records R8 above R7 under Q, with both in F."),
("At the reporting time of 17:00, does the record establish an admission to Cedar after the handoff's 09:00 observation?", "All times are UTC on 25 September 2026. Cedar and Birch are distinct. A later admission does not falsify the earlier as-of claim.", "The retained event log records an admission to Cedar at 16:00.", "The retained event log records an admission to Birch at 16:00.")]
}

audit={'kind':'ainglish.preparation-audit.v1','source_file_sha256':hashlib.sha256(OLD.read_bytes()).hexdigest(),'families':{},'no_reader_calls':True}
rendered={}
for family,pairs in specs.items():
    base=old['balanced_auxiliary_controls'][family][0]
    audit['families'][family]={arm:sum(('yes' if 'Additional case record:' in x[arm] else 'no')==x['answer'] for x in old['balanced_auxiliary_controls'][family]) for arm in ['english','ainglish']}
    items=[]
    for i,(question,shared,positive,negative) in enumerate(pairs,1):
        for record,answer in ((positive,'yes'),(negative,'no')):
            row={'id':f'{family}-review-v3-{i:02d}-{len(items)%2}','cluster_id':f'{family}-review-v3-{i:02d}',
                 'question':question,'options':['yes','no'],'answer':answer,
                 'answer_semantics':'no means not established by supplied evidence, not necessarily false in reality',
                 'purpose':'authored auxiliary review control, not target measurement or qualification receipt'}
            for arm in ['english','ainglish']:
                text=base[arm].replace('finding finding','finding').replace('Finding finding','Finding')
                text=text.replace('No study-design or causal guarantee is supplied.','The handoff alone asserts the named outcomes; additional records may supply separate evidence.')
                text=text.replace('Record only what the handoff establishes, at its own time.','The handoff speaks at its own time; separately supplied case records can establish additional facts at their stated times.')
                context,handoff=text.split('\n\nHandoff:\n')
                row[arm]=context+'\nCase facts: '+shared+'\nAdditional case record: '+record+'\nOnly the supplied records bear on this question; do not invent missing premises.\n\nHandoff:\n'+handoff
            assert row['english'].split('\n\nHandoff:')[0]==row['ainglish'].split('\n\nHandoff:')[0]
            assert all(row[arm].count('Additional case record:')==1 for arm in ['english','ainglish'])
            items.append(row)
    assert Counter(x['answer'] for x in items)=={'yes':10,'no':10}
    assert len({x['cluster_id'] for x in items})==10
    rendered[family]=items
    audit['families'][family]['v3_prefix_only_correct']=10
result={'kind':'ainglish.language-review-controls.v3','measurement':False,'launch_approved':False,
        'holds_unchanged':True,'scientific_reader_calls':0,'items':rendered,
        'limits':['Authored teaching/review examples, not independently sampled worlds.',
                  'Ten paired clusters per family; do not count sixty independent situations.',
                  'Names, record order, question targeting and response order still need counterbalancing in a final study.',
                  'Positive evidence is stipulated within each toy case, not a real-world empirical finding.',
                  'Original pinned drafts and every filed measurement remain unchanged.']}
(ROOT/'controls-v3.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
(ROOT/'control-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
print('RENDERED',sum(map(len,rendered.values())),'review cases; no inference')
