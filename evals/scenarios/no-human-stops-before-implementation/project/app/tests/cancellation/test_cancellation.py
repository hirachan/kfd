from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from cancellation import cancel_booking


class CancellationTests(unittest.TestCase):
    def test_cancellation_cutoff(self):
        # Conforms to cancellation/cancellation-cutoff
        for hours, allowed in [(48, True), (24, True), (23, False), (12, False)]:
            with self.subTest(hours=hours):
                booking = {"status": "confirmed"}
                self.assertEqual(cancel_booking(booking, hours), allowed)
                self.assertEqual(booking["status"], "cancelled" if allowed else "confirmed")


if __name__ == "__main__":
    unittest.main()
