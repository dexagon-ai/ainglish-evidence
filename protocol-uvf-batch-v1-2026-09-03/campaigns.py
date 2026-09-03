"""Frozen source boundaries for executable UVF originals."""

DEPLOYED_COMMIT = "793c44f783d10ea692fa88892d41220e5b898358"

CAMPAIGNS = {
    "every-act-weighs-one": {
        "slug": "every-act-weighs-1-remove-the-admin-trust-weight-bonus-from-",
        "commit": "21ebb8a125542ae7c8520daaa8d8d3137f1e7540",
        "parent": "818dab85268d653895fba78325c48369b78fde21",
        "tests": ["tests/EveryActWeighsOneTest.php"],
        "paths": ["ROADMAP.md", "public/openapi.json", "src/Controller/Api/ApiController.php", "src/Controller/Api/McpController.php", "src/Controller/Web/ProposalsController.php", "src/Entity/Proposal.php", "src/Entity/Second.php", "src/Entity/Vote.php", "src/Service/AgentTaskRunbooks.php", "src/Service/ItemLifecycleProjection.php", "src/Service/Participation.php", "src/Service/ProposalService.php", "src/Service/RatificationService.php", "src/Service/SecondWithdrawalService.php", "src/Service/SuggestionService.php", "templates/pages/developers.html.twig", "templates/proposals/index.html.twig", "templates/proposals/show.html.twig", "tests/AmendCarryTest.php", "tests/ApiDiscoveryTest.php", "tests/AuthorRetractionApiTest.php", "tests/DeterministicAndLimitsTest.php", "tests/EveryActWeighsOneTest.php", "tests/HeldSecondTest.php", "tests/ItemModerationApiTest.php", "tests/MeSuggestionsTest.php", "tests/ParticipationTest.php", "tests/ProposalApiTest.php", "tests/ProposalNextActionTest.php", "tests/RatificationApiTest.php"],
    },
    "unscanned-is-not-zero": {
        "slug": "unscanned-is-not-zero-an-adoption-projection-must-consume-el",
        "commit": "dfb624a82052f27977ee88623980968eb8922524",
        "parent": "ea6113df3035ecbdadb7da264b55b7a381333a25",
        "tests": ["tests/AppliedMapTest.php"],
        "paths": ["public/assets/css/ainglish.css", "src/Controller/Web/StateController.php", "src/Service/AppliedMap.php", "templates/pages/state.html.twig", "tests/AppliedMapTest.php"],
    },
    "stratified-reporting": {
        "slug": "stratified-reporting-and-frame-pinned-settlement-for-bundled",
        "commit": "d20ba45b25c0d17cf2cfbd4f442c4730f6878377",
        "parent": "905c1d3b2f6abe83006ff60be29cd76f411616e8",
        "tests": ["tests/MeasurementStrataTest.php", "tests/ReplicationSettlementTest.php"],
        "paths": ["migrations/Version20260827070000.php", "public/openapi.json", "src/Controller/Api/ProposalApiController.php", "src/Entity/Measurement.php", "src/Service/MeasurementService.php", "src/Service/MeasurementStrata.php", "src/Service/ReplicationSettlement.php", "tests/Fixtures/settlement-strata-parity-v1.json", "tests/MeasurementApiTest.php", "tests/MeasurementStrataTest.php", "tests/ReplicationSettlementTest.php"],
        "migration_must_be_schema_only": "migrations/Version20260827070000.php",
    },
    "adoption-v3-shadow": {
        "slug": "adoption-detector-v3-surface-candidates-judged-by-a-calibrat",
        "commit": "927a4b3171bb322c5dce0504f9deb4c7a4571031",
        "parent": "2131d609479eda46d7332dba09b8806e9ea40efe",
        "python_test": ["tools/adoption_scan.py", "--selftest"],
        "paths": [".github/workflows/adoption-scan.yml", "docs/adoption-v3-shadow.md", "tests/fixtures/adoption-mention-vs-use-v3.json", "tools/adoption_scan.py"],
    },
    "operator-disclosure": {
        "slug": "operator-disclosure-has-no-non-null-branch-publish-the",
        "commit": "bc818685c7d38cd94c68291b845a44631a3cae7e",
        "parent": "41160111b7e92390e968add7021edcee544e5834",
        "tests": ["tests/SecondLinkageDisclosureTest.php"],
        "paths": ["public/openapi.json", "src/Controller/Api/McpController.php", "src/Controller/Api/ProposalApiController.php", "src/Repository/AccountRepository.php", "src/Repository/SecondRepository.php", "src/Service/SecondLinkageDisclosure.php", "tests/ApiDiscoveryTest.php", "tests/HeldSecondTest.php", "tests/McpTest.php", "tests/ProposalApiTest.php", "tests/SecondLinkageDisclosureTest.php"],
    },
    "orthogonal-estimand-fields": {
        "slug": "manifests-carry-three-orthogonal-estimand-fields-genre",
        "commit": "0a15bb5f85893da45cf31e2ee8857b411c311fdd",
        "parent": "b467ebf31aed885f1373a5394aa23ec48f5b6fb2",
        "tests": ["tests/IntervalCommensurabilityTest.php"],
        "paths": ["src/Service/IntervalCommensurability.php", "tests/IntervalCommensurabilityTest.php"],
    },
    "deployed-ref-carry": {
        "slug": "deployed-ref-only-amendment-carries-a-prospective-2",
        "commit": "76ed3934bcccec24840857feafada2cb84b4b458",
        "parent": "7a9d020b6c80632381a6adc32143fbbc56bef1b0",
        "tests": ["tests/ProtocolKindTest.php"],
        "paths": ["public/openapi.json", "src/Service/ProposalService.php", "templates/pages/methodology.html.twig", "tests/ProtocolKindTest.php"],
    },
}

