import json
import math
import statistics
from pathlib import Path

STATUSES = {"explicit", "derived", "assumed", "unknown", "conflicting"}


def evaluate(spec, runs):
    """Compare repeated measurements only after checking evidence and validity."""
    for key in ("source_id", "spec_id", "policy_version"):
        if not isinstance(spec.get(key), str) or not spec[key].strip():
            raise ValueError(f"{key} is required")
    if not spec.get("conditions"):
        raise ValueError("At least one condition is required")
    conditions = spec["conditions"]
    problems, differences = [], []
    for name, item in conditions.items():
        status = item.get("status")
        if status not in STATUSES:
            raise ValueError(f"Invalid evidence status for {name}: {status}")
        if status == "explicit" and ("value" not in item or item["value"] is None or not item.get("evidence")):
            raise ValueError(f"Explicit condition {name} requires a value and evidence")
        if status in {"unknown", "conflicting"} or item.get("value") is None:
            problems.append(f"Unresolved condition: {name} ({status})")
    expected = spec.get("repeats", 1)
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 1:
        raise ValueError("repeats must be a positive integer")
    tolerance = spec.get("tolerance", 0.10)
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be a finite nonnegative number")
    reference = spec["reference_metrics"]
    if not reference:
        raise ValueError("At least one reference metric is required")
    for name, value in reference.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"Reference metric {name} must be positive and finite")
    if len(runs) != expected:
        problems.append(f"Expected {expected} runs, received {len(runs)}")
    invalid = []
    ids = [r.get("run_id") for r in runs]
    if any(not isinstance(x, str) or not x.strip() for x in ids) or len(ids) != len(set(ids)):
        invalid.append("Each run must have a unique nonempty run_id")
    for i, run in enumerate(runs, 1):
        if run.get("valid") is not True:
            invalid.append(f"Run {i} is not explicitly valid")
        for name, item in conditions.items():
            actual = run.get("conditions", {}).get(name)
            if actual is None:
                problems.append(f"Run {i} missing condition: {name}")
            elif item.get("value") is not None and actual != item["value"]:
                differences.append(f"Run {i}: {name} differs from reference")
        for name in reference:
            value = run.get("metrics", {}).get(name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                invalid.append(f"Run {i} has invalid metric: {name}")
    metrics = {}
    if len(runs) == expected and not invalid:
        for name, target in reference.items():
            values = [r["metrics"][name] for r in runs]
            mean = statistics.mean(values)
            metrics[name] = {"reference": target, "samples": len(values), "mean": mean,
                             "min": min(values), "max": max(values),
                             "stdev": statistics.stdev(values) if len(values) > 1 else None,
                             "relative_error": abs(mean - target) / target}
    assumptions = [name for name, item in conditions.items() if item["status"] in {"assumed", "derived"}]
    if invalid:
        status = "Invalid"
    elif problems:
        status = "Blocked"
    elif any(m["relative_error"] > tolerance for m in metrics.values()):
        status = "Not Reproduced"
    elif differences or assumptions:
        status = "Approximate Reproduced"
    else:
        status = "Provisional Reproduced"
    single_run = expected == 1 and len(runs) == 1
    if single_run and status == "Provisional Reproduced":
        status = "Single-Run Provisional"
    elif single_run and status == "Approximate Reproduced":
        status = "Single-Run Approximate"
    note = ("仅有单轮测量；均值仅代表该轮，标准差不可计算，不具备重复测量稳定性证据。" if single_run
            else "仅按重复测量均值和容差初步评估；未进行统计检验，不能判定严格复现。")
    return {"source_id": spec["source_id"], "spec_id": spec["spec_id"], "policy_version": spec["policy_version"], "run_ids": [r.get("run_id") for r in runs], "status": status, "measurement_strength": "single_run" if single_run else "repeated_runs", "metrics": metrics, "unresolved": problems, "differences": differences, "assumptions": assumptions, "invalid": invalid, "note": note}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

