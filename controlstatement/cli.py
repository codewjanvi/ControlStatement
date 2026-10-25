"""Command-line interface for ControlStatement."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from controlstatement.parsers.detector import parse_document

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def print_table(transactions: List) -> None:
    """Format and display transactions as a readable terminal table."""
    if not transactions:
        print("No transactions found.")
        return

    headers = ["Date", "Description", "Amount", "Balance", "Ref"]
    col_widths = [12, 38, 14, 14, 12]

    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    divider_line = "-+-".join("-" * w for w in col_widths)

    print(header_line)
    print(divider_line)

    for txn in transactions:
        amt_str = f"{txn.amount:+.2f} {txn.currency}"
        bal_str = f"{txn.balance:.2f}" if txn.balance is not None else "-"
        desc_str = txn.description[:36] + ".." if len(txn.description) > 38 else txn.description
        ref_str = (txn.reference_no or "-")[:12]

        row = [
            txn.date.ljust(col_widths[0]),
            desc_str.ljust(col_widths[1]),
            amt_str.rjust(col_widths[2]),
            bal_str.rjust(col_widths[3]),
            ref_str.ljust(col_widths[4]),
        ]
        print(" | ".join(row))

    print(divider_line)
    credits = sum(t.amount for t in transactions if t.amount > 0)
    debits = sum(abs(t.amount) for t in transactions if t.amount < 0)
    print(f"Total Transactions: {len(transactions)} | Credits: +{credits:.2f} | Debits: -{debits:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="controlstatement",
        description="ControlStatement - Privacy-first local AI banking document analysis",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # parse subcommand
    parse_parser = subparsers.add_parser("parse", help="Parse and normalize a banking document (PDF/CSV)")
    parse_parser.add_argument("file", help="Path to the PDF or CSV statement")
    parse_parser.add_argument("--json", action="store_true", help="Output raw JSON array of transactions")
    parse_parser.add_argument("--currency", default="INR", help="Default currency (default: INR)")

    # verify subcommand
    verify_parser = subparsers.add_parser("verify", help="Verify statement balance reconciliation and integrity")
    verify_parser.add_argument("file", help="Path to the statement file to verify")
    verify_parser.add_argument("--json", action="store_true", help="Output raw JSON verification report")
    verify_parser.add_argument("--currency", default="INR", help="Default currency (default: INR)")

    # report subcommand
    report_parser = subparsers.add_parser("report", help="Generate financial intelligence analysis report")
    report_parser.add_argument("file", help="Path to the statement file")
    report_parser.add_argument("--json", action="store_true", help="Output structured JSON report")
    report_parser.add_argument("--currency", default="INR", help="Default currency (default: INR)")
    report_parser.add_argument("--model", action="store_true", default=False, help="Enable local AI model summary and nudges")
    report_parser.add_argument("--no-model", action="store_true", default=False, help="Run pure rule-based analysis without calling local LLM")
    report_parser.add_argument("--output", help="Save report to specified JSON file path")
    # ask subcommand
    ask_parser = subparsers.add_parser("ask", help="Ask plain-language questions about your transactions")
    ask_parser.add_argument("question", help="Question about your spending (e.g. 'How much did I spend on dining?')")
    ask_parser.add_argument("--file", "-f", required=True, help="Path to statement file to query")
    ask_parser.add_argument("--currency", default="INR", help="Default currency (default: INR)")
    # serve subcommand
    serve_parser = subparsers.add_parser("serve", help="Launch the local private web UI dashboard")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1 strictly)")
    serve_parser.add_argument("--port", type=int, default=8080, help="Local port (default: 8080)")
    serve_parser.add_argument("--open", action="store_true", default=False, help="Automatically open dashboard in browser")
    # tax subcommand (Phase 7)
    tax_parser = subparsers.add_parser("tax", help="Tag tax-relevant transactions and export a CSV for review")
    tax_parser.add_argument("file", help="Path to statement file")
    tax_parser.add_argument("--currency", default="INR", help="Default currency (default: INR)")
    tax_parser.add_argument("--export", help="Export tax-tagged CSV to this file path")
    tax_parser.add_argument("--json", action="store_true", help="Output JSON list of tagged transactions")
    # budget subcommand (Phase 7)
    budget_parser = subparsers.add_parser("budget", help="Compare actual spending against monthly category budgets")
    budget_parser.add_argument("file", help="Path to statement file")
    budget_parser.add_argument("--currency", default="INR", help="Default currency (default: INR)")
    budget_parser.add_argument("--json", action="store_true", help="Output structured JSON budget report")

    args = parser.parse_args()

    if args.command == "parse":
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            transactions, summary = parse_document(file_path, currency=args.currency)
        except Exception as e:
            print(f"Error parsing document: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            result = [t.to_dict() for t in transactions]
            print(json.dumps(result, indent=2))
        else:
            print(f"\nDocument: {summary.source_file}")
            print(f"Statement ID (SHA-256): {summary.statement_id[:16]}...")
            if summary.opening_balance is not None or summary.closing_balance is not None:
                print(f"Opening Balance: {summary.opening_balance} | Closing Balance: {summary.closing_balance}")
            print()
            print_table(transactions)

    elif args.command == "verify":
        from controlstatement.verifier import verify_statement

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            transactions, summary = parse_document(file_path, currency=args.currency)
            report = verify_statement(transactions, summary)
        except Exception as e:
            print(f"Error during verification: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            status_symbol = {
                "PASS": "[PASS] - Statement integrity verified",
                "WARN": "[WARN] - Needs review",
                "FAIL": "[FAIL] - Integrity check failed",
            }.get(report.status.value, report.status.value)

            print(f"\nVerification Status: {status_symbol}")
            print(f"Document: {report.source_file}")
            print(f"Statement ID: {report.statement_id[:16]}...")
            print("-" * 60)
            if report.reconciliation_checked:
                print(f"Opening Balance:   {report.opening_balance:.2f}")
                print(f"Closing Balance:   {report.closing_balance:.2f}")
                print(f"Computed Closing:  {report.computed_closing:.2f}")
                print(f"Difference:        {report.reconciliation_difference:.2f}")
            print(f"Running Balance Sequence: {'PASSED' if report.running_balance_passed else 'FAILED'}")
            print(f"Duplicate Transactions:   {report.duplicate_count}")
            print("-" * 60)
            print("Diagnostics:")
            for reason in report.reasons:
                print(f"  * {reason}")
            print()

        if report.status.value == "FAIL":
            sys.exit(2)

    elif args.command == "report":
        from controlstatement.verifier import verify_statement
        from controlstatement.rules import analyze_transactions
        from controlstatement.report import render_terminal_report, build_full_report_dict

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            transactions, summary = parse_document(file_path, currency=args.currency)
            verification = verify_statement(transactions, summary)
            analysis = analyze_transactions(transactions)
        except Exception as e:
            print(f"Error generating report: {e}", file=sys.stderr)
            sys.exit(1)

        model_summary = ""
        from controlstatement.model_client import generate_ai_summary, is_local_model_available
        from controlstatement.config import get_config

        cfg = get_config()
        # If --no-model is passed, skip. If --model is passed, run. If neither, auto-run if model is running.
        should_run_model = args.model or (not args.no_model and is_local_model_available(cfg))
        if args.no_model:
            should_run_model = False

        if should_run_model:
            if not args.json:
                print(f"Generating AI insights via local model '{cfg.local_model_name}' on localhost...")
            model_summary = generate_ai_summary(analysis, transactions, config=cfg)

        report_dict = build_full_report_dict(analysis, verification, transactions, model_summary=model_summary)

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2)
            print(f"Report saved to: {out_path}")

        if args.json:
            print(json.dumps(report_dict, indent=2))
        else:
            render_terminal_report(analysis, verification, model_summary=model_summary)

    elif args.command == "ask":
        from controlstatement.qa import answer_question
        from controlstatement.rules import assign_categories
        from controlstatement.config import get_config

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            transactions, _ = parse_document(file_path, currency=args.currency)
            assign_categories(transactions)
        except Exception as e:
            print(f"Error loading document: {e}", file=sys.stderr)
            sys.exit(1)

        cfg = get_config()
        print(f"\nQuerying local model '{cfg.local_model_name}' on transactions from {file_path.name}...")
        print(f"Question: \"{args.question}\"\n")
        response = answer_question(args.question, transactions, config=cfg)
        print("Answer:")
        print(response)
        print()

    elif args.command == "serve":
        from controlstatement.web.server import run_server
        from controlstatement.config import get_config

        cfg = get_config()
        run_server(host=args.host, port=args.port, open_browser=args.open, config=cfg)

    elif args.command == "tax":
        from controlstatement.tax_tagger import tag_tax_transactions, export_tax_csv
        from controlstatement.rules import assign_categories
        import json as _json

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            transactions, _ = parse_document(file_path, currency=args.currency)
            assign_categories(transactions)
            tagged = tag_tax_transactions(transactions)
        except Exception as e:
            print(f"Error during tax tagging: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(_json.dumps([t.to_dict() for t in tagged], indent=2))
        elif args.export:
            export_path = Path(args.export)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            csv_content = export_tax_csv(tagged)
            export_path.write_text(csv_content, encoding="utf-8")
            print(f"Tax-tagged CSV exported to: {export_path}")
            print(f"Total tax-relevant transactions: {len(tagged)}")
        else:
            print(f"\n[TAX-RELEVANT TRANSACTIONS] — {file_path.name}")
            print("-" * 70)
            print(f"  {'Date':<12} {'Description':<36} {'Amount':>12}  Tax Category")
            print(f"  {'-'*12} {'-'*36} {'-'*12}  {'-'*26}")
            for t in tagged:
                print(f"  {t.date:<12} {t.description[:36]:<36} {t.amount:>12.2f}  {t.tax_category}")
            print("-" * 70)
            print(f"  Total potentially deductible: {len(tagged)} transactions")
            print(f"  Tip: Use --export <path.csv> to save for your accountant\n")

    elif args.command == "budget":
        from controlstatement.budget import compare_budget_vs_actuals
        from controlstatement.rules import analyze_transactions
        import json as _json

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            transactions, _ = parse_document(file_path, currency=args.currency)
            analysis = analyze_transactions(transactions)
            budget_report = compare_budget_vs_actuals(analysis.categories, currency=args.currency)
        except Exception as e:
            print(f"Error during budget analysis: {e}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(_json.dumps(budget_report.to_dict(), indent=2))
        else:
            curr = args.currency
            print(f"\n[BUDGET VS. ACTUALS REPORT] — {file_path.name}")
            print("=" * 72)
            status_icons = {"OK": "✓", "WARN": "!", "OVER": "✗"}
            print(f"  {'Category':<28} {'Budget':>10} {'Actual':>10} {'Variance':>10}  Status")
            print(f"  {'-'*28} {'-'*10} {'-'*10} {'-'*10}  {'-'*6}")
            for b in budget_report.budget_lines:
                icon = status_icons.get(b.status, "?")
                bud_str = f"{b.budgeted:>10,.0f}" if b.budgeted > 0 else f"{'(no budget)':>10}"
                print(f"  {b.category:<28} {bud_str} {b.actual:>10,.0f} {b.variance:>+10,.0f}  [{icon}] {b.status}")
            print("=" * 72)
            print(f"  Total Budgeted:  {budget_report.total_budgeted:>10,.0f} {curr}")
            print(f"  Total Actual:    {budget_report.total_actual:>10,.0f} {curr}")
            variance_prefix = "+" if budget_report.total_variance >= 0 else ""
            print(f"  Net Variance:    {variance_prefix}{budget_report.total_variance:>10,.0f} {curr}")
            print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
