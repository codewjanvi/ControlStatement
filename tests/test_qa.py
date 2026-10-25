"""Unit tests for Natural-Language Q&A engine."""

import unittest
from unittest.mock import patch, MagicMock
import json
import urllib.error

from controlstatement.qa import build_qa_prompt, answer_question
from controlstatement.models import Transaction
from controlstatement.config import AppConfig


class TestQAEngine(unittest.TestCase):
    def setUp(self):
        self.sample_txns = [
            Transaction(date="2026-06-05", description="Swiggy Order #8821", amount=-450.0, category="Dining & Food"),
            Transaction(date="2026-06-15", description="Swiggy Order #8934", amount=-520.0, category="Dining & Food"),
            Transaction(date="2026-06-20", description="Zomato Dining Out", amount=-1450.0, category="Dining & Food"),
            Transaction(date="2026-06-08", description="Netflix Subscription", amount=-649.0, category="Subscriptions & Streaming"),
        ]

    def test_build_qa_prompt(self):
        prompt = build_qa_prompt("How much did I spend on Swiggy?", self.sample_txns)
        self.assertIn("GUARDRAILS", prompt)
        self.assertIn("Swiggy Order #8821", prompt)
        self.assertIn("-450.00 INR", prompt)
        self.assertIn("USER QUESTION: How much did I spend on Swiggy?", prompt)

    @patch("urllib.request.urlopen")
    def test_answer_question_mocked(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "response": "You spent a total of 970.00 INR on Swiggy across 2 orders (450.00 INR on June 5 and 520.00 INR on June 15)."
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        cfg = AppConfig(local_model_endpoint="http://localhost:11434")
        answer = answer_question("How much did I spend on Swiggy?", self.sample_txns, config=cfg)
        self.assertIn("970.00 INR on Swiggy", answer)

    def test_answer_question_empty_transactions(self):
        answer = answer_question("Any questions?", [])
        self.assertIn("No transactions are available", answer)

    @patch("urllib.request.urlopen")
    def test_answer_question_unreachable(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        cfg = AppConfig(local_model_endpoint="http://localhost:11434")
        answer = answer_question("What did I spend?", self.sample_txns, config=cfg)
        self.assertIn("unreachable", answer.lower())


if __name__ == "__main__":
    unittest.main()
