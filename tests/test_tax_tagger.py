"""Unit tests for Phase 7 tax tagging module."""

import unittest
from controlstatement.models import Transaction
from controlstatement.tax_tagger import (
    tag_tax_transactions,
    export_tax_csv,
    TaxTaggedTransaction,
    DEFAULT_TAX_RULES,
    TAX_TAG_PREFIX,
)


def make_txn(desc, amount, date="2026-06-15", currency="INR"):
    t = Transaction(
        date=date,
        description=desc,
        amount=amount,
        currency=currency,
        statement_id="test",
        source_file="test.csv",
    )
    return t


class TestTaxTagger(unittest.TestCase):

    def test_medical_expense_tagged(self):
        txns = [make_txn("Apollo Pharmacy Purchase", -850.0)]
        tagged = tag_tax_transactions(txns)
        self.assertEqual(len(tagged), 1)
        self.assertEqual(tagged[0].tax_category, "Medical & Health Expenses")
        self.assertIn(f"{TAX_TAG_PREFIX}Medical & Health Expenses", txns[0].tags)

    def test_insurance_premium_tagged(self):
        txns = [make_txn("LIC Premium Payment", -12000.0)]
        tagged = tag_tax_transactions(txns)
        self.assertEqual(len(tagged), 1)
        self.assertEqual(tagged[0].tax_category, "Insurance Premiums")

    def test_professional_education_tagged(self):
        txns = [make_txn("Coursera Subscription Annual", -6000.0)]
        tagged = tag_tax_transactions(txns)
        self.assertEqual(len(tagged), 1)
        self.assertEqual(tagged[0].tax_category, "Professional Education")

    def test_donation_tagged(self):
        txns = [make_txn("GiveIndia Donation", -5000.0)]
        tagged = tag_tax_transactions(txns)
        self.assertEqual(len(tagged), 1)
        self.assertEqual(tagged[0].tax_category, "Charitable Donations")

    def test_credits_not_tagged(self):
        """Income / credit transactions should never be tax-tagged as expenses."""
        txns = [make_txn("Salary Credit", +75000.0)]
        tagged = tag_tax_transactions(txns)
        self.assertEqual(len(tagged), 0)
        self.assertEqual(txns[0].tags, [])

    def test_ordinary_expense_not_tagged(self):
        txns = [make_txn("Swiggy Food Order", -450.0)]
        tagged = tag_tax_transactions(txns)
        self.assertEqual(len(tagged), 0)

    def test_multiple_transactions_mixed(self):
        txns = [
            make_txn("Apollo Pharmacy", -600.0),
            make_txn("Swiggy Dinner", -350.0),
            make_txn("LIC Premium", -8000.0),
            make_txn("Salary", +75000.0),
            make_txn("Udemy Course", -2999.0),
        ]
        tagged = tag_tax_transactions(txns)
        self.assertEqual(len(tagged), 3)
        categories = [t.tax_category for t in tagged]
        self.assertIn("Medical & Health Expenses", categories)
        self.assertIn("Insurance Premiums", categories)
        self.assertIn("Professional Education", categories)

    def test_tag_not_duplicated(self):
        """Re-running tagger should not add duplicate tags."""
        txns = [make_txn("Apollo Pharmacy", -600.0)]
        tag_tax_transactions(txns)
        tag_tax_transactions(txns)  # second run
        tax_tags = [t for t in txns[0].tags if t.startswith(TAX_TAG_PREFIX)]
        self.assertEqual(len(tax_tags), 1)

    def test_export_csv_format(self):
        txns = [
            make_txn("Apollo Pharmacy", -600.0),
            make_txn("LIC Premium", -8000.0),
        ]
        tagged = tag_tax_transactions(txns)
        csv_str = export_tax_csv(tagged)
        self.assertIn("date,description,reference_no,amount,currency,tax_category,tax_tag", csv_str)
        self.assertIn("Apollo Pharmacy", csv_str)
        self.assertIn("Medical & Health Expenses", csv_str)

    def test_export_csv_empty(self):
        csv_str = export_tax_csv([])
        self.assertIn("date,description", csv_str)
        lines = [l for l in csv_str.strip().split("\n") if l]
        self.assertEqual(len(lines), 1)  # only header

    def test_custom_rules(self):
        custom_rules = {"Custom Expense": ["mycustom"]}
        txns = [make_txn("MyCustom Vendor Payment", -1000.0)]
        tagged = tag_tax_transactions(txns, custom_rules=custom_rules)
        self.assertEqual(len(tagged), 1)
        self.assertEqual(tagged[0].tax_category, "Custom Expense")


if __name__ == "__main__":
    unittest.main()
