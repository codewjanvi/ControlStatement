"""CSV and delimited text statement parser."""

import csv
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union

from controlstatement.models import Transaction, StatementSummary
from controlstatement.utils import (
    compute_file_hash,
    parse_date_to_iso,
    parse_amount,
    clean_description,
)


def _find_header_and_delimiter(lines: List[str]) -> Tuple[int, str, List[str]]:
    """Inspect lines to find the table header row index, delimiter, and column names."""
    delimiters = [",", "\t", ";", "|"]
    date_keywords = ["date", "txn date", "transaction date", "value date", "posting date"]
    desc_keywords = ["description", "narration", "particulars", "remarks", "details", "payee"]

    for idx, line in enumerate(lines[:30]):
        line_clean = line.strip()
        if not line_clean:
            continue
        for delim in delimiters:
            parts = [p.strip().strip('"').strip("'").lower() for p in line_clean.split(delim)]
            has_date = any(any(k in col for k in date_keywords) for col in parts)
            has_desc = any(any(k in col for k in desc_keywords) for col in parts)
            if has_date and has_desc:
                # Found table header
                raw_headers = [p.strip().strip('"').strip("'") for p in line_clean.split(delim)]
                return idx, delim, raw_headers

    # Default fallback to first line with comma
    first_line = lines[0].strip() if lines else ""
    return 0, ",", [p.strip().strip('"') for p in first_line.split(",")]


def _map_columns(headers: List[str]) -> Dict[str, Optional[int]]:
    """Map standard fields to column indices based on header names."""
    col_map: Dict[str, Optional[int]] = {
        "date": None,
        "description": None,
        "debit": None,
        "credit": None,
        "amount": None,
        "balance": None,
        "reference": None,
        "type": None,
    }

    for idx, header in enumerate(headers):
        h = header.lower().replace("_", " ").strip()
        if not h:
            continue
        if col_map["date"] is None and any(k in h for k in ["date"]):
            col_map["date"] = idx
        elif col_map["description"] is None and any(k in h for k in ["description", "narration", "particulars", "remarks", "details", "payee"]):
            col_map["description"] = idx
        elif col_map["debit"] is None and any(k in h for k in ["debit", "withdrawal", "dr amount"]):
            col_map["debit"] = idx
        elif col_map["credit"] is None and any(k in h for k in ["credit", "deposit", "cr amount"]):
            col_map["credit"] = idx
        elif col_map["balance"] is None and any(k in h for k in ["balance"]):
            col_map["balance"] = idx
        elif col_map["reference"] is None and any(k in h for k in ["ref", "chq", "cheque", "txn id", "transaction id"]):
            col_map["reference"] = idx
        elif col_map["type"] is None and any(k == h or "dr/cr" in h or "type" in h for k in ["type", "cr/dr"]):
            col_map["type"] = idx
        elif col_map["amount"] is None and "amount" in h and "debit" not in h and "credit" not in h:
            col_map["amount"] = idx

    return col_map


def parse_csv_statement(
    file_path: "Union[str, Path]",
    currency: str = "INR",
) -> Tuple[List[Transaction], StatementSummary]:
    """Parse a CSV or delimited bank statement into normalized transactions and summary."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Statement file not found: {path}")

    statement_id = compute_file_hash(path)
    source_filename = path.name

    # Read all lines with utf-8-sig to handle BOM
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        lines = f.readlines()

    if not lines:
        summary = StatementSummary(source_file=source_filename, statement_id=statement_id, currency=currency)
        return [], summary

    header_idx, delimiter, headers = _find_header_and_delimiter(lines)
    col_map = _map_columns(headers)

    if col_map["date"] is None or col_map["description"] is None:
        raise ValueError(f"Could not identify required 'Date' and 'Description' columns in CSV: {headers}")

    transactions: List[Transaction] = []
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None

    # Parse data rows starting after the header
    data_lines = lines[header_idx + 1 :]
    reader = csv.reader(data_lines, delimiter=delimiter)

    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue

        def get_val(col_idx: Optional[int]) -> str:
            if col_idx is not None and col_idx < len(row):
                return row[col_idx].strip()
            return ""

        raw_date = get_val(col_map["date"])
        raw_desc = get_val(col_map["description"])
        raw_balance = get_val(col_map["balance"])
        raw_ref = get_val(col_map["reference"])

        parsed_balance = parse_amount(raw_balance)
        desc_clean = clean_description(raw_desc)

        # Check for opening / closing balance metadata rows
        desc_lower = desc_clean.lower()
        if "opening balance" in desc_lower or "balance b/f" in desc_lower or "brought forward" in desc_lower:
            if parsed_balance is not None:
                opening_balance = parsed_balance
            continue

        if "closing balance" in desc_lower or "balance c/f" in desc_lower or "carried forward" in desc_lower:
            if parsed_balance is not None:
                closing_balance = parsed_balance
            continue

        iso_date = parse_date_to_iso(raw_date)
        if not iso_date:
            # Not a transaction row (might be footer or notes)
            continue

        # Determine transaction amount
        amount: Optional[float] = None

        # Case 1: Separate Debit and Credit columns
        if col_map["debit"] is not None or col_map["credit"] is not None:
            raw_debit = get_val(col_map["debit"])
            raw_credit = get_val(col_map["credit"])
            parsed_debit = parse_amount(raw_debit)
            parsed_credit = parse_amount(raw_credit)

            if parsed_credit is not None and parsed_credit > 0:
                amount = abs(parsed_credit)
            elif parsed_debit is not None and parsed_debit != 0:
                amount = -abs(parsed_debit)
            elif parsed_credit is not None and parsed_credit != 0:
                amount = abs(parsed_credit)

        # Case 2: Single amount column with Type / DrCr indicator or signed amount
        if amount is None and col_map["amount"] is not None:
            raw_amt = get_val(col_map["amount"])
            parsed_amt = parse_amount(raw_amt)
            if parsed_amt is not None:
                raw_type = get_val(col_map["type"]).upper()
                if "DR" in raw_type or "DEBIT" in raw_type:
                    amount = -abs(parsed_amt)
                elif "CR" in raw_type or "CREDIT" in raw_type:
                    amount = abs(parsed_amt)
                else:
                    amount = parsed_amt

        if amount is None:
            continue

        # If opening balance was not explicitly set yet, but first row has balance and amount:
        if opening_balance is None and parsed_balance is not None:
            # opening = balance - amount
            opening_balance = round(parsed_balance - amount, 2)

        # Update running latest balance as potential closing balance
        if parsed_balance is not None:
            closing_balance = parsed_balance

        txn = Transaction(
            date=iso_date,
            description=desc_clean,
            amount=amount,
            currency=currency,
            source_file=source_filename,
            statement_id=statement_id,
            balance=parsed_balance,
            reference_no=raw_ref if raw_ref else None,
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
