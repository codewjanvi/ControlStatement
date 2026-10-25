"""PDF statement parser using local pypdf library (no cloud calls, no external OCR)."""

import re
from pathlib import Path
from typing import List, Tuple, Optional, Union
import pypdf

from controlstatement.models import Transaction, StatementSummary
from controlstatement.utils import (
    compute_file_hash,
    parse_date_to_iso,
    parse_amount,
    clean_description,
)

# Regex to detect lines starting with a date
DATE_PREFIX_REGEX = re.compile(
    r"^(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}|\d{1,2}-[A-Za-z]{3,9}-\d{2,4})\b"
)


def parse_pdf_statement(
    file_path: Union[str, Path],
    currency: str = "INR",
) -> Tuple[List[Transaction], StatementSummary]:
    """Extract and parse transactions from a native PDF bank statement."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF statement not found: {path}")

    statement_id = compute_file_hash(path)
    source_filename = path.name

    reader = pypdf.PdfReader(str(path))
    raw_text_pages: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        raw_text_pages.append(text)

    full_text = "\n".join(raw_text_pages)
    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]

    transactions: List[Transaction] = []
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None

    # Check for metadata in headers/footers
    for line in lines:
        line_lower = line.lower()
        if "opening balance" in line_lower or "balance b/f" in line_lower:
            parts = line.split(":") if ":" in line else line.rsplit(None, 1)
            if len(parts) > 1:
                amt = parse_amount(parts[-1])
                if amt is not None and opening_balance is None:
                    opening_balance = amt
        elif "closing balance" in line_lower or "balance c/f" in line_lower:
            parts = line.split(":") if ":" in line else line.rsplit(None, 1)
            if len(parts) > 1:
                amt = parse_amount(parts[-1])
                if amt is not None:
                    closing_balance = amt

    running_balance = opening_balance

    for line in lines:
        match = DATE_PREFIX_REGEX.match(line)
        if not match:
            # Check if this line is a continuation of previous transaction description
            if transactions and not any(kw in line.lower() for kw in ["page", "statement", "account", "total", "closing balance"]):
                # If short narration snippet, append
                if len(line) < 120 and not re.search(r"\b\d{1,3}(,\d{3})*\.\d{2}\b", line):
                    transactions[-1].description = clean_description(
                        transactions[-1].description + " " + line
                    )
            continue

        date_token = match.group(1)
        iso_date = parse_date_to_iso(date_token)
        if not iso_date:
            continue

        remainder = line[match.end() :].strip()
        if not remainder:
            continue

        # Look for opening balance line disguised as a row
        if "opening balance" in remainder.lower() or "balance b/f" in remainder.lower():
            nums = re.findall(r"[-+]?₹?\$?[0-9,]+\.[0-9]{2}(?:\s*(?:Cr|Dr))?", remainder, re.IGNORECASE)
            if nums:
                amt = parse_amount(nums[-1])
                if amt is not None:
                    opening_balance = amt
                    running_balance = amt
            continue

        if "closing balance" in remainder.lower() or "balance c/f" in remainder.lower():
            nums = re.findall(r"[-+]?₹?\$?[0-9,]+\.[0-9]{2}(?:\s*(?:Cr|Dr))?", remainder, re.IGNORECASE)
            if nums:
                amt = parse_amount(nums[-1])
                if amt is not None:
                    closing_balance = amt
            continue

        # Find all monetary amount tokens (e.g., 1,450.00, 25000.00 Cr, etc.)
        tokens = remainder.split()
        if not tokens:
            continue

        # Extract numeric amounts from the right-hand side of the line
        extracted_amounts: List[float] = []
        desc_tokens: List[str] = []

        # Iterate tokens from right to left to collect numbers
        idx = len(tokens) - 1
        while idx >= 0:
            token = tokens[idx]
            # Check for Dr / Cr suffix attached to previous token
            if token.upper() in ("DR", "CR") and idx > 0:
                combined = tokens[idx - 1] + " " + token
                amt = parse_amount(combined)
                if amt is not None:
                    extracted_amounts.insert(0, amt)
                    idx -= 2
                    continue

            amt = parse_amount(token)
            if amt is not None and ("." in token or len(extracted_amounts) < 2):
                extracted_amounts.insert(0, amt)
                idx -= 1
            else:
                break

        desc_tokens = tokens[: idx + 1]
        desc = clean_description(" ".join(desc_tokens))
        if not desc:
            desc = "Transaction"

        amount: Optional[float] = None
        row_balance: Optional[float] = None

        if len(extracted_amounts) == 1:
            amount = extracted_amounts[0]
        elif len(extracted_amounts) == 2:
            amt_candidate, row_balance = extracted_amounts[0], extracted_amounts[1]
            if running_balance is not None:
                # If balance decreased, it's a debit
                if round(running_balance - abs(amt_candidate), 2) == round(row_balance, 2):
                    amount = -abs(amt_candidate)
                # If balance increased, it's a credit
                elif round(running_balance + abs(amt_candidate), 2) == round(row_balance, 2):
                    amount = abs(amt_candidate)
                else:
                    amount = amt_candidate
            else:
                amount = amt_candidate
        elif len(extracted_amounts) >= 3:
            # Typical format: Debit, Credit, Balance
            debit_val = extracted_amounts[0]
            credit_val = extracted_amounts[1]
            row_balance = extracted_amounts[2]
            if credit_val != 0 and abs(credit_val) > 0:
                amount = abs(credit_val)
            elif debit_val != 0:
                amount = -abs(debit_val)
            else:
                amount = 0.0

        if amount is None:
            continue

        if row_balance is not None:
            running_balance = row_balance
            closing_balance = row_balance

        txn = Transaction(
            date=iso_date,
            description=desc,
            amount=amount,
            currency=currency,
            source_file=source_filename,
            statement_id=statement_id,
            balance=row_balance,
        )
        transactions.append(txn)

    total_credit = sum(t.amount for t in transactions if t.amount > 0)
    total_debit = sum(abs(t.amount) for t in transactions if t.amount < 0)

    summary = StatementSummary(
        source_file=source_filename,
        statement_id=statement_id,
        currency=currency,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        total_credit=round(total_credit, 2),
        total_debit=round(total_debit, 2),
        period_start=transactions[0].date if transactions else None,
        period_end=transactions[-1].date if transactions else None,
    )

    return transactions, summary
