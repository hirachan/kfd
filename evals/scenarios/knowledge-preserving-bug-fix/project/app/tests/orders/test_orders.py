from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from orders import orders_for_customer


class OrderHistoryTests(unittest.TestCase):
    def test_single_customer_store(self):
        # Conforms to orders/own-orders-only
        orders = [{"id": "A-1", "customer_id": "alice", "created_at": 1}]
        self.assertEqual(orders_for_customer(orders, "alice"), orders)

    def test_empty_store(self):
        self.assertEqual(orders_for_customer([], "alice"), [])

    def test_newest_first(self):
        # Conforms to orders/newest-first
        orders = [
            {"id": "A-1", "customer_id": "alice", "created_at": 1},
            {"id": "A-2", "customer_id": "alice", "created_at": 2},
        ]
        self.assertEqual([order["id"] for order in orders_for_customer(orders, "alice")], ["A-2", "A-1"])


if __name__ == "__main__":
    unittest.main()
