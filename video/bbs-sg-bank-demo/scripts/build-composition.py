#!/usr/bin/env python3
"""Generate index.html for the BBS SG Bank demo video.

Scene lengths come from the measured narration in assets/audio/timings.json,
so the composition is rebuilt (not hand-edited) whenever narration changes.

Usage: python3 scripts/build-composition.py
"""

from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEAD = 0.20      # silence before narration inside a scene
TAIL = 0.35      # breathing room after narration before the next scene
FADE = 0.40      # scene in/out fade length


def load_lines() -> list[dict]:
    data = json.loads((ROOT / "assets" / "audio" / "timings.json").read_text())
    order = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]
    lines = []
    for key in order:
        entry = dict(data["lines"][key])
        entry["id"] = key
        lines.append(entry)
    return lines


def split_caption(text: str) -> list[str]:
    words = text.split()
    if len(words) < 12:
        return [text]
    best, best_delta = None, None
    for i in range(4, len(words) - 3):
        first, second = " ".join(words[:i]), " ".join(words[i:])
        delta = abs(len(first) - len(second))
        if best_delta is None or delta < best_delta:
            best, best_delta = (first, second), delta
    return list(best)


CSS = """
:root {
  --canvas-a: #fbfcfe;
  --canvas-b: #eef2f9;
  --ink: #0f1728;
  --muted: #3c4864;
  --line: #e2e8f2;
  --blue: #2563eb;
  --blue-soft: #e8effc;
  --teal: #0d9488;
  --teal-soft: #e3f5f1;
  --amber: #b45309;
  --amber-soft: #fdf0e2;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #ffffff;
  color: var(--ink);
  font-family: system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
#root { position: relative; width: 100%; height: 100%; overflow: hidden; }

.ground {
  position: absolute; inset: 0;
  background: linear-gradient(168deg, var(--canvas-a) 0%, #f5f7fc 52%, var(--canvas-b) 100%);
}

.scene {
  display: flex; flex-direction: column;
  padding: 66px 92px 152px;
  gap: 26px;
}

.eyebrow {
  font-size: 21px; font-weight: 700; letter-spacing: .17em; text-transform: uppercase;
  color: #55627e; margin: 0;
}
h1 { font-size: 118px; font-weight: 800; letter-spacing: -.03em; line-height: 1; margin: 0; }
h2 { font-size: 54px; font-weight: 700; letter-spacing: -.02em; line-height: 1.12; margin: 0; max-width: 1180px; }
.lede { font-size: 29px; line-height: 1.45; color: var(--muted); margin: 0; max-width: 980px; }
.small { font-size: 22px; line-height: 1.4; color: #55617c; margin: 0; }

.split { display: grid; grid-template-columns: 1fr 1fr; gap: 54px; align-items: center; flex: 1; min-height: 0; }
.split--wide-left { grid-template-columns: 1.15fr 1fr; }
.stack { display: flex; flex-direction: column; gap: 22px; min-width: 0; }

.card {
  background: #ffffff; border: 1px solid var(--line); border-radius: 22px;
  box-shadow: 0 22px 48px -26px rgba(15, 23, 40, .38);
}
.card--pad { padding: 30px 34px; }

.shot { position: relative; overflow: hidden; border-radius: 20px; background: #0b1220; border: 1px solid #cdd7e8; }
.shot img { display: block; width: 100%; height: 100%; object-fit: cover; object-position: top left; }
.shot--tall { height: 620px; }
.shot--mid { height: 520px; }
.shot--small { height: 330px; }
.shot__tag {
  position: absolute; left: 18px; bottom: 16px; z-index: 2;
  font-family: ui-monospace, monospace; font-size: 19px; letter-spacing: .04em;
  color: #d8e3f6; background: rgba(8, 14, 26, .82); border: 1px solid #22304a;
  padding: 8px 14px; border-radius: 10px;
}

.chips { display: flex; flex-wrap: wrap; gap: 14px; }
.chip {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 12px 20px; border-radius: 999px; font-size: 23px; font-weight: 600;
  background: var(--blue-soft); color: #1c3fa8;
}
.chip--after { background: var(--teal-soft); color: #0a6a58; }
.chip--warn { background: var(--amber-soft); color: var(--amber); }
.chip--plain { background: #fff; border: 1px solid var(--line); color: var(--muted); }
.chip__dot { width: 12px; height: 12px; border-radius: 50%; background: currentColor; opacity: .85; }

.mono { font-family: ui-monospace, monospace; }
.big { font-size: 92px; font-weight: 800; letter-spacing: -.03em; line-height: 1; }
.tiny-label { font-size: 20px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: #5d6a86; }

/* --- legacy scan graphic --- */
.rows { display: flex; flex-direction: column; gap: 9px; position: relative; padding: 18px; }
.row {
  height: 26px; border-radius: 6px; background: #dde5f2;
  border: 1px solid #cfd9ea;
}
.row--hit { background: #cfd9f5; border-color: #b9c8ee; }
.rows__scan {
  position: absolute; left: 12px; right: 12px; height: 5px; top: 18px;
  background: linear-gradient(90deg, rgba(37,99,235,0), #2563eb, rgba(37,99,235,0));
  border-radius: 4px;
}
.rows__head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }

/* --- index graphic --- */
.index { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; }
.index__cell {
  height: 42px; border-radius: 8px; background: #e6ecf7; border: 1px solid #d6e0f1;
}
.index__cell--key { background: var(--teal-soft); border-color: #bfe6dd; }

/* --- bars --- */
.bars { display: flex; align-items: flex-end; gap: 46px; height: 356px; }
.bar { width: 128px; border-radius: 12px 12px 4px 4px; background: #c9d3e6; }
.bar--after { background: var(--teal); }
.bar--legacy { background: #8fa5c9; }
.bar-val { font-size: 30px; font-weight: 700; margin-bottom: 10px; }

.sizes { display: flex; flex-direction: column; gap: 14px; }
.size-line { display: grid; grid-template-columns: 210px 1fr 92px; align-items: center; gap: 16px; }
.size-track { height: 22px; border-radius: 6px; background: #e6ecf7; overflow: hidden; }
.size-fill { height: 100%; border-radius: 6px; }
.size-fill--before { background: #9db1d2; }
.size-fill--after { background: var(--teal); }

/* --- parity --- */
.out {
  background: #0f1728; color: #dbe6fb; border-radius: 16px; padding: 22px 24px;
  font-family: ui-monospace, monospace; font-size: 22px; line-height: 1.65;
}
.out__title { font-size: 19px; letter-spacing: .12em; text-transform: uppercase; color: #8ea6cf; margin-bottom: 10px; }
.rules { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 26px; }
.rule { display: flex; gap: 12px; align-items: center; font-size: 24px; color: #33405c; }
.rule__tick {
  width: 28px; height: 28px; border-radius: 50%; background: var(--teal-soft); color: #0a6a58;
  display: grid; place-items: center; font-size: 17px; font-weight: 700;
}
.stamp {
  display: inline-flex; align-items: center; gap: 14px; padding: 16px 26px; border-radius: 16px;
  border: 2px solid var(--teal); color: #0a6a58; background: var(--teal-soft);
  font-size: 27px; font-weight: 700;
}

/* --- forge rail --- */
.rail { position: relative; display: flex; justify-content: space-between; gap: 16px; margin-top: 8px; }
.rail__line { position: absolute; left: 0; right: 0; top: 42px; height: 4px; background: #dce4f2; border-radius: 3px; }
.rail__line > span { display: block; height: 100%; width: 100%; background: var(--blue); border-radius: 3px; transform-origin: left center; }
.stage { position: relative; z-index: 1; width: 240px; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.stage__dot {
  width: 30px; height: 30px; border-radius: 50%; background: var(--blue);
  border: 5px solid #f7f9fd; box-shadow: 0 0 0 2px #cddbf5;
}
.stage__name { font-size: 24px; font-weight: 700; text-align: center; }
.stage__note { font-size: 20px; color: #55617c; text-align: center; }

/* --- captions --- */
.captions {
  position: absolute; inset: 0; width: 100%; height: 100%;
  display: flex; align-items: flex-end; justify-content: center; padding: 0 120px 54px;
}
.cap {
  background: rgba(255, 255, 255, .94); border: 1px solid var(--line);
  box-shadow: 0 16px 36px -20px rgba(15, 23, 40, .5);
  color: #101a2e; font-size: 33px; line-height: 1.35; font-weight: 500;
  padding: 18px 36px; border-radius: 18px; max-width: 1440px; text-align: center;
}
.cap__wrap { position: relative; display: flex; justify-content: center; width: 100%; }
"""


