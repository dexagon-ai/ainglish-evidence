import unittest
from datetime import datetime, timedelta, timezone
from oracles import calendar_breaks, sliding_breaks, stock_and_distinct_flow, incident_commitments

def at(value):return datetime.fromisoformat(value.replace('Z','+00:00'))

class Oracles(unittest.TestCase):
    def test_boundary_bursts_differ(self):
        events=[at('2026-09-07T12:59:00Z'),at('2026-09-07T13:00:00Z')]
        self.assertFalse(calendar_breaks(events,1,'hour','UTC'))
        self.assertTrue(sliding_breaks(events,1,timedelta(hours=1)))

    def test_exact_sliding_endpoints(self):
        events=[at('2026-09-07T12:00:00Z'),at('2026-09-07T13:00:00Z')]
        self.assertFalse(sliding_breaks(events,1,timedelta(hours=1)))
        self.assertTrue(sliding_breaks([events[0],events[1]-timedelta(microseconds=1)],1,timedelta(hours=1)))

    def test_short_dst_day_not_a_sliding_day(self):
        events=[at('2026-03-29T00:00:00Z'),at('2026-03-29T23:00:00Z')]
        self.assertFalse(calendar_breaks(events,1,'day','Europe/London'))
        self.assertTrue(sliding_breaks(events,1,timedelta(hours=24)))

    def test_long_dst_day_not_a_sliding_day(self):
        events=[at('2026-10-24T23:00:00Z'),at('2026-10-25T23:00:00Z')]
        self.assertTrue(calendar_breaks(events,1,'day','Europe/London'))
        self.assertFalse(sliding_breaks(events,1,timedelta(hours=24)))

    def test_zero_and_repeated_events(self):
        event=at('2026-09-07T12:00:00Z')
        self.assertFalse(sliding_breaks([],0,timedelta(hours=1)))
        self.assertTrue(sliding_breaks([event],0,timedelta(hours=1)))
        self.assertTrue(sliding_breaks([event,event],1,timedelta(hours=1)))

    def test_distinct_flow_reentry_and_event_multiplicity(self):
        start=at('2026-09-07T08:00:00Z');end=start+timedelta(hours=1)
        events=[(start,0,'A',False),(start+timedelta(minutes=1),1,'A',True),
                (start+timedelta(minutes=2),2,'A',False),(end,3,'A',True)]
        self.assertEqual({'stock_at_cutoff':1,'distinct_departures':1},stock_and_distinct_flow({'A'},events,end,start,end))

    def test_right_endpoint_excluded_from_flow_included_in_stock(self):
        start=at('2026-09-07T08:00:00Z');end=start+timedelta(hours=1)
        self.assertEqual({'stock_at_cutoff':0,'distinct_departures':0},stock_and_distinct_flow({'A'},[(end,0,'A',False)],end,start,end))

    def test_arrivals_do_not_count_as_departures(self):
        start=at('2026-09-07T08:00:00Z');end=start+timedelta(hours=1)
        self.assertEqual({'stock_at_cutoff':1,'distinct_departures':0},stock_and_distinct_flow(set(),[(start,0,'A',True)],end,start,end))

    def test_future_changes_do_not_change_earlier_stock(self):
        start=at('2026-09-07T08:00:00Z');end=start+timedelta(hours=1)
        self.assertEqual(1,stock_and_distinct_flow({'A'},[(end,0,'A',False)],start,start,end)['stock_at_cutoff'])

    def test_simultaneous_order_must_resolve(self):
        start=at('2026-09-07T08:00:00Z');end=start+timedelta(hours=1)
        with self.assertRaises(ValueError):stock_and_distinct_flow({'A'},[(start,0,'A',False),(start,0,'A',True)],end,start,end)

    def test_incident_axes_do_not_imply_each_other(self):
        self.assertEqual({'status':'resolved','impact_absent':True,'cause_removed':None},incident_commitments(impact=True))
        self.assertEqual({'status':'resolved','impact_absent':None,'cause_removed':True},incident_commitments(cause=True))
        self.assertEqual({'status':'resolved','impact_absent':True,'cause_removed':True},incident_commitments(impact=True,cause=True))
        self.assertEqual({'status':'resolved','impact_absent':None,'cause_removed':None},incident_commitments())

    def test_unresolved_pin_is_not_a_positive_or_negative_fact(self):
        self.assertEqual({'status':'underspecified','impact_absent':None,'cause_removed':None},incident_commitments(impact=True,cause=True,references_resolve=False))

if __name__=='__main__':unittest.main()
