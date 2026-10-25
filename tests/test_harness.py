import csv
from pathlib import Path
import unittest


class TestHarnessSetup(unittest.TestCase):
    """Smoke test to verify that the test harness and fixtures are operational."""

    def test_fixture_statement_exists_and_readable(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_statement.csv"
        self.assertTrue(fixture_path.exists(), f"Fixture file not found at: {fixture_path}")

        with open(fixture_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertGreater(len(rows), 0, "Fixture CSV has no data rows")
        expected_columns = {"Date", "Description", "ReferenceNo", "Debit", "Credit", "Balance"}
        self.assertTrue(expected_columns.issubset(reader.fieldnames), "Missing expected columns in fixture")


if __name__ == "__main__":
    unittest.main()
