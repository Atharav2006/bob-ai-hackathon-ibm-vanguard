import unittest
from app.services.planner import generate_optimized_plan

class TestPlanner(unittest.TestCase):
    def test_incompatible_categories(self):
        needs = [{"id": "n1", "category": "rescue", "amount": 1, "urgency": 5}]
        resources = [{"id": "r1", "capabilities": {"medical": 10}, "version": 1}]
        result = generate_optimized_plan(needs, resources)
        self.assertEqual(len(result["assignments"]), 0)

    def test_null_and_zero_capacity(self):
        needs = [{"id": "n1", "category": "rescue", "amount": 5, "urgency": 5}]
        resources = [
            {"id": "r1", "capabilities": {"rescue": 0}, "version": 1},
            {"id": "r2", "capabilities": {"rescue": None}, "version": 1},
            {"id": "r3", "capabilities": {"rescue": -5}, "version": 1}
        ]
        result = generate_optimized_plan(needs, resources)
        self.assertEqual(len(result["assignments"]), 0)

    def test_multiple_needs_sharing_one_resource(self):
        needs = [
            {"id": "n1", "category": "supply", "amount": 3, "urgency": 5},
            {"id": "n2", "category": "supply", "amount": 2, "urgency": 5}
        ]
        resources = [{"id": "r1", "capabilities": {"supply": 10}, "version": 1}]
        result = generate_optimized_plan(needs, resources)
        self.assertEqual(len(result["assignments"]), 2)
        total_assigned = sum(a["amount_assigned"] for a in result["assignments"])
        self.assertEqual(total_assigned, 5)

    def test_partial_fulfillment(self):
        needs = [{"id": "n1", "category": "medical", "amount": 10, "urgency": 5}]
        resources = [{"id": "r1", "capabilities": {"medical": 4}, "version": 1}]
        result = generate_optimized_plan(needs, resources)
        self.assertEqual(len(result["assignments"]), 1)
        self.assertEqual(result["assignments"][0]["amount_assigned"], 4)

    def test_total_allocation_bounded_by_capacity(self):
        needs = [
            {"id": "n1", "category": "rescue", "amount": 10, "urgency": 5},
            {"id": "n2", "category": "rescue", "amount": 10, "urgency": 5}
        ]
        resources = [{"id": "r1", "capabilities": {"rescue": 5}, "version": 1}]
        result = generate_optimized_plan(needs, resources)
        total_assigned = sum(a["amount_assigned"] for a in result["assignments"])
        self.assertEqual(total_assigned, 5)

if __name__ == "__main__":
    unittest.main()

