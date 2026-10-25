"""Unit tests for CSV bank statement parser."""

from pathlib import Path
import unittest
from controlstatement.parsers.csv_parser import parse_csv_statement


class TestCsvParser(unittest.TestCase):
    def setUp(self):
        self.fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_statement.csv"

    def test_parse_csv_statement(self):
        txns, summary = parse_csv_statement(self.fixture_path, currency="INR")

        self.assertEqual(len(txns), 9)
        self.assertEqual(summary.opening_balance, 10000.0)
        self.assertEqual(summary.closing_balance, 36881.0)
        self.assertEqual(summary.total_credit, 75000.0)
        self.assertEqual(summary.total_debit, 48119.0)

        # Check first transaction
        first = txns[0]
        self.assertEqual(first.date, "2026-06-02")
        self.assertEqual(first.description, "Salary Credit - Corp Inc")
        self.assertEqual(first.amount, 75000.0)
        self.assertEqual(first.reference_no, "TXN10001")
        self.assertEqual(first.balance, 85000.0)

        # Check debit transaction
        rent = txns[1]
        self.assertEqual(rent.date, "2026-06-03")
        self.assertEqual(rent.description, "House Rent Transfer")
        self.assertEqual(rent.amount, -25000.0)
        self.assertEqual(rent.balance, 60000.0)


if __name__ == "__main__":
    unittest.main()
