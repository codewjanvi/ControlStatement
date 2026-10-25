"""Lightweight, offline local web server for ControlStatement dashboard."""

import json
import mimetypes
import os
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

from controlstatement.config import AppConfig, get_config
from controlstatement.parsers.detector import parse_document
from controlstatement.verifier import verify_statement
from controlstatement.rules import analyze_transactions, assign_categories
from controlstatement.report import build_full_report_dict
from controlstatement.model_client import generate_ai_summary, is_local_model_available
from controlstatement.qa import answer_question
from controlstatement.tax_tagger import tag_tax_transactions, export_tax_csv
from controlstatement.budget import compare_budget_vs_actuals

STATIC_DIR = Path(__file__).parent / "static"


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for ControlStatement web dashboard."""

    config: AppConfig = get_config()
    cached_transactions = {}
    cached_analysis = {}

    def log_message(self, format, *args):
        # Override to prevent logging of sensitive query params or details
        if self.config.log_level == "DEBUG":
            super().log_message(format, *args)

    def _send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self.send_error(404, "File not found")
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path in ("/", "/index.html"):
            self._send_file(STATIC_DIR / "index.html")
        elif path == "/style.css":
            self._send_file(STATIC_DIR / "style.css")
        elif path == "/app.js":
            self._send_file(STATIC_DIR / "app.js")
        elif path == "/api/status":
            model_online = is_local_model_available(self.config, timeout=1.0)
            self._send_json({
                "status": "online",
                "model_name": self.config.local_model_name,
                "model_online": model_online,
                "currency": self.config.default_currency,
            })
        elif path == "/api/fixtures":
            fixtures_dir = Path(__file__).parent.parent.parent / "fixtures"
            files = []
            if fixtures_dir.is_dir():
                for f in fixtures_dir.glob("*.*"):
                    if f.suffix.lower() in (".csv", ".pdf"):
                        files.append({"name": f.name, "path": str(f.resolve())})
            self._send_json({"fixtures": files})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b""

        if path == "/api/analyze":
            try:
                data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                file_target = data.get("file_path")
                # Fast response mode: default skip_model=True unless explicitly requested
                skip_model = data.get("skip_model", True)

                if not file_target:
                    default_fixture = Path(__file__).parent.parent.parent / "fixtures" / "sample_statement.csv"
                    file_target = str(default_fixture)

                target_path = Path(file_target)
                if not target_path.is_file():
                    self._send_json({"error": f"File not found: {file_target}"}, status=400)
                    return

                transactions, summary = parse_document(target_path, currency=self.config.default_currency)
                verification = verify_statement(transactions, summary)
                analysis = analyze_transactions(transactions)

                model_summary = ""
                if not skip_model and is_local_model_available(self.config, timeout=0.5):
                    model_summary = generate_ai_summary(analysis, transactions, config=self.config)

                # Phase 7: tax tagging and budget
                tagged = tag_tax_transactions(transactions)
                budget_report = compare_budget_vs_actuals(
                    analysis.categories,
                    currency=self.config.default_currency,
                )

                report = build_full_report_dict(analysis, verification, transactions, model_summary=model_summary)
                report["tax_tagged"] = [t.to_dict() for t in tagged]
                report["budget"] = budget_report.to_dict()
                # Cache transactions and analysis in memory for instantaneous Q&A and AI summary
                DashboardHandler.cached_transactions[target_path.name] = transactions
                DashboardHandler.cached_analysis[target_path.name] = (analysis, transactions)

                self._send_json(report)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif path == "/api/ai-summary":
            # Asynchronous dedicated endpoint for AI insights
            try:
                data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                doc_name = data.get("doc_name", "")
                cached = DashboardHandler.cached_analysis.get(doc_name)
                if cached:
                    analysis, transactions = cached
                else:
                    file_path = data.get("file_path")
                    target = Path(file_path) if file_path else (Path(__file__).parent.parent.parent / "fixtures" / "sample_statement.csv")
                    transactions, _ = parse_document(target, currency=self.config.default_currency)
                    analysis = analyze_transactions(transactions)
                    DashboardHandler.cached_analysis[doc_name or target.name] = (analysis, transactions)
                    DashboardHandler.cached_transactions[doc_name or target.name] = transactions

                if is_local_model_available(self.config, timeout=0.5):
                    model_summary = generate_ai_summary(analysis, transactions, config=self.config)
                else:
                    model_summary = "[Notice: Local AI model is offline. Rule-based financial analysis remains active.]"

                self._send_json({"model_summary": model_summary})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif path == "/api/upload":
            # Handle direct file upload in memory/temp directory with instant response
            filename = self.headers.get("X-Filename", "uploaded_statement.csv")
            safe_name = Path(filename).name
            upload_dir = Path(__file__).parent.parent.parent / "data" / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            saved_path = upload_dir / safe_name
            with open(saved_path, "wb") as f:
                f.write(raw_body)

            try:
                transactions, summary = parse_document(saved_path, currency=self.config.default_currency)
                verification = verify_statement(transactions, summary)
                analysis = analyze_transactions(transactions)

                tagged = tag_tax_transactions(transactions)
                budget_report = compare_budget_vs_actuals(
                    analysis.categories,
                    currency=self.config.default_currency,
                )
                report = build_full_report_dict(analysis, verification, transactions, model_summary="")
                report["tax_tagged"] = [t.to_dict() for t in tagged]
                report["budget"] = budget_report.to_dict()
                DashboardHandler.cached_transactions[safe_name] = transactions
                DashboardHandler.cached_analysis[safe_name] = (analysis, transactions)
                self._send_json(report)
            except Exception as e:
                self._send_json({"error": f"Failed to parse uploaded document: {e}"}, status=500)

        elif path == "/api/ask":
            try:
                data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                question = data.get("question", "").strip()
                doc_name = data.get("doc_name", "")

                if not question:
                    self._send_json({"error": "Empty question"}, status=400)
                    return

                # Retrieve transactions from cache or load default
                txns = DashboardHandler.cached_transactions.get(doc_name)
                if not txns:
                    # Fallback to sample fixture
                    default_fixture = Path(__file__).parent.parent.parent / "fixtures" / "sample_statement.csv"
                    txns, _ = parse_document(default_fixture, currency=self.config.default_currency)
                    assign_categories(txns)

                answer = answer_question(question, txns, config=self.config)
                self._send_json({"question": question, "answer": answer})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif path == "/api/tax-export":
            # Export tax-tagged transactions as downloadable CSV
            try:
                data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                doc_name = data.get("doc_name", "")
                txns = DashboardHandler.cached_transactions.get(doc_name)
                if not txns:
                    default_fixture = Path(__file__).parent.parent.parent / "fixtures" / "sample_statement.csv"
                    txns, _ = parse_document(default_fixture, currency=self.config.default_currency)
                    assign_categories(txns)
                tagged = tag_tax_transactions(txns)
                csv_str = export_tax_csv(tagged)
                payload = csv_str.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="tax_tagged_transactions.csv"')
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            self.send_error(404, "Not Found")


def run_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    open_browser: bool = False,
    config: Optional[AppConfig] = None,
) -> None:
    """Start the privacy-enforced local web dashboard."""
    cfg = config or get_config()
    # Enforce strictly local binding
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError(f"Privacy error: Web dashboard must only bind to localhost, got {host}")

    DashboardHandler.config = cfg
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    url = f"http://{host}:{port}"
    print(f"\n==============================================================")
    print(f" CONTROLSTATEMENT PRIVATE LOCAL DASHBOARD")
    print(f" Web UI Running at: {url}")
    print(f" Local Model:       {cfg.local_model_name} (Ollama)")
    print(f" Privacy Guarantee: 100% Offline, Zero Cloud Requests")
    print(f" Press Ctrl+C to stop server")
    print(f"==============================================================\n")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping dashboard server...")
        server.server_close()
