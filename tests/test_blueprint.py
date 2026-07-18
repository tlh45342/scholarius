import unittest
from pathlib import Path

from app.parser_qti import load_qti_bank
from app.selector import build_test, largest_remainder_counts


class BlueprintTests(unittest.TestCase):
    def test_largest_remainder_total(self):
        counts = largest_remainder_counts(50, {"D1": 28, "D2": 37, "D3": 35})
        self.assertEqual(sum(counts.values()), 50)
        self.assertEqual(counts, {"D1": 14, "D2": 19, "D3": 17})

    def test_legacy_bank_falls_back_to_random(self):
        root = Path(__file__).resolve().parents[1]
        bank = load_qti_bank(root / "app" / "qti" / "R2BpzuSgCYo.xml")
        result = build_test(bank, 2, selection_mode="blueprint", seed=1)
        self.assertEqual(len(result.questions), 2)


if __name__ == "__main__":
    unittest.main()
