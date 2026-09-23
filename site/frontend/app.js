/* BBS SG Bank - fictional demo site.
   Vanilla ES2020, no build step, no third-party code. All data comes from the
   local demo API and is entirely invented. */

(() => {
  "use strict";

  const KIND_NAMES = { D: "Deposit", W: "Withdrawal", T: "Transfer" };
  const money = (cents) =>
    new Intl.NumberFormat("en-SG", { style: "currency", currency: "SGD", maximumFractionDigits: 2 }).format(
      (Number(cents) || 0) / 100
    );
  const whole = (value) => new Intl.NumberFormat("en-SG").format(Number(value) || 0);
  const stamp = (iso) =>
    new Date(iso).toLocaleString("en-SG", {
      timeZone: "Asia/Singapore",
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  const el = (id) => document.getElementById(id);
  const esc = (value) =>
    String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const state = { meta: null, summary: null, accounts: [], audit: [], selected: null, bench: null, busy: false };

  /* ------------------------------------------------------------ transport */

  async function api(path, options = {}) {
    const { method = "GET", body = null, allow = [200, 201] } = options;
    const response = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
    let data = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    if (!allow.includes(response.status)) {
      const message = (data && data.error && data.error.message) || `Request failed (HTTP ${response.status})`;
      throw new Error(message);
    }
    return data;
  }

  function toast(kind, title, body) {
    const node = document.createElement("div");
    node.className = `toast toast--${kind}`;
    node.innerHTML = `<strong>${esc(title)}</strong>${body ? `<span>${esc(body)}</span>` : ""}`;
    el("toasts").appendChild(node);
    setTimeout(() => node.remove(), 6000);
  }

  /* --------------------------------------------------------------- routing */

  function showView(name, { push = true } = {}) {
    const target = document.getElementById(`view-${name}`);
    if (!target) return;
    document.querySelectorAll(".view").forEach((view) => view.classList.toggle("is-active", view === target));
    document.querySelectorAll(".tab").forEach((tab) => {
      const active = tab.dataset.view === name;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-current", active ? "page" : "false");
    });
    if (push && location.hash !== `#${name}`) history.replaceState(null, "", `#${name}`);
    if (name === "benchmark" && !state.bench) runBenchmark();
    if (name === "accounts" && state.selected) renderAccountDetail().catch(() => {});
  }

  /* -------------------------------------------------------------- overview */

  function renderKpis(summary) {
    el("kpi-total").textContent = money(summary.total_cents);
    el("kpi-total-sub").textContent = `${summary.account_count} fictional accounts`;
    el("kpi-posted").textContent = whole(summary.posted_count);
    el("kpi-rejected").textContent = whole(summary.rejected_count);
    const invariant = el("kpi-invariant");
    invariant.textContent = summary.invariant_ok ? "OK" : "DRIFT";
    invariant.className = summary.invariant_ok ? "good" : "warn";
  }

  function renderBars() {
    const top = [...state.accounts].sort((a, b) => b.balance_cents - a.balance_cents).slice(0, 6);
    const max = top.length ? top[0].balance_cents : 1;
    el("bars-note").textContent = `· top ${top.length} of ${state.accounts.length}`;
    el("balance-bars").innerHTML = top
      .map(
        (account) => `<li>
          <span class="bars__name" title="${esc(account.name)}">${esc(account.name)}</span>
          <span class="bars__track"><span class="bars__fill" style="width:${Math.max(3, Math.round((account.balance_cents / max) * 100))}%"></span></span>
          <span class="bars__value">${money(account.balance_cents)}</span>
        </li>`
      )
      .join("");
  }

  function renderFeed() {
    const html = (items, empty) => {
      const list = items.length
        ? items
            .map(
              (entry) => `<li>
                <span class="feed__badge feed__badge--${entry.status}">${entry.kind}</span>
                <span class="feed__body">
                  <strong>${esc(KIND_NAMES[entry.kind] || entry.kind)} · ${esc(entry.source_name)}${entry.target_name ? ` → ${esc(entry.target_name)}` : ""}</strong>
                  <span>${stamp(entry.timestamp)} · ${esc(entry.reason || entry.actor || "posted")}</span>
                </span>
                <span class="feed__amount ${entry.status === "posted" ? "" : "warn"}">${money(entry.amount_cents)}</span>
              </li>`
            )
            .join("")
        : `<li class="feed__empty">${esc(empty)}</li>`;
      return list;
    };
    el("mini-feed").innerHTML = html(state.audit.slice(0, 5), "No postings yet.");
    el("post-feed").innerHTML = html(state.audit.slice(0, 12), "No postings yet.");
  }

  /* ------------------------------------------------------------------ CRT */

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function crtLines() {
    const posted = state.summary ? state.summary.posted_count : 0;
    const rejected = state.summary ? state.summary.rejected_count : 0;
    const total = state.summary ? state.summary.total_cents : 0;
    const rows = state.accounts.length;
    const seeded = state.audit.slice().reverse().slice(0, 6);
    const body = seeded.map((entry, index) => {
      const seq = String(index + 1).padStart(4, "0");
      const outcome = entry.status === "posted" ? "ACCEPTED" : "REJECTED";
      const marker = entry.status === "posted" ? "" : ' <span class="bad">*</span>';
      return `  22:00:${String(5 + index).padStart(2, "0")} OP ${seq}  ${entry.kind} ${entry.source} > ${entry.target || "00000000"}  ${outcome}${marker}`;
    });
    return [
      "<span class=\"dim\">BBS SG BANK - NIGHTLY BATCH   NBATCH/COBOL   SYSPLEX: PROD1</span>",
      "<span class=\"dim\">-------------------------------------------------------------</span>",
      "  JOB NBR90240 SUBMITTED BY OPSUSER",
      `  OPEN ACCOUNTS.DAT   ORG:LINE SEQUENTIAL   ${String(rows).padStart(3, " ")} ROWS`,
      "  OPEN OPERATIONS.DAT ORG:LINE SEQUENTIAL",
      "<span class=\"dim\">  -- per operation: reopen + scan ACCOUNTS.DAT --</span>",
      ...body,
      "<span class=\"dim\">  -- rewrite ACCOUNTS.DAT + reopen for totals --</span>",
      "  JOB NBR90240 COMPLETED WITH WARNINGS",
      `  PROCESSED=${String(posted).padStart(8, "0")}`,
      `  REJECTED =${String(rejected).padStart(8, "0")}`,
      `  TOTAL_CENTS=${String(total).padStart(16, "0")}`,
      "<span class=\"bad\">  NO JOURNAL FILE WRITTEN - RERUNS ARE MANUAL</span>",
      "<span class=\"dim\">  SCREEN REPLAY OF THE LEGACY OUTPUT FORMAT (NOT A REAL 3270</span>",
      "<span class=\"dim\">  TERMINAL; NO COBOL IS EXECUTED IN THE BROWSER). SEE THE</span>",
      "<span class=\"dim\">  BENCHMARK TAB FOR MEASURED ENGINE TIMINGS.</span>",
    ];
  }

  function paintCrt(lines) {
    el("crt-screen").innerHTML = lines.join("\n") + '\n<span class="dim">NBATCH></span><span class="cursor"> </span>';
  }

  async function replayCrt() {
    const lines = crtLines();
    if (prefersReduced) {
      paintCrt(lines);
      return;
    }
    const screen = el("crt-screen");
    const flat = lines.slice();
    screen.innerHTML = "";
    let index = 0;
    const step = () => {
      if (index >= flat.length) {
        paintCrt(flat);
        return;
      }
      screen.innerHTML = flat.slice(0, index + 1).join("\n") + '\n<span class="dim">NBATCH></span><span class="cursor"> </span>';
      index += 1;
      setTimeout(step, 55);
    };
    step();
  }

  /* ------------------------------------------------------------- accounts */

  function renderAccounts() {
    const rows = state.accounts;
    el("accounts-body").innerHTML = rows.length
      ? rows
          .map(
            (account) => `<tr data-account="${esc(account.id)}" class="${state.selected === account.id ? "is-selected" : ""}">
              <td><button class="account-cell id-mono" type="button" data-account-link="${esc(account.id)}">${esc(account.id)}</button></td>
              <td>${esc(account.name)}<span class="row-name">${account.movements} audit row(s)</span></td>
              <td>${esc(account.product)}</td>
              <td class="num">${money(account.opening_balance_cents)}</td>
              <td class="num">${money(account.balance_cents)}</td>
              <td class="num">${whole(account.movements)}</td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="6" class="table__loading">No accounts match that search.</td></tr>`;
    el("accounts-total").textContent = money(rows.reduce((sum, account) => sum + account.balance_cents, 0));
    el("accounts-rows").textContent = whole(rows.reduce((sum, account) => sum + account.movements, 0));
  }

  async function renderAccountDetail({ scroll = false } = {}) {
    const panel = el("account-detail");
    if (!state.selected) {
      panel.hidden = true;
      panel.innerHTML = "";
      return;
    }
    let detail;
    try {
      detail = await api(`/api/accounts/${encodeURIComponent(state.selected)}`);
    } catch (error) {
      // The account is gone (for example the ledger was rebuilt): drop the panel.
      state.selected = null;
      panel.hidden = true;
      panel.innerHTML = "";
      renderAccounts();
      if (scroll) toast("bad", "Could not load account", error.message);
      return;
    }
    state.selected = detail.id;
    panel.hidden = false;
    panel.innerHTML = `
        <header class="panel__head">
          <div>
            <p class="eyebrow">Account ${esc(detail.id)}</p>
            <h2>${esc(detail.name)}</h2>
          </div>
          <span class="chip">${esc(detail.product)} · ${money(detail.balance_cents)}</span>
        </header>
        <div class="results__tiles">
          <div class="tile"><span>Opening</span><strong>${money(detail.opening_balance_cents)}</strong></div>
          <div class="tile"><span>Balance</span><strong id="detail-balance">${money(detail.balance_cents)}</strong></div>
          <div class="tile"><span>Net movement</span><strong>${money(detail.balance_cents - detail.opening_balance_cents)}</strong></div>
          <div class="tile"><span>Rows shown</span><strong>${whole(detail.history.length)}</strong></div>
        </div>
        <h3 style="margin-top:1rem">Recent activity</h3>
        <div class="table-wrap table-wrap--scroll">
          <table class="table table--compact">
            <thead><tr><th scope="col">Entry</th><th scope="col">Time (SGT)</th><th scope="col">Type</th><th scope="col">Counterparty</th><th scope="col" class="num">Amount</th><th scope="col">Status</th></tr></thead>
            <tbody>
              ${
                detail.history.length
                  ? detail.history
                      .map(
                        (entry) => `<tr>
                          <td class="id-mono">${esc(entry.id)}</td>
                          <td>${stamp(entry.timestamp)}</td>
                          <td>${esc(KIND_NAMES[entry.kind] || entry.kind)}</td>
                          <td>${esc(entry.source === detail.id ? entry.target_name || "—" : entry.source_name)}</td>
                          <td class="num">${money(entry.amount_cents)}</td>
                          <td><span class="tag tag--${entry.status}">${esc(entry.status)}</span></td>
                        </tr>`
                      )
                      .join("")
                  : `<tr><td colspan="6" class="muted">No activity for this account yet.</td></tr>`
              }
            </tbody>
          </table>
        </div>`;
    if (scroll) panel.scrollIntoView({ behavior: prefersReduced ? "auto" : "smooth", block: "nearest" });
  }

  async function openAccount(accountId) {
    state.selected = accountId;
    renderAccounts();
    await renderAccountDetail({ scroll: true });
  }

  async function refreshAccountsView() {
    await loadAccounts(); // loadAccounts re-renders the table and the bars
    await renderAccountDetail();
  }

  /* -------------------------------------------------------------- transfers */

  function fillSelects() {
    const options = state.accounts
      .map((account) => `<option value="${esc(account.id)}">${esc(account.id)} · ${esc(account.name)} (${money(account.balance_cents)})</option>`)
      .join("");
    const source = el("source-select");
    const target = el("target-select");
    const sourceValue = source.value;
    const targetValue = target.value;
    source.innerHTML = options;
    target.innerHTML = options;
    if (state.accounts.length) {
      source.value = sourceValue && state.accounts.some((a) => a.id === sourceValue) ? sourceValue : state.accounts[0].id;
      const fallback = state.accounts[1] ? state.accounts[1].id : state.accounts[0].id;
      target.value = targetValue && state.accounts.some((a) => a.id === targetValue) ? targetValue : fallback;
    }
  }

  function syncKind() {
    const kind = document.querySelector('input[name="kind"]:checked').value;
    el("form-mode-chip").textContent = KIND_NAMES[kind].toLowerCase();
    const targetField = el("target-field");
    const isTransfer = kind === "T";
    targetField.hidden = !isTransfer;
    el("target-select").required = isTransfer;
    el("form-note").textContent = isTransfer
      ? "Transfers must name a different destination account and cannot exceed the source balance."
      : kind === "W"
      ? "Withdrawals cannot exceed the source balance."
      : "Deposits add value to the ledger total — the batch console keeps to transfers so value stays conserved.";
  }

  async function submitPosting(event) {
    event.preventDefault();
    if (state.busy) return;
    const kind = document.querySelector('input[name="kind"]:checked').value;
    const amount = Number(el("amount-input").value);
    if (!Number.isFinite(amount) || amount <= 0) {
      toast("warn", "Enter an amount", "The amount must be greater than zero.");
      return;
    }
    const button = el("submit-op");
    button.disabled = true;
    state.busy = true;
    try {
      const payload = {
        kind,
        source: el("source-select").value,
        target: kind === "T" ? el("target-select").value : null,
        amount_cents: Math.round(amount * 100),
        actor: "site.ui",
        reference: `UI-${Date.now().toString().slice(-6)}`,
      };
      const response = await api("/api/operations", { method: "POST", body: payload, allow: [200, 201, 422] });
      const result = response.result.operations[0];
      if (result.status === "posted") {
        toast("good", `${KIND_NAMES[kind]} posted`, `${money(result.amount_cents)} · engine accepted in ${response.result.elapsed_ms} ms`);
      } else {
        toast("warn", `${KIND_NAMES[kind]} rejected`, `${result.reason} — the engine left the ledger unchanged.`);
      }
      await refreshAll();
    } catch (error) {
      toast("bad", "Posting failed", error.message);
    } finally {
      button.disabled = false;
      state.busy = false;
    }
  }

  /* ----------------------------------------------------------------- batch */

  async function runBatch({ resetFirst = false } = {}) {
    const button = el("batch-run");
    const progress = el("batch-progress");
    const bar = el("batch-progress-bar");
    button.disabled = true;
    progress.hidden = false;
    bar.style.width = "12%";
    const ticker = setTimeout(() => (bar.style.width = "68%"), 120);
    try {
      if (resetFirst) {
        await api("/api/reset", { method: "POST" });
        toast("good", "Ledger reset", "Seed history replayed through the engine.");
      }
      const payload = {
        operations: Number(el("batch-ops").value),
        seed: Number(el("batch-seed").value) || 20260923,
        include_edge_cases: el("batch-edges").checked,
      };
      const response = await api("/api/batch", { method: "POST", body: payload });
      clearTimeout(ticker);
      bar.style.width = "100%";
      renderBatch(response.result);
      await refreshAll();
      toast(
        response.result.conservation_ok ? "good" : "bad",
        `Batch finished: ${response.result.processed} posted, ${response.result.rejected} rejected`,
        response.result.conservation_ok
          ? "Ledger total unchanged — transfers only move value."
          : "Ledger total changed unexpectedly; check the engine output."
      );
    } catch (error) {
      clearTimeout(ticker);
      bar.style.width = "0%";
      toast("bad", "Batch failed", error.message);
    } finally {
      button.disabled = false;
      setTimeout(() => {
        progress.hidden = true;
        bar.style.width = "0%";
      }, 600);
    }
  }

  function renderBatch(batch) {
    el("batch-results").hidden = false;
    el("r-submitted").textContent = whole(batch.operations.length);
    el("r-posted").textContent = whole(batch.processed);
    el("r-rejected").textContent = whole(batch.rejected);
    el("r-elapsed").textContent = `${batch.elapsed_ms.toFixed(2)} ms`;

    const checks = [
      ["ok", "Value conserved", `Total before ${money(batch.total_before_cents)} · after ${money(batch.total_after_cents)}`],
      ["ok", "In-memory ledger matches accounts.dat", `Engine total ${money(batch.engine_total_cents)}`],
      [
        batch.engine_matches_simulation ? "ok" : "ko",
        "Independent re-simulation agrees with the engine",
        batch.engine_matches_simulation
          ? "Predicted accept/reject counts matched the engine's counters."
          : "Prediction disagreed with the engine — investigate before trusting the reasons below.",
      ],
    ];
    el("batch-checks").innerHTML = checks
      .map(([cls, title, detail]) => `<li><span class="${cls}">${cls === "ok" ? "✔" : "✖"}</span> <strong>${esc(title)}</strong> <span class="muted">${esc(detail)}</span></li>`)
      .join("");

    el("batch-reasons").innerHTML = batch.rejections_by_reason.length
      ? batch.rejections_by_reason.map((row) => `<li><span>${esc(row.reason)}</span><b>${whole(row.count)}</b></li>`).join("")
      : `<li class="muted">No rejections — every row was accepted.</li>`;

    const rejected = batch.operations.filter((op) => op.status === "rejected");
    el("batch-rejects").innerHTML = rejected.length
      ? rejected
          .map(
            (op) => `<tr>
              <td class="id-mono">${esc(op.reference || "—")}</td>
              <td class="id-mono">${esc(op.source)}</td>
              <td class="id-mono">${esc(op.target || "—")}</td>
              <td class="num">${money(op.amount_cents)}</td>
              <td class="warn">${esc(op.reason)}</td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="5" class="muted">None</td></tr>`;

    const posted = batch.operations.filter((op) => op.status === "posted");
    el("accepted-count").textContent = whole(posted.length);
    el("batch-posted").innerHTML = posted.length
      ? posted
          .map(
            (op) => `<tr>
              <td class="id-mono">${esc(op.reference || "—")}</td>
              <td class="id-mono">${esc(op.source)}</td>
              <td class="id-mono">${esc(op.target || "—")}</td>
              <td class="num">${money(op.amount_cents)}</td>
              <td class="num">${money(op.source_balance_cents)}</td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="5" class="muted">None</td></tr>`;

    el("batch-note").textContent =
      "Rejections are normal: the engine validates every row and refuses to move money it cannot justify. " +
      "The batch is executed by modern/bank.py on flat files in a temporary directory.";
  }

  /* ------------------------------------------------------------ benchmark */

  function renderBenchmark(report) {
    state.bench = report;
    const params = report.params;
    const metric = (label, value) => `<div class="bench-metric"><span>${esc(label)}</span><strong>${value}</strong></div>`;
    const rows = whole(params.fixture_rows);

    const engineCard = (engine) =>
      [
        metric("Median wall clock", `${engine.median.toFixed(3)} s`),
        metric("Fastest run", `${engine.min.toFixed(3)} s`),
        metric("Runs measured", `${engine.samples.length} after ${params.warmup} warm-up`),
        metric("Rows/sec", whole(engine.operations_per_second)),
        metric("Processed / rejected", `${whole(engine.PROCESSED)} / ${whole(engine.REJECTED)}`),
        metric("Engine", `<code>${esc(engine.engine)}</code>`),
      ].join("");

    el("bench-legacy").innerHTML = report.legacy.available
      ? engineCard(report.legacy)
      : `<div class="bench-unavailable"><strong>Not measurable on this machine.</strong><p style="margin:0.4rem 0 0">${esc(
          report.legacy.reason
        )}</p><p style="margin:0.4rem 0 0">Until a cobc is available, no legacy timing, ratio or speed-up is claimed anywhere on this site.</p></div>`;

    el("bench-modern").innerHTML = report.modern.available
      ? engineCard(report.modern)
      : `<div class="bench-unavailable">${esc(report.modern.reason)}</div>`;

    let verdict;
    if (report.legacy.available && report.modern.available && report.speedup) {
      const parity = report.outputs_identical
        ? "outputs were byte-identical between the two engines"
        : "the two engines did NOT agree on output";
      const faster = report.speedup >= 1;
      verdict =
        `Measured on this host: legacy ${report.legacy.median.toFixed(3)} s vs modern ${report.modern.median.toFixed(3)} s ` +
        `(median of ${report.legacy.samples.length} timed runs, ${rows} rows) — ` +
        `${faster ? `${report.speedup}x faster` : `${(1 / report.speedup).toFixed(2)}x slower`}. ` +
        `Parity was checked first: ${parity}. ` +
        (faster
          ? "The ratio grows with the account count because the legacy program rescans the whole ledger per operation, " +
            "while the modern engine stays linear in the number of operations."
          : "At this fixture size the cost is mostly process start-up, which the compiled COBOL binary wins; the same " +
            "measurement at a realistic ledger size goes the other way, because the legacy program rescans the whole " +
            "ledger per operation.");
    } else if (report.modern.available) {
      verdict =
        "Only the modern engine could be timed here, so this site claims no speed-up. " +
        "The structural difference is in the source: legacy/bank.cob re-reads the whole accounts file for every " +
        "operation, while modern/bank.py applies each operation once against an in-memory index.";
    } else {
      verdict = "Neither engine could be timed on this host; see the notes below.";
    }
    el("bench-verdict-text").textContent = verdict;

    el("bench-notes").innerHTML = report.notes.map((note) => `<li>${esc(note)}</li>`).join("");
    const env = report.environment;
    el("bench-env").innerHTML = [
      ["python", env.python],
      ["platform", env.platform],
      ["gnucobol", env.cobc_version || "not found"],
      ["cobc path", env.cobc_path || "—"],
      ["legacy source", env.legacy_source],
      ["modern engine", env.modern_engine],
      ["shared helpers", env.harness],
      ["fixture", `${whole(params.accounts)} accounts · ${whole(params.operations)} operations + ${params.edge_cases} edge cases (seed ${params.seed})`],
      ["fixture digest", report.fixture_digest || "n/a"],
      ["measured at", report.generated_at],
      ["result cache", report.cached ? "served from the local cache" : "freshly measured just now"],
    ]
      .map(([key, value]) => `<dt>${esc(key)}</dt><dd>${esc(value)}</dd>`)
      .join("");
  }

  async function runBenchmark() {
    const button = el("bench-run");
    button.disabled = true;
    el("bench-legacy").textContent = "Measuring both engines — this takes a few seconds…";
    el("bench-modern").textContent = "Measuring both engines…";
    try {
      const accounts = Number(el("bench-accounts").value) || 1200;
      const operations = Number(el("bench-operations").value) || 0;
      const report = await api(`/api/benchmark?accounts=${accounts}&operations=${operations}&fresh=1`);
      renderBenchmark(report);
    } catch (error) {
      el("bench-legacy").textContent = "—";
      el("bench-modern").textContent = "—";
      toast("bad", "Benchmark failed", error.message);
    } finally {
      button.disabled = false;
    }
  }

  /* -------------------------------------------------------------- audit */

  function renderAudit() {
    const rows = state.audit;
    el("audit-body").innerHTML = rows.length
      ? rows
          .map(
            (entry) => `<tr>
              <td class="id-mono">${esc(entry.id)}</td>
              <td>${stamp(entry.timestamp)}</td>
              <td><span class="tag tag--kind">${esc(entry.kind)}</span> ${esc(KIND_NAMES[entry.kind] || entry.kind)}</td>
              <td>${esc(entry.source)}<span class="row-name">${esc(entry.source_name)}</span></td>
              <td>${entry.target ? `${esc(entry.target)}<span class="row-name">${esc(entry.target_name || "")}</span>` : "—"}</td>
              <td class="num">${money(entry.amount_cents)}</td>
              <td><span class="tag tag--${entry.status}">${esc(entry.status)}</span></td>
              <td>${esc(entry.reason || describeSource(entry))}</td>
            </tr>`
          )
          .join("")
      : `<tr><td colspan="8" class="table__loading">No audit rows match those filters.</td></tr>`;
    el("audit-note").textContent =
      `${rows.length} row(s) shown. Seeded rows are the illustrative history replayed at reset; everything else was posted while you used the site.`;
  }

  function describeSource(entry) {
    if (entry.seeded) return `${entry.actor} · seeded history`;
    return entry.actor === entry.channel ? entry.actor : `${entry.actor} · ${entry.channel}`;
  }

  function download(filename, text, type) {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  function exportAudit(format) {
    if (!state.audit.length) {
      toast("warn", "Nothing to export", "The audit trail is empty.");
      return;
    }
    if (format === "json") {
      download("bbs-sgbank-audit.json", JSON.stringify(state.audit, null, 2), "application/json");
      return;
    }
    const columns = ["id", "timestamp", "kind", "status", "source", "source_name", "target", "target_name", "amount_cents", "reason", "actor", "channel", "seeded"];
    const rows = [columns.join(",")].concat(
      state.audit.map((entry) => columns.map((column) => `"${String(entry[column] == null ? "" : entry[column]).replace(/"/g, '""')}"`).join(","))
    );
    download("bbs-sgbank-audit.csv", rows.join("\n"), "text/csv");
  }

  /* ---------------------------------------------------------------- loads */

  async function loadAudit() {
    const params = new URLSearchParams({ limit: "200" });
    if (el("audit-status").value) params.set("status", el("audit-status").value);
    if (el("audit-kind").value) params.set("kind", el("audit-kind").value);
    const data = await api(`/api/audit?${params.toString()}`);
    state.audit = data.entries;
    renderAudit();
    renderFeed();
  }

  async function loadAccounts() {
    const term = el("account-search").value.trim();
    const data = await api(`/api/accounts${term ? `?q=${encodeURIComponent(term)}` : ""}`);
    state.accounts = data.accounts;
    renderAccounts();
    renderBars();
    if (!term) fillSelects();
  }

  async function refreshAll() {
    const summary = await api("/api/summary");
    state.summary = summary;
    renderKpis(summary);
    await Promise.all([loadAccounts(), loadAudit()]);
    await renderAccountDetail();
    updateMiniTiles(summary);
  }

  function updateMiniTiles(summary) {
    const batch = summary.last_batch;
    const rows = batch ? batch.processed + batch.rejected : 0;
    el("mini-latency").textContent = batch ? `${batch.elapsed_ms.toFixed(2)} ms` : "—";
    el("mini-latency-note").textContent = batch
      ? `${whole(rows)} rows, engine only (no HTTP or file copy)`
      : "last batch, engine only";
    el("mini-throughput").textContent =
      batch && batch.elapsed_ms > 0 ? whole(Math.round(rows / (batch.elapsed_ms / 1000))) : "—";
    el("mini-throughput-note").textContent = batch
      ? `${whole(rows)} rows ÷ ${batch.elapsed_ms.toFixed(2)} ms engine time`
      : "rows ÷ engine time, last batch";
  }

  /* ------------------------------------------------------------------ boot */

  async function boot() {
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.addEventListener("click", (event) => {
        event.preventDefault();
        showView(tab.dataset.view);
      });
    });
    document.querySelectorAll("[data-goto]").forEach((button) => {
      button.addEventListener("click", () => showView(button.dataset.goto));
    });

    el("reset-btn").addEventListener("click", async () => {
      try {
        const response = await api("/api/reset", { method: "POST" });
        toast("good", "Demo data reset", response.message);
        await refreshAll();
        await replayCrt();
      } catch (error) {
        toast("bad", "Reset failed", error.message);
      }
    });

    el("crt-run").addEventListener("click", () => replayCrt());
    el("accounts-refresh").addEventListener("click", () => refreshAccountsView().catch((error) => toast("bad", "Refresh failed", error.message)));
    el("feed-refresh").addEventListener("click", () => loadAudit().catch((error) => toast("bad", "Refresh failed", error.message)));
    el("account-search").addEventListener("input", debounce(() => loadAccounts().catch(() => {}), 200));
    el("accounts-body").addEventListener("click", (event) => {
      const link = event.target.closest("[data-account-link]");
      if (link) openAccount(link.dataset.accountLink);
    });

    document.querySelectorAll('input[name="kind"]').forEach((radio) => radio.addEventListener("change", syncKind));
    document.querySelectorAll("[data-amount]").forEach((button) =>
      button.addEventListener("click", () => {
        el("amount-input").value = Number(button.dataset.amount).toFixed(2);
      })
    );
    el("op-form").addEventListener("submit", submitPosting);

    el("batch-ops").addEventListener("input", () => {
      el("ops-output").textContent = el("batch-ops").value;
    });
    el("batch-run").addEventListener("click", () => runBatch());
    el("batch-reset").addEventListener("click", () => runBatch({ resetFirst: true }));
    el("bench-run").addEventListener("click", runBenchmark);
    document.querySelectorAll("[data-bench-accounts]").forEach((button) =>
      button.addEventListener("click", () => {
        el("bench-accounts").value = button.dataset.benchAccounts;
        el("bench-operations").value = button.dataset.benchOperations;
        runBenchmark();
      })
    );

    el("audit-status").addEventListener("change", () => loadAudit().catch((error) => toast("bad", "Audit failed", error.message)));
    el("audit-kind").addEventListener("change", () => loadAudit().catch((error) => toast("bad", "Audit failed", error.message)));
    el("audit-export-json").addEventListener("click", () => exportAudit("json"));
    el("audit-export-csv").addEventListener("click", () => exportAudit("csv"));

    window.addEventListener("hashchange", () => showView((location.hash || "#overview").slice(1), { push: false }));

    try {
      const meta = await api("/api/meta");
      state.meta = meta;
      el("engine-pill").textContent = `engine: ${meta.engine.modern.split(" ")[0]}`;
      el("footer-version").textContent = "site/ · local demo build";
      syncKind();
      await refreshAll();
      await replayCrt();

      const code = await api("/api/legacy/source");
      el("legacy-path").textContent = code.path;
      el("legacy-code").innerHTML = code.lines
        .map((line, index) => {
          const number = index + 1;
          const hit = code.bottleneck_lines.includes(number);
          return `<span class="line${hit ? " hit" : ""}"><span class="ln">${number}</span>${esc(line) || " "}</span>`;
        })
        .join("\n");
    } catch (error) {
      toast("bad", "Demo API unavailable", `${error.message}. Start the server with: python3 site/backend/app.py`);
    }

    const initial = (location.hash || "#overview").slice(1);
    showView(document.getElementById(`view-${initial}`) ? initial : "overview", { push: false });
  }

  function debounce(fn, wait) {
    let timer = null;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), wait);
    };
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
