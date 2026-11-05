#!/usr/bin/env python3
"""Run isolated, auditable AIPerf concurrency sweeps for a vLLM service."""
import argparse
import json
import os
import subprocess
from pathlib import Path

BASE = Path('/mnt/md0/reproducersi/dsv4_20261103')
TOKENIZER = os.environ.get('REPRO_TOKENIZER', '/mnt/md0/checkpoints/deepseek-ai/DeepSeek-V4-Flash-0731')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tag', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--output-tokens', type=int, required=True)
    p.add_argument('--concurrency', type=int, nargs='+', required=True)
    p.add_argument('--repeats', type=int, default=1)
    p.add_argument('--warmup', type=int, default=20)
    args = p.parse_args()
    if not args.tag.replace('_', '').isalnum() or args.output_tokens < 1 or args.repeats < 1 or any(c < 1 for c in args.concurrency):
        p.error('invalid tag, token count, repeat count, or concurrency')
    rows = []
    summary = BASE / 'results' / f'{args.tag}_summary.json'
    if summary.exists():
        raise RuntimeError(f'refusing to overwrite {summary}')
    for concurrency in args.concurrency:
        for repeat in range(1, args.repeats + 1):
            name = f'{args.tag}_c{concurrency}_r{repeat}'
            out = BASE / 'results' / name
            logpath = BASE / 'logs' / (name + '.log')
            if out.exists() or logpath.exists():
                raise RuntimeError(f'refusing to overwrite {name}')
            cmd = ['docker', 'exec', 'compare2', 'aiperf', 'profile', '--model', args.model,
                   '--url', f'http://127.0.0.1:{args.port}', '--endpoint-type', 'completions',
                   '--streaming', '--tokenizer', TOKENIZER, '--tokenizer-trust-remote-code',
                   '--use-server-token-count', '--synthetic-input-tokens-mean', '8192',
                   '--synthetic-input-tokens-stddev', '0', '--output-tokens-mean', str(args.output_tokens),
                   '--output-tokens-stddev', '0', '--concurrency', str(concurrency),
                   '--request-count', str(10 * concurrency), '--warmup-request-count', str(args.warmup),
                   '--warmup-concurrency', str(concurrency), '--extra-inputs', '{"ignore_eos":true}',
                   '--artifact-dir', str(out)]
            with logpath.open('x') as log:
                result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=3600)
            if result.returncode:
                raise RuntimeError(f'{name} failed: exit {result.returncode}; see {logpath}')
            d = json.loads((out / 'profile_export_aiperf.json').read_text())
            for key, expected in [('input_sequence_length', 8192), ('output_sequence_length', args.output_tokens),
                                  ('usage_prompt_tokens', 8192), ('usage_completion_tokens', args.output_tokens)]:
                if key not in d or d[key]['min'] != expected or d[key]['max'] != expected:
                    raise RuntimeError(f'{name}: invalid {key}: {d.get(key)}')
            if d['request_error_rate']['avg'] != 0 or d['request_count']['avg'] != 10 * concurrency:
                raise RuntimeError(f'{name}: error rate or request count mismatch')
            row = {'run_id': name, 'concurrency': concurrency, 'requests': 10 * concurrency,
                   'ttft_ms': d['time_to_first_token']['avg'], 'ttft_p99_ms': d['time_to_first_token']['p99'],
                   'input_tok_s': d['input_token_throughput']['avg'],
                   'output_tok_s': d['output_token_throughput']['avg'],
                   'total_tok_s': d['total_token_throughput']['avg'], 'artifact': str(out)}
            if args.output_tokens > 1:
                row.update(tpot_ms=d['inter_token_latency']['avg'], tpot_p99_ms=d['inter_token_latency']['p99'])
            rows.append(row)
            temp = summary.with_suffix('.tmp')
            temp.write_text(json.dumps(rows, indent=2))
            temp.replace(summary)
            print(json.dumps(row), flush=True)

if __name__ == '__main__':
    main()

