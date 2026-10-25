"""Unit tests for offline local web server and API endpoints."""

import json
import threading
import time
import unittest
import unittest.mock
import urllib.request
from pathlib import Path
from http.server import HTTPServer
from socketserver import ThreadingMixIn

from controlstatement.web.server import DashboardHandler, run_server
from controlstatement.config import AppConfig


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded test server so concurrent requests don't block each other."""
    daemon_threads = True


class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind to localhost on an ephemeral port using a threaded server
        cls.config = AppConfig(local_model_endpoint="http://localhost:11434")
        DashboardHandler.config = cls.config
        DashboardHandler.cached_transactions = {}
        cls.server = ThreadedHTTPServer(("127.0.0.1", 0), DashboardHandler)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_privacy_enforces_localhost_binding(self):
        with self.assertRaises(ValueError):
            run_server(host="192.168.1.100", port=8080)

    def test_serve_index_html(self):
        req = urllib.request.Request(f"{self.base_url}/")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("ControlStatement", body)
            self.assertIn("On-Device", body)

    def test_serve_static_css_and_js(self):
        with urllib.request.urlopen(f"{self.base_url}/style.css", timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/css", resp.headers.get("Content-Type", ""))

        with urllib.request.urlopen(f"{self.base_url}/app.js", timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)

    def test_api_status(self):
        with urllib.request.urlopen(f"{self.base_url}/api/status", timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "online")
            self.assertEqual(data["model_name"], "gemma4:e2b")

    def test_api_fixtures(self):
        with urllib.request.urlopen(f"{self.base_url}/api/fixtures", timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("fixtures", data)
            self.assertGreater(len(data["fixtures"]), 0)

    def test_api_analyze(self):
        sample_path = Path(__file__).parent.parent / "fixtures" / "sample_statement.csv"
        payload = json.dumps({"file_path": str(sample_path), "skip_model": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/analyze",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("cash_flow", data)
            self.assertEqual(data["cash_flow"]["net_savings"], 26881.0)
            self.assertEqual(data["verification"]["status"], "PASS")
            self.assertIn("monthly_trends", data)

    @unittest.mock.patch("controlstatement.web.server.answer_question", return_value="Mocked answer for test.")
    def test_api_ask(self, _mock_answer):
        """Mock the LLM call so the test doesn't depend on Ollama being responsive."""
        # First populate the cache via analyze
        sample_path = Path(__file__).parent.parent / "fixtures" / "sample_statement.csv"
        payload = json.dumps({"file_path": str(sample_path), "skip_model": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/analyze",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8.0):
            pass

        payload = json.dumps({"question": "Test question?", "doc_name": "sample_statement.csv"}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/ask",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("answer", data)


if __name__ == "__main__":
    unittest.main()
