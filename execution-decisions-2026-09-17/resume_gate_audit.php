<?php
declare(strict_types=1);

// Synthetic arithmetic fixtures, NOT model responses or fileable measurements.
// Usage: php resume_gate_audit.php SYMFONY_CHECKOUT [VENDOR_AUTOLOAD]
// Calls the actual current rules. No database, network, inference or governance writes.
use App\Entity\Measurement;
use App\Service\EvidenceReadiness;
use App\Service\MeasurementProtocols;
use App\Service\MeasurementService;
use App\Service\MeasurementStrata;
use App\Service\ReplicationSettlement;

$root = realpath($argv[1] ?? '') ?: throw new RuntimeException('Supply a Symfony checkout.');
$loader = require ($argv[2] ?? $root.'/vendor/autoload.php');
$loader->setPsr4('App\\', $root.'/src');
$checks = 0;
function check(bool $condition, string $name): void {
    global $checks;
    if (!$condition) { throw new RuntimeException('FAIL: '.$name); }
    ++$checks;
}

// Only the pure stance dependency is needed; no uninitialised repository is called.
$serviceClass = new ReflectionClass(MeasurementService::class);
$service = $serviceClass->newInstanceWithoutConstructor();
$serviceClass->getProperty('protocols')->setValue($service, new MeasurementProtocols());
$readinessClass = new ReflectionClass(EvidenceReadiness::class);
$readiness = $readinessClass->newInstanceWithoutConstructor();
$readinessClass->getProperty('measurementService')->setValue($readiness, $service);
$boundedStance = $readinessClass->getMethod('stanceFor');

function classify(array $strata, float $lo, float $hi): array {
    global $service, $readiness, $boundedStance;
    $m = new Measurement();
    $m->metric = 'comprehension_accuracy_delta';
    $m->arms = ['english' => 0., 'ainglish' => 0., 'chance' => 0.5];
    $m->value = 0.;
    foreach ($strata as &$row) {
        $row['resolution_bound'] = MeasurementProtocols::resolutionBound($row['arms'], $m->metric);
        $m->arms['english'] += $row['share'] * $row['arms']['english'];
        $m->arms['ainglish'] += $row['share'] * $row['arms']['ainglish'];
        $m->value += $row['share'] * $row['value'];
    }
    unset($row);
    $m->valueLo = $lo; $m->valueHi = $hi;
    $m->resolutionBound = MeasurementStrata::resolutionBound(
        $strata, MeasurementProtocols::resolutionBound($m->arms, $m->metric),
    );
    return [
        'strata' => $strata, 'aggregate_arms' => $m->arms, 'value' => $m->value,
        'synthetic_interval' => [$lo, $hi], 'resolution_bound' => $m->resolutionBound,
        'generic_stance' => $service->effectiveStance($m),
        'at_least_zero_stance' => $boundedStance->invoke($readiness, $m, ['at_least' => 0]),
    ];
}
function cell(string $id, float $english, float $ainglish): array {
    return ['id' => $id, 'weight' => 1., 'share' => 0.5,
        'value' => round(100 * ($ainglish - $english), 4),
        'arms' => ['english' => $english, 'ainglish' => $ainglish, 'chance' => 0.5]];
}

$cases = [];
foreach ([
    ['both_perfect', 1., 1., 1., 1., 0., 0., 'unresolved'],
    ['both_high', .95, .97, .95, .97, -5., 9., 'unresolved'],
    ['only_one_policy_at_ceiling', .95, .95, .80, .85, -10., 15., 'unresolved'],
    ['resolvable_equal_points_wide_interval', .85, .85, .85, .85, -20., 20., 'supports'],
    ['resolvable_positive', .80, .95, .80, .95, 5., 25., 'supports'],
    ['resolvable_negative', .85, .80, .85, .80, -20., 10., 'opposes'],
    ['both_at_chance', .50, .50, .50, .50, -20., 20., 'unresolved'],
] as [$name, $e1, $a1, $e2, $a2, $lo, $hi, $expected]) {
    $cases[$name] = classify([cell('resume-core', $e1, $a1), cell('redo-core', $e2, $a2)], $lo, $hi);
    check($cases[$name]['at_least_zero_stance'] === $expected, $name);
}
check($cases['resolvable_equal_points_wide_interval']['generic_stance'] === 'neutral', 'bounded point is not a positive generic interval');

