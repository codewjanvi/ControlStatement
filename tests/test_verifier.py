"""Unit tests for statement verifier."""

from pathlib import Path
import unittest

from controlstatement.parsers.csv_parser import parse_csv_statement
from controlstatement.parsers.pdf_parser import parse_pdf_statement
from controlstatement.verifier import verify_statement, Status
from controlstatement.models import Transaction, StatementSummary


class TestVerifier(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"

    def test_verify_valid_csv_passes(self):
        txns, summary = parse_csv_statement(self.fixtures_dir / "sample_statement.csv")
        report = verify_statement(txns, summary)
        self.assertEqual(report.status, Status.PASS)
        self.assertTrue(report.reconciliation_passed)
        self.assertTrue(report.running_balance_passed)
        self.assertEqual(report.reconciliation_difference, 0.0)
        self.assertEqual(report.duplicate_count, 0)

    def test_verify_valid_pdf_passes(self):
        txns, summary = parse_pdf_statement(self.fixtures_dir / "sample_statement.pdf")
        report = verify_statement(txns, summary)
        self.assertEqual(report.status, Status.PASS)
        self.assertTrue(report.reconciliation_passed)
        self.assertTrue(report.running_balance_passed)
        self.assertEqual(report.reconciliation_difference, 0.0)
        self.assertEqual(report.duplicate_count, 0)

    def test_verify_tampered_reconciliation_fails(self):
        txns, summary = parse_csv_statement(self.fixtures_dir / "tampered_statement.csv")
        report = verify_statement(txns, summary)
        self.assertEqual(report.status, Status.FAIL)
        self.assertFalse(report.reconciliation_passed)
        self.assertGreater(report.reconciliation_difference, 1000)

    def test_verify_running_balance_divergence_fails(self):
        # Create a statement with broken running balance sequence
        summary = StatementSummary(
            source_file="test.csv",
            statement_id="hash123",
            opening_balance=1000.0,
            closing_balance=1500.0,
        )
        txns = [
            Transaction(date="2026-06-01", description="Credit 1", amount=300.0, balance=1300.0),
            Transaction(date="2026-06-02", description="Credit 2", amount=200.0, balance=1999.0),  # Divergence
        ]
        report = verify_statement(txns, summary)
        self.assertEqual(report.status, Status.FAIL)
        self.assertFalse(report.running_balance_passed)
        self.assertEqual(len(report.divergent_rows), 1)

    def test_verify_duplicate_transactions_warns(self):
        summary = StatementSummary(
            source_file="test.csv",
            statement_id="hash123",
            opening_balance=1000.0,
            closing_balance=1500.0,
        )
        txns = [
            Transaction(date="2026-06-01", description="Charge A", amount=-100.0, balance=900.0),
            Transaction(date="2026-06-01", description="Charge A", amount=-100.0, balance=800.0),  # Duplicate
            Transaction(date="2026-06-02", description="Deposit", amount=700.0, balance=1500.0),
        ]
        report = verify_statement(txns, summary)
        self.assertEqual(report.status, Status.WARN)
        self.assertEqual(report.duplicate_count, 1)

    def test_verify_missing_balances_warns(self):
        summary = StatementSummary(
            source_file="test.csv",
            statement_id="hash123",
            opening_balance=None,
            closing_balance=None,
        )
        txns = [
            Transaction(date="2026-06-01", description="Charge", amount=-50.0),
        ]
        report = verify_statement(txns, summary)
        self.assertEqual(report.status, Status.WARN)
        self.assertFalse(report.reconciliation_checked)


if __name__ == "__main__":
    unittest.main()
