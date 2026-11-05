import copy
import unittest
from autoreproduce.core import evaluate, load_json


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.spec = load_json("examples/spec.json")
        self.runs = load_json("examples/runs.json")

    def test_baseline_is_provisional(self):
        self.assertEqual(evaluate(self.spec, self.runs)["status"], "Provisional Reproduced")

    def test_changed_condition_is_not_strict(self):
        self.runs[0]["conditions"]["gpu_count"] = 4
        self.assertEqual(evaluate(self.spec, self.runs)["status"], "Approximate Reproduced")

    def test_unknown_blocks(self):
        self.spec["conditions"]["gpu_count"] = {"value": None, "status": "unknown"}
        self.assertEqual(evaluate(self.spec, self.runs)["status"], "Blocked")

    def test_invalid_and_insufficient_runs(self):
        self.runs[0]["valid"] = False
        self.assertEqual(evaluate(self.spec, self.runs)["status"], "Invalid")
        self.assertEqual(evaluate(self.spec, self.runs[1:])["status"], "Blocked")

    def test_large_error(self):
        for run in self.runs:
            run["metrics"]["output_tps"] = 500
        self.assertEqual(evaluate(self.spec, self.runs)["status"], "Not Reproduced")

    def test_explicit_requires_evidence(self):
        del self.spec["conditions"]["gpu_model"]["evidence"]
        with self.assertRaises(ValueError):
            evaluate(self.spec, self.runs)


if __name__ == "__main__":
    unittest.main()
