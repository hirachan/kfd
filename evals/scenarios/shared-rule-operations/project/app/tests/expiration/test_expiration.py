from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from expiration import expire


class OperationTests(unittest.TestCase):
    def test_operation_and_promotion(self):
        # Conforms to expiration/expire-and-promote
        state = {"capacity": 2, "confirmed": ["alice", "bob"], "waiting": ["carol", "dan"]}
        self.assertEqual(expire(state, "bob"), "carol")
        self.assertEqual(state["confirmed"], ["alice", "carol"])
        self.assertEqual(state["waiting"], ["dan"])

    def test_no_waiting_attendee(self):
        state = {"capacity": 1, "confirmed": ["alice"], "waiting": []}
        self.assertIsNone(expire(state, "alice"))
        self.assertEqual(state["confirmed"], [])


if __name__ == "__main__":
    unittest.main()
