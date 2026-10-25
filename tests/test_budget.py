"""Unit tests for Phase 7 budget vs. actuals module."""

import unittest
from controlstatement.rules import CategorySummary
from controlstatement.budget import (
    compare_budget_vs_actuals,
    BudgetReport,
    BudgetLine,
    DEFAULT_MONTHLY_BUDGETS,
)


def make_cat(name, amount, pct=10.0, count=3):
    return CategorySummary(
        category=name,
        total_amount=amount,
        percentage_of_spend=pct,
        transaction_count=count,
    )


class TestBudgetComparison(unittest.TestCase):

    def test_under_budget_status_ok(self):
        cats = [make_cat("Dining & Food", 2000.0)]
        report = compare_budget_vs_actuals(cats, currency="INR")
        dining_line = next(b for b in report.budget_lines if b.category == "Dining & Food")
        self.assertEqual(dining_line.status, "OK")
        self.assertGreater(dining_line.variance, 0)  # under budget = positive variance

    def test_over_budget_status_over(self):
        cats = [make_cat("Dining & Food", 8000.0)]  # budget is 5000
        report = compare_budget_vs_actuals(cats, currency="INR")
        dining_line = next(b for b in report.budget_lines if b.category == "Dining & Food")
        self.assertEqual(dining_line.status, "OVER")
        self.assertLess(dining_line.variance, 0)

    def test_warn_threshold_at_80_pct(self):
        cats = [make_cat("Dining & Food", 4100.0)]  # 82% of 5000
        report = compare_budget_vs_actuals(cats, currency="INR", warn_threshold_pct=80.0)
        dining_line = next(b for b in report.budget_lines if b.category == "Dining & Food")
        self.assertEqual(dining_line.status, "WARN")

    def test_no_budget_set_category_included(self):
        """Categories with spending but no budget should be included with status OVER (infinite %)."""
        cats = [make_cat("Unknown Category", 3000.0)]
        budgets = {}  # empty budgets
        report = compare_budget_vs_actuals(cats, budgets=budgets, currency="INR")
        lines = [b for b in report.budget_lines if b.category == "Unknown Category"]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].status, "OVER")

    def test_income_category_excluded(self):
        cats = [make_cat("Income", 75000.0), make_cat("Dining & Food", 2000.0)]
        report = compare_budget_vs_actuals(cats, currency="INR")
        categories = [b.category for b in report.budget_lines]
        self.assertNotIn("Income", categories)

    def test_other_category_excluded(self):
        cats = [make_cat("Other", 500.0)]
        report = compare_budget_vs_actuals(cats, currency="INR")
        categories = [b.category for b in report.budget_lines]
        self.assertNotIn("Other", categories)

    def test_totals_correct(self):
        cats = [
            make_cat("Dining & Food", 3000.0),
            make_cat("Groceries", 5000.0),
        ]
        budgets = {"Dining & Food": 5000.0, "Groceries": 8000.0}
        report = compare_budget_vs_actuals(cats, budgets=budgets, currency="INR")
        self.assertEqual(report.total_actual, 8000.0)
        self.assertEqual(report.total_budgeted, 13000.0)
        self.assertEqual(report.total_variance, 5000.0)

    def test_over_lines_sorted_first(self):
        cats = [
            make_cat("Dining & Food", 2000.0),   # OK
            make_cat("Groceries", 10000.0),       # OVER (budget 8000)
        ]
        report = compare_budget_vs_actuals(cats, currency="INR")
        # OVER should come before OK
        statuses = [b.status for b in report.budget_lines
                    if b.category in ("Dining & Food", "Groceries")]
        over_idx = next(i for i, s in enumerate(statuses) if s == "OVER")
        ok_idx   = next(i for i, s in enumerate(statuses) if s == "OK")
        self.assertLess(over_idx, ok_idx)

    def test_custom_budgets(self):
        cats = [make_cat("Dining & Food", 4000.0)]
        custom = {"Dining & Food": 3000.0}
        report = compare_budget_vs_actuals(cats, budgets=custom, currency="INR")
        dining_line = next(b for b in report.budget_lines if b.category == "Dining & Food")
        self.assertEqual(dining_line.status, "OVER")
        self.assertEqual(dining_line.budgeted, 3000.0)

    def test_to_dict_serializable(self):
        cats = [make_cat("Groceries", 4000.0)]
        report = compare_budget_vs_actuals(cats, currency="INR")
        d = report.to_dict()
        self.assertIn("budget_lines", d)
        self.assertIn("total_budgeted", d)
        self.assertIn("total_actual", d)
        self.assertIn("total_variance", d)
        # Ensure serializable
        import json
        json.dumps(d)


if __name__ == "__main__":
    unittest.main()
