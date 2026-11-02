from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from receipts import render_receipt


class ReceiptTests(unittest.TestCase):
    def test_total_format(self):
        # Conforms to receipts/total-format
        for pence, expected in [(0, "Total: £0.00"), (5, "Total: £0.05"), (12345, "Total: £123.45")]:
            with self.subTest(pence=pence):
                self.assertEqual(render_receipt(pence), expected)


if __name__ == "__main__":
    unittest.main()
