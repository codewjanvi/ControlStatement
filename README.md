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
| Local model integration (Ollama / llama.cpp) | **Completed** |
| Spending categorization | **Completed** |
| Plain-language monthly summary | **Completed** |
| Cash flow view (income vs. outflow) | **Completed** |
| Anomaly & duplicate detection | **Completed** |
| Trend analysis (MoM, rolling windows) | **Completed** |
| Recurring charge / subscription tracker | **Completed** |
| Budget vs. actuals comparison | **Planned** |
| Natural-language Q&A over transactions | **Completed** |
| Tax-relevant transaction tagging | **Planned** |
| Terminal report + JSON output | **Completed** |
| Local web UI dashboard | **Completed** |
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

#### 3. Financial Intelligence Report (Phase 3)
Generate comprehensive spending analysis, cash flow summaries, recurring subscription tracking, and anomaly detection:

```bash
# Full report with local AI monthly summary and nudges (Ollama)
python -m controlstatement report fixtures/sample_statement.csv --model
python -m controlstatement report fixtures/sample_statement.pdf --model

# Fast rule-based analysis without invoking local LLM
python -m controlstatement report fixtures/sample_statement.csv --no-model

# Output structured JSON report (includes model_summary)
python -m controlstatement report fixtures/sample_statement.csv --json

# Save report directly to file
python -m controlstatement report fixtures/sample_statement.csv --output report.json
```

#### 4. Natural-Language Q&A (Phase 5)
Ask plain-language questions about your spending directly to your local LLM:

```bash
# Ask specific questions over transaction records
python -m controlstatement ask "How much did I spend on Swiggy in total?" --file fixtures/sample_statement.csv
python -m controlstatement ask "What was my highest expense?" --file fixtures/sample_statement.pdf
python -m controlstatement ask "How much went to utilities and bills?" --file fixtures/sample_statement.csv
```

#### 5. Local Web Dashboard (Phase 6)
Launch the offline-capable browser dashboard — all charts and data served strictly from localhost:

```bash
# Open dashboard at http://127.0.0.1:8080 (auto-opens browser)
python -m controlstatement serve --open

# Custom port (still enforces localhost-only binding)
python -m controlstatement serve --port 9090
```

The dashboard provides:
- 📊 **Month-over-month trend chart** (Canvas, no CDN)
- 🗂 **Category breakdown** with animated progress bars
- 📒 **Normalized transactions ledger**
- 🔄 **Recurring subscriptions** panel
- ⚠️ **Anomaly flags** panel
- 💬 **On-device Q&A** (strict guardrails, no cloud)

### Running Tests

Execute the automated test suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```
