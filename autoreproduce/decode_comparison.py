"""Create a provisional H20 TP4 Decode comparison from recorded sweep summaries."""
import json
import sys
from collections import Counter
from pathlib import Path
from autoreproduce.sla import evaluate_sla

TARGETS = {10: 3048.35, 20: 6248.65, 30: 7303.19}


def main():
    if len(sys.argv) != 3:
        raise SystemExit('Usage: python -m autoreproduce.decode_comparison SUMMARY_JSON OUTPUT_MD')
    rows = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    counts = Counter(row['concurrency'] for row in rows)
    if not counts or len(set(counts.values())) != 1:
        raise SystemExit('Each concurrency must have the same number of recorded runs')
    repeats = next(iter(counts.values()))
    lines = ['# H20 TP4 Decode 暂定对比', '',
             f'mean TPOT 按每个并发点的 {repeats} 轮正式请求计算；每轮请求数为并发的 10 倍。',
             '模型使用 DeepSeek-V4-Flash 预览权重和 MTP=1；图片没有给出权重版本。',
             '用户确认图片 token/s 为输入加输出 token 的总吞吐；输出吞吐另列供参考。',
             '仅比较已完成的并发点；当前报告为阶段性结果。', '',
             '| 平均 TPOT 条件 | 已测最佳并发 | 平均 TPOT (ms) | 输出吞吐 (token/s) | 总吞吐 (token/s) | 图中 token/s |',
             '| --- | ---: | ---: | ---: | ---: | ---: |']
    for threshold, ref in TARGETS.items():
        result = evaluate_sla(rows, latency_key='tpot_ms', threshold=threshold,
                              throughput_key='total_tok_s', repeats=repeats,
                              pass_rule='mean_of_repeats')
        best = result['best_observed']
        if best is None:
            lines.append(f'| < {threshold} ms | 未找到 | — | — | — | {ref:.2f} |')
            continue
        c = best['concurrency']
        values = [r['output_tok_s'] for r in rows if r['concurrency'] == c]
        output = sum(values) / len(values)
        lines.append(f"| < {threshold} ms | {c} | {best['latency_mean']:.3f} | {output:.2f} | {best['throughput_mean']:.2f} | {ref:.2f} |")
    lines += ['', '吞吐最高的已测点与最大达标并发可能不同。模型版本、其他测试条件及所有并发点尚未确认前，不能判定严格复现。']
    Path(sys.argv[2]).write_text('\n'.join(lines) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
