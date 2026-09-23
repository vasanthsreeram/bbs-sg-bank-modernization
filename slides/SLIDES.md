# SLIDES.md — Markdown deck source (speaker notes)

Source of truth for [`index.html`](index.html). Slide separator: `---`. Speaker notes in
`> **Notes:**`. Keep the honesty rules: no unmeasured multiplier, no Forge artifact we
didn't export.

**Presenter:** `{PRESENTER_NAME}` · **Deck length:** 12 slides · **Talk:** ≤3 min (see
[`../docs/05-demo-script.md`](../docs/05-demo-script.md)).

**Theme:** light (white slides, navy ink, indigo/emerald accents). **Graphics:** inline SVG,
so they scale without artefacts and print cleanly. **Screenshots:** real captures in
[`assets/`](assets/) from the local demo app and the operator terminal — see
[§ Screenshot provenance](#screenshot-provenance).

---

## Slide 1 — Title

**BBS SG Bank: from flat-file COBOL to an indexed batch**

A truthful, evidence-linked legacy modernization — the planning driven through the
**Opsera Forge** pipeline, the engine written and tested here.

Pipeline chips: 1 Assessment · 2 Intent · 3 PRD-Spec · 4 Architecture · 5 User Stories ·
6 Testing · 7 Delivery — pending.

`{TEAM_NAME}` · `{DATE}` · hosted: `{HOSTED_URL}`

*Right:* screenshot of the local demo app overview (legacy panel beside modern panel).

> **Notes:** One sentence opener, then straight into the problem. Say plainly that the bank
> is fictional and the data synthetic — the screenshot is labelled that way too. Don't oversell.

---

## Slide 2 — The problem

The overnight batch gets slower as the bank grows.

For **every single operation**, the legacy program re-opens `accounts.dat`, scans **every**
account, then rewrites **every** account row.

- Cost = operations × accounts → double the volume and the work roughly quadruples.
- Legacy flow: read ops → (scan all, rewrite all) per op → print counts.

*Right:* SVG chart — legacy work (O(M·A)) curves sharply upward; modern work (O(M+A)) stays
near flat. Shapes are drawn from the code, not from a benchmark.

*Bottom band:* the overnight window is fixed, the transaction volume is not — at the default
fixture the legacy batch performs on the order of **1.4 million row visits** where about
**1,600** would do (`docs/02-before-after.md` §3).

> **Notes:** Emphasise "every operation" twice. The audience should feel the quadratic before
> you name it.

---

## Slide 3 — Before

`legacy/bank.cob`, two lines of the real source:

- L108: *"reopen and scan the flat file for every operation."*
- L133: *"rewrite every account for every accepted operation."*

Stat cards: cost model `O(M·A)` · **3× full-file passes per accepted op** · runtime dep
GnuCOBOL. SVG shows the three traversals (find/validate → rewrite to temp → temp back to
accounts).

*Right:* screenshot of the operator terminal running a **real compiled `bank.cob`** job
(GnuCOBOL 3.2.0). Preset S: 400 accounts × 150 ops → **150 processed / 3 rejected**,
**0.162 s** real COBOL wall clock, parity **PASS**.

> **Notes:** Show the actual file, highlight the two comments. This is the "before" evidence.
> The terminal is not a replay: it compiles and runs the unmodified COBOL. The fixture is
> synthetic and the screen labels its replay rows as simulated — say both.

---

## Slide 4 — After

`modern/bank.py`: load accounts into a dict once → apply ops with O(1) lookups → write once.

- Cost `O(A+M)` · exactly one write per run · python3 stdlib only.
- Same rules, same file format, same stdout contract.

*Right:* SVG shows each file touched exactly once (read accounts, read operations, write
accounts). *Bottom band:* three file touches per run, regardless of how many operations
arrive — versus three full traversals of the ledger per accepted operation before.

> **Notes:** Point at the single write. Stress that behaviour is frozen — that is the whole
> safety story.

---

## Slide 5 — Before / after table

| Dimension | Before — legacy | After — modern |
|---|---|---|
| Paradigm | Flat-file, re-scan per op | In-memory index, one pass |
| Cost | O(operations × accounts) | O(accounts + operations) |
| File writes | Whole file per accepted op (via temp file) | Once per run |
| Source | 172 lines COBOL | 54 lines Python |
| Toolchain | GnuCOBOL | python3 (stdlib) |
| Change safety net | None in repo | Parity harness + 5 unit tests |
| Output contract | byte-identical on identical input | byte-identical on identical input |

Closing callout: **unchanged output is the headline.** Then the stated safety divergences —
the modern engine **fails closed** on duplicate account ids and on an overflow past
`PIC 9(12)`, where the legacy program keeps duplicates and truncates (deliberate, and
characterised by tests).

> **Notes:** "Unchanged output" is the headline — this is a safe migration. Mention the two
> fail-closed divergences yourself before someone finds them.

---

## Slide 6 — Correctness

`scripts/benchmark.py` runs both programs on identical fixtures and asserts identical counts
**and** byte-identical `accounts.dat`.

Acceptance status: AT-1…AT-13 pass · core suites green (**33** in `scripts/test_bank.py` +
**5** in `tests/test_modern.py`) · **108** local tests passing (site **50**, operator
terminal **20**) · legacy/modern parity is **byte-identical**.

*Right:* screenshot of the demo-app batch console after a live run: 63 rows submitted →
**60 posted / 3 rejected**, engine time **0.37 ms**, with value-conservation,
`accounts.dat` and re-simulation checks all green.

*Bottom band:* **AT-12 is the parity gate** (identical counts, byte-identical
`accounts.dat`); **AT-13 is the scaling gate** — the speedup must grow with the account
count, and it does: 4.3× → 8.0× → 13.1× → 24.6× across the sweep.

> **Notes:** Correctness is a test. AT-11 (malformed input) is fixed and tested; parity is
> executed, not just designed. The console re-derives the expected counts independently —
> that is why "re-simulation agrees" is on screen.

---

## Slide 7 — Performance: measured, with the caveat

- **Measured** (isolated GnuCOBOL 3.2.0, byte-identical parity): **28.6×** at 1200×400
  (1.004 s → 0.035 s) and **128.1×** at 5000×500 (4.728 s → 0.037 s).
- **Sweep** (200 ops fixed): 300 → 4.3×, 600 → 8.0×, 1200 → 13.1×, 2400 → 24.6× — the ratio
  grows with the account count, the signature of the O(m×n) → O(m+n) change.
- **Live COBOL** in `legacy-ui/`: a preset-M job (1200×400) ran **400 processed / 3
  rejected** in **1.197 s actual COBOL execution** (1.234 s overall); modern total
  **5489403400** matched.
- **Complexity:** O(M·A) → O(M+A); writes go from many-per-run to exactly one.
- **Disclosure:** synthetic workload, and the legacy design is **deliberately inefficient**
  (whole-file rewrite per operation) — a property of *that* algorithm, not a general COBOL
  claim. Transcripts in `scripts/evidence/`. Where `cobc` is absent the app reports
  `speedup: null` — never an estimate.

*Right:* screenshot of the benchmark tab measuring this host live: legacy **0.984 s** vs
modern **0.035 s**, parity checked first.

> **Notes:** Pre-empts "prove the speedup." State the disclosure in the same breath as the
> number. The live screenshot is a single run on this host and says so next to it; the
> headline figures are the recorded medians in `scripts/evidence/`.

---

## Slide 8 — Built with Opsera Forge

Pipeline rail: Assessment → Intent → PRD-Spec → Architecture → User Stories → Testing → Delivery.
Forge authored the **planning artifacts**; the modern engine was written separately.

Forge **Assessment complete**: ForgeScore **57/100 (Developing)**, **10 findings incl. 3
high** (`O(m×n)` scans, full-file rewrites, missing specs); the raw report is not exported
(`docs/forge/assessment.md` is a team transcription of the observed values). **Intent v1**,
**PRD-Spec v1** (~95%), **Architecture v1** (~100%) and **User Stories v1** (6 epics / **33
proposed stories**, ~75%) are **approved and downloaded**; **Testing v1** (**132 proposed test
cases**) was **generated and downloaded without an approval step** (no Approve action shown) —
all into `docs/forge/` with recorded SHA-256 hashes. The stories and test cases are
**proposals — not implemented features and not executed tests**; the local suites are 108
passing. **Delivery is pending.** The supplied MCP token returns 401, so exports came via
signed-in browser downloads. Forge did **not** generate or run the modern Python, and nothing
was deployed — that engine is our local code. Forge's document proposals (safe temp-file
replacement, append-only audit retention, FastAPI, Forge Shipping) are **not implemented**.

