"""Rule-based analysis engine for ControlStatement.

Includes:
1. Category keyword matcher with sensible defaults and override support
2. Recurring charge and subscription detector
3. Anomaly detector (outliers, round numbers, large unexpected debits)
4. Cash flow aggregator (income, outflow, net savings, savings rate, MoM)
"""

from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import statistics
import re

from controlstatement.models import Transaction

# Default category keyword rules (case-insensitive substring matches)
DEFAULT_CATEGORY_RULES: Dict[str, List[str]] = {
    "Income": [
        "salary", "payroll", "corp inc", "techcorp", "dividend", "interest",
        "stipend", "bonus", "reimbursement", "deposit corp",
    ],
    "Housing & Rent": [
        "rent", "house rent", "landlord", "maintenance fee", "society",
        "apartment", "mortgage", "housing",
    ],
    "Dining & Food": [
        "swiggy", "zomato", "restaurant", "cafe", "coffee", "starbucks",
        "mcdonald", "burger", "pizza", "subway", "bistro", "dining", "eats",
    ],
    "Groceries": [
        "reliance fresh", "bigbasket", "blinkit", "zepto", "supermarket",
        "grocery", "dmart", "instamart", "spencer", "nature basket", "mart",
    ],
    "Utilities & Bills": [
        "electricity", "power", "tata power", "bescom", "water bill",
        "gas bill", "broadband", "wifi", "airtel", "jio", "vodafone",
        "utility", "recharge", "mobile bill",
    ],
    "Subscriptions & Streaming": [
        "netflix", "spotify", "prime video", "amazon prime", "hotstar",
        "youtube", "disney", "apple.com/bill", "google play", "gym", "membership",
    ],
    "Shopping & Retail": [
        "amazon", "flipkart", "myntra", "retail", "zara", "h&m", "nike",
        "watch gallery", "electronics", "store", "mall",
    ],
    "Transportation & Travel": [
        "uber", "ola", "rapido", "metro", "fuel", "petrol", "diesel",
        "indian oil", "hpcl", "bpcl", "flight", "indigo", "air india",
        "irctc", "railway", "makemytrip", "parking", "toll", "fastag",
    ],
    "Health & Wellness": [
        "pharmacy", "apollo", "medplus", "hospital", "clinic", "medical",
        "doctor", "1mg", "pharmeasy", "dentist", "lab",
    ],
    "Investments & Transfers": [
        "zerodha", "groww", "mutual fund", "sip", "fixed deposit",
        "ppf", "nps", "transfer", "neft", "rtgs", "imps",
    ],
}


@dataclass
class RecurringItem:
    merchant: str
    typical_amount: float
    frequency: str
    transaction_count: int
    transactions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AnomalyItem:
    date: str
    description: str
    amount: float
    category: str
    reason: str


@dataclass
class CategorySummary:
    category: str
    total_amount: float
    percentage_of_spend: float
    transaction_count: int


@dataclass
class CashFlowSummary:
    total_inflow: float
    total_outflow: float
    net_savings: float
    savings_rate_pct: float
    currency: str = "INR"


@dataclass
class RuleAnalysisReport:
    cash_flow: CashFlowSummary
    categories: List[CategorySummary]
    recurring: List[RecurringItem]
    anomalies: List[AnomalyItem]
    total_transactions: int
    period_start: Optional[str] = None
    period_end: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cash_flow": asdict(self.cash_flow),
            "categories": [asdict(c) for c in self.categories],
            "recurring": [asdict(r) for r in self.recurring],
            "anomalies": [asdict(a) for a in self.anomalies],
            "total_transactions": self.total_transactions,
            "period_start": self.period_start,
            "period_end": self.period_end,
        }


def assign_categories(
    transactions: List[Transaction],
    custom_rules: Optional[Dict[str, List[str]]] = None,
) -> None:
    """Categorize transactions in-place using keyword rules."""
    rules = custom_rules or DEFAULT_CATEGORY_RULES

    for txn in transactions:
        desc_lower = txn.description.lower()

        # If already categorized, keep it
        if txn.category and txn.category != "Uncategorized":
            continue

        # If positive income
        if txn.amount > 0 and any(kw in desc_lower for kw in rules.get("Income", [])):
            txn.category = "Income"
            continue

        assigned = False
        for cat, keywords in rules.items():
            if cat == "Income" and txn.amount <= 0:
                continue
            if any(kw in desc_lower for kw in keywords):
                txn.category = cat
                assigned = True
                break

        if not assigned:
            # Fallback for credits
            if txn.amount > 0:
                txn.category = "Income"
            else:
                txn.category = "Other"


