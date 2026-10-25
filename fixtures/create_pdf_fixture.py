"""Generate a synthetic native PDF bank statement fixture for testing."""

from pathlib import Path


def generate_pdf_fixture(output_path: Path) -> None:
    lines = [
        "APEX COMMERCIAL BANK - ACCOUNT STATEMENT",
        "Statement Period: 2026-06-01 to 2026-06-30",
        "Account Holder: John Doe | Account No: XXXX-XXXX-4589",
        "Currency: INR",
        "Opening Balance: 12500.00",
        "----------------------------------------------------------------------",
        "Date Description Debit Credit Balance",
        "2026-06-02 Salary Deposit TechCorp 80000.00 92500.00",
        "2026-06-04 Rent Payment Landlord 22000.00 70500.00",
        "2026-06-07 Swiggy Bangalore 650.00 69850.00",
        "2026-06-10 Amazon Shopping 3499.00 66351.00",
        "2026-06-14 Spotify Monthly 119.00 66232.00",
        "2026-06-18 Zomato Food Delivery 840.00 65392.00",
        "2026-06-22 Tata Power Electricity 2100.00 63292.00",
        "2026-06-27 BigBasket Grocery Store 4200.00 59092.00",
        "2026-06-29 Luxury Watch Gallery 25000.00 34092.00",
        "----------------------------------------------------------------------",
        "Closing Balance: 34092.00",
    ]

    stream_content = "BT\n/F1 10 Tf\n14 TL\n40 760 Td\n"
    for line in lines:
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({safe_line}) ' \n"
    stream_content += "ET\n"
    stream_bytes = stream_content.encode("latin1")

    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    obj4 = (
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1")
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    header = b"%PDF-1.4\n"
    body = header + obj1 + obj2 + obj3 + obj4 + obj5
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    offsets = [
        0,
        len(header),
        len(header) + len(obj1),
        len(header) + len(obj1) + len(obj2),
        len(header) + len(obj1) + len(obj2) + len(obj3),
        len(header) + len(obj1) + len(obj2) + len(obj3) + len(obj4),
    ]
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode("latin1")
    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{len(body)}\n%%EOF\n".encode(
        "latin1"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(body + xref + trailer)


if __name__ == "__main__":
    out_file = Path(__file__).parent / "sample_statement.pdf"
    generate_pdf_fixture(out_file)
    print(f"Generated fixture at: {out_file}")
