from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from customer_quotes import cancellation_fee


class CancellationQuoteTests(unittest.TestCase):
    def test_early_cancellation_fee(self):
        # Conforms to customer/early-cancellation-fee
        self.assertEqual(cancellation_fee(24), 0)
        self.assertEqual(cancellation_fee(48), 0)


if __name__ == "__main__":
    unittest.main()
