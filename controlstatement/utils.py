"""Utility functions for date parsing, amount normalization, and hashing."""

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file for document identification and deduping."""
    path = Path(file_path)
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_date_to_iso(raw_date: str) -> Optional[str]:
    """Parse various bank date formats into ISO 8601 YYYY-MM-DD.

    Supports:
      - 2026-06-15, 2026/06/15
      - 15-06-2026, 15/06/2026
      - 06/15/2026
      - 15 Jun 2026, 15-Jun-2026, 15-June-2026
      - 15-06-26, 15/06/26
    """
    if not raw_date:
        return None

    cleaned = raw_date.strip().replace(".", "-").replace("/", "-")
    # Collapse multiple spaces or dashes
    cleaned = re.sub(r"\s+", " ", cleaned)

    date_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%d-%m-%y",
        "%m-%d-%y",
        "%Y%m%d",
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            # If two digit year, assume 2000s
            if dt.year < 1950:
                dt = dt.replace(year=dt.year + 100)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def parse_amount(val: Any) -> Optional[float]:
    """Normalize numeric strings into float.

    Handles:
      - '1,450.00', '1450.00'
      - '₹1,450.00', '$1,450.00'
      - '(500.00)' -> -500.00
      - '-120.50' -> -120.50
      - '120.50 Cr' / '120.50 Dr'
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "-", "nil", "null"):
        return None

    is_negative = False
    is_explicit_dr = False
    is_explicit_cr = False

    # Check for trailing or leading Dr / Cr
    upper = s.upper()
    if "DR" in upper:
        is_explicit_dr = True
    elif "CR" in upper:
        is_explicit_cr = True

    # Check for parentheses indicating negative: (100.00)
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1]
    elif s.startswith("-") or s.endswith("-"):
        is_negative = True

    # Strip currency symbols, commas, letters, and whitespace
    cleaned = re.sub(r"[^0-9.]", "", s)
    if not cleaned:
        return None

    try:
        num = float(cleaned)
        if is_negative or is_explicit_dr:
            return -abs(num)
        elif is_explicit_cr:
            return abs(num)
        return num
    except ValueError:
        return None


def clean_description(desc: str) -> str:
    """Clean narration and merchant description by removing extra whitespace and artifacts."""
    if not desc:
        return ""
    # Strip common separator line patterns like '---', '===', '___', '***'
    cleaned = re.sub(r"[-=_*]{3,}", " ", str(desc))
    # Replace newlines/tabs with space and collapse spaces
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Strip any trailing or leading punctuation like trailing dashes or colons
    cleaned = re.sub(r"^[\s\-:_]+|[\s\-:_]+$", "", cleaned)
    return cleaned

