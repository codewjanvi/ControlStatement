# ControlStatement — Master Developer Prompt & Implementation Plan

Oct 25, 2026 · @amber

## 0. How to use this document (read first)

> **This document is the single source of truth for the coding agent.** If code, README, or chat history disagree with this file, STOP and ask the user which is correct. Do not guess. Anything not yet built must be marked **Planned** (in this file and in the README). Never describe a Planned feature as working.

You are an autonomous coding agent building **ControlStatement**, a privacy-first local AI tool for personal banking document analysis. Your job is to build it **in strict phases**, one verified step at a time.

1. Read this entire document before touching anything.
2. Execute **Phase 0 first**, always. Do not start Phase 1 until the user has replied "OK" to your Phase 0 summary and open questions.
3. Follow the operating rules in Section 2 for **every** change, including tiny ones.
4. When a fact is uncertain (a library API, a model loading flag, a file format behavior), **verify it** by reading official docs or running a small spike test. Never rely on memory. Record what you verified in the Decisions Log (Section 6).

## 1. Mission & scope

### 1.1 The problem

People generate bank statements, credit card PDFs, and transaction exports every month and do almost nothing useful with them. Manually reviewing them is tedious; sharing them with cloud services is a privacy risk; and generic budgeting apps require account linking. There is no tool that lets someone drop their raw banking documents onto a local machine and get immediate, intelligent insight without any data leaving the device.

### 1.2 The solution

`ControlStatement` is a locally-run desktop or CLI application. The user uploads their banking documents (PDFs, CSVs, spreadsheet exports) and a local AI model — running entirely on their machine — reads, parses, and analyzes them. No data ever touches an external server.

The pipeline is:

1. **Ingest** — accept PDF statements, CSV exports, and common bank/card formats; extract and normalize transactions.
2. **Verify** — check document integrity, detect duplicate uploads, reconcile totals against statement summaries.
3. **Analyze** — run the local AI over normalized transactions to produce summaries, categorization, trends, and flags.
4. **Report** — surface findings in a clean local UI or terminal output.

**Core principle: your data stays on your machine.** The local model runs offline; no API keys, no cloud sync, no telemetry.

### 1.3 What ControlStatement provides

| Output | Description |
| --- | --- |
| **Plain-language summary** | "You spent ₹42,000 last month. Top categories: groceries (28%), dining (19%), utilities (14%)." |
| **Spending categorization** | Auto-tags every transaction by merchant type; user can rename categories. |
| **Trend analysis** | Month-over-month and rolling 3/6-month spend trends per category. |
| **Anomaly & duplicate flags** | Unusual charges, potential double-billings, first-seen merchants. |
| **Cash flow view** | Income vs. outflow per month; net savings rate. |
| **Budget vs. actuals** | User sets a budget per category; AI compares and flags overruns. |
| **Debt & subscription tracker** | Recurring charges identified; EMI/loan payments tracked separately. |
| **Tax-relevant tagging** | Flags transactions likely relevant for expense claims or tax filing (travel, professional services). |
| **Natural-language Q&A** | Ask the model: "How much did I spend on Swiggy in June?" or "Which month was most expensive?" |
| **Advice & nudges** | Plain-language suggestions: "Your dining spend rose 40% last month — here are the top merchants." |

### 1.4 Scope

| Category | Items |
| --- | --- |
| **Must have** | PDF + CSV ingestion; transaction normalization; local model integration; summary + categorization; cash flow view; anomaly flags; terminal + basic web UI report |
| **Nice to have** | Budget vs. actuals; Q&A chat interface; tax tagging; multi-account reconciliation |
| **Out of scope** | Cloud sync; account API linking (Plaid/Yodlee); investment analysis; multi-user/shared accounts |

### 1.5 Feature status (keep current; update in same commit as code)