def build() -> str:
    lines = load_lines()
    durations, starts, audio_starts = [], [], []
    cursor = 0.0
    for line in lines:
        audio = float(line["duration_s"])
        scene_dur = LEAD + audio + TAIL
        starts.append(round(cursor, 3))
        audio_starts.append(round(cursor + LEAD, 3))
        durations.append(round(scene_dur, 3))
        cursor += scene_dur
    total = round(cursor, 3)

    scenes_html, audio_html, caption_html = [], [], []
    for i, (line, start, audio_start, scene_dur) in enumerate(zip(lines, starts, audio_starts, durations)):
        sid = line["id"]
        audio_dur = float(line["duration_s"])
        scene_end = round(start + scene_dur, 3)
        # One clip per caption chunk, so exactly one caption is ever on screen and
        # the layout audit never samples two overlapping text blocks.
        chunks = split_caption(line["text"])
        if len(chunks) == 1:
            windows = [(chunks[0], audio_start, audio_dur)]
        else:
            share = len(chunks[0]) / (len(chunks[0]) + len(chunks[1]))
            mid = round(audio_start + audio_dur * share, 3)
            windows = [
                (chunks[0], audio_start, round(mid - audio_start, 3)),
                (chunks[1], mid, round(audio_start + audio_dur - mid, 3)),
            ]
        CAP_TIMES[sid] = [w[1] for w in windows]
        for n, (chunk_text, chunk_start, chunk_dur) in enumerate(windows, start=1):
            caption_html.append(
                f'<div class="captions clip" id="cap-{sid}-{n}" data-start="{chunk_start}" '
                f'data-duration="{chunk_dur}"><div class="cap__wrap">'
                f'<div class="cap">{chunk_text}</div></div></div>'
            )
        audio_html.append(
            f'<audio id="vo-{sid}" src="assets/audio/{sid}.mp3" preload="auto" '
            f'data-start="{audio_start}" data-duration="{audio_dur}" data-volume="1"></audio>'
        )
        scenes_html.append(SCENES[i].format(start=start, dur=scene_dur, end=scene_end, sid=sid))
    return TEMPLATE.format(
        css=CSS,
        duration=total,
        scenes="\n".join(scenes_html),
        audio="\n".join(audio_html),
        captions="\n".join(caption_html),
        script=animation_script(starts, audio_starts, durations),
    )


