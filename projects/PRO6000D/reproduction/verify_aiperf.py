"""Independently audit AIPerf per-request exports for completed measurements."""
import argparse
import json
import math
from pathlib import Path


def verify(folder, concurrency, input_tokens, output_tokens):
    folder = Path(folder)
    aggregate = json.loads((folder / 'profile_export_aiperf.json').read_text(encoding='utf-8'))
    records = [json.loads(line) for line in (folder / 'profile_export.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    formal = [r for r in records if r['metadata']['phase_kind'] == 'profiling']
    if len(formal) != 10 * concurrency or aggregate['request_count']['avg'] != len(formal):
        raise ValueError('Formal request count is not 10 times concurrency')
    if aggregate['request_error_rate']['avg'] != 0:
        raise ValueError('Request errors reported')
    itls = []
    ttfts = []
    for row in formal:
        if row['metadata'].get('was_cancelled') or row.get('error'):
            raise ValueError('Cancelled or failed request')
        metrics = row['metrics']
        for key, target in [('input_sequence_length', input_tokens), ('usage_prompt_tokens', input_tokens),
                            ('output_sequence_length', output_tokens), ('usage_completion_tokens', output_tokens)]:
            if metrics[key]['value'] != target:
                raise ValueError(f'{key} does not match required token length')
        ttfts.append(metrics['time_to_first_token']['value'])
        if output_tokens > 1:
            actual = metrics['inter_token_latency']['value']
            expected = (metrics['request_latency']['value'] - metrics['time_to_first_token']['value']) / (output_tokens - 1)
            if not math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8):
                raise ValueError('Per-request TPOT differs from the assumed first-token formula')
            itls.append(actual)
    if not math.isclose(sum(ttfts) / len(ttfts), aggregate['time_to_first_token']['avg'], rel_tol=1e-8):
        raise ValueError('Aggregated TTFT does not match formal requests')
    if itls and not math.isclose(sum(itls) / len(itls), aggregate['inter_token_latency']['avg'], rel_tol=1e-8):
        raise ValueError('Aggregated TPOT does not match formal requests')
    return {'formal_requests': len(formal), 'warmup_requests': sum(r['metadata']['phase_kind'] == 'warmup' for r in records),
            'input_tokens': input_tokens, 'output_tokens': output_tokens, 'mean_ttft_ms': sum(ttfts) / len(ttfts),
            'mean_tpot_ms': sum(itls) / len(itls) if itls else None}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('folder')
    p.add_argument('--concurrency', type=int, required=True)
    p.add_argument('--input-tokens', type=int, default=8192)
    p.add_argument('--output-tokens', type=int, required=True)
    args = p.parse_args()
    print(json.dumps(verify(args.folder, args.concurrency, args.input_tokens, args.output_tokens), indent=2))

if __name__ == '__main__':
    main()

