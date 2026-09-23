---
workflow: product-launch-video
flow: automation
storyboard: no
message: "The same bank, same files and same rules — measured 115x faster after the migration, with real COBOL still running in the demo."
destination: hackathon submission (public demo + judges)
aspect: "16:9 (1920x1080)"
language: en
audience: hackathon judges and reviewers
length: "60-75 seconds"
angle: "Before/after evidence: show the deliberately inefficient COBOL path, the indexed modern engine, and the measured parity-checked result."
---

# BBS SG Bank — modernization demo video

## Intent

A show-it-as-is demo of what happened in this hackathon entry: a fictional bank's
nightly COBOL batch, the modern indexed Python engine that replaced it, and the
measured, parity-checked difference between them. The video's assets are the
application's own captured screens plus graphics built from the repository's
evidence files.

## Confirmed by the user

- 16:9, about 60-75 seconds.
- Narration in the **Eve** Grok voice via the xAI text-to-speech API.
- Burned-in subtle captions (sound-off viewing for judges).
- One-shot build: brief confirmed, then build and render; review the finished MP4.
- Light theme with graphics and screenshots so the story is easy to follow.

## Customizations

- Screenshots captured with the cmux browser from the running demo (`site/` on
  127.0.0.1:8788 and the COBOL operator terminal on 127.0.0.1:8792) — never Chrome.
- The operator-terminal shot is a real job: `cobc` compiled `legacy/bank.cob` and
  ran it live (1,200 accounts / 400 operations, 400 processed, 3 rejected,
  0.915s of COBOL wall clock, `STEP020 VERIFY PASS` against `modern/bank.py`).

## Notes

- Every number on screen comes from `scripts/evidence/*.txt` or a live run.
- The disclosure that the workload is synthetic and the legacy design
  deliberately inefficient appears on the results scene and in the closing line.
- Light theme: warm off-white canvas, dark ink, blue/slate accents; the dark
  application screenshots sit in rounded cards with soft shadows.
