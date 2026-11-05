"""Evidence-scoped experiment lessons for reuse across reproduction tasks.

Lessons are hints for planning, never substitutes for checking the current
runtime. Search ranks exact tags and terms while retaining evidence and scope.
"""
import json
import re
from pathlib import Path

DEFAULT_STORE = Path(__file__).resolve().parent.parent / "knowledge" / "experiences.json"


def load_experiences(path=DEFAULT_STORE):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported experience store schema")
    entries = data.get("experiences")
    if not isinstance(entries, list):
        raise ValueError("experiences must be a list")
    required = {"id", "title", "status", "scope", "observation", "evidence", "reuse"}
    for entry in entries:
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"Experience missing fields: {', '.join(sorted(missing))}")
        if entry["status"] not in {"confirmed", "hypothesis", "failed_attempt"}:
            raise ValueError(f"Invalid experience status: {entry['status']}")
    return data


def search_experiences(query, *, path=DEFAULT_STORE, limit=10):
    """Return relevant lessons with transparent lexical scores and caveats."""
    if limit < 1:
        raise ValueError("limit must be positive")
    terms = set(re.findall(r"[\w.+-]+", query.casefold()))
    ranked = []
    for entry in load_experiences(path)["experiences"]:
        tags = {str(x).casefold() for x in entry.get("tags", [])}
        haystack = " ".join([
            entry["title"], entry["observation"], entry["reuse"],
            json.dumps(entry["scope"], ensure_ascii=False),
        ]).casefold()
        matched_tags = sorted(t for t in tags if t in terms)
        matched_terms = sorted(t for t in terms if len(t) > 2 and t in haystack)
        score = len(matched_tags) * 3 + len(matched_terms)
        if score:
            ranked.append((score, entry["id"], {
                **entry, "relevance": score,
                "matched_tags": matched_tags, "matched_terms": matched_terms,
            }))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked[:limit]]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="搜索可复用的实验成功/失败经验")
    parser.add_argument("query", nargs="+", help="运行环境、框架、错误或问题关键词")
    parser.add_argument("--store", default=str(DEFAULT_STORE))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    results = search_experiences(" ".join(args.query), path=args.store, limit=args.limit)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
