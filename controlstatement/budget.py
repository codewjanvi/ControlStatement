"""Budget vs. actuals comparison module.

Allows users to set monthly category budgets and compares them against
actual spending from analyzed transactions.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

from controlstatement.rules import CategorySummary


# ── Default budget configuration ─────────────────────────────────────────────
# Users can override this via .env or config file.
# Values are in the default currency (INR).
DEFAULT_MONTHLY_BUDGETS: Dict[str, float] = {
    "Dining & Food": 5000.0,
    "Groceries": 8000.0,
    "Transportation & Travel": 4000.0,
    "Subscriptions & Streaming": 1500.0,
    "Shopping & Retail": 6000.0,
    "Health & Wellness": 3000.0,
    "Utilities & Bills": 5000.0,
    "Investments & Transfers": 20000.0,
    "Housing & Rent": 30000.0,
}


@dataclass
class BudgetLine:
    """Comparison of budgeted vs actual spending for a category."""
    category: str
    budgeted: float
    actual: float
    variance: float            # positive = under budget, negative = over budget
    variance_pct: float        # percentage of budget used
    status: str                # "OK" / "WARN" / "OVER"
    currency: str = "INR"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BudgetReport:
    """Full budget vs actuals comparison report."""
    budget_lines: List[BudgetLine]
    total_budgeted: float
    total_actual: float
    total_variance: float
    currency: str = "INR"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "budget_lines": [b.to_dict() for b in self.budget_lines],
            "total_budgeted": self.total_budgeted,
            "total_actual": self.total_actual,
            "total_variance": self.total_variance,
            "currency": self.currency,
        }


def compare_budget_vs_actuals(
    categories: List[CategorySummary],
    budgets: Optional[Dict[str, float]] = None,
    currency: str = "INR",
    warn_threshold_pct: float = 80.0,
) -> BudgetReport:
    """Compare actual spending against user-configured budgets.

    Args:
        categories: List of CategorySummary from rule analysis.
        budgets: Optional mapping of category name → monthly budget amount.
                 Defaults to DEFAULT_MONTHLY_BUDGETS.
        currency: Currency code for display.
        warn_threshold_pct: Percentage of budget at which to show WARN status.

    Returns:
        BudgetReport with per-category comparisons and totals.
    """
    active_budgets = budgets or DEFAULT_MONTHLY_BUDGETS
    actual_by_cat = {c.category: c.total_amount for c in categories}

    budget_lines: List[BudgetLine] = []

    # Include all categories that have either a budget or actual spend
    all_cats = set(active_budgets.keys()) | set(actual_by_cat.keys())
    # Exclude income-type categories from budget tracking
    exclude_cats = {"Income", "Other"}
    all_cats -= exclude_cats

    for cat in sorted(all_cats):
        budgeted = active_budgets.get(cat, 0.0)
        actual = actual_by_cat.get(cat, 0.0)
        variance = budgeted - actual  # positive = under budget

        if budgeted > 0:
            used_pct = (actual / budgeted) * 100.0
        elif actual > 0:
            used_pct = float("inf")  # no budget set but spent something
        else:
            used_pct = 0.0

        if used_pct > 100.0:
            status = "OVER"
        elif used_pct >= warn_threshold_pct:
            status = "WARN"
        else:
            status = "OK"

        budget_lines.append(BudgetLine(
            category=cat,
            budgeted=round(budgeted, 2),
            actual=round(actual, 2),
            variance=round(variance, 2),
            variance_pct=round(min(used_pct, 9999.0), 1),
            status=status,
            currency=currency,
        ))

    # Sort: OVER first, then WARN, then OK
    order = {"OVER": 0, "WARN": 1, "OK": 2}
    budget_lines.sort(key=lambda b: (order.get(b.status, 3), -b.actual))

    total_budgeted = sum(b.budgeted for b in budget_lines if b.budgeted > 0)
    total_actual = sum(b.actual for b in budget_lines)

    return BudgetReport(
        budget_lines=budget_lines,
        total_budgeted=round(total_budgeted, 2),
        total_actual=round(total_actual, 2),
        total_variance=round(total_budgeted - total_actual, 2),
        currency=currency,
    )