| Feature | Status |
| --- | --- |
| Document ingestion (PDF, CSV) | Completed |
| Transaction normalization & deduplication | Completed |
| Statement verification (totals reconciliation) | Completed |
| Local model integration (Ollama / llama.cpp) | Planned |
| Spending categorization | Planned |
| Plain-language monthly summary | Planned |
| Cash flow view (income vs. outflow) | Planned |
| Anomaly & duplicate detection | Planned |
| Trend analysis (MoM, rolling windows) | Planned |
| Recurring charge / subscription tracker | Planned |
| Budget vs. actuals comparison | Planned |
| Natural-language Q&A over transactions | Planned |
| Tax-relevant transaction tagging | Planned |
| Terminal report + JSON output | Planned |
| Local web UI dashboard | Planned |
| Multi-account / multi-bank support | Planned (post-MVP) |
| Export to CSV / PDF report | Planned (post-MVP) |

## 2. Operating rules (non-negotiable)

### 2.1 Phase 0 mandate

Phase 0 is **always** first and consists of:

- Read all provided docs (this file, README if present, any user-supplied links/files).
- Write/refresh `IMPLEMENTATION_PLAN.md` (this file) to reflect any clarified decisions.
- Create `.env.example` and make sure `.env` is in `.gitignore`.
- List every ambiguity as a numbered question and **wait for the user's OK**.
- Mark everything unbuilt as **Planned**.

### 2.2 The 3-step routine for EVERY change

**Step 1: Plan first.** Update the plan (README and/or this file) *before* writing code: what you will change, why, which phase, and acceptance criteria.

**Step 2: Verify current state.** Read the existing code, config, and README. State plainly what works and what doesn't (run the tests/commands; don't assume).

**Step 3: Check for conflicts.** Does this break the architecture, violate a requirement, or make the README/`.env.example` outdated? If the change is risky or might fail, **STOP and ask the user for permission.** Do not guess.

### 2.3 Code & commit discipline

- Make **small, focused changes**. One concern per commit.
- Update `README.md` and `.env.example` **in the same commit** as the code that changes them.
- Build strictly in phases. **One end-to-end path (ingest → parse → analyze → report) must work before adding complex features.**
- Every phase ends with: tests passing, README current, status table updated, and a short summary to the user.
- Commit message format: `phase-N: <what changed>`.

### 2.4 No hallucinations or shortcuts

- **Never** hardcode user-specific values (model names, file paths, currency symbols, bank-specific parser rules) without asking the user first. Put such values in configuration.
- `.env.example` lists variable **names with empty values and comments**, never real paths or model names.
- If you don't know something, say so and verify. Never invent library APIs, file format specs, or parser behavior.
- No silent scope cuts. If something can't be done, report it and propose alternatives.

### 2.5 Privacy & data safety rules (this project handles sensitive financial data)

1. **No data leaves the machine.** Never add any HTTP call that sends transaction data, document content, or file metadata to an external server — not even for error reporting or analytics.
2. **Uploaded documents are read-only inputs.** Do not copy, cache, or persist the raw document files beyond the session unless the user explicitly enables a local database.
3. **Local model inference only.** The AI step must call a locally-running model endpoint (e.g. Ollama on `localhost`). Verify the endpoint is local before building the call. Never fall back to a cloud API silently.
4. **No logging of transaction details.** Debug logs must never contain account numbers, amounts, merchant names, or balances — only metadata (file name, row count, parse status).
5. **Generated outputs stay local.** Reports, JSON exports, and summaries write only to paths the user controls. No auto-upload.

### 2.6 Stop-and-ask triggers

Stop and ask the user before doing any of these:

- Choosing or changing language, runtime, framework, local model backend (Ollama / llama.cpp / LM Studio), or UI framework.
- Adding a dependency that is large, unmaintained, or requires native compilation.
- Any change that adds a network call, even to localhost on a non-default port.
- Changing the document parsing strategy for any bank/card format.
- Deviating from this plan, or any change that could invalidate previous phases.
- Anything that needs a value you don't have (model name, local endpoint, file paths, currency, timezone).

## 3. Architecture & components

### 3.1 High-level flow

```
User uploads documents
        ↓
[3.2] Ingestion layer  (PDF/CSV → raw text + rows)
        ↓
[3.3] Parser / normalizer  (raw → unified Transaction schema)
        ↓
[3.4] Verifier  (totals check, dedup, integrity)
        ↓
[3.5] Analyzer  (local model + rule-based layer)
        ↓
[3.6] Report renderer  (terminal / web UI / JSON)
```