CAP_TIMES: dict[str, list[float]] = {}

SCENES = [
    # 1 — hook
    """  <section class="clip scene" id="s1" data-start="{start}" data-duration="{dur}">
    <div class="split split--wide-left" data-anim="scene-in" style="align-items:center">
      <div class="stack">
        <p class="eyebrow" data-anim="fade-up">SF Enterprise Hackathon 2.0 · synthetic demo</p>
        <h1 data-anim="fade-up">BBS SG Bank</h1>
        <p class="lede" data-anim="fade-up" style="font-size:34px">A nightly COBOL batch becomes an always-on ledger — same files, same rules, measured both ways.</p>
        <div class="chips" data-anim="fade-up">
          <span class="chip chip--plain"><span class="chip__dot"></span>before: legacy/bank.cob · 172 lines</span>
          <span class="chip chip--after"><span class="chip__dot"></span>after: modern/bank.py · 54 lines</span>
        </div>
      </div>
      <div class="shot shot--mid" data-anim="card-in">
        <img src="assets/screens/overview.png" alt="BBS SG Bank demo site">
        <span class="shot__tag">127.0.0.1:8788 · live demo</span>
      </div>
    </div>
  </section>""",
    # 2 — legacy
    """  <section class="clip scene" id="s2" data-start="{start}" data-duration="{dur}">
    <p class="eyebrow" data-anim="fade-up">01 · the nightly batch, before</p>
    <h2 data-anim="fade-up">Every operation re-reads the whole account file</h2>
    <div class="split">
      <div class="card card--pad">
        <div class="rows__head">
          <span class="tiny-label">accounts.dat</span>
          <span class="tiny-label mono">one file, re-read every row</span>
        </div>
        <div class="rows" id="s2-rows">
          <span class="rows__scan" id="s2-scan"></span>
          <span class="row"></span><span class="row"></span><span class="row"></span>
          <span class="row"></span><span class="row"></span><span class="row"></span>
          <span class="row"></span><span class="row"></span><span class="row"></span>
        </div>
        <p class="small" style="margin-top:14px">Legacy COBOL opens the master file per operation, finds two accounts, then rewrites the whole file — three full traversals per accepted row.</p>
      </div>
      <div class="stack">
        <div class="card card--pad">
          <p class="tiny-label">row visits, 1,200 accounts × 400 operations</p>
          <p class="big" id="s2-count" style="margin-top:8px">0</p>
        </div>
        <div class="chips">
          <span class="chip chip--plain">O(operations × accounts)</span>
          <span class="chip chip--warn"><span class="chip__dot"></span>full file rewrite per accepted row</span>
        </div>
        <p class="small">GnuCOBOL 3.2.0, compiled with <span class="mono">cobc</span>, running as a real subprocess.</p>
      </div>
    </div>
  </section>""",
    # 3 — modern
    """  <section class="clip scene" id="s3" data-start="{start}" data-duration="{dur}">
    <p class="eyebrow" data-anim="fade-up">02 · the replacement, after</p>
    <h2 data-anim="fade-up">Same rules, held in an in-memory index</h2>
    <div class="split">
      <div class="stack">
        <div class="card card--pad">
          <div class="rows__head"><span class="tiny-label">accounts dict · integer cents</span><span class="tiny-label mono">O(1) lookup</span></div>
          <div class="index" id="s3-index">
            <span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell index__cell--key"></span><span class="index__cell"></span><span class="index__cell"></span>
            <span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span>
            <span class="index__cell"></span><span class="index__cell index__cell--key"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span>
            <span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell"></span><span class="index__cell index__cell--key"></span><span class="index__cell"></span>
          </div>
        </div>
        <div class="card card--pad sizes">
          <div class="size-line">
            <span class="mono" style="font-size:21px">legacy/bank.cob</span>
            <span class="size-track"><span class="size-fill size-fill--before" id="s3-bar-a" style="width:100%"></span></span>
            <span style="font-size:23px;font-weight:700;text-align:right">172 lines</span>
          </div>
          <div class="size-line">
            <span class="mono" style="font-size:21px">modern/bank.py</span>
            <span class="size-track"><span class="size-fill size-fill--after" id="s3-bar-b" style="width:31.4%"></span></span>
            <span style="font-size:23px;font-weight:700;text-align:right">54 lines</span>
          </div>
          <p class="small">Python standard library only. One read of accounts, one read of operations, one write — no temp file.</p>
        </div>
      </div>
      <div class="shot shot--tall" data-anim="card-in">
        <img src="assets/screens/batch-live.png" alt="Batch console running the modern engine">
        <span class="shot__tag">batch console · 63 rows · 60 posted · 3 rejected</span>
      </div>
    </div>
  </section>""",
    # 4 — parity
    """  <section class="clip scene" id="s4" data-start="{start}" data-duration="{dur}">
    <p class="eyebrow" data-anim="fade-up">03 · parity before speed</p>
    <h2 data-anim="fade-up">Byte-identical output, checked on every run</h2>
    <div class="split">
      <div class="stack">
        <div class="out" data-anim="fade-up">
          <div class="out__title">legacy/bank.cob · stdout</div>
          PROCESSED=00000400<br>REJECTED=00000003<br>TOTAL_CENTS=0000005489403400
        </div>
        <span class="stamp" data-anim="pop">accounts.dat byte-identical ✓</span>
      </div>
      <div class="stack">
        <div class="out" data-anim="fade-up">
          <div class="out__title">modern/bank.py · stdout</div>
          PROCESSED=00000400<br>REJECTED=00000003<br>TOTAL_CENTS=0000005489403400
        </div>
        <div class="rules" data-anim="stagger">
          <span class="rule"><span class="rule__tick">✓</span>amount shape</span>
          <span class="rule"><span class="rule__tick">✓</span>kind in D/W/T</span>
          <span class="rule"><span class="rule__tick">✓</span>no self-transfer</span>
          <span class="rule"><span class="rule__tick">✓</span>source exists</span>
          <span class="rule"><span class="rule__tick">✓</span>destination exists</span>
          <span class="rule"><span class="rule__tick">✓</span>funds check</span>
        </div>
      </div>
    </div>
  </section>""",
    # 5 — measured
    """  <section class="clip scene" id="s5" data-start="{start}" data-duration="{dur}">
    <p class="eyebrow" data-anim="fade-up">04 · measured on this machine</p>
    <h2 data-anim="fade-up">5,000 accounts, 500 operations</h2>
    <div class="split split--wide-left">
      <div class="stack">
        <div class="card card--pad" style="display:flex;align-items:flex-end;gap:56px">
          <div class="bars">
            <div style="text-align:center">
              <div class="bar-val">4.72 s</div>
              <div class="bar bar--legacy" id="s5-bar-legacy" style="height:356px"></div>
            </div>
            <div style="text-align:center">
              <div class="bar-val">0.041 s</div>
              <div class="bar bar--after" id="s5-bar-modern" style="height:4px"></div>
            </div>
          </div>
          <div style="padding-bottom:16px">
            <p class="tiny-label">speedup</p>
            <p class="big" id="s5-speedup" style="color:#0d9488">1×</p>
            <p class="small" style="margin-top:10px">median of three timed runs<br>after one warm-up</p>
          </div>
        </div>
        <p class="small">Bars drawn to scale from <span class="mono">scripts/evidence/benchmark-final-5000x500.txt</span>; the screenshot is a fresh rerun of the same fixture. Synthetic workload against a deliberately inefficient legacy design — a property of that access pattern, not a claim about COBOL in general.</p>
      </div>
      <div class="shot shot--mid" data-anim="card-in">
        <img src="assets/screens/benchmark-live.png" alt="Benchmark view in the demo app">
        <span class="shot__tag">fresh app rerun: 4.32 s → 0.036 s · 120× · byte-identical</span>
      </div>
    </div>
  </section>""",
    # 6 — terminal
    """  <section class="clip scene" id="s6" data-start="{start}" data-duration="{dur}">
    <p class="eyebrow" data-anim="fade-up">05 · the legacy path, running live</p>
    <h2 data-anim="fade-up">Real COBOL, compiled and executed for each job</h2>
    <div class="split split--wide-left">
      <div class="shot shot--tall" data-anim="card-in">
        <img src="assets/screens/terminal-result.png" alt="Operator terminal output of a real COBOL job">
        <span class="shot__tag">operator terminal · 127.0.0.1:8792</span>
      </div>
      <div class="stack" data-anim="stagger">
        <span class="chip"><span class="chip__dot"></span>0.915 s of COBOL wall clock, measured</span>
        <span class="chip"><span class="chip__dot"></span>400 processed · 3 rejected</span>
        <span class="chip chip--after"><span class="chip__dot"></span>STEP020 VERIFY PASS — matches modern/bank.py</span>
        <span class="chip chip--plain">not a replay: the server runs cobc, then the job</span>
        <p class="small">1,200 accounts × 400 operations, preset M, seed 20260923.</p>
      </div>
    </div>
  </section>""",
    # 7 — forge
    """  <section class="clip scene" id="s7" data-start="{start}" data-duration="{dur}">
    <p class="eyebrow" data-anim="fade-up">06 · how the migration was run</p>
    <h2 data-anim="fade-up">Opsera Forge carried the pipeline</h2>
    <div class="card card--pad" style="margin-top:6px">
      <div class="rail">
        <span class="rail__line"><span id="s7-line"></span></span>
        <span class="stage"><span class="stage__dot"></span><span class="stage__name">Assessment</span><span class="stage__note">57/100 · 10 findings, 3 high</span></span>
        <span class="stage"><span class="stage__dot"></span><span class="stage__name">Intent</span><span class="stage__note">problem + scope</span></span>
        <span class="stage"><span class="stage__dot"></span><span class="stage__name">PRD &amp; Spec</span><span class="stage__note">exported</span></span>
        <span class="stage"><span class="stage__dot"></span><span class="stage__name">Architecture</span><span class="stage__note">before / after</span></span>
        <span class="stage"><span class="stage__dot"></span><span class="stage__name">User stories</span><span class="stage__note">6 epics · 33 stories</span></span>
        <span class="stage"><span class="stage__dot"></span><span class="stage__name">Testing</span><span class="stage__note">132 test cases</span></span>
      </div>
    </div>
    <p class="small">Forge artifacts are planning and review documents; the running COBOL and Python engines in this demo are hand-written and tested in the repository.</p>
  </section>""",
    # 8 — close
    """  <section class="clip scene" id="s8" data-start="{start}" data-duration="{dur}" style="justify-content:center">
    <p class="eyebrow" data-anim="fade-up">BBS SG Bank · modernization walkthrough</p>
    <h1 data-anim="fade-up" style="font-size:96px">Legacy to modern, measured</h1>
    <div class="chips" data-anim="fade-up" style="margin-top:6px">
      <span class="chip chip--plain">28.6× · 1,200 × 400</span>
      <span class="chip chip--plain">115× · 5,000 × 500</span>
      <span class="chip chip--after"><span class="chip__dot"></span>parity: byte-identical</span>
      <span class="chip chip--plain">108 tests passing</span>
    </div>
    <p class="small" data-anim="fade-up" style="margin-top:18px;max-width:1200px">
      Synthetic demonstration: invented accounts and balances, no real customers, no real transactions, and no affiliation with any bank.
    </p>
  </section>""",
]


