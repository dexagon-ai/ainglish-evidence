"""Portable reference functions from this repository's calendar_design.py.

Source: fee5d860f2bd202ca4a9956a9b09ba7f364807d6,
progression-audits-2026-09-22/calendar_design.py. No independent-person claim.
"""
from datetime import timedelta
from math import comb

def oracle_arithmetic(anchor, target, weekstart, form):
    if form == 'next-up':
        distance = (target - anchor.weekday()) % 7 or 7
    else:
        distance = 7 - (anchor.weekday() - weekstart) % 7 + (target - weekstart) % 7
    return anchor + timedelta(days=distance), distance

def matrix(repeats=2):
    return [dict(form=form, weekstart=start, anchor_weekday=a, target_weekday=t,
                 repetitions=repeats, weight_per_world=1/(84*repeats))
            for form in ('next-up', 'next-week') for start in (0, 6)
            for a in range(7) for t in range(7)
            if (t-start) % 7 > (a-start) % 7]

def cdf(k, n, p):
    return sum(comb(n, j) * p**j * (1-p)**(n-j) for j in range(k+1))
