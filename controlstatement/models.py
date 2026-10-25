"""Data models and schemas for ControlStatement."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Transaction:
    """Unified schema for a normalized financial transaction."""

    date: str  # ISO 8601 date format: YYYY-MM-DD
    description: str  # Cleaned narration / merchant text
    amount: float  # Positive = credit / income, Negative = debit / expense
    currency: str = "INR"
    category: str = "Uncategorized"
    tags: List[str] = field(default_factory=list)
    source_file: str = ""  # Base filename only, no system path
    statement_id: str = ""  # SHA-256 hash of the source document
    balance: Optional[float] = None  # Running balance if printed on statement
    reference_no: Optional[str] = None  # Transaction reference or check number

    def __post_init__(self):
        # Validate date format (YYYY-MM-DD)
        if not self.date:
            raise ValueError("Transaction date cannot be empty")
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Transaction date '{self.date}' must be in ISO format YYYY-MM-DD") from e

        # Validate amount is numeric
        if not isinstance(self.amount, (int, float)):
            raise TypeError(f"Transaction amount must be numeric, got {type(self.amount)}")

        # Ensure description is string and stripped
        self.description = (self.description or "").strip()
        if not self.description:
            raise ValueError("Transaction description cannot be empty")

        # Round amount and balance to 2 decimal places to avoid float drift
        self.amount = round(float(self.amount), 2)
        if self.balance is not None:
            self.balance = round(float(self.balance), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        """Construct a Transaction instance from a dictionary."""
        return cls(
            date=data["date"],
            description=data["description"],
            amount=data["amount"],
            currency=data.get("currency", "INR"),
            category=data.get("category", "Uncategorized"),
            tags=list(data.get("tags", [])),
            source_file=data.get("source_file", ""),
            statement_id=data.get("statement_id", ""),
            balance=data.get("balance"),
            reference_no=data.get("reference_no"),
        )


@dataclass
class StatementSummary:
    """Header/footer summary metadata extracted directly from a statement."""

    source_file: str
    statement_id: str
    currency: str = "INR"
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    total_credit: Optional[float] = None
    total_debit: Optional[float] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