### 3.2 Ingestion layer

Accepts user-supplied files and extracts raw content without any modification to the originals.

- **PDF parser** — extracts text using a local library (no OCR cloud calls). Handles multi-page statements.
- **CSV/TSV parser** — reads standard bank export formats; handles encoding differences.
- **Format detector** — identifies the bank/card format from headers and layout heuristics; maps to the correct parser config.
- Files are treated as read-only. Originals are never modified.

### 3.3 Transaction normalizer

Converts all parsed rows into a unified `Transaction` schema:

| Field | Type | Notes |
| --- | --- | --- |
| `date` | ISO date | Parsed from statement date column |
| `description` | string | Raw merchant/narration text |
| `amount` | decimal | Positive = credit, negative = debit |
| `currency` | string | From statement header |
| `category` | string | Assigned by categorizer |
| `tags` | string\[\] | Recurring, tax-relevant, anomaly, etc. |
| `source_file` | string | Filename only, no path |
| `statement_id` | string | Hash of file content |

The normalizer must handle: date format variations, credit/debit column splits, running balance columns, and foreign currency lines.

### 3.4 Verifier

Runs after normalization, before analysis:

- Reconciles extracted transaction totals against the opening/closing balance printed on the statement.
- Flags rows where the computed running balance diverges from the statement's own balance column.
- Deduplicates transactions across multiple uploaded files (same `statement_id` + same row = skip; same transaction data across different files = warn).
- Reports verification status: `PASS`, `WARN`, or `FAIL`. Analysis proceeds on `PASS` and `WARN`; `FAIL` prompts the user.

### 3.5 Analyzer (local model + rules)

Two-layer approach — rules run first (fast, deterministic), model runs second (contextual, slower):

**Rule-based layer:**

- Keyword + pattern matching for category assignment (e.g. `swiggy`, `zomato` → Dining).
- Recurring charge detection (same merchant, similar amount, \~30-day interval).
- Anomaly detection: amount > 3× category average, first-seen merchant, round-number large transactions.
- Cash flow aggregation: sum credits and debits per month.

**Local model layer (Ollama or llama.cpp):**

- Called with a structured prompt containing the normalized transaction list (never raw document text).
- Outputs: plain-language summary, category corrections, trend commentary, actionable nudges.
- Q&A mode: user's question + transaction context → model answers.
- The prompt is templated and versioned. Model name and endpoint are configurable, never hardcoded.
- If the local model endpoint is unreachable, the rule-based layer output is returned alone with a clear notice. Never fail silently or call a cloud fallback.

### 3.6 Report renderer

- **Terminal output** — structured text summary: totals, top categories, anomaly flags, nudges.
- **JSON output** — full structured result; used by the web UI and for export.
- **Local web UI** — lightweight HTML/JS page served on `localhost` (no internet dependency). Shows: monthly overview, category breakdown, trend charts, anomaly list, Q&A input.
- All rendered output references only normalized data, never raw document text.

### 3.7 Configuration

All user-tunable values live in a config file (e.g. `config.yaml` or `.env`):

- Local model endpoint URL and model name.
- Currency symbol and locale.
- Category keyword mapping overrides.
- Budget limits per category.
- Paths for document uploads and report output.
- Log verbosity (metadata only — never transaction content).

## 4. Build phases

### Phase 0 — Setup & questions

**Goal:** working repo skeleton; all ambiguities resolved before a line of feature code is written.

Tasks:

- Read this file in full.
- Create repo structure, `README.md` (all features marked Planned), `.env.example`, `.gitignore`.
- Confirm language, runtime, and framework choices with the user (see Section 6).
- Confirm local model backend (Ollama / llama.cpp / LM Studio) and verify it is available on the user's machine.
- Set up test harness with a sample fixture document.
- Ask all Phase 0 questions (Section 6.1) and wait for the user's OK.

Done when: repo initializes cleanly; all open questions answered; user replies OK.

### Phase 1 — Ingestion & normalization

**Goal:** the system can read a real bank statement and produce a clean `Transaction` list.

