<?php
declare(strict_types=1);

// Isolated domain-method probe. No HTTP, database, persisted rows or inference.
// The stub supplies only fields read by the unmodified upstream methods.
namespace App\Entity {
    class Measurement {
        public string $metric = 'comprehension_accuracy_delta';
        public ?string $resolutionBound = null;
        public ?array $arms = null;
        public float $value = 0.0;
        public ?float $valueLo = null;
        public ?float $valueHi = null;
        public function isEvidenceActive(): bool { return true; }
    }
}
namespace {
    foreach (['ProtocolMeta', 'MeasurementProtocols', 'MeasurementService', 'EvidenceReadiness', 'ReplicationSettlement'] as $name) {
        require $argv[1] . '/' . $name . '.php';
    }
    $protocols = new \App\Service\MeasurementProtocols();
    $msReflection = new \ReflectionClass(\App\Service\MeasurementService::class);
    $ms = $msReflection->newInstanceWithoutConstructor();
    $msReflection->getProperty('protocols')->setValue($ms, $protocols);
    $erReflection = new \ReflectionClass(\App\Service\EvidenceReadiness::class);
    $er = $erReflection->newInstanceWithoutConstructor();
    $erReflection->getProperty('measurementService')->setValue($er, $ms);
    $stanceFor = $erReflection->getMethod('stanceFor');
    $cases = [];
    foreach ([
        ['both_95_percent_narrow_interval', .95, .95, 0., -1., 1.],
        ['perfect_accuracy_zero_width_bootstrap', 1., 1., 0., 0., 0.],
        ['wide_interval_outside_ceiling', .80, .79, -1., -20., 20.],
        ['confirmed_loss_inside_five_point_margin', .80, .78, -2., -3., -1.],
    ] as [$label, $en, $ai, $value, $lo, $hi]) {
        $m = new \App\Entity\Measurement();
        $m->arms = ['english' => $en, 'ainglish' => $ai, 'chance' => .125];
        $m->value = $value; $m->valueLo = $lo; $m->valueHi = $hi;
        $cases[] = [
            'synthetic_case' => $label, 'arms' => $m->arms, 'value' => $value,
            'interval' => [$lo, $hi],
            'resolution' => $protocols::resolutionBound($m->arms, $m->metric),
            'effective_stance' => $ms->effectiveStance($m),
            'bounded_prerequisite_stance' => $stanceFor->invoke($er, $m, ['at_least' => -5]),
        ];
    }
    $replications = [];
    foreach ([[0., .1], [0., 1.], [1., 1.2], [0., 0.]] as [$o, $r]) {
        $replications[] = \App\Service\ReplicationSettlement::comparison(
            $o, $r, ['fixed-reader'], ['fixed-reader'], null, null,
        );
    }
    echo json_encode(['kind' => 'SYNTHETIC_DOMAIN_METHOD_AUDIT_NOT_EVIDENCE',
        'cases' => $cases, 'replication_examples' => $replications,
        'scope' => 'Real upstream methods, minimal measurement stub; not full HTTP/lifecycle integration.',
    ], JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR) . "\n";
}
