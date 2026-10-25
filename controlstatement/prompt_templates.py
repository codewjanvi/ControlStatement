"""Versioned prompt templates for local LLM inference.

Privacy Guarantee: Templates receive only normalized, aggregated metrics and
transaction descriptions, never raw document text, account numbers, or PII.
"""

from typing import List
from controlstatement.rules import RuleAnalysisReport
from controlstatement.models import Transaction

PROMPT_VERSION = "1.0.0"


def build_analysis_prompt(
    analysis: RuleAnalysisReport,
    transactions: List[Transaction],
) -> str:
    """Build a versioned, structured prompt for financial summarization and nudges."""
    cf = analysis.cash_flow
    curr = cf.currency

    category_lines = []
    for cat in analysis.categories:
        category_lines.append(f"- {cat.category}: {cat.total_amount:,.2f} {curr} ({cat.percentage_of_spend:.1f}% of spend, {cat.transaction_count} txns)")

    recurring_lines = []
    for rec in analysis.recurring:
        recurring_lines.append(f"- {rec.merchant}: ~{rec.typical_amount:,.2f} {curr} ({rec.frequency})")

    anomaly_lines = []
    for anom in analysis.anomalies:
        anomaly_lines.append(f"- {anom.date}: {anom.description} ({anom.amount:,.2f} {curr}) -> Reason: {anom.reason}")

    prompt = f"""You are ControlStatement AI, a private on-device financial analyst.
Analyze the following normalized personal banking summary for the period {analysis.period_start or 'N/A'} to {analysis.period_end or 'N/A'}.

FINANCIAL METRICS:
- Total Inflow / Income: {cf.total_inflow:,.2f} {curr}
- Total Outflow / Expenses: {cf.total_outflow:,.2f} {curr}
- Net Savings: {cf.net_savings:,.2f} {curr}
- Savings Rate: {cf.savings_rate_pct:.1f}%

SPENDING BY CATEGORY:
{chr(10).join(category_lines) if category_lines else 'None recorded'}

RECURRING CHARGES & SUBSCRIPTIONS:
{chr(10).join(recurring_lines) if recurring_lines else 'None detected'}

UNUSUAL & ANOMALOUS CHARGES:
{chr(10).join(anomaly_lines) if anomaly_lines else 'None flagged'}

INSTRUCTIONS:
1. Provide a concise, plain-language monthly summary (2-3 sentences) describing the overall cash flow and financial health.
2. Highlight spending observations and category distribution.
3. Provide 2-3 specific, actionable nudges or saving suggestions based strictly on the data above.
4. Keep the tone helpful, objective, and privacy-respecting. Do NOT hallucinate data not listed above. Do not refer to yourself as a large language model.
"""
    return prompt.strip()
