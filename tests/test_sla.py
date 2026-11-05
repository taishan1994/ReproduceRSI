import unittest
from autoreproduce.sla import evaluate_sla


class SlaTests(unittest.TestCase):
    def test_only_complete_points_with_all_repeats_passing_are_eligible(self):
        rows = [dict(run_id=str(i), concurrency=1, ttft_ms=v, input_tok_s=100) for i, v in enumerate([900, 950, 1000])]
        rows += [dict(run_id='3', concurrency=2, ttft_ms=1200, input_tok_s=200)]
        result = evaluate_sla(rows, latency_key='ttft_ms', threshold=1500, throughput_key='input_tok_s')
        self.assertEqual(result['best_observed']['concurrency'], 1)
        rows += [dict(run_id='4', concurrency=2, ttft_ms=1600, input_tok_s=200), dict(run_id='5', concurrency=2, ttft_ms=1200, input_tok_s=200)]
        self.assertFalse(evaluate_sla(rows, latency_key='ttft_ms', threshold=1500, throughput_key='input_tok_s')['points'][1]['passes'])

    def test_duplicate_ids_are_rejected(self):
        row = dict(run_id='same', concurrency=1, ttft_ms=1, input_tok_s=1)
        with self.assertRaises(ValueError):
            evaluate_sla([row, row], latency_key='ttft_ms', threshold=2, throughput_key='input_tok_s')
