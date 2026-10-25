"""Report renderer for terminal and JSON outputs."""

import json
from typing import Dict, Any, List

from controlstatement.rules import RuleAnalysisReport
from controlstatement.verifier import VerificationReport
from controlstatement.models import Transaction


def make_ascii_bar(pct: float, width: int = 16) -> str:
    """Generate a clean ASCII progress bar for percentages."""
    filled = int(round((pct / 100.0) * width))
    filled = max(0, min(width, filled))
    return "#" * filled + "-" * (width - filled)


def render_terminal_report(
    analysis: RuleAnalysisReport,
    verification: VerificationReport,
    model_summary: str = "",
) -> None:
    """Print an aesthetic, structured terminal report."""
    cf = analysis.cash_flow
    curr = cf.currency

    print("\n" + "=" * 70)
    print(" CONTROLSTATEMENT FINANCIAL INTELLIGENCE REPORT")
    print(f" Document: {verification.source_file} | Period: {analysis.period_start or 'N/A'} to {analysis.period_end or 'N/A'}")
    print(f" Statement ID: {verification.statement_id[:16]}...")
    print(f" Verification Status: [{verification.status.value}] ({'Reconciliation Exact' if verification.reconciliation_passed else 'Unverified'})")
    print("=" * 70)

    # If AI Model Summary is present
    if model_summary:
        print("\n[LOCAL AI SUMMARY & NUDGES]")
        print("-" * 70)
        print(model_summary.strip())
        print("-" * 70)

    # Cash Flow Overview
    print("\n[CASH FLOW OVERVIEW]")
    print("-" * 70)
    print(f"  * Total Income / Inflow:    +{cf.total_inflow:>12,.2f} {curr}")
    print(f"  * Total Expenses / Outflow: -{cf.total_outflow:>12,.2f} {curr}")
    net_prefix = "+" if cf.net_savings >= 0 else "-"
    print(f"  * Net Savings:               {net_prefix}{abs(cf.net_savings):>12,.2f} {curr}")
    print(f"  * Net Savings Rate:           {cf.savings_rate_pct:>12.1f} %")

    # Spending by Category
    print("\n[SPENDING BY CATEGORY]")
    print("-" * 70)
    if not analysis.categories:
        print("  No expense categories recorded.")
    else:
        print(f"  {'Category':<26} {'Amount':>12} {'Share':>7}   {'Distribution'}")
        print(f"  {'-'*26} {'-'*12} {'-'*7}   {'-'*18}")
        for cat in analysis.categories:
            bar = make_ascii_bar(cat.percentage_of_spend, width=16)
            amt_str = f"{cat.total_amount:,.2f} {curr}"
            print(f"  {cat.category:<26} {amt_str:>12} {cat.percentage_of_spend:>6.1f}%   [{bar}]")

    # Recurring Charges & Subscriptions
    print("\n[RECURRING CHARGES & SUBSCRIPTIONS]")
    print("-" * 70)
    if not analysis.recurring:
        print("  No regular recurring subscriptions detected.")
    else:
        for r in analysis.recurring:
            print(f"  * {r.merchant:<32} {r.typical_amount:>10,.2f} {curr} ({r.frequency})")

    # Anomalies & Outliers
    print("\n[ANOMALY & OUTLIER FLAGS]")
    print("-" * 70)
    if not analysis.anomalies:
        print("  No anomalous or suspicious transactions detected.")
    else:
        for a in analysis.anomalies:
            amt_str = f"{a.amount:,.2f} {curr}"
            print(f"  * [{a.date}] {a.description:<28} {amt_str:>12}")
            print(f"    Reason: {a.reason}")

    print("\n" + "=" * 70)
    print(" [Core Principle: 100% Local Inference - No financial data leaves this device]")
    print("=" * 70 + "\n")


def build_full_report_dict(
    analysis: RuleAnalysisReport,
    verification: VerificationReport,
    transactions: List[Transaction],
    model_summary: str = "",
) -> Dict[str, Any]:
    """Compile the complete report into a structured dictionary for JSON export and API."""
    data = analysis.to_dict()
    data["verification"] = verification.to_dict()
    data["model_summary"] = model_summary
    data["transactions"] = [t.to_dict() for t in transactions]
    return data
