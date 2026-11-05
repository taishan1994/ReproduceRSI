import unittest
from autoreproduce.planner import next_concurrency


def rows(c, values):
    return [dict(run_id=f'{c}-{i}', concurrency=c, latency=x, throughput=100) for i, x in enumerate(values)]


class PlannerTests(unittest.TestCase):
    def decide(self, samples):
        return next_concurrency(samples, latency_key='latency', threshold=10, throughput_key='throughput')

    def test_expands_and_bisects(self):
        self.assertEqual(self.decide(rows(2, [1, 2, 3]))['concurrency'], 4)
        self.assertEqual(self.decide(rows(2, [1, 2, 3]) + rows(6, [11, 12, 13]))['concurrency'], 4)

    def test_boundary_and_nonmonotonic(self):
        self.assertEqual(self.decide(rows(2, [1]*3) + rows(3, [11]*3))['action'], 'boundary_found')
        self.assertEqual(self.decide(rows(2, [11]*3) + rows(3, [1]*3))['action'], 'investigate')

    def test_incomplete_points_are_not_used(self):
        self.assertEqual(self.decide(rows(2, [1]))['action'], 'complete_repeats')
