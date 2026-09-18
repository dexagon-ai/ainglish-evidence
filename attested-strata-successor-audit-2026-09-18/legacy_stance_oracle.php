<?php

declare(strict_types=1);

// Read-only oracle: execute the existing register's real stanceFor() on frozen
// documents. No kernel, database, network, fixture insertion or mocked stance.
// Usage: php legacy_stance_oracle.php /path/to/symfony /path/to/packet
$root = realpath($argv[1] ?? '') ?: throw new RuntimeException('Symfony path required');
$packet = realpath($argv[2] ?? '') ?: throw new RuntimeException('Packet path required');
$loader = require $root . '/vendor/autoload.php';
$loader->addPsr4('App\\', $root . '/src', true);

$service = (new ReflectionClass(App\Service\MeasurementService::class))->newInstanceWithoutConstructor();
(new ReflectionProperty($service, 'protocols'))->setValue($service, new App\Service\MeasurementProtocols());
// stanceFor() uses no repository methods. The unconstructed repository is never
// called; leaving other service dependencies unset makes accidental I/O fail.
$repository = (new ReflectionClass(App\Repository\MeasurementRepository::class))->newInstanceWithoutConstructor();
$readiness = new App\Service\EvidenceReadiness($service, $repository);
$observations = [];
foreach (glob($packet . '/raw/proposals/*.json') as $path) {
    $proposal = json_decode(file_get_contents($path), true, flags: JSON_THROW_ON_ERROR);
    foreach ($proposal['evidence_contract']['prerequisites'] ?? [] as $prerequisite) {
        if (!is_array($prerequisite)
            || ($prerequisite['metric'] ?? null) !== 'comprehension_accuracy_delta'
            || !array_key_exists('at_least', $prerequisite)) {
            continue;
        }
        foreach ($proposal['measurements'] ?? [] as $row) {
            if ($row['metric'] !== 'comprehension_accuracy_delta' || $row['evidence_state'] !== 'valid') {
                continue;
            }
            $measurement = new App\Entity\Measurement();
            $measurement->metric = $row['metric'];
            $measurement->value = (float) $row['value'];
            $measurement->valueLo = $row['value_lo'];
            $measurement->valueHi = $row['value_hi'];
            $measurement->resolutionBound = $row['resolution_bound'];
            $measurement->evidenceState = $row['evidence_state'];
            $observations[] = [
                'proposal' => $proposal['public_id'],
                'hash' => $row['manifest_hash'],
                'value' => $measurement->value,
                'resolution_bound' => $measurement->resolutionBound,
                'evidence_state' => $measurement->evidenceState,
                'generic_stance' => $service->effectiveStance($measurement),
                // Reflection also works at 5723faa, where this same method body
                // was private. #627 made it public without changing its body.
                'legacy_prerequisite_stance' => (new ReflectionMethod($readiness, 'stanceFor'))->invoke($readiness, $measurement, $prerequisite),
            ];
        }
    }
}
usort($observations, static fn (array $a, array $b): int => strcmp($a['hash'], $b['hash']));
$files = [];
foreach (['src/Service/EvidenceReadiness.php', 'src/Service/MeasurementService.php', 'src/Service/MeasurementProtocols.php', 'src/Entity/Measurement.php'] as $file) {
    $files[$file] = hash_file('sha256', $root . '/' . $file);
}
echo json_encode([
    'kind' => 'ainglish.read-only-legacy-stance-oracle.v1',
    'php_version' => PHP_VERSION,
    'source_sha256' => $files,
    'observations' => $observations,
    'scope' => 'Existing unkeyed stanceFor only; not a candidate deploy, whole-register replay, or protocol measurement.',
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR), "\n";