def animation_script(starts: list[float], audio_starts: list[float], durations: list[float]) -> str:
    ids = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]
    parts = []
    for i, sid in enumerate(ids):
        s0, a0, dur = starts[i], audio_starts[i], durations[i]
        end = round(s0 + dur, 3)
        parts.append(f"""
// ---- scene {sid} ----
tl.fromTo("#{sid} [data-anim='fade-up']", {{ y: 34, opacity: 0 }},
  {{ y: 0, opacity: 1, duration: 0.62, ease: "power3.out", stagger: 0.11 }}, {round(s0 + 0.06, 3)});
tl.fromTo("#{sid} [data-anim='card-in']", {{ scale: 0.94, opacity: 0 }},
  {{ scale: 1, opacity: 1, duration: 0.85, ease: "power2.out" }}, {round(s0 + 0.28, 3)});
tl.fromTo("#{sid} [data-anim='stagger'] > *", {{ x: 40, opacity: 0 }},
  {{ x: 0, opacity: 1, duration: 0.5, ease: "power2.out", stagger: 0.14 }}, {round(a0 + 0.4, 3)});
tl.fromTo("#{sid} [data-anim='pop']", {{ scale: 0.8, opacity: 0 }},
  {{ scale: 1, opacity: 1, duration: 0.5, ease: "back.out(1.6)" }}, {round(a0 + 1.2, 3)});
tl.to("#{sid}", {{ opacity: 0, duration: 0.34, ease: "power2.in" }}, {round(end - 0.36, 3)});""")

    # scene 2: scan sweep + row-visit counter
    s2 = starts[1]
    s2a = audio_starts[1]
    cycle = 1.35
    repeats = max(0, int((durations[1] - 1.2) / cycle) - 1)
    parts.append(f"""
// ---- s2 detail: repeated full-file scans ----
tl.fromTo("#s2-scan", {{ y: 0 }}, {{ y: 250, duration: {cycle}, ease: "none", repeat: {repeats}, yoyo: true }}, {round(s2a + 0.2, 3)});
tl.fromTo("#s2 .row", {{ backgroundColor: "#dde5f2" }}, {{ backgroundColor: "#cfd9f5", duration: 0.3, repeat: {repeats}, yoyo: true, stagger: 0.05 }}, {round(s2a + 0.2, 3)});
""")
    counter = {"el": "#s2-count", "from": 0, "to": 1400000, "start": round(s2a + 0.3, 3), "dur": 3.4}
    parts.append(counter_js(counter, prefix="tl"))

    # scene 3: index pop, size bars
    s3a = audio_starts[2]
    parts.append(f"""
// ---- s3 detail: index lookup + code size ----
tl.fromTo("#s3-index .index__cell", {{ scale: 0.4, opacity: 0 }},
  {{ scale: 1, opacity: 1, duration: 0.34, ease: "back.out(1.8)", stagger: 0.035 }}, {round(s3a + 0.2, 3)});
tl.to("#s3-index .index__cell--key", {{ backgroundColor: "#0d9488", duration: 0.3, stagger: 0.28, repeat: 2, yoyo: true }}, {round(s3a + 1.5, 3)});
tl.fromTo("#s3-bar-a", {{ scaleX: 0 }}, {{ scaleX: 1, transformOrigin: "left center", duration: 0.7, ease: "power2.out" }}, {round(s3a + 4.2, 3)});
tl.fromTo("#s3-bar-b", {{ scaleX: 0 }}, {{ scaleX: 1, transformOrigin: "left center", duration: 0.7, ease: "power2.out" }}, {round(s3a + 5.0, 3)});
""")

    # scene 5: bars + speedup counter
    s5a = audio_starts[4]
    parts.append(f"""
// ---- s5 detail: measured bars + speedup ----
tl.fromTo("#s5-bar-legacy", {{ scaleY: 0 }}, {{ scaleY: 1, transformOrigin: "bottom center", duration: 1.1, ease: "power2.out" }}, {round(s5a + 0.5, 3)});
tl.fromTo("#s5-bar-modern", {{ scaleY: 0 }}, {{ scaleY: 1, transformOrigin: "bottom center", duration: 0.5, ease: "power2.out" }}, {round(s5a + 3.0, 3)});
""")
    parts.append(counter_js({"el": "#s5-speedup", "from": 1, "to": 115, "start": round(s5a + 4.2, 3),
                             "dur": 1.9, "suffix": "×"}, prefix="tl"))

    # scene 7: pipeline rail
    s7a = audio_starts[6]
    parts.append(f"""
// ---- s7 detail: forge pipeline ----
tl.fromTo("#s7-line", {{ scaleX: 0 }}, {{ scaleX: 1, transformOrigin: "left center", duration: 3.2, ease: "none" }}, {round(s7a + 0.3, 3)});
tl.fromTo("#s7 .stage", {{ y: 22, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power2.out", stagger: 0.52 }}, {round(s7a + 0.35, 3)});
tl.fromTo("#s7 .stage__dot", {{ scale: 0.5 }}, {{ scale: 1, duration: 0.4, ease: "back.out(2)", stagger: 0.52 }}, {round(s7a + 0.35, 3)});
""")

    # captions: each chunk is its own clip, so only one is visible at a time
    for i, sid in enumerate(ids):
        for n, chunk_start in enumerate(CAP_TIMES.get(sid, []), start=1):
            parts.append(
                f'tl.fromTo("#cap-{sid}-{n} .cap", {{ opacity: 0, y: 14 }}, '
                f'{{ opacity: 1, y: 0, duration: 0.32, ease: "power2.out" }}, {round(chunk_start, 3)});'
            )
    return "\n".join(parts)


