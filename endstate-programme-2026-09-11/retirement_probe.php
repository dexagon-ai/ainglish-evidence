<?php
declare(strict_types=1);

// Execute only after mint. Public source is read, never modified. The one removed
// guard is the counterfactual; all other deployed logic is identical between arms.
$web = $argv[1] ?? throw new RuntimeException('Need Symfony checkout');
$snapshot = $argv[2] ?? throw new RuntimeException('Need frozen input census');
require $web.'/vendor/autoload.php';

use App\Entity\Measurement;
use App\Entity\Proposal;
use App\Repository\MeasurementRepository;
use App\Service\MeasurementProtocols;
use App\Service\MeasurementService;

final class FrozenRetirementMeasurements extends MeasurementRepository
{
    public function __construct(private array $frozenRows) {}
    public function confirmedForProposal(int $proposalId): array { return $this->frozenRows; }
}

$source = file_get_contents($web.'/src/Service/MeasurementService.php');
$guard = "if (!\$p->isPublished() || \$p->stage === 'withdrawn') {";
if (substr_count($source, $guard) !== 1) { throw new RuntimeException('Exact changed guard drifted'); }
$counterfactual = str_replace('final class MeasurementService', 'final class PreRetirementCounterfactual', $source, $names);
if ($names !== 1) { throw new RuntimeException('Unexpected class shape'); }
$counterfactual = str_replace($guard, "if (!\$p->isPublished()) {", $counterfactual, $guards);
if ($guards !== 1) { throw new RuntimeException('Unexpected guard shape'); }
eval(substr($counterfactual, 5));

function machine(string $class, array $measurements): object {
    $reflection = new ReflectionClass($class);
    $object = $reflection->newInstanceWithoutConstructor();
    $reflection->getProperty('measurements')->setValue($object, new FrozenRetirementMeasurements($measurements));
    $reflection->getProperty('protocols')->setValue($object, new MeasurementProtocols());
    // This instrument only executes the changed withdrawn branch. It must never
    // reach a database/ledger dependency; other branches are byte-identical.
    return $object;
}
function runPair(array $measurements): array {
    $before = new Proposal(); $before->id = 1; $before->stage = 'withdrawn';
    $before->publicationStatus = 'visible'; $after = clone $before;
    machine('App\\Service\\PreRetirementCounterfactual', $measurements)->assess($before);
    machine(MeasurementService::class, $measurements)->assess($after);
    return ['before' => $before->stage, 'after' => $after->stage, 'moved' => $before->stage !== $after->stage];
}
function hydrate(array $row): Measurement {
    $m = new Measurement(); $m->metric = $row['metric']; $m->value = (float)$row['value'];
    $m->valueLo = isset($row['value_lo']) ? (float)$row['value_lo'] : null;
    $m->valueHi = isset($row['value_hi']) ? (float)$row['value_hi'] : null;
    $m->arms = $row['arms'] ?? null; $m->resolutionBound = $row['resolution_bound'] ?? null;
    return $m;
}

$input = json_decode(file_get_contents($snapshot), true, flags: JSON_THROW_ON_ERROR);
$rows = []; $total = 0;
foreach ($input['records'] as $r) {
    if ($r['stage'] !== 'withdrawn') {
        $rows[] = ['public_id' => $r['public_id'], 'stage' => $r['stage'], 'unclaimed_flips' => 0,
            'reason' => 'The only changed assess guard is false; the rest of the execution is byte-identical.'];
        continue;
    }
    $detail = $input['withdrawn_details'][$r['public_id']] ?? throw new RuntimeException('Missing withdrawn detail');
    if ($detail['stage'] !== $r['stage']) { throw new RuntimeException('Frozen pages disagree on stage'); }
    $confirmed = [];
    foreach ($detail['measurements'] as $m) {
        if (($m['confirmed'] ?? false) && !($m['is_replication'] ?? false)
            && ($m['evidence_state'] ?? null) === 'valid' && ($m['voided_at'] ?? null) === null
            && !($m['retraction']['retracted'] ?? false)) {
            $confirmed[] = hydrate($m);
        }
    }
    $result = runPair($confirmed); $flips = (int)$result['moved']; $total += $flips;
    $rows[] = ['public_id' => $r['public_id'], 'stage' => $r['stage'],
        'confirmed_rows' => count($confirmed), 'counterfactual' => $result, 'unclaimed_flips' => $flips];
}

// Planted counterexamples demonstrate this test CAN observe a non-zero effect.
// They never enter the live denominator or the filed scientific value.
$harm = new Measurement(); $harm->metric = 'comprehension_accuracy_delta'; $harm->value = -30;
$harm->arms = ['english' => .9, 'ainglish' => .6, 'chance' => .25]; $harm->resolutionBound = 'resolvable';
$support = new Measurement(); $support->metric = 'token_delta'; $support->value = -3;
$controls = ['confirmed_harm' => runPair([$harm]), 'confirmed_non_harm' => runPair([$support]),
    'no_confirmed_evidence' => runPair([])];
if (!$controls['confirmed_harm']['moved'] || !$controls['confirmed_non_harm']['moved']
    || $controls['no_confirmed_evidence']['moved']) { throw new RuntimeException('Sensitivity control failed'); }
echo json_encode(['kind' => 'ainglish.retirement-causal-regression.v1', 'value' => $total,
    'domain_count' => count($rows), 'rows' => $rows, 'synthetic_controls_excluded' => $controls,
    'meaning' => 'Unclaimed live reassessment flips from the exact guard change; not a stable-post-deploy proxy and not activation authorisation.'], JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES), "\n";
