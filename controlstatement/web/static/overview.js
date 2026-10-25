// ControlStatement — Control Overview Component
// Vanilla JS, zero dependencies, strictly offline and privacy-first.
"use strict";

(function () {
  // ── 1. Escaping Helper ─────────────────────────────────────────
  function esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function fmtAmount(val, curr) {
    const num = Number(val || 0);
    return `${num.toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ${esc(curr)}`;
  }

  // ── 2. Initialization ──────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    const mount = document.getElementById("control-overview-mount");
    if (!mount) return;

    mount.innerHTML = `
      <section class="co-root" id="control-overview-root" aria-label="Control Overview">
        <div class="co-container">
          <div class="co-header">
            <div class="co-title-group">
              <svg class="co-title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <path d="M3 9h18M9 21V9"/>
              </svg>
              <h2 class="co-title">Control Overview</h2>
              <span class="co-subtitle">Local Verification Pipeline &amp; Cash Flow</span>
            </div>
            <button class="co-theme-btn" id="co-theme-toggle" type="button" aria-label="Toggle theme">
              <span id="co-theme-icon">◐</span>
              <span id="co-theme-label">Theme</span>
            </button>
          </div>
          <div id="co-content" class="co-grid">
            <div class="co-state-msg">Loading verified pipeline data…</div>
          </div>
        </div>
      </section>
    `;

    const rootEl = document.getElementById("control-overview-root");
    const contentEl = document.getElementById("co-content");
    const themeBtn = document.getElementById("co-theme-toggle");
    const themeLabel = document.getElementById("co-theme-label");

    // ── 3. Theme Switcher ────────────────────────────────────────
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    let isDark = prefersDark;

    function applyTheme(dark) {
      isDark = dark;
      if (dark) {
        rootEl.classList.remove("co-light");
        themeLabel.textContent = "Dark";
      } else {
        rootEl.classList.add("co-light");
        themeLabel.textContent = "Light";
      }
    }
    applyTheme(prefersDark);

    themeBtn.addEventListener("click", () => {
      applyTheme(!isDark);
    });

    // ── 4. Fetch Overview Data ───────────────────────────────────
    fetch("/api/overview")
      .then((res) => {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then((data) => {
        renderOverview(data, contentEl);
      })
      .catch((err) => {
        contentEl.innerHTML = `<div class="co-state-msg" style="color:var(--co-red);">Local server did not respond.</div>`;
      });
  });

  // ── 5. Render Overview ─────────────────────────────────────────
  function renderOverview(data, container) {
    const files = data.files || [];
    const months = data.months || [];
    const income = data.income || [];
    const spending = data.spending || [];
    const currency = data.currency || "INR";

    if (files.length === 0) {
      container.innerHTML = `
        <div class="co-state-msg">
          No statements found. Drop a bank statement file to start.
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <!-- Card 1: Flow Diagram (Wide) -->
      <div class="co-card co-card-wide" id="co-flow-card">
        <div class="co-bracket co-bracket-tl"></div>
        <div class="co-bracket co-bracket-tr"></div>
        <div class="co-bracket co-bracket-bl"></div>
        <div class="co-bracket co-bracket-br"></div>
        <div class="co-card-title">
          <span>Statement Verification Flow</span>
          <span style="font-weight:500;font-size:11px;color:var(--co-text-muted);">${files.length} Statement${files.length > 1 ? "s" : ""}</span>
        </div>
        <div class="co-flow-stage">
          <!-- Files Column -->
          <div class="co-files-col" role="list" aria-label="Statement files">
            ${files.map((f, i) => {
              const dotClass = f.status === "PASS" ? "co-dot-pass" : f.status === "WARN" ? "co-dot-warn" : "co-dot-fail";
              return `
                <div class="co-file-item" role="listitem" tabindex="0" aria-label="${esc(f.name)}: ${esc(f.status)}">
                  <span class="co-status-dot ${dotClass}" aria-hidden="true"></span>
                  <span class="co-file-name" title="${esc(f.name)}">${esc(f.name)}</span>
                  <div class="co-file-tooltip" role="tooltip">${esc(f.name)} · ${esc(f.status)}</div>
                </div>
              `;
            }).join("")}
          </div>

          <!-- Middle: Verifier Chip -->
          <div class="co-flow-mid">
            <svg class="co-flow-line-svg" viewBox="0 0 200 48" fill="none">
              <path d="M 10 24 L 80 24" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.3"/>
              <path d="M 120 24 L 190 24" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.3"/>
            </svg>
            <div class="co-verifier-chip">
              <svg class="co-chip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span>Local verifier</span>
            </div>
          </div>

          <!-- Right: Report Stack -->
          <div class="co-report-stack" aria-label="Generated report preview">
            <div class="co-sheet co-sheet-3"></div>
            <div class="co-sheet co-sheet-2"></div>
            <div class="co-sheet co-sheet-top">
              <div class="co-sheet-title">Report from ${files.length} statement${files.length > 1 ? "s" : ""}</div>
              <div class="co-sheet-bars" title="Last spending distribution">
                ${buildMiniBars(spending)}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Card 2: Pipeline Card -->
      <div class="co-card" id="co-pipeline-card">
        <div class="co-bracket co-bracket-tl"></div>
        <div class="co-bracket co-bracket-tr"></div>
        <div class="co-bracket co-bracket-bl"></div>
        <div class="co-bracket co-bracket-br"></div>
        <div class="co-card-title">
          <span>Processing Pipeline</span>
          <span id="co-pinned-badge" style="font-size:10px;text-transform:none;opacity:0.7;">Auto-cycling</span>
        </div>
        <div class="co-pipeline-list" id="co-pipeline-list" role="tablist">
          <div class="co-pipe-stage co-active" data-stage="0" tabindex="0" role="tab" aria-selected="true">
            <div class="co-pipe-left">
              <span class="co-pipe-num">01</span>
              <div>
                <div class="co-pipe-name">Ingest</div>
                <div class="co-pipe-desc">PDF &amp; CSV multi-format detection</div>
              </div>
            </div>
            <span class="co-pipe-indicator"></span>
          </div>
          <div class="co-pipe-stage" data-stage="1" tabindex="0" role="tab" aria-selected="false">
            <div class="co-pipe-left">
              <span class="co-pipe-num">02</span>
              <div>
                <div class="co-pipe-name">Verify</div>
                <div class="co-pipe-desc">Balance &amp; running ledger integrity</div>
              </div>
            </div>
            <span class="co-pipe-indicator"></span>
          </div>
          <div class="co-pipe-stage" data-stage="2" tabindex="0" role="tab" aria-selected="false">
            <div class="co-pipe-left">
              <span class="co-pipe-num">03</span>
              <div>
                <div class="co-pipe-name">Analyze</div>
                <div class="co-pipe-desc">Categorization, anomalies, budgets</div>
              </div>
            </div>
            <span class="co-pipe-indicator"></span>
          </div>
          <div class="co-pipe-stage" data-stage="3" tabindex="0" role="tab" aria-selected="false">
            <div class="co-pipe-left">
              <span class="co-pipe-num">04</span>
              <div>
                <div class="co-pipe-name">Report</div>
                <div class="co-pipe-desc">Visual intelligence &amp; Q&amp;A summaries</div>
              </div>
            </div>
            <span class="co-pipe-indicator"></span>
          </div>
        </div>
      </div>

      <!-- Card 3: Chart Card (Money In vs Money Out) -->
      <div class="co-card" id="co-chart-card">
        <div class="co-bracket co-bracket-tl"></div>
        <div class="co-bracket co-bracket-tr"></div>
        <div class="co-bracket co-bracket-bl"></div>
        <div class="co-bracket co-bracket-br"></div>
        <div class="co-card-title">
          <span>Month-Over-Month Flow</span>
          <span style="font-size:11px;color:var(--co-text-muted);">${esc(currency)}</span>
        </div>
        <div class="co-chart-container" id="co-chart-box">
          <div class="co-chart-tooltip" id="co-chart-tip"></div>
          <svg class="co-chart-svg" id="co-chart-svg" viewBox="0 0 500 180" preserveAspectRatio="none">
            <!-- Rendered by renderSmoothChart -->
          </svg>
        </div>
        <div class="co-chart-legend">
          <div class="co-legend-item">
            <span class="co-legend-dot co-legend-in"></span>
            <span>Money In (Income)</span>
          </div>
          <div class="co-legend-item">
            <span class="co-legend-dot co-legend-out"></span>
            <span>Money Out (Spending)</span>
          </div>
        </div>
      </div>
    `;

    // Initialize Card 2 & Card 3 interactivity
    initPipelineStageCycling();
    renderSmoothChart(months, income, spending, currency);
  }

  // ── 6. Mini Bar Chart for Report Sheet ─────────────────────────
  function buildMiniBars(spending) {
    if (!spending || spending.length === 0) {
      return `
        <div class="co-sheet-bar-wrap"><div class="co-sheet-bar-fill" style="height:30%;"></div></div>
        <div class="co-sheet-bar-wrap"><div class="co-sheet-bar-fill" style="height:55%;"></div></div>
        <div class="co-sheet-bar-wrap"><div class="co-sheet-bar-fill" style="height:85%;"></div></div>
      `;
    }
    const recent = spending.slice(-6);
    const maxVal = Math.max(...recent, 1);
    return recent
      .map((val) => {
        const pct = Math.max(15, Math.round((val / maxVal) * 100));
        return `<div class="co-sheet-bar-wrap"><div class="co-sheet-bar-fill" style="height:${pct}%;"></div></div>`;
      })
      .join("");
  }

  // ── 7. Pipeline Stage Cycling (1.7s interval) ─────────────────
  function initPipelineStageCycling() {
    const stages = document.querySelectorAll(".co-pipe-stage");
    const badge = document.getElementById("co-pinned-badge");
    if (!stages.length) return;

    let currentStage = 0;
    let isPinned = false;
    let timer = null;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function activateStage(idx) {
      stages.forEach((s, i) => {
        if (i === idx) {
          s.classList.add("co-active");
          s.setAttribute("aria-selected", "true");
        } else {
          s.classList.remove("co-active");
          s.setAttribute("aria-selected", "false");
        }
      });
      currentStage = idx;
    }

    function startCycle() {
      if (prefersReducedMotion || isPinned) return;
      stopCycle();
      timer = setInterval(() => {
        if (!isPinned) {
          activateStage((currentStage + 1) % stages.length);
        }
      }, 1700);
    }

    function stopCycle() {
      if (timer) clearInterval(timer);
      timer = null;
    }

    stages.forEach((stage, idx) => {
      // Hover or focus pins the stage
      const pinHandler = () => {
        isPinned = true;
        activateStage(idx);
        if (badge) badge.textContent = "Pinned";
        stopCycle();
      };
      const unpinHandler = () => {
        isPinned = false;
        if (badge) badge.textContent = "Auto-cycling";
        startCycle();
      };

      stage.addEventListener("mouseenter", pinHandler);
      stage.addEventListener("focus", pinHandler);
      stage.addEventListener("mouseleave", unpinHandler);
      stage.addEventListener("blur", unpinHandler);
    });

    if (!prefersReducedMotion) {
      startCycle();
    }
  }

  // ── 8. Chart: Smooth Bezier Lines & Interactive Scrubber ──────
  function renderSmoothChart(months, income, spending, currency) {
    const svg = document.getElementById("co-chart-svg");
    const box = document.getElementById("co-chart-box");
    const tip = document.getElementById("co-chart-tip");
    if (!svg || !box) return;

    // Default to at least 2 points if data is single-month for smooth rendering
    let displayMonths = months.slice();
    let displayIn = income.slice();
    let displayOut = spending.slice();

    if (displayMonths.length === 0) {
      displayMonths = ["Month 1", "Month 2"];
      displayIn = [0, 0];
      displayOut = [0, 0];
    } else if (displayMonths.length === 1) {
      displayMonths = ["Prev", displayMonths[0]];
      displayIn = [Math.round(displayIn[0] * 0.8), displayIn[0]];
      displayOut = [Math.round(displayOut[0] * 0.85), displayOut[0]];
    }

    const W = 500;
    const H = 180;
    const padX = 30;
    const padY = 24;
    const maxVal = Math.max(...displayIn, ...displayOut, 100);

    const stepX = (W - padX * 2) / (displayMonths.length - 1);
    const scaleY = (val) => H - padY - (val / maxVal) * (H - padY * 2);

    const ptsIn = displayIn.map((v, i) => ({ x: padX + i * stepX, y: scaleY(v), val: v }));
    const ptsOut = displayOut.map((v, i) => ({ x: padX + i * stepX, y: scaleY(v), val: v }));

    // Helper: generate smooth cubic bezier path
    function smoothPath(pts) {
      if (pts.length === 0) return "";
      if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;
      let d = `M ${pts[0].x} ${pts[0].y}`;
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[i === 0 ? 0 : i - 1];
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const p3 = pts[i + 2] || p2;

        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;

        d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
      }
      return d;
    }

    const dIn = smoothPath(ptsIn);
    const dOut = smoothPath(ptsOut);

    svg.innerHTML = `
      <!-- Grid lines -->
      <line x1="${padX}" y1="${H - padY}" x2="${W - padX}" y2="${H - padY}" stroke="var(--co-card-border)" stroke-width="1"/>
      <line x1="${padX}" y1="${padY}" x2="${W - padX}" y2="${padY}" stroke="var(--co-card-border)" stroke-width="1" stroke-dasharray="2 4"/>

      <!-- Smooth Lines -->
      <path d="${dIn}" fill="none" stroke="var(--co-blue)" stroke-width="2.5" stroke-linecap="round"/>
      <path d="${dOut}" fill="none" stroke="var(--co-yellow)" stroke-width="2.5" stroke-linecap="round"/>

      <!-- Scrubber elements -->
      <line id="co-scrub-line" class="co-scrubber-line" x1="0" y1="${padY}" x2="0" y2="${H - padY}"/>
      <circle id="co-scrub-dot-in" class="co-scrubber-dot-in" cx="0" cy="0" r="4.5"/>
      <circle id="co-scrub-dot-out" class="co-scrubber-dot-out" cx="0" cy="0" r="4.5"/>
    `;

    const scrubLine = document.getElementById("co-scrub-line");
    const scrubDotIn = document.getElementById("co-scrub-dot-in");
    const scrubDotOut = document.getElementById("co-scrub-dot-out");

    // Pointer move scrubbing
    box.addEventListener("pointermove", (e) => {
      const rect = box.getBoundingClientRect();
      const pointerX = e.clientX - rect.left;
      const pct = Math.max(0, Math.min(1, pointerX / rect.width));
      const targetSvgX = pct * W;

      // Find closest month index
      let closestIdx = 0;
      let minDiff = Infinity;
      ptsIn.forEach((pt, i) => {
        const diff = Math.abs(pt.x - targetSvgX);
        if (diff < minDiff) {
          minDiff = diff;
          closestIdx = i;
        }
      });

      const ptIn = ptsIn[closestIdx];
      const ptOut = ptsOut[closestIdx];
      const monName = displayMonths[closestIdx];

      scrubLine.setAttribute("x1", ptIn.x);
      scrubLine.setAttribute("x2", ptIn.x);
      scrubLine.style.opacity = "1";

      scrubDotIn.setAttribute("cx", ptIn.x);
      scrubDotIn.setAttribute("cy", ptIn.y);
      scrubDotIn.style.opacity = "1";

      scrubDotOut.setAttribute("cx", ptOut.x);
      scrubDotOut.setAttribute("cy", ptOut.y);
      scrubDotOut.style.opacity = "1";

      // Update Tooltip
      if (tip) {
        tip.innerHTML = `
          <strong>${esc(monName)}</strong> &nbsp;
          <span class="in">in ${fmtAmount(ptIn.val, currency)}</span>
          <span class="out">out ${fmtAmount(ptOut.val, currency)}</span>
        `;
        tip.style.opacity = "1";
        // Position tooltip near cursor
        const tipX = (ptIn.x / W) * rect.width;
        tip.style.left = `${Math.max(60, Math.min(rect.width - 60, tipX))}px`;
      }
    });

    box.addEventListener("pointerleave", () => {
      scrubLine.style.opacity = "0";
      scrubDotIn.style.opacity = "0";
      scrubDotOut.style.opacity = "0";
      if (tip) tip.style.opacity = "0";
    });
  }
})();
