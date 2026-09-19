<?php
declare(strict_types=1);
// OFFLINE SYNTHETIC RULE EXAMPLES, NOT OBSERVED EVIDENCE. No database or API writes.
if ($argc !== 2) {
    fwrite(STDERR, "usage: php audit_resolution.php /path/to/symfony-checkout\n");
    exit(2);
}
$root = realpath($argv[1]);
require $root . '/vendor/autoload.php';
use App\Entity\Measurement;
use App\Service\EvidenceReadiness;
use App\Service\MeasurementProtocols;
use App\Service\MeasurementService;

// Only pure scoring methods are called. Their unrelated persistence dependencies
// are deliberately never constructed or used by this read-only audit.
$service = (new ReflectionClass(MeasurementService::class))->newInstanceWithoutConstructor();
(new ReflectionProperty(MeasurementService::class, 'protocols'))->setValue($service, new MeasurementProtocols());
$readiness = (new ReflectionClass(EvidenceReadiness::class))->newInstanceWithoutConstructor();
(new ReflectionProperty(EvidenceReadiness::class, 'measurementService'))->setValue($readiness, $service);
$cases = [
    ['perfect_tie', 1.0, 1.0, 0.0, 0.0, 'ceiling', 'unresolved'],
    ['high_tie', 0.95, 0.95, -2.0, 2.0, 'ceiling', 'unresolved'],
    ['high_gain', 0.95, 1.0, 1.0, 9.0, 'ceiling', 'unresolved'],
    ['at_cutoff_gain', 0.90, 0.96, 1.0, 11.0, 'ceiling', 'unresolved'],
    ['below_cutoff_gain', 0.89, 0.95, 1.0, 11.0, 'resolvable', 'supports'],
    ['below_cutoff_tie', 0.85, 0.85, -4.0, 4.0, 'resolvable', 'supports'],
    ['informative_loss', 0.95, 0.85, -15.0, -5.0, 'resolvable', 'opposes'],
];
$rows = [];
foreach ($cases as [$name, $en, $ai, $lo, $hi, $expectedResolution, $expectedStance]) {
    $m = new Measurement();
    $m->metric = 'comprehension_accuracy_delta';
    $m->value = round(100 * ($ai - $en), 6);
    $m->valueLo = $lo;
    $m->valueHi = $hi;
    $m->arms = ['english' => $en, 'ainglish' => $ai, 'chance' => 1 / 3];
    $resolution = MeasurementProtocols::resolutionBound($m->arms, $m->metric);
    $stance = $readiness->stanceFor($m, ['at_least' => 0]);
    if ($resolution !== $expectedResolution || $stance !== $expectedStance) {
        throw new RuntimeException("Unexpected live-code rule for $name: $resolution / $stance");
    }
    $rows[] = compact('name', 'en', 'ai', 'lo', 'hi', 'resolution', 'stance');
}
$learn = new Measurement();
$learn->metric = 'learnability';
$learn->value = 0.953125;
$learn->valueLo = 0.85;
$learn->valueHi = 1.0;
$learnStance = $readiness->stanceFor($learn, ['at_least' => 0.95]);
if ($learnStance !== 'supports' || MeasurementProtocols::resolutionBound(null, 'learnability') !== 'not_applicable') {
    throw new RuntimeException('Unexpected learnability reading');
}
$hashes = [];
foreach (['MeasurementProtocols', 'MeasurementService', 'EvidenceReadiness'] as $file) {
    $hashes[$file] = hash_file('sha256', $root . '/src/Service/' . $file . '.php');
}
echo json_encode([
    'kind' => 'synthetic-deployed-rule-audit.v1',
    'not_measurements' => true,
    'source_commit' => 'd85f9316d3ed58a864bd1b0296767211b95c6a73',
    'service_file_sha256' => $hashes,
    'ceiling_constant' => MeasurementProtocols::CEILING,
    'cad_cases' => $rows,
    'learnability_example' => ['value' => $learn->value, 'lo' => $learn->valueLo, 'hi' => $learn->valueHi, 'bounded_stance' => $learnStance],
    'boundary' => 'Rule replay only; no sampled readers, results, intervals, confirmations or governance actions. An illustrative interval is not a statistical calculation.'
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
