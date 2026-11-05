import unittest
from autoreproduce.planner import next_concurrency

class ExecutionFailurePolicyTests(unittest.TestCase):
    def test_does_not_escalate_after_failure(self):
        rows=[{'run_id':f'{c}-{i}', 'concurrency':c, 'ttft':v, 'throughput':100} for c,v in [(1,800),(2,1512),(3,1197),(4,1575),(5,1970),(6,2338),(7,2718)] for i in range(3)]
        kw={'latency_key':'ttft','threshold':3000,'throughput_key':'throughput','pass_rule':'mean_of_repeats'}
        self.assertEqual(next_concurrency(rows,failed_concurrencies=[8],**kw)['action'],'investigate_execution')
        self.assertEqual(next_concurrency(rows,**kw)['concurrency'],14)

if __name__ == '__main__':
    unittest.main()
