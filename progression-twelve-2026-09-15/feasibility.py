"""Offline planning and resolution audit. No inference, fitting, seed search or writes to Ainglish."""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def zero_error_upper(n,alpha=.05):
    if n<=0 or not 0<alpha<1: raise ValueError('Invalid binomial reference inputs')
    return -math.expm1(math.log(alpha)/n)

def best_case_fixed_panel_lower(n_by_reader,alpha=.05,forms=1):
    """Bonferroni arm bounds, equal-reader contrast; ideal all-success illustration only.

    Each reader contributes its own A lower minus E upper. With perfect results, E upper=1.
    The denominator is independent trials PER ARM PER READER, not the pooled number of calls.
    These assumptions are not automatically true of a generated vignette bank.
    """
    tail=alpha/(2*len(n_by_reader)*forms)
    return 100*sum(math.expm1(math.log(tail)/n) for n in n_by_reader)/len(n_by_reader)

def choose_assignment():
    assignment=json.loads((REPO/'language-participation-2026-09-15/choose-any-assignment/assignment.json').read_text())
    mapping=assignment['mapping']
    assert hashlib.sha256(canonical(mapping)).hexdigest()=='d4c1c6aa85abd335bd04ce996a0c4f1e78e14b92aaa6036568b2eb71a29c6c00'
    old=json.loads((REPO/'choose-any-completion-2026-09-14/fresh-bank-v2/planned-cells.json').read_text())['cells']
    by=defaultdict(Counter)
    for cell in old:
        # Arm allocation depends on unchanged reader, item ID and panel seed, not requested form.
        by[mapping[cell['world_id']]][cell['reader']+'/'+cell['arm']]+=1
    result={}
    for form,counts in sorted(by.items()):
        readers=sorted({name.rsplit('/',1)[0] for name in counts})
        a_total=sum(counts[r+'/ainglish'] for r in readers)
        e_total=sum(counts[r+'/english'] for r in readers)
        mix={r:counts[r+'/ainglish']/a_total-counts[r+'/english']/e_total for r in readers}
        # Algebraic stress case only: one reader is always correct and another always wrong,
        # identically in both arms. This is not a simulated or observed model outcome.
        result[form]={'planned_cells':dict(sorted(counts.items())),
            'worst_absolute_composition_delta_pp_with_zero_within_reader_effect':100*sum(max(0,w) for w in mix.values()),
            'reader_mixture_weight_differences':mix,
            'best_case_equal_reader_NI_lower_pp':best_case_fixed_panel_lower([counts[r+'/ainglish'] for r in readers]),
            'all_success_is_hypothetical':True}
    return {'mapping_sha256':hashlib.sha256(canonical(mapping)).hexdigest(),
            'status':'ASSIGNMENT_AUDIT_ONLY_COMPARATOR_AND_AUTHOR_HOLD_REMAIN',
            'panel_seed_preserved':2026091451,'form_counts':dict(Counter(mapping.values())),
            'worlds':len(mapping),'forms':result,'rerolls':0,'reader_calls':0}

def verified_resolution():
    base=REPO/'overnight-decisions-2026-09-14/verified-replication'
    cells=json.loads((base/'runspec.json.attempt-0b9fab88-e060-4070-bb52-d33abb813771.cells.json').read_text())['rows']
    original={'paid-missing-receipt':-33.33,'unpaid-invoice':-29.16,'stale-check':-25,
              'normal-settled':-33.33,'ledger-refuted':-33.34,'verified-settled-coexistence':-54.17}
    counts=defaultdict(Counter)
    for c in cells: counts[c['strata']['branch']][c['arm']]+=1
    out=[]
    for branch,count in counts.items():
        tolerance=max(.02,.1*abs(original[branch]))
        steps={arm:100/n for arm,n in count.items()}
        out.append({'stratum':branch,'actual_scored_cells_by_arm':dict(count),
            'one_changed_answer_pp_by_arm':steps,'source_point_tolerance_pp':tolerance,
            'an_arm_single_answer_exceeds_tolerance':any(step>tolerance for step in steps.values())})
    return {'source':'4a928d0df73a9ff52660354302765eb9288fd110b4cadc726fdb853dddf45b12',
            'replication':'aa145ceec71d126aefe1ce2e9fb83bf2be9cefa361b714d0a85d0cbb289a9581',
            'rows':out,'scope':'Observed design resolution, not a re-score or invalidation. Aggregate intervals overlap; all six required strata disagree under the current rule.'}

def report():
    return {'kind':'ainglish.study-feasibility-audit.v1','observed_reader_calls':0,
        'zero_error_IID_reference':[{'independent_trials':n,'upper_95_percent_error_probability':zero_error_upper(n)} for n in [8,16,32,40,59,64,72,80,100,128,160]],
        'perfect_equal_reader_IID_reference':[{'independent_trials_per_arm_per_reader':n,
            'lower_95_percent_delta_pp_one_form':best_case_fixed_panel_lower([n,n]),
            'lower_95_percent_delta_pp_two_forms_familywise':best_case_fixed_panel_lower([n,n],forms=2)} for n in [16,32,36,40,72,86,99,128]],
        'choose_any':choose_assignment(),'verified_state':verified_resolution(),
        'limits':['No result-dependent sample expansion or reader/seed selection.',
                  'Binomial references require independent exchangeable trials; authored frames and paired contexts can be correlated.',
                  'These conservative references are not a proof that every valid NI method must fail at the same N.',
                  'A fixed-panel contrast is not a population inference over all models.',
                  'Official CAD bootstrap intervals, declared point criteria, and prospective NI uncertainty are distinct.',
                  'No prospective calculation overrides current server rules, author decisions or independent confirmation.']}

if __name__=='__main__':
    assert zero_error_upper(59)<.05<zero_error_upper(58)
    assert best_case_fixed_panel_lower([86,86])> -5
    assert best_case_fixed_panel_lower([85,85])< -5
    data=report()
    (ROOT/'FEASIBILITY.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))