def detect_recurring_charges(transactions: List[Transaction]) -> List[RecurringItem]:
    """Detect recurring subscription and bill charges."""
    recurring_items: List[RecurringItem] = []
    # Group debits by cleaned merchant name prefix (first 2 words)
    merchant_groups = defaultdict(list)

    subscription_keywords = [
        "netflix", "spotify", "prime", "hotstar", "youtube", "rent",
        "electricity", "power", "water", "wifi", "broadband", "gym", "membership",
    ]

    for txn in transactions:
        if txn.amount >= 0:
            continue
        desc_lower = txn.description.lower()
        # Extract base merchant name
        tokens = re.findall(r"[a-zA-Z0-9]+", desc_lower)
        merchant_key = " ".join(tokens[:2]) if len(tokens) >= 2 else (tokens[0] if tokens else "unknown")

        merchant_groups[merchant_key].append(txn)

    for merchant_key, txns in merchant_groups.items():
        is_subscription_name = any(kw in merchant_key for kw in subscription_keywords)
        amounts = [abs(t.amount) for t in txns]

        # Case 1: Multiple occurrences with similar amounts
        if len(txns) >= 2:
            amt_spread = max(amounts) - min(amounts)
            if amt_spread <= 10.0 or (amt_spread / max(amounts)) < 0.05:
                for t in txns:
                    if "recurring" not in t.tags:
                        t.tags.append("recurring")
                recurring_items.append(
                    RecurringItem(
                        merchant=txns[0].description,
                        typical_amount=round(statistics.mean(amounts), 2),
                        frequency="Monthly",
                        transaction_count=len(txns),
                        transactions=[t.to_dict() for t in txns],
                    )
                )
        # Case 2: Known subscription keyword even if single month statement
        elif len(txns) == 1 and is_subscription_name:
            t = txns[0]
            if "recurring" not in t.tags:
                t.tags.append("recurring")
            recurring_items.append(
                RecurringItem(
                    merchant=t.description,
                    typical_amount=abs(t.amount),
                    frequency="Monthly (Detected by service type)",
                    transaction_count=1,
                    transactions=[t.to_dict()],
                )
            )

    return recurring_items


def detect_anomalies(transactions: List[Transaction]) -> List[AnomalyItem]:
    """Flag unusual expenses, large outliers, and suspicious round-number charges."""
    anomalies: List[AnomalyItem] = []
    debits = [abs(t.amount) for t in transactions if t.amount < 0]

    if not debits:
        return anomalies

    mean_debit = statistics.mean(debits)
    # Group debits by category to compute category averages
    cat_debits = defaultdict(list)
    for t in transactions:
        if t.amount < 0:
            cat_debits[t.category].append(abs(t.amount))

    for txn in transactions:
        if txn.amount >= 0:
            continue
        amt = abs(txn.amount)
        cat_amounts = cat_debits.get(txn.category, [])
        cat_mean = statistics.mean(cat_amounts) if cat_amounts else mean_debit

        flag_reasons = []

        # 1. Outlier amount > 3x category average (when category has other spends)
        if len(cat_amounts) >= 2 and amt > 3.0 * cat_mean and amt > 500.0:
            flag_reasons.append(f"Amount ({amt:.2f}) is > 3x the category average ({cat_mean:.2f})")
        # 2. Large overall outlier (> 3x overall mean and > 5,000)
        elif amt > 3.0 * mean_debit and amt >= 5000.0:
            flag_reasons.append(f"High-value expenditure ({amt:.2f}) significantly above statement average ({mean_debit:.2f})")

        # 3. Large round number charge (e.g. exactly 10,000, 15,000, 25,000)
        if amt >= 5000.0 and amt % 1000.0 == 0.0 and "rent" not in txn.description.lower():
            flag_reasons.append(f"Large round-number debit ({amt:.2f})")

        if flag_reasons:
            if "anomaly" not in txn.tags:
                txn.tags.append("anomaly")
            anomalies.append(
                AnomalyItem(
                    date=txn.date,
                    description=txn.description,
                    amount=txn.amount,
                    category=txn.category,
                    reason="; ".join(flag_reasons),
                )
            )

    return anomalies


def analyze_transactions(
    transactions: List[Transaction],
    custom_rules: Optional[Dict[str, List[str]]] = None,
) -> RuleAnalysisReport:
    """Run full rule-based analysis: categorization, recurring check, anomalies, and cash flow."""
    if not transactions:
        return RuleAnalysisReport(
            cash_flow=CashFlowSummary(0.0, 0.0, 0.0, 0.0),
            categories=[],
            recurring=[],
            anomalies=[],
            total_transactions=0,
        )

    # 1. Assign categories
    assign_categories(transactions, custom_rules=custom_rules)

    # 2. Recurring subscriptions
    recurring = detect_recurring_charges(transactions)

    # 3. Anomalies
    anomalies = detect_anomalies(transactions)

    # 4. Cash Flow & Categories
    total_inflow = sum(t.amount for t in transactions if t.amount > 0)
    total_outflow = sum(abs(t.amount) for t in transactions if t.amount < 0)
    net_savings = total_inflow - total_outflow
    savings_rate = (net_savings / total_inflow * 100.0) if total_inflow > 0 else 0.0

    category_totals = defaultdict(float)
    category_counts = defaultdict(int)

    for t in transactions:
        if t.amount < 0:
            category_totals[t.category] += abs(t.amount)
            category_counts[t.category] += 1

    categories_summary: List[CategorySummary] = []
    for cat, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = (total / total_outflow * 100.0) if total_outflow > 0 else 0.0
        categories_summary.append(
            CategorySummary(
                category=cat,
                total_amount=round(total, 2),
                percentage_of_spend=round(pct, 1),
                transaction_count=category_counts[cat],
            )
        )

    currency = transactions[0].currency if transactions else "INR"
    sorted_txns = sorted(transactions, key=lambda x: x.date)

    return RuleAnalysisReport(
        cash_flow=CashFlowSummary(
            total_inflow=round(total_inflow, 2),
            total_outflow=round(total_outflow, 2),
            net_savings=round(net_savings, 2),
            savings_rate_pct=round(savings_rate, 1),
            currency=currency,
        ),
        categories=categories_summary,
        recurring=recurring,
        anomalies=anomalies,
        total_transactions=len(transactions),
        period_start=sorted_txns[0].date if sorted_txns else None,
        period_end=sorted_txns[-1].date if sorted_txns else None,
    )