> **Notes:** Point at `docs/04-forge-pipeline-mapping.md`. The working-tree COBOL hash
> differs from the uploaded copy (later header edits), so don't claim the assessment covers
> the current bytes. Don't call Testing v1 "approved" — it was generated/exported only. Don't
> let the 33 stories or 132 test cases read as delivered work, and don't let the
> Architecture/PRD proposals read as delivered features — they are planning only.

---

## Slide 9 — Modernization impact

Eight cards: scales · cheaper I/O · safer change · portable · compatible · documented ·
observable · frozen semantics. Below them, a single value chain: **before** (nightly window,
no queryable audit, whole-file rewrite per op) → **after** (always-on ledger, per-row audit,
one write per run, parity harness) → **not claimed** (public hosting, demo recording, Forge
Delivery, published posts, raw Assessment export).

*Bottom band:* the net effect — the batch stops being the constraint, the overnight window no
longer grows with the customer base, and future changes are guarded by the parity harness.

> **Notes:** Tie back to the bank: the overnight window fits growth; no downstream breakage.
> The third box is deliberate — keep the unclaimed column visible on screen.

---

## Slide 10 — Honest status

**Done (evidence in the repo):** modern batch, AT-1…AT-13, core suites 33 + 5 green
(site 50, terminal 20), byte-identical parity, measured 28.6×/128.1× and a live real-COBOL
job, working local demo app, Forge Assessment complete (57/100), Forge Intent, PRD-Spec,
Architecture and User Stories v1 approved and exported, and Testing v1 generated/exported
(not approved), to `docs/forge/` (33 stories / 132 test cases are proposals, not executed).

