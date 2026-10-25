"""Document format detector and router."""

from pathlib import Path
from typing import List, Tuple, Union

from controlstatement.models import Transaction, StatementSummary
from controlstatement.parsers.csv_parser import parse_csv_statement
from controlstatement.parsers.pdf_parser import parse_pdf_statement


def parse_document(
    file_path: Union[str, Path],
    currency: str = "INR",
) -> Tuple[List[Transaction], StatementSummary]:
    """Detect document type and parse into unified Transaction list and summary."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix in (".csv", ".tsv", ".txt"):
        return parse_csv_statement(path, currency=currency)
    elif suffix == ".pdf":
        return parse_pdf_statement(path, currency=currency)
    else:
        # Try inspecting file header bytes
        with open(path, "rb") as f:
            header = f.read(8)
        if header.startswith(b"%PDF"):
            return parse_pdf_statement(path, currency=currency)
        else:
            # Fallback attempt with CSV parser
            return parse_csv_statement(path, currency=currency)
