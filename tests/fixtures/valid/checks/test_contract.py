import unittest

from src.orders.history import history_for
from src.profiles import customer_id


class ContractTests(unittest.TestCase):
    def test_customer_history(self):
        """Conforms to orders/own-only, orders/newest-first."""
        orders = [
            {"customer_id": "alice", "date": 1},
            {"customer_id": "bob", "date": 3},
            {"customer_id": "alice", "date": 2},
        ]
        self.assertEqual([order["date"] for order in history_for("alice", orders)], [2, 1])

    def test_stable_identifier(self):
        """Conforms to profiles/stable-id."""
        self.assertEqual(customer_id({"id": "alice"}), "alice")