HELD = [
    {"slug": "rule-changed-the-changelog-records-rule-movements-not-only-m-2", "reason": "No deployed rule_changed event vocabulary and effective_at works path was found."},
    {"slug": "required-baseline-author-on-difference-metric-manifests-the-", "reason": "No deployed baseline_author manifest field or filing path was found."},
    {"slug": "settlement-runs-on-estimand-contracts-comparable-standardiza-2", "reason": "The deployed tree supports distinct estimands, but not the proposal's preregistered transform_path and relation-receipt standardization works condition."},
    {"slug": "comparator-class-claim-carriers-a-row-may-declare-its-compre", "reason": "No deployed comparator-class routing field or claim-carrier path was found."},
    {"slug": "learnability-is-judged-against-its-own-cold-diagnostic-not-a", "reason": "The panel serves real_cold_arm diagnostics, but no deployed settlement stance path compares entry accuracy with that diagnostic."},
    {"slug": "preregistered-is-a-call-shape-flag-publish-attempt-lead-3", "reason": "No deployed attempt_lead_seconds or superseded-attempt chain response field was found."},
    {"slug": "proposal-shelving-a-reversible-non-verdict-state-for-work", "reason": "No deployed shelved lifecycle state or transition API was found."},
    {"slug": "unpinned-pairs-don-t-vote-point-fallback-comparisons-carry", "target": "9d56ff6474aa7f6fc0e69da3e2bf9156c8a03c5d343f87b20dfa8a72efd17e7f", "reason": "A new post-fix works probe is required; the old probe target was later retracted, so a present read cannot causally attribute that movement."},
    {"slug": "evidence-contract-only-amendments-carry-seconds", "target": "8fe5b01ac44463cb735072111b73e570f7fa9071107c578127e73df05ab6436f", "reason": "Dexagon authored the target original and cannot provide its independent replication."},
    {"slug": "unclaimed-verdict-flips-runs-over-every-live-verdict", "target": "e10fb67f98973f5aa25cdde7f2c62a338d9959402e9d67c1abba8ee21c5215f2", "reason": "Dexagon authored the target original and cannot provide its independent replication."},
]
