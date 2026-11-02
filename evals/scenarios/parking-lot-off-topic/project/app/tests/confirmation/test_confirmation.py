from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from confirmation import confirmation_label


class ConfirmationTests(unittest.TestCase):
    def test_confirmation_text(self):
        # Conforms to confirmation/confirmation-text
        label = confirmation_label("ORD-42")
        self.assertIn("Order confirmed: ORD-42</span>", label)

    def test_identifier_is_escaped(self):
        self.assertIn("&lt;42&gt;", confirmation_label("<42>"))


if __name__ == "__main__":
    unittest.main()
