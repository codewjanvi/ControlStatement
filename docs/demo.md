# ControlStatement — Demo Script

> **Privacy Guarantee:** All steps below run entirely on your local machine.
> No financial data leaves your device at any point.

This demo uses the included synthetic fixture file `fixtures/sample_statement.csv`.
It covers every feature from ingestion to the web dashboard.

---

## Prerequisites

```bash
# Python 3.10+ (tested on 3.14.4 Windows)
pip install -r requirements.txt

# Optional: Ollama for AI summaries
# Install from https://ollama.ai and pull a model:
# ollama pull gemma4:e2b
```

---

## Step 1 — Parse and normalize

```bash
python -m controlstatement parse fixtures/sample_statement.csv
```

**Expected output:**

```
Document: sample_statement.csv
Statement ID (SHA-256): abc123...

Date         | Description                            | Amount        | Balance       | Ref
------------ | -------------------------------------- | ------------- | ------------- | ------------
2026-06-01   | Opening Balance                        |   +0.00 INR   |  10000.00     | -
2026-06-02   | Salary Credit - Corp Inc               | +75000.00 INR |  85000.00     | TXN10001
2026-06-03   | House Rent Transfer                    | -25000.00 INR |  60000.00     | TXN10002
...
Total Transactions: 22 | Credits: +101000.00 | Debits: -74119.00
```

---

## Step 2 — Verify statement integrity

```bash
python -m controlstatement verify fixtures/sample_statement.csv
```

**Expected output:**

```
Verification Status: [PASS] - Statement integrity verified
Document: sample_statement.csv
Statement ID: abc123...
------------------------------------------------------------
Opening Balance:   10000.00
Closing Balance:   36881.00
Computed Closing:  36881.00
Difference:        0.00
Running Balance Sequence: PASSED
Duplicate Transactions:   0
```

---

## Step 3 — Full financial intelligence report (rule-based)

```bash
python -m controlstatement report fixtures/sample_statement.csv --no-model
```

**Expected highlights:**
- Total Income: +101,000.00 INR | Total Expenses: -74,119.00 INR
- Net Savings: +26,881.00 INR (26.6% savings rate)
- Top categories: Shopping & Retail (31%), Housing & Rent (52%), Dining & Food (5%)
- Recurring charges detected: Netflix, Spotify, House Rent
- Anomaly flagged: Watch Gallery Electronics purchase (15,000.00 INR — large round number)

---

## Step 4 — AI-powered report (with Ollama)

> Requires Ollama running on localhost with `gemma4:e2b` or compatible model.

```bash
python -m controlstatement report fixtures/sample_statement.csv --model
```

**Expected:** Plain-language paragraph summarizing spending patterns, trend commentary per category, and 3–5 actionable financial nudges — all computed on-device.

---

## Step 5 — Natural-language Q&A

```bash
python -m controlstatement ask "How much did I spend on Swiggy in total?" \
    --file fixtures/sample_statement.csv
```

**Expected output:**
```
Querying local model 'gemma4:e2b' on transactions from sample_statement.csv...
Question: "How much did I spend on Swiggy in total?"

Answer:
Based on the provided transactions, you spent a total of ₹970.00 INR on Swiggy
across 2 transactions:
  • [2026-06-05] Swiggy Order #8821 — ₹520.00
  • [2026-06-12] Swiggy Order #9003 — ₹450.00
```

---

## Step 6 — Budget vs. actuals

```bash
python -m controlstatement budget fixtures/sample_statement.csv
```

**Expected:** Table showing per-category variance with ✓ OK / ! WARN / ✗ OVER status.
Shopping & Retail will show OVER (₹15,000 actual vs. ₹6,000 budget).

---

## Step 7 — Tax-relevant transaction tagging

```bash
# Terminal view
python -m controlstatement tax fixtures/sample_statement.csv

# Export CSV for accountant
python -m controlstatement tax fixtures/sample_statement.csv --export tax_report.csv
```

**Expected:** House Rent Transfer flagged as "Rent Paid" (potential HRA deduction).

---

## Step 8 — Local web dashboard

```bash
python -m controlstatement serve --open
```

Opens `http://127.0.0.1:8080` in your browser. Features:
- 📊 Month-over-month stacked bar chart (Canvas, zero CDN)
- 🗂 Category breakdown with animated progress bars
- 📒 Full normalized transactions ledger
- 🔄 Recurring subscriptions panel
- ⚠️ Anomaly flags panel
- 🎯 Budget vs. actuals with OK/WARN/OVER indicators
- 🧾 Tax-relevant transactions with ⬇ Export CSV button
- 💬 On-device Q&A (powered by local Ollama)

---

## Step 9 — JSON output (for integrations)

```bash
# Full structured report as JSON
python -m controlstatement report fixtures/sample_statement.csv --json --no-model

# Budget JSON
python -m controlstatement budget fixtures/sample_statement.csv --json

# Tax JSON
python -m controlstatement tax fixtures/sample_statement.csv --json
```

---

## Privacy Verification

All of the above steps run with zero network requests to external servers.
You can verify this yourself by running with a network monitor (e.g. Wireshark or
`netstat -an`) while executing any command — no outbound connections outside `localhost`.

---

## Known Limitations (Honest Pass)

| Limitation | Impact |
| --- | --- |
| Only tested with synthetic CSV fixture | Real bank CSVs may need column mapping tweaks |
| PDF parsing requires native text (not scanned) | Scanned PDFs need OCR pre-processing |
| AI model quality depends on hardware | 7B models may give vague summaries |
| Category matching is keyword-based | Unusual merchant names may be uncategorized |
| Budgets are hard-coded defaults | Future: load from `.env` or config file |
| Tax tagging is heuristic only | Not professional tax advice |
| Single-currency only | Multi-currency not yet aggregated |
| No persistent storage | Analysis is in-memory per run |
