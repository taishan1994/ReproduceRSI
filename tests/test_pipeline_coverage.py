import unittest
from autoreproduce.planner import unmeasured_after_failure

class PipelineCoverageTests(unittest.TestCase):
    def test_gaps_above_failure_are_not_discarded(self):
        rows=[]
        for c, latency in [(1, 800), (2, 1512), (4, 1575), (8, 3092)]:
            rows.extend({'run_id':f'{c}-{i}', 'concurrency':c, 'ttft':latency, 'throughput':c} for i in range(3))
        actual=unmeasured_after_failure(rows, latency_key='ttft', threshold=1500, throughput_key='throughput')
        self.assertEqual(actual,[3,5,6,7])

if __name__ == '__main__':
    unittest.main()
