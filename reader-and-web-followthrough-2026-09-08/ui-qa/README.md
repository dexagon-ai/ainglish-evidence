# Human reading checks

These are **owned local synthetic display fixtures**, not live proposal observations or human usability validation. No remote model/browser download, production database write or shared GPU interruption was used.

Three UI branches were tested independently against the same deployed base. The fourth website branch adds measured-stage regression coverage without changing production guard semantics. An API `ready` flag means the deterministic ratification screen is clear; it does not mean every declared evidence requirement is complete. The guard was retained, not relaxed.

| Changed view | Viewport cells | Real 400% tab-zoom routes | Result |
| --- | ---: | ---: | --- |
| Language/protocol work scope | 20 | 3 | Pass |
| Cost versus allowance versus confirmation | 8 | 2 | Pass |
| Selected experiment comparison and picker | 8 | 1 | Pass |

Viewports were 320, 390, 768 and 1440 CSS pixels. Additional checks cover keyboard access and visible focus, 2x root-font reflow, forced colours and print. Real browser zoom uses Chromium `tabs.setZoom(4)` with an unchanged 16px root font and 1280 -> 320 CSS-pixel viewport; it is not CSS scaling or pinch zoom.

The comparison/control browser suites also passed 16 journey cells across JavaScript/no-JavaScript, 320/390 mobile, 844×390 landscape and desktop. They exercise native summaries, source identity, escaping, exact experiment selection, control pagination, search, clear/back, nested fragment reveal and exact print-state restoration. At 400% zoom, the test found that a submitted search could be hidden inside the collapsed picker with two selected results; the final template opens the picker for search results, with a PHP regression assertion. Explicit input requests similarly open their parent record without JavaScript.

The retained viewport report predates only these server-side explicit-search/input-open refinements; the final browser interaction, real zoom and full PHP tests include them. Final reading-layout suite: 1,506 tests and 24,741 assertions, no failures, six environment-dependent skips, three pre-existing PHPUnit deprecations. Scope: 1,509 tests / 24,745 assertions. Cost: 1,507 / 24,723. Measured-stage guards: 1,507 / 24,728. CSS shared-ownership contracts pass.

Two initial harness invocations used nonexistent route spellings and the default unrelated `/state` print route in the limited fixture database. Those diagnostic failures were not treated as successful UI cells; the retained reports use the verified routes and scoped print paths. This report does not claim a complete site-wide accessibility certification, independent human review, or deployment of the PRs.

[Mobile comparison](compare-mobile.png) · [Desktop comparison](compare-desktop.png)
