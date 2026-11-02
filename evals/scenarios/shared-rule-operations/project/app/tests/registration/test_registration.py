from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from registration import register


class OperationTests(unittest.TestCase):
    def test_operation_and_promotion(self):
        # Conforms to waitlist/registration-promotes
        state = {"capacity": 2, "confirmed": ["alice"], "waiting": []}
        self.assertEqual(register(state, "bob"), "bob")
        self.assertEqual(state["confirmed"], ["alice", "bob"])
        self.assertEqual(state["waiting"], [])

    def test_full_registration_stays_waiting(self):
        state = {"capacity": 1, "confirmed": ["alice"], "waiting": []}
        self.assertIsNone(register(state, "bob"))
        self.assertEqual(state["waiting"], ["bob"])


if __name__ == "__main__":
    unittest.main()
