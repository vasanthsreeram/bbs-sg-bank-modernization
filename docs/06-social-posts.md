# 06 — Per-Teammate Medium / LinkedIn Post Outlines

**Submission rule:** *an original public Medium or LinkedIn post from **each** team member.**
This file is a **starting outline per person**, not a finished post. Every member must
rewrite it in their own voice, add their own screenshots, and replace the placeholders with
what they actually did. Do not publish identical text across members — that fails the rule.

## Honesty rules for every post

- Claim the **algorithmic** improvement (`O(M·A)` → `O(A+M)`, one write per run). The
  wall-clock figures are **28.6x** (1200×400) and **128.1x** (5000×500) — quote them **only**
  with the disclosure: synthetic fixtures, a deliberately inefficient legacy whole-file
  rewrite, and **not** a general claim about COBOL. Link the transcript you cite
  (`scripts/evidence/`).
- Do not state Opsera Forge produced an artifact unless it exists. Forge's **Assessment is
  complete** (ForgeScore 57/100, Developing; raw report not exported; `docs/forge/assessment.md`
  is a team transcription); **Intent v1**, **PRD-Spec v1**, **Architecture v1** and
  **User Stories v1** (6 epics / 33 **proposed** stories) are **approved** and downloaded,
  and **Testing v1** (132 **proposed** cases) was **generated/exported without an approval
  step** (no Approve action was shown) — all into `docs/forge/` (SHA-256 in
  `docs/forge/README.md`).
  **Never claim Forge generated the modern Python, deployed anything, implemented the 33
  stories, ran the 132 tests, or built its proposals** (safe temp-file replacement,
  append-only audit, FastAPI, Forge Shipping are *not* implemented) — the engine is our own
  local code and the local suites are 108 passing.
- Personalize: name the specific file/PR/decision **you** owned. A post with no genuine
  personal contribution is plagiarism-adjacent and reads as filler.

## Post ownership map

| Member | Role | Owned area (edit to match reality) | Post angle | Post URL |
|---|---|---|---|---|
| `{MEMBER_1_NAME}` | `{MEMBER_1_ROLE}` | Legacy assessment / COBOL analysis | "How I read 172 lines of COBOL and found the bottleneck" | `{MEMBER_1_POST_URL}` |
| `{MEMBER_2_NAME}` | `{MEMBER_2_ROLE}` | Target architecture + `modern/bank.py` | "Rewriting a flat-file batch as an in-memory index without changing a byte" | `{MEMBER_2_POST_URL}` |
| `{MEMBER_3_NAME}` | `{MEMBER_3_ROLE}` | Parity harness + tests + Forge Testing | "Making a migration provably safe: byte-identical parity tests" | `{MEMBER_3_POST_URL}` |
| `{MEMBER_4_NAME}` | `{MEMBER_4_ROLE}` | Forge pipeline lead + delivery + presentation | "Driving a legacy modernization through the Opsera Forge pipeline" | `{MEMBER_4_POST_URL}` |

> Add rows if there are more/fewer members. One row = one required post.

---

## Member 1 — Legacy assessment / COBOL analysis

**Contribution placeholder (fill first):** `{MEMBER_1_CONTRIBUTION — e.g. "I read bank.cob,
documented the data contract, and flagged the L108/L133 double scan."}`

**Angle:** the archaeology of understanding legacy code before touching it.
**Hook:** *"This 172-line COBOL program is a bank's overnight batch. Two lines explain why
it gets slower every year — and neither is about how fast COBOL is."*

**LinkedIn outline (~180 words):**
1. Hook (above), with a screenshot of `bank.cob` L108 and L133.
2. What the program does: reads operations, then — for *each* one — rescans all accounts and
   rewrites the file.
3. Why that's `O(operations × accounts)`, in one plain sentence.
4. The data contract I documented (fixed-column fields at `(1:8)`, `(10:12)`, …) and why it
   matters for compatibility.
5. What surprised me about reading legacy code `{MEMBER_1_SURPRISE}`.
6. One takeaway: *find the cost before you find the replacement.*
7. Links: `https://github.com/vasanthsreeram/bbs-sg-bank-modernization`, demo `https://bbs-sg-bank-demo.pages.dev/media/bbs-sg-bank-demo.mp4`, hosted `https://bbs-sg-bank-demo.pages.dev`.
8. Hashtags: #LegacyModernization #COBOL #SoftwareEngineering #Hackathon.

**Medium outline (~600–900 words):** expand with the exact offsets table, a before/after
diagram of the write pattern, and a paragraph on the difficulty of testing `bank.cob` in
isolation (it re-opens files per op).

---

## Member 2 — Architecture + modern implementation

**Contribution placeholder:** `{MEMBER_2_CONTRIBUTION — e.g. "I designed the dict-indexed
run() and wrote modern/bank.py, then wired the demo service to the unmodified engine."}`

**Angle:** changing the *cost model* while freezing the *behaviour*.
**Hook:** *"How do you make a batch 100x-faster-sounding without lying? You don't quote a
number — you change the algorithm from `O(M×A)` to `O(M+A)` and prove the output is
identical."*

