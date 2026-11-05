"""Evaluate concurrency sweeps against a latency objective at a configured run count."""
import math
import statistics


def evaluate_sla(rows, *, latency_key, threshold, throughput_key, repeats=1, pass_rule="mean_of_repeats"):
    """Evaluate complete measured points by the selected rule; do not infer unmeasured points."""
    if repeats < 1 or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError('A positive threshold and at least one repeat is required')
    if pass_rule not in ('all_repeats', 'mean_of_repeats'):
        raise ValueError('Unknown pass rule')
    grouped = {}
    ids = set()
    for row in rows:
        run_id = row.get('run_id')
        concurrency = row.get('concurrency')
        if not isinstance(run_id, str) or not run_id or run_id in ids:
            raise ValueError('run IDs must be unique nonempty strings')
        ids.add(run_id)
        if not isinstance(concurrency, int) or isinstance(concurrency, bool) or concurrency <= 0:
            raise ValueError('concurrency must be a positive integer')
        for key in (latency_key, throughput_key):
            value = row.get(key)
            if not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError(f'invalid {key} for {run_id}')
        grouped.setdefault(concurrency, []).append(row)
    points = []
    for concurrency, runs in sorted(grouped.items()):
        complete = len(runs) == repeats
        latencies = [r[latency_key] for r in runs]
        throughput = [r[throughput_key] for r in runs]
        points.append({'concurrency': concurrency, 'run_ids': [r['run_id'] for r in runs],
                       'complete': complete, 'passes': complete and (all(x < threshold for x in latencies) if pass_rule == 'all_repeats' else statistics.mean(latencies) < threshold),
                       'latency_mean': statistics.mean(latencies), 'latency_max': max(latencies),
                       'throughput_mean': statistics.mean(throughput)})
    passing = [p for p in points if p['passes']]
    return {'threshold': threshold, 'latency_key': latency_key, 'throughput_key': throughput_key, 'pass_rule': pass_rule,
            'points': points, 'best_observed': max(passing, key=lambda p: p['throughput_mean']) if passing else None,
            'note': 'Best among measured complete points only; mean-of-repeats weights repeats equally. Statistical equivalence and unmeasured concurrencies are not established.'}