Tasks:

1. PDF text extractor for at least one confirmed bank format.
2. CSV parser for at least one confirmed bank/card export format.
3. `Transaction` schema defined and validated.
4. Normalizer: date parsing, amount sign normalization, description cleaning.
5. Unit tests on fixture documents (real statements with PII removed, or synthetic data).
6. `README` updated with supported formats.

Done when: `parse <file>` produces a valid `Transaction[]` for both fixture types; tests pass.

### Phase 2 — Verifier

**Goal:** parsed data can be checked for integrity before analysis.

Tasks:

1. Balance reconciliation (opening + transactions = closing).
2. Running-balance column check where present.
3. Deduplication across multiple uploaded files.
4. Verification report: `PASS` / `WARN` / `FAIL` with reasons.
5. Tests: fixture that passes, fixture with a deliberate mismatch.

Done when: both fixture types produce correct verification status; a tampered fixture produces `FAIL`.

### Phase 3 — Rule-based analysis → first end-to-end report

**Goal:** the system produces a useful report using only rules, with no model required.

Tasks:

1. Category keyword matcher (configurable; sensible defaults).
2. Recurring charge detector.
3. Anomaly detector (large outliers, first-seen merchants, round numbers).
4. Cash flow aggregator (monthly income vs. outflow).
5. Terminal report rendering: totals, categories, anomalies.
6. JSON output.

Done when: `controlstatement report <file>` prints a readable summary; JSON output validates against schema; tests pass for all rule types.

> **Gate:** do not start Phase 4 until the user confirms the Phase 3 report is useful on their real documents.

### Phase 4 — Local model integration

**Goal:** AI-generated plain-language summary, trend commentary, and nudges layered on top of Phase 3 output.

Tasks:

1. Spike: confirm local model endpoint (Ollama), model name, and response time on the user's hardware. Report findings to user before building.
2. Prompt template: versioned, structured, sending only normalized transactions (not raw text).
3. Plain-language monthly summary.
4. Category-level trend commentary.
5. Actionable nudges ("Your dining spend is up 40% vs last month").
6. Graceful degradation: if model unreachable, return Phase 3 output with a notice.
7. Tests: mock model endpoint for unit tests; real-model integration test (optional, documented).

Done when: `controlstatement report <file> --model` produces a summary paragraph + nudges; `--no-model` returns Phase 3 output alone.

### Phase 5 — Natural-language Q&A

**Goal:** user can ask questions about their transactions in plain language.

Tasks:

1. Q&A interface (CLI: `controlstatement ask "<question>"`).
2. Prompt: question + full normalized transaction context.
3. Guardrails: model response must only reference transactions in the provided context (no invented data).
4. Test: questions with known correct answers against fixture transactions.

Done when: "How much did I spend on dining in July?" returns a correct, cited answer.

### Phase 6 — Local web UI

**Goal:** a clean, offline-capable local dashboard.

Tasks:

1. Lightweight local server (serves only on `localhost`; no external dependencies at runtime).
2. Monthly overview: total in/out, net savings.
3. Category breakdown (bar/pie).
4. Trend chart (month-over-month per category).
5. Anomaly list.
6. Q&A input (calls the Phase 5 backend).
7. No external CDN calls at runtime; all assets bundled or inlined.

Done when: `controlstatement serve` opens the dashboard in the browser; all charts render from local data; no network requests leave localhost.

### Phase 7 — Nice-to-have (only if Phases 0–6 are done and the user approves)

- **Budget vs. actuals:** user sets monthly budget per category in config; UI shows progress bars and overruns.
- **Tax tagging:** keyword-based tagger for likely expense-claimable transactions; exportable CSV.
- **Multi-account reconciliation:** cross-statement balance check when multiple accounts are uploaded.
- **PDF report export:** generate a printable summary PDF locally.

### Phase 8 — Demo polish & honesty pass

Tasks: demo script (`docs/demo.md`) using synthetic fixture data; README final pass (supported formats, how to run, known limitations, privacy guarantees); confirm every "Planned" item in Section 1.5 is accurately marked; clean-clone setup test.

## 5. Known limitations (copy into README; keep honest)

