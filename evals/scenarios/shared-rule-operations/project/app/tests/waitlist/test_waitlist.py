from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from waitlist import promote


class PromotionTests(unittest.TestCase):
    def test_first_waiting_attendee_gets_one_free_place(self):
        # Conforms to waitlist/promotion-condition
        state = {"capacity": 2, "confirmed": ["alice"], "waiting": ["bob", "carol"]}
        self.assertEqual(promote(state), "bob")
        self.assertEqual(state["confirmed"], ["alice", "bob"])
        self.assertEqual(state["waiting"], ["carol"])

    def test_promotes_exactly_one_with_multiple_free_places(self):
        state = {"capacity": 3, "confirmed": [], "waiting": ["bob", "carol"]}
        self.assertEqual(promote(state), "bob")
        self.assertEqual(state["confirmed"], ["bob"])
        self.assertEqual(state["waiting"], ["carol"])

    def test_full_roster_does_not_promote(self):
        state = {"capacity": 1, "confirmed": ["alice"], "waiting": ["bob"]}
        self.assertIsNone(promote(state))
        self.assertEqual(state["waiting"], ["bob"])

    def test_empty_waitlist_does_not_promote(self):
        state = {"capacity": 1, "confirmed": [], "waiting": []}
        self.assertIsNone(promote(state))


if __name__ == "__main__":
    unittest.main()
