/**
 * Headless interaction test for legacy-ui/terminal.html.
 *
 * No browser is installed on this machine, so this harness supplies the small
 * DOM surface the terminal wiring touches, runs the page's two inline scripts
 * against the real helper server (legacy-ui/server.py) and drives the terminal
 * with synthetic key events. Every assertion is made against what the screen
 * actually renders.
 *
 * Usage: node legacy-ui/tests/interaction.mjs [baseUrl] [--offline]
 *   --offline  point the page at an unreachable engine and assert that every
 *              batch screen is labelled SIMULATED instead of claiming a job.
 * Exit code 0 = all checks passed.
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const HERE = dirname(fileURLToPath(import.meta.url));
const HTML = readFileSync(join(HERE, "..", "terminal.html"), "utf8");
const OFFLINE = process.argv.includes("--offline");
const BASE = process.argv[2] && !process.argv[2].startsWith("--")
  ? process.argv[2]
  : OFFLINE ? "http://127.0.0.1:9" : "http://127.0.0.1:8792";

const checks = [];
function check(name, ok, detail) {
  checks.push({ name, ok: !!ok });
  console.log(`${ok ? "ok  " : "FAIL"} ${name}${detail ? "  [" + detail + "]" : ""}`);
  return !!ok;
}

function script(id) {
  const m = HTML.match(new RegExp('<script id="' + id + '">([\\s\\S]*?)</script>'));
  if (!m) throw new Error(`script ${id} not found in terminal.html`);
  return m[1];
}

// ------------------------------------------------------------------ fake DOM
function makeEl(tag) {
  const classes = new Set();
  return {
    tagName: tag, innerHTML: "", textContent: "", children: [], handlers: {},
    classList: { toggle: (n, on) => (on ? classes.add(n) : classes.delete(n)), contains: (n) => classes.has(n) },
    appendChild(child) { this.children.push(child); return child; },
    addEventListener(type, fn) { (this.handlers[type] = this.handlers[type] || []).push(fn); },
    focus() { document.activeElement = this; },
    dispatch(type, event) { (this.handlers[type] || []).forEach((fn) => fn(event || {})); },
    press(key) { this.dispatch("keydown", { key, ctrlKey: false, metaKey: false, altKey: false, preventDefault() {} }); },
    type(text) { for (const ch of String(text)) this.press(ch); }
  };
}

const elements = {};
["screen", "keypad", "led", "engine-label", "doc-mode", "doc-engine", "doc-session", "doc-warehouse"]
  .forEach((id) => (elements[id] = makeEl("div")));

const document = {
  activeElement: null,
  getElementById: (id) => elements[id] || null,
  createElement: (tag) => makeEl(tag),
  addEventListener() {}
};

const ctx = {
  console, document, URLSearchParams, JSON, Math, Date, Object, String, Array, Number, RegExp,
  setTimeout, setInterval, clearInterval, clearTimeout,
  fetch: (path, options) => fetch(BASE + path, options)
};
ctx.window = { location: { search: "" }, addEventListener() {}, setTimeout, setInterval, clearInterval };
ctx.globalThis = ctx;
vm.createContext(ctx);

// --------------------------------------------------------------- run scripts
vm.runInContext(script("terminal-logic"), ctx, { filename: "terminal-logic.js" });
ctx.window.BbsTerminal = ctx.BbsTerminal;
check("logic module exposes BbsTerminal", ctx.BbsTerminal && typeof ctx.BbsTerminal.createState === "function");
vm.runInContext(script("terminal-wiring"), ctx, { filename: "terminal-wiring.js" });

const screen = elements["screen"];
const text = () => screen.innerHTML.replace(/<[^>]*>/g, "")
  .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
const label = () => elements["engine-label"].textContent;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function step(name, predicate, timeout = 45000, detail) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    let value;
    try { value = predicate(); } catch { value = false; }
    if (value) return check(name, true, typeof value === "string" ? value : (typeof detail === "function" ? detail() : detail));
    await sleep(100);
  }
  return check(name, false, detail || "timed out");
}

async function offlineWalkthrough() {
  // The page must never claim a job ran when no engine is reachable.
  await step("offline boot renders the sign-on screen", () => /SIGN ON/.test(text()));
  await step("offline page says the engine is unreachable", () => /SIMULATED/.test(label()) && /ENGINE UNREACHABLE/.test(text()), 20000,
    () => label());
  check("offline page never claims LIVE COBOL", !/LIVE COBOL/.test(text()) && !/local cobc/.test(label()));
  check("offline status line still shows the synthetic tag", /SYNTHETIC DEMO/.test(text()));

  screen.focus();
  screen.type("OPS01");
  screen.press("Enter");
  await step("offline sign-on reaches the menu", () => /OPERATIONS MENU/.test(text()));
  screen.press("3");
  screen.press("Enter");
  await step("offline batch screen warns about the missing engine", () => /BATCH SUBMISSION/.test(text()) && /SIMULATED/.test(text()));
  screen.press("S");
  screen.press("Enter");
  await sleep(150);
  screen.press("F9");
  await step("offline job screen is marked SIMULATED", () => /\*\*\* SIMULATED \*\*\*/.test(text()), 20000);
  await step("offline journal says no COBOL job executed",
    () => /NO COBOL JOB EXECUTED|NO LOCAL COBOL ENGINE REACHABLE/.test(text()), 20000);
  await step("offline job completes as a replay", () => /COMPLETE\s+PROCESSED/.test(text()), 30000);
  check("offline result is flagged as a replay", /SIMULATED/.test(text()) && /SPOOL DISPLAY \(SIMULATED/.test(text()));

  screen.press("F12");
  await step("offline logoff returns to sign-on", () => /SIGN ON/.test(text()), 15000);

  const failed = checks.filter((c) => !c.ok);
  console.log(`\n${checks.length - failed.length}/${checks.length} checks passed`);
  if (failed.length) {
    failed.forEach((f) => console.log("  failed: " + f.name));
    process.exit(1);
  }
  process.exit(0);
}