def counter_js(spec: dict, prefix: str = "tl") -> str:
    suffix = spec.get("suffix", "")
    return (
        f'const {spec["el"].strip("#").replace("-", "_")} = {{ v: {spec["from"]} }};\n'
        f'{prefix}.to({spec["el"].strip("#").replace("-", "_")}, {{ v: {spec["to"]}, duration: {spec["dur"]}, ease: "power2.out", '
        f'onUpdate: function () {{ document.querySelector("{spec["el"]}").textContent = '
        f'Math.round(this.targets()[0].v).toLocaleString("en-US") + "{suffix}"; }} }}, {spec["start"]});'
    )


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1920, height=1080">
<title>BBS SG Bank — legacy to modern, measured</title>
<script src="assets/vendor/gsap.min.js"></script>
<style>{css}</style>
</head>
<body>
<div id="root" data-composition-id="bbs-demo" data-start="0" data-width="1920" data-height="1080" data-duration="{duration}">
  <div class="ground clip" id="ground" data-start="0" data-duration="{duration}"></div>
{scenes}
{audio}
{captions}
</div>
<script>
(function () {{
  const tl = gsap.timeline({{ paused: true }});
{script}
  window.__timelines["bbs-demo"] = tl;
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    html = build()
    (ROOT / "index.html").write_text(html)
    print(f"wrote index.html ({len(html)} bytes)")