- **Format coverage is narrow at MVP.** Only bank/card formats explicitly tested with fixture documents are supported. New formats require a new parser config; untested formats may silently produce wrong data.
- **PDF parsing is fragile.** Scanned PDFs (image-only, no embedded text) are not supported without OCR. Multi-column and table-heavy layouts may parse incorrectly.
- **Model quality varies by hardware.** Smaller local models (≤7B parameters) may produce vague or incorrect summaries. The rule-based layer is always more reliable for numbers.
- **Categorization is keyword-based by default.** Unusual merchant names or UPI references may be uncategorized or miscategorized. The user should review and override.
- **Reconciliation is not always possible.** Some bank exports do not include opening/closing balance fields; in those cases verification is skipped with a notice.
- **Not a financial advisor.** Nudges and advice are pattern-based observations, not professional financial guidance.
- **No multi-currency consolidation.** Foreign currency transactions are flagged but not converted or aggregated with domestic spend.
- **No real-time data.** ControlStatement only knows what is in the uploaded documents.

## 6. Open questions & Decisions Log

### 6.1 Questions the agent must ask in Phase 0 (numbered; wait for answers)

1. **Language/runtime:** confirm Python (proposed) or another? Package manager (pip / uv / poetry)?
2. **Local model backend:** Ollama (proposed), llama.cpp, LM Studio, or other? Is it already installed on the user's machine? Which model?
3. **Document formats for MVP:** which bank(s) / card(s) will the user test with? Can they supply a redacted fixture statement?
4. **Currency and locale:** primary currency and date format? (affects display and parsing)
5. **UI for MVP:** terminal only, or also the local web UI? Which to prioritize?
6. **Persistent storage:** should normalized transactions be stored in a local DB between sessions (SQLite proposed), or is in-memory per-run acceptable for MVP?
7. **Budget feature for MVP:** should budget vs. actuals be included in MVP or deferred to Phase 7?
8. **Operating system:** macOS / Linux / Windows? (affects file path handling and local server defaults)
9. **Fixture data:** will the user provide real redacted statements, or should the agent generate synthetic fixture data?
10. **Repo:** existing repo or new? License? Branching convention (proposed: branch per phase, `phase-N:` commit prefix).

### 6.2 Decisions Log (agent appends; never delete entries)

| Date | Decision | Verified how | Approved by |
| --- | --- | --- | --- |
| 2026-10-25 | Environment verified: Python 3.14.4 on Windows; Ollama running on localhost:11434 with model `gemma4:e2b` | Ran `python --version` and queried `http://localhost:11434/api/tags` | Approved by user ("okay continue") |
| 2026-10-25 | Phase 1 architecture: Python 3.14 + pypdf for PDF extraction, CSV parser with multi-format column detection, ISO date normalization, signed decimal amounts, SHA-256 statement_id | Verified pypdf text extraction on minimal PDF | Approved by user |
| 2026-10-25 | Phase 2 verifier: balance reconciliation, running balance sequence consistency, intra/cross-statement deduplication, PASS/WARN/FAIL reporting | Verified against valid CSV, valid PDF, and tampered CSV fixtures | Approved by user |




## 7. Definition of Done (every change)

- [ ] Plan updated **before** coding (3-step routine, Step 1)
- [ ] Current state verified by running code/tests (Step 2)
- [ ] Conflict check done; risky items escalated to the user (Step 3)
- [ ] Tests added/updated and passing
- [ ] README updated in the **same commit**
- [ ] `.env.example` updated in the **same commit** (names only, empty values, comments)
- [ ] Status table in Section 1.5 updated; unbuilt features still marked **Planned**
- [ ] No hardcoded config, model names, file paths, or transaction data in source
- [ ] No network call added that sends data outside localhost
- [ ] Phase summary delivered to the user; waiting for OK where required

---

## 8. First message the agent should send after reading this file

> "I've read IMPLEMENTATION\_PLAN.md. Starting Phase 0: I will create `.env.example`, ensure `.env` is gitignored, draft the README with all features marked Planned, and then send you my numbered open questions. I will not write feature code until you reply OK."
