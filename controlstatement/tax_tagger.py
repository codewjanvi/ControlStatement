"""Tax-relevant transaction tagging module.

Identifies likely tax-deductible or tax-relevant expense transactions
using keyword-based pattern matching. Provides an export function to
generate a CSV summary for tax review.

Disclaimer: This is a pattern-based heuristic. Always verify with a
qualified tax professional before filing claims.
"""

import csv
import io
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

from controlstatement.models import Transaction

# ── Tax Tag Keyword Rules ────────────────────────────────────────────────────
# Maps a tax-relevant category to keyword patterns (case-insensitive substring).
DEFAULT_TAX_RULES: Dict[str, List[str]] = {
    "Medical & Health Expenses": [
        "pharmacy", "apollo", "medplus", "hospital", "clinic", "medical",
        "doctor", "1mg", "pharmeasy", "dentist", "lab", "diagnostic",
        "health checkup", "pathology", "blood test",
    ],
    "Professional Education": [
        "coursera", "udemy", "linkedin learning", "pluralsight", "skillshare",
        "books", "book store", "amazon kindle", "training", "certification",
        "workshop", "seminar", "conference",
    ],
    "Home Office & Equipment": [
        "laptop", "monitor", "keyboard", "mouse", "webcam", "headset",
        "office supplies", "printer", "scanner", "home office",
        "desk", "chair", "stationery",
    ],
    "Professional Services": [
        "ca fees", "chartered accountant", "lawyer", "legal", "consulting",
        "professional fee", "advisory", "accountant",
    ],
    "Insurance Premiums": [
        "insurance", "premium", "lic", "health insurance", "life insurance",
        "term insurance", "mediclaim",
    ],
    "Charitable Donations": [
        "donation", "charity", "ngo", "trust", "relief fund", "pm cares",
        "giveindia", "milaap",
    ],
    "Rent Paid": [
        "house rent", "rent transfer", "landlord", "hra",
    ],
    "Interest Paid": [
        "home loan emi", "emi interest", "loan interest",
    ],
}

TAX_TAG_PREFIX = "tax:"


@dataclass
class TaxTaggedTransaction:
    """A transaction tagged as potentially tax-relevant."""
    date: str
    description: str
    amount: float
    currency: str
    tax_category: str
    tax_tag: str
    reference_no: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def tag_tax_transactions(
    transactions: List[Transaction],
    custom_rules: Optional[Dict[str, List[str]]] = None,
) -> List[TaxTaggedTransaction]:
    """Identify and tag transactions likely relevant for tax filing.

    Modifies transactions in-place by adding 'tax:<category>' tags.
    Returns a list of TaxTaggedTransaction summaries.

    Note: Only expense (negative amount) transactions are considered.
    """
    rules = custom_rules or DEFAULT_TAX_RULES
    tagged: List[TaxTaggedTransaction] = []

    for txn in transactions:
        # Only debits can be deductible expenses
        if txn.amount >= 0:
            continue

        desc_lower = txn.description.lower()
        matched_category: Optional[str] = None

        for tax_cat, keywords in rules.items():
            if any(kw in desc_lower for kw in keywords):
                matched_category = tax_cat
                break

        if matched_category:
            tag = f"{TAX_TAG_PREFIX}{matched_category}"
            if tag not in txn.tags:
                txn.tags.append(tag)

            tagged.append(
                TaxTaggedTransaction(
                    date=txn.date,
                    description=txn.description,
                    amount=txn.amount,
                    currency=txn.currency,
                    tax_category=matched_category,
                    tax_tag=tag,
                    reference_no=txn.reference_no,
                )
            )

    return tagged


def export_tax_csv(tagged: List[TaxTaggedTransaction]) -> str:
    """Export tax-tagged transactions as a CSV string for accountant review."""
    output = io.StringIO()
    fieldnames = ["date", "description", "reference_no", "amount", "currency", "tax_category", "tax_tag"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for t in tagged:
        writer.writerow({
            "date": t.date,
            "description": t.description,
            "reference_no": t.reference_no or "",
            "amount": t.amount,
            "currency": t.currency,
            "tax_category": t.tax_category,
            "tax_tag": t.tax_tag,
        })
    return output.getvalue()
