"""Model-free semantic prototypes. Not scientific target items or registered evidence."""
from datetime import timedelta
from zoneinfo import ZoneInfo

def sliding_breaks(events, cap, span):
    """Any half-open duration window; equality at opposite endpoints is not overlap."""
    if cap<0 or span<=timedelta(0):raise ValueError('nonnegative cap and positive span required')
    ordered=sorted(events)
    return any(ordered[i+cap]-ordered[i]<span for i in range(len(ordered)-cap))

def calendar_breaks(events, cap, unit, zone):
    """Named-zone day/hour/minute windows; repeated clock hours distinguished by fold."""
    if cap<0:raise ValueError('nonnegative cap required')
    if unit not in ('minute','hour','day'):raise ValueError('prototype covers minute/hour/day only')
    counts={};tz=ZoneInfo(zone)
    for event in events:
        if event.tzinfo is None:raise ValueError('aware event timestamp required')
        local=event.astimezone(tz);key=(local.year,local.month,local.day)
        if unit in ('hour','minute'):key+=(local.hour,local.fold)
        if unit=='minute':key+=(local.minute,)
        counts[key]=counts.get(key,0)+1
    return any(n>cap for n in counts.values())

def stock_and_distinct_flow(initial, events, cutoff, interval_start, interval_end):
    """events=(aware time, declared order, member id, inside-after); interval [start,end)."""
    if interval_start>=interval_end or cutoff<interval_start:raise ValueError('invalid observation interval')
    if len({(t,order) for t,order,_,_ in events})!=len(events):raise ValueError('simultaneous changes need a unique declared order')
    members=set(initial);departed=set();stock=None
    for t,order,member,inside_after in sorted(events):
        if stock is None and t>cutoff:stock=len(members)
        was_inside=member in members
        if interval_start<=t<interval_end and was_inside and not inside_after:departed.add(member)
        if inside_after:members.add(member)
        else:members.discard(member)
    if stock is None:stock=len(members)
    return {'stock_at_cutoff':stock,'distinct_departures':len(departed)}

def incident_commitments(*, impact=False, cause=False, references_resolve=True):
    """Truth commitments only: unasserted is unknown, never a negative assertion."""
    if not references_resolve:return {'status':'underspecified','impact_absent':None,'cause_removed':None}
    return {'status':'resolved','impact_absent':True if impact else None,'cause_removed':True if cause else None}
