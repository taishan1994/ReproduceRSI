"""Deterministic SLA boundary search; latency samples must already be validated."""
from .sla import evaluate_sla


def next_concurrency(rows, *, latency_key, threshold, throughput_key, repeats=1, ceiling=64, pass_rule="mean_of_repeats", failed_concurrencies=()):
    """Suggest one untested concurrency, keeping workload and thresholds fixed.

    Uses only complete points at the configured repeat count. If measurements are non-monotonic, stop
    and request investigation rather than silently assuming a monotonic curve.
    """
    if ceiling < 1:
        raise ValueError('ceiling must be positive')
    failed_concurrencies = tuple(failed_concurrencies)
    if any(not isinstance(c, int) or isinstance(c, bool) or c < 1 for c in failed_concurrencies):
        raise ValueError('failed concurrencies must be positive integers')

    def proposal(c, reason):
        if failed_concurrencies and c >= min(failed_concurrencies):
            return {'action': 'investigate_execution', 'failed_concurrency': min(failed_concurrencies),
                    'reason': 'A prior execution failure must be diagnosed before equal or higher concurrency'}
        return {'action': 'measure', 'concurrency': c, 'reason': reason}

    points = evaluate_sla(rows, latency_key=latency_key, threshold=threshold,
                          throughput_key=throughput_key, repeats=repeats, pass_rule=pass_rule)['points']
    if any(not p['complete'] for p in points):
        return {'action': 'complete_repeats', 'reason': 'Incomplete measured point'}
    passing = [p['concurrency'] for p in points if p['passes']]
    failing = [p['concurrency'] for p in points if not p['passes']]
    if passing and failing and max(passing) > min(failing):
        return {'action': 'investigate', 'reason': 'Observed pass/fail outcomes are non-monotonic'}
    if not points:
        return proposal(1, 'Establish minimum-load baseline')
    if not passing:
        low_fail = min(failing)
        if low_fail == 1:
            return {'action': 'no_passing_point', 'reason': 'Minimum concurrency failed'}
        return proposal(max(1, low_fail // 2), 'Find a passing lower bound')
    low = max(passing)
    high = min((x for x in failing if x > low), default=None)
    if high is None:
        if low >= ceiling:
            return {'action': 'ceiling', 'reason': 'Search budget reached without a failing upper bound'}
        return proposal(min(ceiling, low * 2), 'Find a failing upper bound')
    if high - low == 1:
        return {'action': 'boundary_found', 'passing_concurrency': low, 'failing_concurrency': high,
                'reason': 'Adjacent tested points bound the observed SLA boundary'}
    return proposal((low + high) // 2, 'Narrow the measured boundary')


def applicable_experiences(query, *, limit=5):
    """Retrieve evidence-scoped lessons before selecting an experiment."""
    from .knowledge import search_experiences
    return search_experiences(query, limit=limit)


def plan_with_experiences(query, rows, *, experience_query=None, experience_limit=5, **planner_options):
    """Return the normal RSI decision together with scoped prior evidence.

    Callers should build experience_query from the current framework/version,
    model, parallelism, workload, and observed symptom. Retrieved lessons do
    not override measured rows or current runtime checks.
    """
    decision = next_concurrency(rows, **planner_options)
    lessons = applicable_experiences(experience_query or query, limit=experience_limit)
    return {"decision": decision, "experiences": lessons}



def unmeasured_after_failure(rows, *, latency_key, threshold, throughput_key, repeats=1, pass_rule='mean_of_repeats'):
    """List unmeasured integer concurrencies above the first observed failure.

    Pipeline latency may be non-monotonic. A failed point does not prove that
    untested higher points fail. This bounded audit does not infer anything
    above the largest tested concurrency and cannot prove a global optimum.
    """
    points = evaluate_sla(rows, latency_key=latency_key, threshold=threshold,
                          throughput_key=throughput_key, repeats=repeats, pass_rule=pass_rule)['points']
    if any(not p['complete'] for p in points):
        raise ValueError('Complete all repeats before coverage audit')
    failed = [p['concurrency'] for p in points if not p['passes']]
    if not failed:
        return []
    measured = {p['concurrency'] for p in points}
    return [c for c in range(min(failed) + 1, max(measured) + 1) if c not in measured]
