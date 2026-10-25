"""Command-line interface for ControlStatement."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from controlstatement.parsers.detector import parse_document


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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
