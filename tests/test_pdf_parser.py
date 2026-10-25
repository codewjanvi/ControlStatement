"""Unit tests for PDF bank statement parser."""

from pathlib import Path
import unittest
from controlstatement.parsers.pdf_parser import parse_pdf_statement


class TestPdfParser(unittest.TestCase):
    def setUp(self):
        self.fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_statement.pdf"

    def test_parse_pdf_statement(self):
        txns, summary = parse_pdf_statement(self.fixture_path, currency="INR")

        self.assertEqual(len(txns), 9)
        self.assertEqual(summary.opening_balance, 12500.0)
        self.assertEqual(summary.closing_balance, 34092.0)
        self.assertEqual(summary.total_credit, 80000.0)
        self.assertEqual(summary.total_debit, 58408.0)

        # First transaction: Salary credit
        first = txns[0]
        self.assertEqual(first.date, "2026-06-02")
        self.assertEqual(first.description, "Salary Deposit TechCorp")
        self.assertEqual(first.amount, 80000.0)
        self.assertEqual(first.balance, 92500.0)

        # Second transaction: Rent debit
        second = txns[1]
        self.assertEqual(second.date, "2026-06-04")
        self.assertEqual(second.description, "Rent Payment Landlord")
        self.assertEqual(second.amount, -22000.0)
        self.assertEqual(second.balance, 70500.0)


if __name__ == "__main__":
    unittest.main()
