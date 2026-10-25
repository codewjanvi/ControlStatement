"""Unit tests for rule-based financial analysis engine."""

import unittest
from pathlib import Path

from controlstatement.parsers.csv_parser import parse_csv_statement
from controlstatement.parsers.pdf_parser import parse_pdf_statement
from controlstatement.rules import (
    analyze_transactions,
    assign_categories,
    detect_recurring_charges,
    detect_anomalies,
)
from controlstatement.models import Transaction


class TestRulesEngine(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"

    def test_assign_categories(self):
        txns = [
            Transaction(date="2026-06-01", description="Swiggy Delivery", amount=-450.0),
            Transaction(date="2026-06-02", description="Reliance Fresh Store", amount=-1200.0),
            Transaction(date="2026-06-03", description="House Rent Payment", amount=-20000.0),
            Transaction(date="2026-06-04", description="Tata Power Bill", amount=-1800.0),
            Transaction(date="2026-06-05", description="Netflix Streaming", amount=-649.0),
            Transaction(date="2026-06-06", description="Salary Deposit", amount=85000.0),
            Transaction(date="2026-06-07", description="Uber Trip", amount=-320.0),
        ]
        assign_categories(txns)

        self.assertEqual(txns[0].category, "Dining & Food")
        self.assertEqual(txns[1].category, "Groceries")
        self.assertEqual(txns[2].category, "Housing & Rent")
        self.assertEqual(txns[3].category, "Utilities & Bills")
        self.assertEqual(txns[4].category, "Subscriptions & Streaming")
        self.assertEqual(txns[5].category, "Income")
        self.assertEqual(txns[6].category, "Transportation & Travel")

    def test_recurring_charges_detection(self):
        txns = [
            Transaction(date="2026-05-08", description="Netflix.com", amount=-649.0),
            Transaction(date="2026-06-08", description="Netflix.com", amount=-649.0),
            Transaction(date="2026-06-15", description="One-off Dinner", amount=-800.0),
        ]
        recurring = detect_recurring_charges(txns)
        self.assertGreaterEqual(len(recurring), 1)
        self.assertIn("netflix", recurring[0].merchant.lower())
        self.assertEqual(recurring[0].typical_amount, 649.0)

    def test_anomaly_detection(self):
        txns = [
            Transaction(date="2026-06-01", description="Coffee Shop", amount=-150.0, category="Dining & Food"),
            Transaction(date="2026-06-05", description="Lunch", amount=-250.0, category="Dining & Food"),
            Transaction(date="2026-06-10", description="Dinner", amount=-300.0, category="Dining & Food"),
            # Anomaly: 3000 in dining (> 3x category average)
            Transaction(date="2026-06-15", description="Super Fancy Banquet", amount=-3000.0, category="Dining & Food"),
            # Anomaly: large round number
            Transaction(date="2026-06-20", description="Electronics Store", amount=-20000.0, category="Shopping & Retail"),
        ]
        anomalies = detect_anomalies(txns)
        self.assertEqual(len(anomalies), 2)
        descriptions = [a.description for a in anomalies]
        self.assertIn("Super Fancy Banquet", descriptions)
        self.assertIn("Electronics Store", descriptions)

    def test_cash_flow_aggregation_on_csv_fixture(self):
        txns, _ = parse_csv_statement(self.fixtures_dir / "sample_statement.csv")
        report = analyze_transactions(txns)

        self.assertEqual(report.cash_flow.total_inflow, 75000.0)
        self.assertEqual(report.cash_flow.total_outflow, 48119.0)
        self.assertEqual(report.cash_flow.net_savings, 26881.0)
        self.assertAlmostEqual(report.cash_flow.savings_rate_pct, 35.8, places=1)
        self.assertEqual(report.total_transactions, 9)

        # Check category percentages sum up to ~100%
        total_pct = sum(c.percentage_of_spend for c in report.categories)
        self.assertAlmostEqual(total_pct, 100.0, delta=0.5)

    def test_cash_flow_aggregation_on_pdf_fixture(self):
        txns, _ = parse_pdf_statement(self.fixtures_dir / "sample_statement.pdf")
        report = analyze_transactions(txns)

        self.assertEqual(report.cash_flow.total_inflow, 80000.0)
        self.assertEqual(report.cash_flow.total_outflow, 58408.0)
        self.assertEqual(report.cash_flow.net_savings, 21592.0)
        self.assertAlmostEqual(report.cash_flow.savings_rate_pct, 27.0, places=1)


if __name__ == "__main__":
    unittest.main()
