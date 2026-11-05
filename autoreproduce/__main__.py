import argparse
import json
from .core import evaluate, load_json


def main():
    parser = argparse.ArgumentParser(description="评估基准复现实验")
    parser.add_argument("spec", help="实验规范 JSON")
    parser.add_argument("runs", help="重复实验结果 JSON 数组")
    parser.add_argument("-o", "--output", help="报告输出路径")
    args = parser.parse_args()
    try:
        report = evaluate(load_json(args.spec), load_json(args.runs))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    result = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(result + "\n", encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
