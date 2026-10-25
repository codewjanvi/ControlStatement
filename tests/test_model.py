"""Unit tests for local model client, prompt templates, and privacy enforcement."""

import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import json
import urllib.error

from controlstatement.config import AppConfig, get_config
from controlstatement.prompt_templates import build_analysis_prompt, PROMPT_VERSION
from controlstatement.model_client import (
    generate_ai_summary,
    is_local_model_available,
)
from controlstatement.rules import RuleAnalysisReport, CashFlowSummary, CategorySummary, RecurringItem, AnomalyItem
from controlstatement.models import Transaction


class TestModelIntegration(unittest.TestCase):
    def setUp(self):
        self.dummy_analysis = RuleAnalysisReport(
            cash_flow=CashFlowSummary(
                total_inflow=50000.0,
                total_outflow=30000.0,
                net_savings=20000.0,
                savings_rate_pct=40.0,
                currency="INR",
            ),
            categories=[
                CategorySummary(category="Dining & Food", total_amount=5000.0, percentage_of_spend=16.7, transaction_count=5),
                CategorySummary(category="Housing & Rent", total_amount=20000.0, percentage_of_spend=66.7, transaction_count=1),
            ],
            recurring=[
                RecurringItem(merchant="Netflix", typical_amount=649.0, frequency="Monthly", transaction_count=1),
            ],
            anomalies=[
                AnomalyItem(date="2026-06-15", description="Big Dinner", amount=-3000.0, category="Dining & Food", reason="Outlier"),
            ],
            total_transactions=7,
            period_start="2026-06-01",
            period_end="2026-06-30",
        )
        self.dummy_txns = [
            Transaction(date="2026-06-01", description="Salary", amount=50000.0),
            Transaction(date="2026-06-02", description="House Rent", amount=-20000.0),
        ]

    def test_privacy_enforcement_blocks_external_endpoints(self):
        # Must block remote URLs
        with self.assertRaises(ValueError):
            AppConfig(local_model_endpoint="https://api.external-cloud.com/v1")

        with self.assertRaises(ValueError):
            AppConfig(local_model_endpoint="http://192.168.1.50:11434")

        # Must allow localhost and loopback
        cfg1 = AppConfig(local_model_endpoint="http://localhost:11434")
        self.assertEqual(cfg1.local_model_endpoint, "http://localhost:11434")

        cfg2 = AppConfig(local_model_endpoint="http://127.0.0.1:11434")
        self.assertEqual(cfg2.local_model_endpoint, "http://127.0.0.1:11434")

    def test_build_analysis_prompt(self):
        prompt = build_analysis_prompt(self.dummy_analysis, self.dummy_txns)
        self.assertIn("Total Inflow / Income: 50,000.00 INR", prompt)
        self.assertIn("Total Outflow / Expenses: 30,000.00 INR", prompt)
        self.assertIn("Dining & Food", prompt)
        self.assertIn("Netflix", prompt)
        self.assertIn("Big Dinner", prompt)
        self.assertNotIn("c:\\", prompt.lower())  # Never leak filesystem paths

    @patch("urllib.request.urlopen")
    def test_mock_successful_ai_summary(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "response": "You maintained a strong 40% savings rate this month. Consider monitoring dining expenses."
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        cfg = AppConfig(local_model_endpoint="http://localhost:11434")
        summary = generate_ai_summary(self.dummy_analysis, self.dummy_txns, config=cfg)
        self.assertIn("strong 40% savings rate", summary)

    @patch("urllib.request.urlopen")
    def test_graceful_degradation_on_connection_error(self, mock_urlopen):
        # Simulate connection refused / offline server
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        cfg = AppConfig(local_model_endpoint="http://localhost:11434")
        summary = generate_ai_summary(self.dummy_analysis, self.dummy_txns, config=cfg)
        self.assertIn("unreachable", summary.lower())
        self.assertIn("rule-based", summary.lower())

    @patch("urllib.request.urlopen")
    def test_is_local_model_available_offline(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Down")
        self.assertFalse(is_local_model_available())


if __name__ == "__main__":
    unittest.main()
