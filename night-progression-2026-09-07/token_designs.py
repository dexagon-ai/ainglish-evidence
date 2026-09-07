"""Three prospective eight-pair replications, no encoding in this module."""


def clock():
    return [
        {'english':'Issue at most 24 tickets in each clock hour; the counter resets at :00, so 24 at 09:59 and 24 at 10:00 are both accepted.',
         'ainglish':'Issue at most 24 tickets per-clock(hour); 24 at 09:59 and 24 at 10:00 are both accepted.'},
        {'english':'Issue at most 24 tickets in any 60-minute span; 24 at 09:59 and 24 at 10:00 is a breach.',
         'ainglish':'Issue at most 24 tickets per-any(60m); 24 at 09:59 and 24 at 10:00 is a breach.'},
        {'english':'Each archivist may seal at most 80 bundles in each UTC calendar day; bursts at 23:40Z and 00:15Z spend two days\' quota and break nothing.',
         'ainglish':'Each archivist may seal at most 80 bundles per-clock(day@UTC); bursts at 23:40Z and 00:15Z spend two days\' quota and break nothing.'},
        {'english':'Start the scanner at most six times in any 60-minute span, or the seventh start is throttled.',
         'ainglish':'Start the scanner at most six times per-any(60m), or the seventh start is throttled.'},
        {'english':'Send at most 16 notices per clock hour; the counter restarts at the hour boundary.',
         'ainglish':'Send at most 16 notices per-clock(hour).'},
        {'english':'Send at most 16 notices in any 60-minute window; sliding window enforcement.',
         'ainglish':'Send at most 16 notices per-any(60m).'},
        {'english':'Each station may upload at most 400 images per UTC day; midnight boundary resets the counter.',
         'ainglish':'Each station may upload at most 400 images per-clock(day@UTC).'},
        {'english':'Each station may upload at most 400 images in any 24-hour span; rolling window.',
         'ainglish':'Each station may upload at most 400 images per-any(24h).'},
    ]


def may_not():
    return [
        {'english':'The courier is forbidden to open the crate; this makes no prediction.',
         'ainglish':'The courier may-not-as-prohibition open the crate.'},
        {'english':'The inspection might not finish; this imposes no rule.',
         'ainglish':'The inspection may-not-as-possibility finish.'},
        {'english':'Guests are forbidden to enter the laboratory; this makes no prediction about whether they will try.',
         'ainglish':'Guests may-not-as-prohibition enter the laboratory.'},
        {'english':'The parcel might not arrive in time; this imposes no rule about whether it should.',
         'ainglish':'The parcel may-not-as-possibility arrive in time.'},
        {'english':'The assistant is forbidden to circulate the minutes; this makes no prediction about their intent.',
         'ainglish':'The assistant may-not-as-prohibition circulate the minutes.'},
        {'english':'The scan might not succeed on the first attempt; this imposes no rule about retries.',
         'ainglish':'The scan may-not-as-possibility succeed on the first attempt.'},
        {'english':'The recorder is forbidden to overwrite the archive; this makes no prediction about whether it tries.',
         'ainglish':'The recorder may-not-as-prohibition overwrite the archive.'},
        {'english':'The delivery might not complete before the cutoff; this imposes no rule about the deadline.',
         'ainglish':'The delivery may-not-as-possibility complete before the cutoff.'},
    ]


def repeat():
    return [
        {'english':'Discard samples that are expired and reagents that are expired.',
         'ainglish':'Discard expired samples and expired reagents.'},
        {'english':'Archive labels without restricting their age and manifests that are outdated.',
         'ainglish':'Archive labels and outdated manifests.'},
        {'english':'Escalate reports that are urgent and queries whether or not they are urgent.',
         'ainglish':'Escalate the urgent reports and the queries.'},
        {'english':'Separate processed specimens from unprocessed specimens.',
         'ainglish':'Separate processed specimens and unprocessed specimens.'},
        {'english':'Review applications that are pending and applications that are approved.',
         'ainglish':'Review pending applications and approved applications.'},
        {'english':'Keep scans that are old and photographs that are new.',
         'ainglish':'Keep old scans and new photographs.'},
        {'english':'Compare inventories that are stale and inventories that are current.',
         'ainglish':'Compare stale inventories and current inventories.'},
        {'english':'List editions that are old and editions that are new.',
         'ainglish':'List old editions and new editions.'},
    ]

GENERATORS={'clock':clock,'may-not':may_not,'repeat':repeat}
