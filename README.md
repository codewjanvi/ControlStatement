# ControlStatement

A privacy-first local AI tool for personal banking document analysis. Drop your bank statements and card exports onto your local machine to get immediate, intelligent insights without any data ever leaving your device.

---

## 🔒 Core Privacy & Security Principles

1. **No data leaves your machine:** Never makes an external network call. Zero cloud sync, zero telemetry, zero analytics.
2. **Local model inference only:** Uses local LLMs (e.g. Ollama on `localhost`) for contextual analysis and summaries.
3. **Read-only document ingestion:** Uploaded banking documents are never modified or persisted beyond session analysis unless locally configured.
4. **No PII or transaction logging:** Application logs record operational metadata only (file names, row counts, parse status) — never account numbers, amounts, or merchant descriptions.
5. **Full user control:** All reports and exported data remain under local user control.

---

## 🚀 High-Level Architecture & Pipeline

```text
User uploads documents (PDF / CSV)
        ↓
1. Ingestion Layer      (PDF/CSV text extraction & tabular parsing)
        ↓
2. Parser & Normalizer  (Raw data → unified Transaction schema)
        ↓
3. Verifier Layer       (Balance reconciliation, deduplication, integrity check)
        ↓
4. Analyzer Layer       (Fast rule-based heuristics + local LLM insights)
        ↓
5. Report Renderer      (Terminal CLI output, JSON export, and local Web UI)
```

---

## 📊 Feature Status

| Feature | Status |
| --- | --- |
| Document ingestion (PDF, CSV) | **Completed** |
| Transaction normalization & deduplication | **Completed** |
| Statement verification (totals reconciliation) | **Completed** |
| Local model integration (Ollama / llama.cpp) | **Planned** |
| Spending categorization | **Planned** |
| Plain-language monthly summary | **Planned** |
| Cash flow view (income vs. outflow) | **Planned** |
| Anomaly & duplicate detection | **Planned** |
| Trend analysis (MoM, rolling windows) | **Planned** |
| Recurring charge / subscription tracker | **Planned** |
| Budget vs. actuals comparison | **Planned** |
| Natural-language Q&A over transactions | **Planned** |
| Tax-relevant transaction tagging | **Planned** |
| Terminal report + JSON output | **Planned** |
| Local web UI dashboard | **Planned** |
| Multi-account / multi-bank support | **Planned (post-MVP)** |
| Export to CSV / PDF report | **Planned (post-MVP)** |

---

## 📑 Supported Formats

| Format | Status | Details |
| --- | --- | --- |
| Bank Statement CSV / TSV | **Supported** | Automatic column detection for Date, Narration, Debit/Credit, Balance, Reference |
| Bank Statement PDF | **Supported** | Native text-based PDF statement extraction via local `pypdf` |

---

## ⚠️ Known Limitations

- **Format coverage is narrow at MVP:** Only bank/card formats explicitly tested with fixture documents are supported. New formats require a new parser config; untested formats may silently produce wrong data.
- **PDF parsing is fragile:** Scanned PDFs (image-only, no embedded text) are not supported without OCR. Multi-column and table-heavy layouts may parse incorrectly.
- **Model quality varies by hardware:** Smaller local models (≤7B parameters) may produce vague or incorrect summaries. The rule-based layer is always more reliable for numbers.
- **Categorization is keyword-based by default:** Unusual merchant names or UPI references may be uncategorized or miscategorized. The user should review and override.
- **Reconciliation is not always possible:** Some bank exports do not include opening/closing balance fields; in those cases verification is skipped with a notice.
- **Not a financial advisor:** Nudges and advice are pattern-based observations, not professional financial guidance.
- **No multi-currency consolidation:** Foreign currency transactions are flagged but not converted or aggregated with domestic spend.
- **No real-time data:** ControlStatement only knows what is in the uploaded documents.

---

## 🛠️ Installation & Usage

### Prerequisites

- **Python:** 3.10+ (Verified with Python 3.14 on Windows)
- **Dependencies:** Install dependencies via `pip install -r requirements.txt`

### Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Ensure `.env` remains uncommitted to version control.

### CLI Usage

#### 1. Ingestion & Normalization
Parse any bank statement (PDF or CSV) into normalized transactions:

```bash
# Terminal table view
python -m controlstatement parse fixtures/sample_statement.csv
python -m controlstatement parse fixtures/sample_statement.pdf

# Structured JSON output
python -m controlstatement parse fixtures/sample_statement.csv --json
```

#### 2. Verification & Reconciliation (Phase 2)
Verify document integrity, reconcile opening/closing balances, and check running balances:

```bash
# Terminal status report (PASS / WARN / FAIL)
python -m controlstatement verify fixtures/sample_statement.csv
python -m controlstatement verify fixtures/sample_statement.pdf

# Verify tampered statement (exits with code 2 on FAIL)
python -m controlstatement verify fixtures/tampered_statement.csv

# JSON verification report
python -m controlstatement verify fixtures/sample_statement.csv --json
```

### Running Tests

Execute the automated test suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```
