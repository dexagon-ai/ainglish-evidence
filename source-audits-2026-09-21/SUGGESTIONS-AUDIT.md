# Decision-view wording audit: no ranking change warranted

Reviewed 21 September2026 against live decision suggestions and Symfony638
merged source (`SuggestionBrief.php`, `SuggestionBriefTest.php`). Production
still reported70efb055 at this check. The decision-view logic under examination
already appears in the live envelope.

The questioned combination is **intentional, not contradictory**:

- `class=last_missing_requirement`: exactly one declared metric remains open and
  the offered source targets that metric.
- `completes_requirement=no`: confirmation of that specific source would not
  satisfy the metric's requirement (neutral, opposing or unresolved evidence).

Live examples include may-as-permission/may-as-possibility66911e2d (neutral),
proxy519ea971 (unresolved), and it(ref)41f245dd (unresolved). Their requirement
remains in `remaining_if_source_confirmed`. The envelope explicitly explains
that the class does not mean one task away from passing. Source selection,
operator eligibility, qualification, scope and preparation remain separate.

The focused PHPUnit suite passes **30 tests /251 assertions**. Its sign-invariance
regression checks supports/neutral/unresolved/opposes/unknown with identical
structural priority and different completion outcomes. Tests also preserve offer
identity and do not invent eligibility. Demoting adverse work to favour positive
results would introduce selection bias and obstruct honest non-adoption.

**Disposition: no patch or new PR for this alleged contradiction.** Existing
explanations are adequate for this exact case. A different, real limitation is
that advisory completion projections do not independently audit whether a legacy
source actually tested all of a proposal's prose promises, used the right
comparator, or retained a scoreable instrument. Our source review found concrete
examples. That cannot safely be repaired by guessing from generic signs or
keyword labels; the proposed comparator-class policy remains prospective and
unactivated. Correct source-specific documentation and author decisions first.
