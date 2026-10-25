// ControlStatement Dashboard — Phase 6
// Pure vanilla JS, zero external libraries.
// Trend chart rendered with HTML5 Canvas (no CDN dependencies).

"use strict";

// ── Palette for trend chart categories (hex) ──────────────────
const CAT_PALETTE = [
  "#6366f1", "#10b981", "#f59e0b", "#f43f5e",
  "#a78bfa", "#22d3ee", "#fb923c", "#84cc16",
  "#e879f9", "#38bdf8",
];

document.addEventListener("DOMContentLoaded", () => {
  // ── Element refs ────────────────────────────────────────────
  const selectFixture    = document.getElementById("select-fixture");
  const btnAnalyze       = document.getElementById("btn-analyze");
  const btnRefreshAi     = document.getElementById("btn-refresh-ai");
  const dropzone         = document.getElementById("dropzone");
  const fileInput        = document.getElementById("file-input");

  const metricInflow     = document.getElementById("metric-inflow");
  const metricOutflow    = document.getElementById("metric-outflow");
  const metricSavings    = document.getElementById("metric-savings");
  const metricRate       = document.getElementById("metric-rate");
  const metricVerify     = document.getElementById("metric-verify-status");
  const metricVerifyDesc = document.getElementById("metric-verify-desc");

  const aiSummaryText    = document.getElementById("ai-summary-text");
  const categoriesWrap   = document.getElementById("categories-container");
  const txnsBody         = document.getElementById("transactions-table-body");
  const txnCountLabel    = document.getElementById("txn-count-label");
  const recurringWrap    = document.getElementById("recurring-container");
  const anomaliesWrap    = document.getElementById("anomalies-container");
  const budgetWrap       = document.getElementById("budget-container");
  const taxWrap          = document.getElementById("tax-container");
  const btnTaxExport     = document.getElementById("btn-tax-export");

  const trendCanvas      = document.getElementById("trend-canvas");
  const trendPlaceholder = document.getElementById("trend-placeholder");
  const trendLegend      = document.getElementById("trend-legend");

  const inputQ           = document.getElementById("input-question");
  const btnAsk           = document.getElementById("btn-ask");
  const qaHistory        = document.getElementById("qa-history");
  const modelDot         = document.getElementById("model-status-dot");
  const modelText        = document.getElementById("model-status-text");

  let currentDoc    = "";
  let currentReport = null;

  // ── 1. System Status ────────────────────────────────────────
  async function fetchStatus() {
    try {
      const data = await apiFetch("/api/status");
      if (data.model_online) {
        modelDot.style.background = "var(--emerald)";
        modelDot.style.boxShadow  = "0 0 8px var(--emerald-glow)";
        modelText.textContent = `${data.model_name} · Active`;
      } else {
        modelDot.style.background = "var(--amber)";
        modelDot.style.boxShadow  = "0 0 8px rgba(245,158,11,0.4)";
        modelText.textContent = "Ollama · Offline";
      }
    } catch { /* silent fail */ }
  }

  // ── 2. Load Fixtures ─────────────────────────────────────────
  async function loadFixtures() {
    try {
      const data = await apiFetch("/api/fixtures");
      selectFixture.innerHTML = "";
      if (data.fixtures && data.fixtures.length > 0) {
        data.fixtures.forEach((f, i) => {
          const opt = document.createElement("option");
          opt.value = f.path;
          opt.textContent = f.name;
          if (i === 0) opt.selected = true;
          selectFixture.appendChild(opt);
        });
        currentDoc = data.fixtures[0].name;
        analyzeStatement(data.fixtures[0].path);
      } else {
        selectFixture.innerHTML = `<option value="">No fixtures found</option>`;
      }
    } catch (e) {
      selectFixture.innerHTML = `<option value="">Failed to load</option>`;
    }
  }

  // ── 3. Analyze ───────────────────────────────────────────────
  async function analyzeStatement(filePath, skipModel = false) {
    if (!filePath) return;
    setAnalyzing(true);
    try {
      const data = await apiFetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath, skip_model: skipModel }),
      });
      if (data.error) { showError("Analysis error: " + data.error); return; }
      currentReport = data;
      currentDoc = (data.verification?.source_file) || currentDoc;
      renderDashboard(data);
    } catch (e) {
      showError("Failed to analyze: " + e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  function setAnalyzing(on) {
    btnAnalyze.disabled = on;
    btnAnalyze.innerHTML = on
      ? `<svg class="btn-icon spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Analyzing…`
      : `<svg class="btn-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"/></svg> Analyze`;
  }

  // ── 4. Render Dashboard ──────────────────────────────────────
  function renderDashboard(report) {
    const cf   = report.cash_flow || {};
    const curr = cf.currency || "INR";

    // KPI Cards
    animateCounter(metricInflow,  `+${fmt(cf.total_inflow, curr)}`);
    animateCounter(metricOutflow, `-${fmt(cf.total_outflow, curr)}`);
    const savingsSign = (cf.net_savings >= 0) ? "+" : "-";
    animateCounter(metricSavings, `${savingsSign}${fmt(Math.abs(cf.net_savings), curr)}`);
    metricRate.textContent = `Savings rate: ${cf.savings_rate_pct || 0}%`;

    // Verification
    if (report.verification) {
      const status = report.verification.status;
      metricVerify.textContent = status;
      metricVerify.style.color = status === "PASS" ? "var(--emerald)" : status === "WARN" ? "var(--amber)" : "var(--rose)";
      metricVerifyDesc.textContent = report.verification.reconciliation_passed
        ? "Reconciliation exact"
        : `Diff: ${report.verification.reconciliation_difference} ${curr}`;
    }

    // AI Summary
    if (report.model_summary && report.model_summary.trim()) {
      aiSummaryText.innerHTML = report.model_summary.replace(/\n/g, "<br>");
    } else {
      aiSummaryText.innerHTML = "Rule-based analysis complete. <span style='color:var(--text-dim)'>Local AI model was offline — enable Ollama to get AI-generated insights.</span>";
    }

    renderCategories(report.categories || [], curr);
    renderRecurring(report.recurring || [], curr);
    renderAnomalies(report.anomalies || [], curr);
    renderTransactions(report.transactions || [], curr);
    renderBudget(report.budget, curr);
    renderTax(report.tax_tagged || [], curr);

    // Trend Chart
    if (report.monthly_trends && report.monthly_trends.length > 0) {
      trendPlaceholder.style.display = "none";
      trendCanvas.style.display = "block";
      renderTrendChart(report.monthly_trends, curr);
    } else {
      trendPlaceholder.style.display = "block";
      trendPlaceholder.textContent = "Not enough data for month-over-month trends (need 2+ months)";
    }
  }

  // ── 5. Category Bars ─────────────────────────────────────────
  function renderCategories(cats, curr) {
    categoriesWrap.innerHTML = "";
    if (!cats.length) {
      categoriesWrap.innerHTML = `<p class="dim-text">No expense categories recorded.</p>`;
      return;
    }
    cats.forEach((cat, i) => {
      const color = CAT_PALETTE[i % CAT_PALETTE.length];
      const div = document.createElement("div");
      div.className = "cat-item";
      div.innerHTML = `
        <div class="cat-info">
          <span class="cat-name">${cat.category}</span>
          <span class="cat-amount">${Number(cat.total_amount).toLocaleString()} ${curr} · ${cat.percentage_of_spend}%</span>
        </div>
        <div class="cat-bar-bg">
          <div class="cat-bar-fill" style="width:0%;background:linear-gradient(90deg,${color}cc,${color})"></div>
        </div>
      `;
      categoriesWrap.appendChild(div);
      // Animate after paint
      requestAnimationFrame(() => {
        setTimeout(() => {
          div.querySelector(".cat-bar-fill").style.width = `${cat.percentage_of_spend}%`;
        }, 50 + i * 60);
      });
    });
  }

  // ── 6. Recurring Charges ─────────────────────────────────────
  function renderRecurring(recs, curr) {
    recurringWrap.innerHTML = "";
    if (!recs.length) {
      recurringWrap.innerHTML = `<p class="dim-text">No recurring charges detected.</p>`;
      return;
    }
    recs.forEach(r => {
      const div = document.createElement("div");
      div.className = "rec-item";
      div.innerHTML = `
        <div>
          <div class="rec-merchant">${r.merchant}</div>
          <div class="rec-freq">${r.frequency} · ${r.transaction_count} occurrences</div>
        </div>
        <div class="rec-amount">${Number(r.typical_amount).toLocaleString()} ${curr}</div>
      `;
      recurringWrap.appendChild(div);
    });
  }

  // ── 7. Anomalies ─────────────────────────────────────────────
  function renderAnomalies(anoms, curr) {
    anomaliesWrap.innerHTML = "";
    if (!anoms.length) {
      anomaliesWrap.innerHTML = `<p class="dim-text">No anomalies flagged.</p>`;
      return;
    }
    anoms.forEach(a => {
      const div = document.createElement("div");
      div.className = "anomaly-item";
      div.innerHTML = `
        <div class="anomaly-header">
          <span class="anomaly-desc">[${a.date}] ${a.description}</span>
          <span class="anomaly-amount">${Number(a.amount).toLocaleString()} ${curr}</span>
        </div>
        <div class="anomaly-reason">↳ ${a.reason}</div>
      `;
      anomaliesWrap.appendChild(div);
    });
  }

  // ── 8. Transactions Table ─────────────────────────────────────
  function renderTransactions(txns, curr) {
    txnsBody.innerHTML = "";
    txnCountLabel.textContent = `${txns.length} transactions`;
    if (!txns.length) {
      txnsBody.innerHTML = `<tr><td colspan="5" class="dim-text center-text">No transactions found</td></tr>`;
      return;
    }
    txns.forEach(t => {
      const isCredit = t.amount > 0;
      const tr = document.createElement("tr");
      const bal = t.balance !== null && t.balance !== undefined ? Number(t.balance).toLocaleString() : "–";
      const catClass = t.tags && t.tags.includes("recurring") ? "tag-recurring" : "";
      tr.innerHTML = `
        <td style="color:var(--text-dim);font-size:12px">${t.date}</td>
        <td style="font-weight:500">${t.description}</td>
        <td><span class="tag-badge ${catClass}">${t.category}</span></td>
        <td class="align-right" style="font-weight:700;color:${isCredit ? "var(--emerald)" : "var(--text)"}">
          ${isCredit ? "+" : ""}${Number(t.amount).toLocaleString()} ${curr}
        </td>
        <td class="align-right" style="font-size:12px;color:var(--text-dim)">${bal}</td>
      `;
      txnsBody.appendChild(tr);
    });
  }

  // ── 9. Trend Chart (Canvas) ───────────────────────────────────
  function renderTrendChart(trends, curr) {
    const canvas = trendCanvas;
    const dpr = window.devicePixelRatio || 1;
    const displayW = canvas.offsetWidth || 900;
    const displayH = 220;
    canvas.width  = displayW * dpr;
    canvas.height = displayH * dpr;
    canvas.style.height = displayH + "px";

    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    const W = displayW, H = displayH;

    // Gather all unique categories across months
    const allCats = [];
    trends.forEach(m => {
      Object.keys(m.category_totals).forEach(c => {
        if (!allCats.includes(c)) allCats.push(c);
      });
    });

    // Sort by total spend
    allCats.sort((a, b) => {
      const aSum = trends.reduce((s, m) => s + (m.category_totals[a] || 0), 0);
      const bSum = trends.reduce((s, m) => s + (m.category_totals[b] || 0), 0);
      return bSum - aSum;
    });

    // Max value for Y axis
    const maxVal = Math.max(...trends.map(m => m.total_outflow), 1);
    const months = trends.map(m => m.month);

    const PAD = { top: 16, right: 24, bottom: 48, left: 64 };
    const chartW = W - PAD.left - PAD.right;
    const chartH = H - PAD.top - PAD.bottom;

    // Draw background grid
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    const gridLines = 4;
    for (let i = 0; i <= gridLines; i++) {
      const y = PAD.top + chartH - (i / gridLines) * chartH;
      ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(W - PAD.right, y); ctx.stroke();
      // Y label
      const val = Math.round((i / gridLines) * maxVal);
      ctx.fillStyle = "rgba(148,163,184,0.6)";
      ctx.font = `${10 * dpr / dpr}px Inter,sans-serif`;
      ctx.textAlign = "right";
      ctx.fillText(val >= 1000 ? `${(val/1000).toFixed(0)}k` : val, PAD.left - 8, y + 4);
    }

    // Stacked bar chart per month
    const barW = months.length > 1 ? (chartW / months.length) * 0.6 : chartW * 0.3;
    const gap  = chartW / months.length;

    trends.forEach((monthData, mi) => {
      const cx = PAD.left + mi * gap + gap / 2;
      let yBase = PAD.top + chartH;

      allCats.forEach((cat, ci) => {
        const val = monthData.category_totals[cat] || 0;
        if (!val) return;
        const barH = (val / maxVal) * chartH;
        const color = CAT_PALETTE[ci % CAT_PALETTE.length];
        ctx.fillStyle = color + "cc";
        const x = cx - barW / 2;
        const y = yBase - barH;
        const r = 4;
        roundRect(ctx, x, y, barW, barH, { tl: r, tr: r, bl: 0, br: 0 });
        ctx.fill();
        yBase -= barH;
      });

      // Net savings line indicator
      const savings = monthData.net_savings;
      const savingsY = PAD.top + chartH - (Math.max(0, Math.min(savings, maxVal)) / maxVal) * chartH;
      ctx.beginPath();
      ctx.arc(cx, savingsY, 4, 0, Math.PI * 2);
      ctx.fillStyle = savings >= 0 ? "#10b981" : "#f43f5e";
      ctx.fill();

      // Month label
      ctx.fillStyle = "rgba(148,163,184,0.8)";
      ctx.textAlign = "center";
      ctx.font = `500 11px Inter,sans-serif`;
      ctx.fillText(monthData.month, cx, H - PAD.bottom + 18);
    });

    // Legend
    trendLegend.innerHTML = "";
    allCats.slice(0, 8).forEach((cat, i) => {
      const item = document.createElement("div");
      item.className = "legend-item";
      item.innerHTML = `<span class="legend-dot" style="background:${CAT_PALETTE[i % CAT_PALETTE.length]}"></span>${cat}`;
      trendLegend.appendChild(item);
    });
    // Net savings legend
    const ns = document.createElement("div");
    ns.className = "legend-item";
    ns.innerHTML = `<span class="legend-dot" style="background:var(--emerald);border-radius:50%"></span>Net savings`;
    trendLegend.appendChild(ns);
  }

  // Rounded rect helper
  function roundRect(ctx, x, y, w, h, r) {
    if (typeof r === "number") r = { tl: r, tr: r, bl: r, br: r };
    ctx.beginPath();
    ctx.moveTo(x + r.tl, y);
    ctx.lineTo(x + w - r.tr, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r.tr);
    ctx.lineTo(x + w, y + h - r.br);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r.br, y + h);
    ctx.lineTo(x + r.bl, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r.bl);
    ctx.lineTo(x, y + r.tl);
    ctx.quadraticCurveTo(x, y, x + r.tl, y);
    ctx.closePath();
  }

  // ── 10. Budget vs Actuals ────────────────────────────────────
  function renderBudget(budget, curr) {
    budgetWrap.innerHTML = "";
    if (!budget || !budget.budget_lines || !budget.budget_lines.length) {
      budgetWrap.innerHTML = `<p class="dim-text">No budget data available.</p>`;
      return;
    }
    const lines = budget.budget_lines;
    lines.forEach((b, i) => {
      const statusClass = b.status === "OK" ? "budget-ok" : b.status === "WARN" ? "budget-warn" : "budget-over";
      const tagClass = b.status === "OK" ? "status-ok" : b.status === "WARN" ? "status-warn" : "status-over";
      const usedPct = Math.min(b.variance_pct, 100);
      const item = document.createElement("div");
      item.className = `budget-item ${statusClass}`;
      const budStr = b.budgeted > 0 ? `${Number(b.budgeted).toLocaleString()} ${curr}` : "No budget";
      const varStr = `${b.variance >= 0 ? "+" : ""}${Number(b.variance).toLocaleString()}`;
      item.innerHTML = `
        <div class="budget-info">
          <span class="budget-cat">${b.category}</span>
          <span class="budget-meta">
            <span class="budget-status-tag ${tagClass}">${b.status}</span>
            ${Number(b.actual).toLocaleString()} / ${budStr}
            <span style="margin-left:4px;color:${b.variance>=0?'var(--emerald)':'var(--rose)'}">(${varStr})</span>
          </span>
        </div>
        <div class="budget-bar-bg">
          <div class="budget-bar-fill" style="width:0%"></div>
        </div>
      `;
      budgetWrap.appendChild(item);
      requestAnimationFrame(() => {
        setTimeout(() => {
          item.querySelector(".budget-bar-fill").style.width = `${usedPct}%`;
        }, 60 + i * 50);
      });
    });
  }

  // ── 11. Tax Panel ─────────────────────────────────────────────
  function renderTax(tagged, curr) {
    taxWrap.innerHTML = "";
    if (!tagged || !tagged.length) {
      taxWrap.innerHTML = `<p class="dim-text">No tax-relevant transactions found.</p>`;
      return;
    }
    tagged.forEach(t => {
      const div = document.createElement("div");
      div.className = "tax-item";
      div.innerHTML = `
        <div class="tax-info">
          <div class="tax-desc" title="${t.description}">[${t.date}] ${t.description}</div>
          <div class="tax-cat">${t.tax_category}</div>
        </div>
        <div class="tax-amount">${Number(t.amount).toLocaleString()} ${curr}</div>
      `;
      taxWrap.appendChild(div);
    });
  }

  // ── 12. Tax CSV Export ────────────────────────────────────────
  if (btnTaxExport) {
    btnTaxExport.addEventListener("click", async () => {
      try {
        const resp = await fetch("/api/tax-export", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doc_name: currentDoc }),
        });
        if (!resp.ok) { alert("Tax export failed."); return; }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "tax_tagged_transactions.csv";
        a.click();
        URL.revokeObjectURL(url);
      } catch (e) {
        alert("Tax export error: " + e.message);
      }
    });
  }

  // ── 13. File Upload / Drag & Drop ────────────────────────────
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") fileInput.click(); });
  fileInput.addEventListener("change", e => { if (e.target.files[0]) uploadFile(e.target.files[0]); });
  dropzone.addEventListener("dragover",  e => { e.preventDefault(); dropzone.classList.add("drag-active"); });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-active"));
  dropzone.addEventListener("drop", e => {
    e.preventDefault(); dropzone.classList.remove("drag-active");
    if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
  });

  async function uploadFile(file) {
    setAnalyzing(true);
    try {
      const resp = await fetch("/api/upload", {
        method: "POST",
        headers: { "X-Filename": file.name },
        body: file,
      });
      const data = await resp.json();
      if (data.error) { showError("Upload error: " + data.error); return; }
      currentReport = data;
      currentDoc = file.name;
      renderDashboard(data);
    } catch (e) {
      showError("File ingestion failed: " + e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  // ── 11. Q&A ──────────────────────────────────────────────────
  btnAsk.addEventListener("click", sendQuestion);
  inputQ.addEventListener("keypress", e => { if (e.key === "Enter") sendQuestion(); });

  async function sendQuestion() {
    const q = inputQ.value.trim();
    if (!q) return;
    addQAMsg("user", q);
    inputQ.value = "";
    const botMsg = addQAMsg("bot", "Thinking on your local machine…", true);
    try {
      const data = await apiFetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, doc_name: currentDoc }),
      });
      botMsg.querySelector(".qa-bubble").textContent = data.answer || "No response received.";
    } catch (e) {
      botMsg.querySelector(".qa-bubble").textContent = "Error: " + e.message;
    }
    qaHistory.scrollTop = qaHistory.scrollHeight;
  }

  function addQAMsg(role, text, italic = false) {
    const wrap = document.createElement("div");
    wrap.className = `qa-msg qa-${role}`;
    wrap.innerHTML = `
      <div class="qa-avatar">${role === "bot" ? "AI" : "ME"}</div>
      <div class="qa-bubble">${italic ? `<em>${text}</em>` : text}</div>
    `;
    qaHistory.appendChild(wrap);
    qaHistory.scrollTop = qaHistory.scrollHeight;
    return wrap;
  }

  // ── 12. Event Listeners ──────────────────────────────────────
  btnAnalyze.addEventListener("click", () => {
    const v = selectFixture.value;
    if (v) analyzeStatement(v);
  });
  btnRefreshAi.addEventListener("click", () => {
    const v = selectFixture.value;
    if (v) analyzeStatement(v, false);
    else if (currentReport) renderDashboard(currentReport);
  });

  // Re-render chart on resize
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (currentReport && currentReport.monthly_trends && currentReport.monthly_trends.length > 0) {
        renderTrendChart(currentReport.monthly_trends, currentReport.cash_flow?.currency || "INR");
      }
    }, 200);
  });

  // ── Helpers ──────────────────────────────────────────────────
  async function apiFetch(url, opts = {}) {
    const resp = await fetch(url, opts);
    return resp.json();
  }

  function fmt(val, curr) {
    return `${Number(val || 0).toLocaleString("en-IN")} ${curr}`;
  }

  function animateCounter(el, targetText) {
    el.style.transition = "opacity 0.25s";
    el.style.opacity = "0";
    setTimeout(() => {
      el.textContent = targetText;
      el.style.opacity = "1";
    }, 200);
  }

  function showError(msg) {
    alert(msg);
  }

  // ── Init ──────────────────────────────────────────────────────
  fetchStatus();
  loadFixtures();

  // Spin animation for loading button
  const styleEl = document.createElement("style");
  styleEl.textContent = `
    @keyframes spin { to { transform: rotate(360deg); } }
    .spin { animation: spin 1s linear infinite; }
  `;
  document.head.appendChild(styleEl);
});