async function main() {
  if (OFFLINE) return offlineWalkthrough();
  // 1. boot: the page must reach the helper server and report the live engine
  await step("boot renders the sign-on screen", () => /SIGN ON/.test(text()));
  await step("helper server reachable (LIVE COBOL mode)", () => /local cobc/.test(label()), 15000, () => label());
  check("sign-on status identifies synthetic demo", /SYNTHETIC DEMO/.test(text()));
  check("menu keys are rendered", elements["keypad"].children.length === 13, elements["keypad"].children.length + " keys");
  check("status line offers a disclosure shortcut", /DISCLOSE|PF12/.test(text()));

  // 2. sign on with a typed operator id
  screen.focus();
  screen.type("OPS01");
  screen.press("Enter");
  await step("sign-on shows the operations menu", () => /OPERATIONS MENU/.test(text()));
  check("operator id echoed in the OIA line", /OPRID OPS01/.test(text()), (text().match(/OPRID\s+\S+/) || [])[0]);

  // 3. accounts: menu option 1, then page forward and back
  screen.press("1");
  screen.press("Enter");
  await step("option 1 opens the account master file", () => /ACCOUNT MASTER FILE/.test(text()));
  const first = (text().match(/PAGE\s+(\d+)\s+OF\s+(\d+)/) || []);
  check("account page reports a page count", Number(first[2]) > 1, first[0]);
  screen.press("F8");
  await step("PF8 pages the account list forward", () => /PAGE\s+2\s+OF/.test(text()), 15000,
    (text().match(/PAGE\s+\d+\s+OF\s+\d+/) || [])[0]);
  screen.press("F7");
  await step("PF7 pages back", () => /PAGE\s+1\s+OF/.test(text()), 15000);
  screen.press("Tab");                 // command prompt
  screen.type("ACCT 00000004");
  screen.press("Enter");
  await step("ACCT command opens the account inquiry", () => /ACCOUNT INQUIRY/.test(text()),
    15000, (text().match(/ACCOUNT INQUIRY -- \d+/) || [])[0]);
  check("inquiry shows holder and balances", /HOLDER/.test(text()) && /CURRENT BALANCE/.test(text()));

  // 4. operations queue (menu option 2)
  screen.press("F3");
  await step("PF3 returns from the inquiry to the account list", () => /ACCOUNT MASTER FILE/.test(text()), 15000);
  screen.press("F3");
  await step("PF3 returns to the menu", () => /OPERATIONS MENU/.test(text()), 15000);
  screen.press("2");
  screen.press("Enter");
  await step("option 2 opens the operations queue", () => /OPERATIONS QUEUE/.test(text()), 15000);
  await step("queue loads its rows and counts from the server", () => /PRED-POSTED/.test(text()), 15000,
    () => (text().match(/ROWS [\d,]+/) || [])[0]);
  check("queue flags its statuses as a replay, not job output",
    /JOB'S COUNTERS ARE ON PF10/.test(text()));
  check("queue lists posted rows", /POSTED/.test(text()));
  check("queue counts the three pinned rejections", /PRED-REJECTED 3/.test(text()),
    (text().match(/PRED-REJECTED \d+/) || [])[0]);
  const pages = (text().match(/PAGE\s+\d+\s+OF\s+(\d+)/) || [])[1];
  screen.type("PAGE " + pages);
  screen.press("Enter");
  await step("PAGE command reaches the last queue page", () => /INSUFFICIENT FUNDS/.test(text()), 15000,
    () => "PAGE " + pages);
  check("rejection reasons are spelled out", /SELF TRANSFER/.test(text()) && /DEST NOT FOUND/.test(text()));

  // 5. run the nightly batch for real, from the batch screen
  screen.press("F2");
  await step("PF2 returns to the menu", () => /OPERATIONS MENU/.test(text()), 15000);
  screen.press("3");
  screen.press("Enter");
  await step("option 3 opens batch submission", () => /BATCH SUBMISSION/.test(text()), 15000);
  check("batch screen explains the O(operations x accounts) cost",
    /O\(150 x 400\)|O\(400 x 1,200\)|O\(500 x 5,000\)/.test(text()));
  screen.press("S");                   // preset field is focused first
  screen.press("Enter");
  await sleep(150);
  screen.press("F9");
  await step("job output screen opens", () => /JOB OUTPUT/.test(text()), 15000);
  await step("job reports a running state", () => /STATE RUNNING/.test(text()), 15000,
    (text().match(/STATE \w+/) || [])[0]);
  await step("STEP010 completes with a real wall-clock time", () => /STEP010 SECONDS/.test(text()), 90000);
  await step("job reports the COBOL counters", () => /COMPLETE\s+PROCESSED/.test(text()), 60000,
    (text().match(/PROCESSED \d+ {2}REJECTED \d+ {2}TOTAL_CENTS \d+/) || [])[0]);
  const counters = (text().match(/PROCESSED (\d+)\s+REJECTED (\d+)\s+TOTAL_CENTS (\d+)/) || []);
  check("counters came from the COBOL job, not a simulation", counters.length === 4 && !/\*\*\* SIMULATED \*\*\*/.test(text()));
  check("spool window is labelled SIMULATED", /SPOOL DISPLAY \(SIMULATED/.test(text()));
  if (counters.length) {
    check("rejections match the three pinned edge cases", Number(counters[2]) === 3, counters[2]);
  }

  // 6. journal records the finished run and its parity verdict
  screen.press("F2");
  await step("menu after the job", () => /OPERATIONS MENU/.test(text()), 15000);
  screen.press("4");
  screen.press("Enter");
  await step("journal screen lists the job", () => /BATCH JOURNAL/.test(text()) && /NB\d{12}/.test(text()), 15000,
    (text().match(/NB\d{12}/) || [])[0]);
  check("journal shows a parity verdict", /PASS/.test(text()));

  // 7. system status, help, disclosure, logoff
  screen.press("F2");
  await step("menu again", () => /OPERATIONS MENU/.test(text()), 15000);
  screen.press("5");
  screen.press("Enter");
  await step("option 5 opens system status", () => /SYSTEM STATUS/.test(text()) && /COBC/.test(text()), 15000);
  check("system status names the legacy source", /legacy\/bank\.cob/.test(text()));
  screen.press("F1");
  await step("PF1 opens help", () => /PROGRAM FUNCTION KEYS/.test(text()), 15000);
  check("help documents PF9 submit", /PF9\s+SUBMIT/.test(text()));
  screen.press("F11");
  await step("PF11 opens the disclosure", () => /DISCLOSURE/.test(text()), 15000);
  check("disclosure names the synthetic data", /fictional/.test(text()));
  screen.press("F12");
  await step("PF12 logs off", () => /SIGN ON/.test(text()), 15000);

  const failed = checks.filter((c) => !c.ok);
  console.log(`\n${checks.length - failed.length}/${checks.length} checks passed`);
  if (failed.length) {
    failed.forEach((f) => console.log("  failed: " + f.name));
    process.exit(1);
  }
  process.exit(0);
}

main().catch((error) => {
  console.error("harness error:", error);
  process.exit(2);
});
