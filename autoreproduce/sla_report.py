"""Evaluate recorded SLA sweeps without inferring unmeasured concurrency points."""
import argparse
import json
from pathlib import Path
from .sla import evaluate_sla


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runs')
    parser.add_argument('--latency', required=True)
    parser.add_argument('--threshold', type=float, required=True)
    parser.add_argument('--throughput', required=True)
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--pass-rule', choices=('all_repeats', 'mean_of_repeats'), default='mean_of_repeats')
    parser.add_argument('-o', '--output')
    args = parser.parse_args()
    try:
        rows = json.loads(Path(args.runs).read_text(encoding='utf-8-sig'))
        result = evaluate_sla(rows, latency_key=args.latency, threshold=args.threshold,
                              throughput_key=args.throughput, repeats=args.repeats, pass_rule=args.pass_rule)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.error(str(exc))
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output + '\n', encoding='utf-8')
    else:
        print(output)


if __name__ == '__main__':
    main()

