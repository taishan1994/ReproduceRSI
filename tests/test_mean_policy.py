import unittest
from autoreproduce.sla import evaluate_sla
from autoreproduce.planner import next_concurrency

class MeanPolicyTests(unittest.TestCase):
    def test_mean_and_all_repeat_policies_remain_distinct(self):
        rows = [dict(run_id=str(i), concurrency=5, latency=x, throughput=100) for i, x in enumerate([9.875, 10.008, 10.003])]
        kw = dict(latency_key='latency', threshold=10, throughput_key='throughput')
        self.assertTrue(evaluate_sla(rows, pass_rule='mean_of_repeats', **kw)['points'][0]['passes'])
        self.assertFalse(evaluate_sla(rows, pass_rule='all_repeats', **kw)['points'][0]['passes'])
        self.assertEqual(next_concurrency(rows, pass_rule='mean_of_repeats', **kw)['concurrency'], 10)

if __name__ == '__main__':
    unittest.main()
