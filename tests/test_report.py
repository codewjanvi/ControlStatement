"""Unit tests for report renderer and JSON schema validation."""

import unittest
from pathlib import Path

from controlstatement.parsers.csv_parser import parse_csv_statement
from controlstatement.verifier import verify_statement
from controlstatement.rules import analyze_transactions
from controlstatement.report import build_full_report_dict, make_ascii_bar


class TestReport(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"

    def test_ascii_bar(self):
        self.assertEqual(make_ascii_bar(0, 10), "----------")
        self.assertEqual(make_ascii_bar(50, 10), "#####-----")
        self.assertEqual(make_ascii_bar(100, 10), "##########")

    def test_build_full_report_dict(self):
        txns, summary = parse_csv_statement(self.fixtures_dir / "sample_statement.csv")
        verification = verify_statement(txns, summary)
        analysis = analyze_transactions(txns)

        report = build_full_report_dict(analysis, verification, txns, model_summary="Test model summary")

        self.assertIn("cash_flow", report)
        self.assertIn("categories", report)
        self.assertIn("recurring", report)
        self.assertIn("anomalies", report)
        self.assertIn("verification", report)
        self.assertIn("transactions", report)
        self.assertEqual(report["model_summary"], "Test model summary")
        self.assertEqual(report["verification"]["status"], "PASS")
        self.assertEqual(report["cash_flow"]["net_savings"], 26881.0)


if __name__ == "__main__":
    unittest.main()
