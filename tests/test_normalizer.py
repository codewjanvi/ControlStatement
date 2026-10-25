"""Unit tests for transaction normalization and utility functions."""

import unittest
from controlstatement.models import Transaction
from controlstatement.utils import parse_date_to_iso, parse_amount, clean_description


class TestNormalizer(unittest.TestCase):
    def test_parse_date_to_iso(self):
        cases = {
            "2026-06-15": "2026-06-15",
            "15/06/2026": "2026-06-15",
            "15-06-2026": "2026-06-15",
            "15 Jun 2026": "2026-06-15",
            "15-Jun-2026": "2026-06-15",
            "15 June 2026": "2026-06-15",
            "20260615": "2026-06-15",
        }
        for raw, expected in cases.items():
            self.assertEqual(parse_date_to_iso(raw), expected, f"Failed for {raw}")

    def test_parse_amount(self):
        self.assertEqual(parse_amount("1,450.00"), 1450.0)
        self.assertEqual(parse_amount("₹25,000.50"), 25000.5)
        self.assertEqual(parse_amount("-500.00"), -500.0)
        self.assertEqual(parse_amount("(750.25)"), -750.25)
        self.assertEqual(parse_amount("1200.00 Dr"), -1200.0)
        self.assertEqual(parse_amount("3400.00 Cr"), 3400.0)
        self.assertIsNone(parse_amount(""))
        self.assertIsNone(parse_amount("nil"))

    def test_clean_description(self):
        self.assertEqual(clean_description("  Swiggy   Order  #123 \n\t "), "Swiggy Order #123")
        self.assertEqual(clean_description("Amazon Purchase ---"), "Amazon Purchase")

    def test_transaction_model_validation(self):
        txn = Transaction(
            date="2026-06-01",
            description="Salary Credit",
            amount=50000.0,
            currency="INR",
        )
        self.assertEqual(txn.date, "2026-06-01")
        self.assertEqual(txn.amount, 50000.0)

        # Invalid date format
        with self.assertRaises(ValueError):
            Transaction(date="01/06/2026", description="Test", amount=100.0)

        # Empty description
        with self.assertRaises(ValueError):
            Transaction(date="2026-06-01", description="   ", amount=100.0)


if __name__ == "__main__":
    unittest.main()
