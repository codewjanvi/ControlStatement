"""Document and transaction verification layer.

Performs:
1. Balance reconciliation: opening_balance + sum(transactions) == closing_balance
2. Running balance consistency check: prev_balance + txn.amount == txn.balance
3. Deduplication within and across uploaded statements
4. Produces PASS, WARN, or FAIL status with detailed diagnostic messages
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Set, Tuple

from controlstatement.models import Transaction, StatementSummary


class Status(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class VerificationReport:
    """Comprehensive integrity report for parsed statement data."""

    status: Status
    source_file: str
    statement_id: str
    reconciliation_checked: bool = False
    reconciliation_passed: bool = False
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    computed_closing: Optional[float] = None
    reconciliation_difference: float = 0.0
    running_balance_checked: bool = False
    running_balance_passed: bool = True
    divergent_rows: List[Dict[str, Any]] = field(default_factory=list)
    duplicate_count: int = 0
    duplicate_rows: List[Dict[str, Any]] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "source_file": self.source_file,
            "statement_id": self.statement_id,
            "reconciliation_checked": self.reconciliation_checked,
            "reconciliation_passed": self.reconciliation_passed,
            "opening_balance": self.opening_balance,
            "closing_balance": self.closing_balance,
            "computed_closing": self.computed_closing,
            "reconciliation_difference": round(self.reconciliation_difference, 2),
            "running_balance_checked": self.running_balance_checked,
            "running_balance_passed": self.running_balance_passed,
            "divergent_rows": self.divergent_rows,
            "duplicate_count": self.duplicate_count,
            "duplicate_rows": self.duplicate_rows,
            "reasons": self.reasons,
        }


def _txn_fingerprint(t: Transaction) -> Tuple[str, str, float, Optional[str]]:
    """Generate a unique fingerprint tuple for a transaction."""
    return (t.date, t.description.strip().lower(), round(t.amount, 2), t.reference_no)


def verify_statement(
    transactions: List[Transaction],
    summary: StatementSummary,
    existing_transactions: Optional[List[Transaction]] = None,
) -> VerificationReport:
    """Verify statement integrity, reconcile balances, and detect duplicates."""
    reasons: List[str] = []
    is_fail = False
    is_warn = False

    # 1. Deduplication checks
    seen_in_batch: Set[Tuple] = set()
    duplicates: List[Dict[str, Any]] = []

    # Check duplicates within the file
    for idx, t in enumerate(transactions):
        fp = _txn_fingerprint(t)
        if fp in seen_in_batch:
            duplicates.append({"row_index": idx, "transaction": t.to_dict(), "type": "intra_file_duplicate"})
        else:
            seen_in_batch.add(fp)

    # Check duplicates against prior uploaded transactions (different statement_id)
    if existing_transactions:
        prior_fps = {_txn_fingerprint(pt) for pt in existing_transactions if pt.statement_id != summary.statement_id}
        for idx, t in enumerate(transactions):
            fp = _txn_fingerprint(t)
            if fp in prior_fps:
                duplicates.append({"row_index": idx, "transaction": t.to_dict(), "type": "cross_file_duplicate"})

    if duplicates:
        is_warn = True
        reasons.append(f"Detected {len(duplicates)} duplicate transaction(s) across or within statements.")

    # 2. Balance Reconciliation Check
    reconciliation_checked = False
    reconciliation_passed = False
    computed_closing: Optional[float] = None
    diff = 0.0

    if summary.opening_balance is not None and summary.closing_balance is not None:
        reconciliation_checked = True
        net_flow = sum(t.amount for t in transactions)
        computed_closing = round(summary.opening_balance + net_flow, 2)
        diff = round(abs(computed_closing - summary.closing_balance), 2)

        if diff <= 0.02:  # Allow 2-cent / 2-paisa rounding tolerance
            reconciliation_passed = True
            reasons.append(
                f"Reconciliation passed: Opening ({summary.opening_balance:.2f}) + "
                f"Net Flow ({net_flow:+.2f}) == Closing ({summary.closing_balance:.2f})"
            )
        else:
            is_fail = True
            reconciliation_passed = False
            reasons.append(
                f"Reconciliation FAIL: Expected closing balance {summary.closing_balance:.2f}, "
                f"but transactions compute to {computed_closing:.2f} (discrepancy of {diff:.2f})"
            )
    else:
        is_warn = True
        reasons.append("Statement missing explicit opening or closing balance. Total reconciliation skipped with notice.")

    # 3. Running Balance Consistency Check
    running_checked = False
    running_passed = True
    divergent_rows: List[Dict[str, Any]] = []

    # Filter rows that have recorded balance
    rows_with_balance = [(idx, t) for idx, t in enumerate(transactions) if t.balance is not None]
    if len(rows_with_balance) >= 2:
        running_checked = True
        prev_idx, prev_txn = rows_with_balance[0]
        for curr_idx, curr_txn in rows_with_balance[1:]:
            expected_curr = round(prev_txn.balance + curr_txn.amount, 2)
            actual_curr = round(curr_txn.balance, 2)
            row_diff = round(abs(expected_curr - actual_curr), 2)
            if row_diff > 0.02:
                running_passed = False
                is_fail = True
                divergent_rows.append(
                    {
                        "row_index": curr_idx,
                        "date": curr_txn.date,
                        "description": curr_txn.description,
                        "amount": curr_txn.amount,
                        "expected_balance": expected_curr,
                        "actual_balance": actual_curr,
                        "difference": row_diff,
                    }
                )
            prev_txn = curr_txn

        if not running_passed:
            reasons.append(f"Running balance check FAIL: Diverged at {len(divergent_rows)} row(s).")
        else:
            reasons.append("Running balance sequence check passed.")

    # Determine final status
    if is_fail:
        final_status = Status.FAIL
    elif is_warn:
        final_status = Status.WARN
    else:
        final_status = Status.PASS

    return VerificationReport(
        status=final_status,
        source_file=summary.source_file,
        statement_id=summary.statement_id,
        reconciliation_checked=reconciliation_checked,
        reconciliation_passed=reconciliation_passed,
        opening_balance=summary.opening_balance,
        closing_balance=summary.closing_balance,
        computed_closing=computed_closing,
        reconciliation_difference=diff,
        running_balance_checked=running_checked,
        running_balance_passed=running_passed,
        divergent_rows=divergent_rows,
        duplicate_count=len(duplicates),
        duplicate_rows=duplicates,
        reasons=reasons,
    )