**Open:** raw Assessment export, Forge Delivery, public hosting, demo recording,
per-member posts, deck not yet rehearsed.

*Bottom band:* the **current defensible claim**, verbatim from
`docs/07-submission-checklist.md` §D — nothing stronger is claimed on this slide.

> **Notes:** Showing the open list is intentional — it matches the submission checklist.

---

## Slide 11 — Team & links

| Member | Contribution | Post |
|---|---|---|
| `{MEMBER_1_NAME}` | Legacy assessment / COBOL analysis | `{MEMBER_1_POST_URL}` |
| `{MEMBER_2_NAME}` | Architecture + modern implementation | `{MEMBER_2_POST_URL}` |
| `{MEMBER_3_NAME}` | Parity harness + tests | `{MEMBER_3_POST_URL}` |
| `{MEMBER_4_NAME}` | Forge pipeline lead + delivery | `{MEMBER_4_POST_URL}` |

Repo `{REPO_URL}` · Demo `{DEMO_VIDEO_URL}` · Hosted `{HOSTED_URL}`

*Bottom band:* the four commands that reproduce the evidence —
`python3 scripts/test_bank.py` (33 tests) · `python3 tests/test_modern.py` (5 tests) ·
`python3 scripts/benchmark.py --accounts 1200 --operations 400` (parity + timings, needs
`cobc`) · `python3 site/backend/app.py` (the demo app on `127.0.0.1`).

> **Notes:** Name each person's real contribution; the per-member posts are a submission
> requirement and are not published yet.

---

## Slide 12 — Close

**Same result. Linear cost. Proof in the repo.**

Closing chips: parity byte-identical · 28.6×/128.1× measured and disclosed · 108 local tests
passing · synthetic data, fictional bank.

Questions welcome — answered with code, tests, and commands.

> **Notes:** End on the parity harness as the differentiator, not on a speed number.

---

## Screenshot provenance

The deck embeds real captures, not mock-ups. All were taken by driving a headless Chrome
for Testing (153.0.8010.12) over the **local** servers with CDP, at 2× device scale, then
cropped to the region shown and saved as WebP.

| Asset | Page | Server | What the capture shows |
|---|---|---|---|
| `assets/app-overview.webp` | Overview tab | `site/backend/app.py` on `127.0.0.1:8788` | Legacy COBOL panel beside the modern engine panel, synthetic demo data |
| `assets/app-batch.webp` | Batch console | `site/backend/app.py` on `127.0.0.1:8788` | Live run of the unmodified engine: 63 rows → 60 posted / 3 rejected, 0.37 ms, conservation + re-simulation checks green |
| `assets/app-benchmark.webp` | Benchmark tab | `site/backend/app.py` on `127.0.0.1:8788` | Live measurement on this host: legacy 0.984 s vs modern 0.035 s, parity checked first |
| `assets/terminal-job.webp` | Operator terminal, job output | `legacy-ui/server.py` on `127.0.0.1:8792` | Real compiled `legacy/bank.cob` (GnuCOBOL 3.2.0), preset S: 150 processed / 3 rejected, STEP010 0.162 s, parity PASS |

Every capture is from the **fictional** BBS SG Bank demo on **synthetic** fixtures. The
terminal labels its replay rows `SIMULATED` and the app labels itself `synthetic demo`; those
labels are visible in the images, so the deck does not imply real customers or data.

---

## Placeholder replacement

| Token | Meaning |
|---|---|
| `{TEAM_NAME}`, `{PRESENTER_NAME}` | Names |
| `{MEMBER_n_NAME}`, `{MEMBER_n_POST_URL}` | Team + posts |
| `{REPO_URL}`, `{DEMO_VIDEO_URL}`, `{HOSTED_URL}` | Links |
| `{EVENT_NAME}`, `{DATE}` | Event + date |

## Viewing & controls

| Action | Control |
|---|---|
| Next / previous | `→` `←` `space` `PgUp` `PgDn`, or click the right/left half of the slide |
| First / last | `Home` / `End` |
| Full screen | `F`, or the **Full screen** button |
| Deep link | `index.html#7` opens slide 7 |
| Print / PDF | Each slide is a page (`@media print`), light theme on white |
| Projector / laptop | The 1280×720 stage scales to fit the window; nothing reflows or clips |
| Phone / narrow screen | The stage scales to fit width, so the whole slide stays visible but small — this deck is designed for a large screen |