$plan = json_decode(file_get_contents(__DIR__.'/resume-phase-one.json'), true, flags: JSON_THROW_ON_ERROR);
$counts = [];
foreach ($plan['allocation'] as $key => $arms) {
    $policy = explode(':', $key, 2)[0];
    foreach ($arms as $arm => $n) { $counts[$policy][$arm] = ($counts[$policy][$arm] ?? 0) + $n; }
}
check($counts === ['resume-core' => ['english' => 37, 'ainglish' => 27], 'redo-core' => ['english' => 33, 'ainglish' => 31]], 'frozen arm allocation');
$grids = [];
foreach ($counts as $id => $arms) {
    $grids[$id] = [
        'cells' => $arms,
        'one_english_answer_pp' => 100 / $arms['english'],
        'one_ainglish_answer_pp' => 100 / $arms['ainglish'],
        'maximum_english_correct_below_ceiling_if_ainglish_at_ceiling' => (int) ceil(MeasurementProtocols::CEILING * $arms['english']) - 1,
    ];
}
check($grids['resume-core']['maximum_english_correct_below_ceiling_if_ainglish_at_ceiling'] === 33, 'resume ceiling boundary');
check($grids['redo-core']['maximum_english_correct_below_ceiling_if_ainglish_at_ceiling'] === 29, 'redo ceiling boundary');

// A possible count pattern on the frozen grid, not a prediction. Replica arm counts
// are held equal here to isolate a one-answer perturbation; its fresh bank is NOT fixed.
$original = [cell('resume-core', round(31/37, 4), round(25/27, 4)),
             cell('redo-core', round(29/33, 4), round(29/31, 4))];
$replica = [cell('resume-core', round(32/37, 4), round(25/27, 4)), $original[1]];
$originalValue = array_sum(array_column($original, 'value')) / 2;
$replicaValue = array_sum(array_column($replica, 'value')) / 2;
$comparison = ReplicationSettlement::comparison($originalValue, $replicaValue,
    [], [], null, null, $original, $replica);
check(!$comparison['strata'][0]['reproduced_ok'], 'one-answer stratum mismatch');
check($comparison['strata'][1]['reproduced_ok'], 'unchanged stratum matches');
check($comparison['strata'][0]['absolute_difference'] > $comparison['strata'][0]['tolerance'], 'grid exceeds point tolerance');

$files = ['MeasurementProtocols.php', 'MeasurementStrata.php', 'MeasurementService.php',
          'EvidenceReadiness.php', 'ReplicationSettlement.php', 'IntervalCommensurability.php'];
$hashes = [];
foreach ($files as $file) { $hashes[$file] = hash_file('sha256', $root.'/src/Service/'.$file); }
echo json_encode([
    'kind' => 'ainglish.synthetic-current-gate-audit.v1',
    'fileable_language_evidence' => false, 'reader_calls' => 0, 'attempts_minted' => 0,
    'scope' => 'Pure current-rule components, not submission validation, independence, full readiness, ballot eligibility or a power study.',
    'source_file_sha256' => $hashes,
    'cases' => $cases, 'frozen_allocation_grids' => $grids,
    'one_answer_perturbation' => $comparison,
    'interval_scope_note' => 'The point comparison is tested here. The separate observation that aggregate overlap retains this per-stratum point requirement comes from reading ReplicationSettlement::settle; no provenance replay or full filing is claimed.',
    'checks_passed' => $checks,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR)."\n";