**LinkedIn outline (~200 words):**
1. Hook.
2. The decision: the flat file was incidental state — replace the shuffle with a `dict` index.
3. Show the 45-line modern `run()`; point at the single `write_text` at the end.
4. The constraint we refused to break: the on-disk format and stdout contract stay the same.
5. A code snippet: the validation block (`bank.py` L28-38) mirroring legacy rules.
6. What I'd do differently `{MEMBER_2_LESSON}`.
7. Links + hashtags.
8. Honesty line: *"We publish the algorithm and the parity test, not an unmeasured ratio."*

**Medium outline:** include the ADR (don't port the shuffle / do index / keep semantics) and
a walkthrough of one operation end-to-end.

---

## Member 3 — Testing / parity harness / Forge Testing

**Contribution placeholder:** `{MEMBER_3_CONTRIBUTION — e.g. "I wrote scripts/benchmark.py
that generates identical fixtures and asserts byte-identical output."}`

**Angle:** proof over promises — how to make a rewrite *safe*.
**Hook:** *"A migration is only as good as the test that can catch it being wrong. Here's the
harness that runs the old COBOL and the new Python on the same data and refuses to let them
disagree."*

**LinkedIn outline (~200 words):**
1. Hook.
2. The risk: a faster batch that computes different balances is worse than a slow one.
3. The approach: one fixture generator feeds both programs; assert identical stdout **and**
   byte-identical `accounts.dat` (the `parity_ok` gate in `scripts/benchmark.py`). Show the
   `parity: … byte-identical: YES` line from `scripts/evidence/benchmark-1200x400.txt`.
4. Why "identical bytes" is a stronger claim than "same totals."
5. The edge cases we explicitly inject: insufficient funds, self-transfer, missing
   destination.
6. The gap I found: malformed amounts used to crash the modern batch — I wrote the failing
   case, we added the guard (`bank.py` L23-25), and it's now a passing test. Documenting a
   defect you then fix beats hiding it.
7. One deliberate divergence worth stating: modern **rejects** duplicate account IDs and
   12-digit balance overflow, where the legacy COBOL rewrites duplicate rows and truncates
   the overflow — fail-closed instead of silently corrupting a balance, pinned in tests.
8. The measured payoff, with the caveat: with an isolated GnuCOBOL 3.2.0 we timed both —
   **28.6x** at 1200×400 and **128.1x** at 5000×500. Say plainly that the fixtures are
   **synthetic** and the legacy design is **deliberately** inefficient, so the ratio is a
   property of that algorithm, not of COBOL.
9. `scripts/test_bank.py` now holds **33** tests (parity, contract, characterization, an
   end-to-end benchmark) alongside the **5** engine tests, and the terminal suite runs the
   **real** COBOL (`legacy-ui/`, 20 tests).
10. Takeaway: *write down what's broken; it builds more trust than a green checkmark.*
11. Links + hashtags.

**Medium outline:** walk through `benchmark.py` section by section; include the AT matrix
and the AT-11 fix.

---

## Member 4 — Forge pipeline lead / delivery / presentation

**Contribution placeholder:** `{MEMBER_4_CONTRIBUTION — e.g. "I mapped our process to the
Forge pipeline stages and built the demo site + docs + slides."}`

**Angle:** using Opsera Forge as the *spine* of the modernization, not a side tool.
**Hook:** *"We didn't just modernize a bank's COBOL batch — we drove the **planning** through
a pipeline: Assessment, Intent, PRD-Spec, Architecture, User Stories, Testing, Delivery.
Forge authored the planning artifacts; we wrote the engine."*

**LinkedIn outline (~200 words):**
1. Hook.
2. Why process matters: a rewrite without a spec is a gamble.
3. The Forge stages, the live project we created from the legacy ZIP, the completed
   **Assessment** — ForgeScore **57/100 (Developing)**, 10 findings incl. 3 high — and the
   **Intent v1**, **PRD-Spec v1**, **Architecture v1** and **User Stories v1** (33 proposed
   stories) documents **approved** and downloaded, plus **Testing v1** (132 proposed cases)
   **generated/exported** (not approved), into `docs/forge/` (hashes recorded) — the
   stories/tests are planning proposals, not shipped
   code or runs (link `04-forge-pipeline-mapping.md`).
4. Draw the line clearly: Forge **assessed and framed** the work; we wrote the modern engine
   ourselves. State this explicitly — it's the honest version and it still shows real Forge use.
5. Keying it honest: every stage maps to a file under `docs/forge/`; pending stays pending.
6. Delivery: hosted app, ≤3-min demo, before/after, one post per teammate.
7. A lesson about shipping under a deadline `{MEMBER_4_LESSON}`.
8. Links + hashtags.

**Medium outline:** the full pipeline narrative with the stage table, what Forge changed vs.
how we'd have done it by hand, and the submission checklist.

---

## Cross-post checklist

- [ ] One post per member, each **public** and **original**.
- [ ] Each post names that member's actual contribution (not "the team").
- [ ] Each post links `https://github.com/vasanthsreeram/bbs-sg-bank-modernization` and, where relevant, `https://bbs-sg-bank-demo.pages.dev/media/bbs-sg-bank-demo.mp4` / `https://bbs-sg-bank-demo.pages.dev`.
- [ ] Any quoted speedup carries the synthetic-workload disclosure and links a transcript.
- [ ] Paste final URLs into the ownership map and into `07-submission-checklist.md`.
