from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from settlement_quotes import cancellation_fee


class CancellationQuoteTests(unittest.TestCase):
    def test_early_cancellation_fee(self):
        # Conforms to settlement/early-cancellation-fee
        self.assertEqual(cancellation_fee(24), 5)
        self.assertEqual(cancellation_fee(48), 5)


if __name__ == "__main__":
    unittest.main()
