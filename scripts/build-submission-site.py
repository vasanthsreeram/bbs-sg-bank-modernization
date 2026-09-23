#!/usr/bin/env python3
"""Assemble the static Cloudflare Pages bundle for the hackathon submission.

Copies the demo video, slides, screenshots and evidence into submission-site/,
and renders the markdown documents to HTML so a judge can read them in a browser.

Usage: python3 scripts/build-submission-site.py
"""

from __future__ import annotations

import html
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "submission-site"
VIDEO = ROOT / "video" / "bbs-sg-bank-demo"

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — BBS SG Bank</title>
<style>
 body {{ margin:0; background:#f7f9fc; color:#0f1728;
   font-family: system-ui, -apple-system, "Segoe UI", sans-serif; line-height:1.6; }}
 .wrap {{ max-width: 900px; margin:0 auto; padding: 34px 22px 70px; }}
 a {{ color:#2563eb; }}
 .back {{ font-size:14px; }}
 h1 {{ font-size:30px; letter-spacing:-.02em; margin:18px 0 8px; }}
 h2 {{ font-size:23px; margin:32px 0 8px; }}
 h3 {{ font-size:18px; margin:24px 0 6px; }}
 h4 {{ font-size:16px; margin:20px 0 4px; }}
 p, li {{ font-size:16px; }}
 pre {{ background:#0f1728; color:#dbe6fb; padding:16px 18px; border-radius:12px;
   overflow:auto; font-size:13.5px; line-height:1.5; }}
 code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.92em;
   background:#eef2f9; padding:1px 5px; border-radius:5px; }}
 pre code {{ background:none; padding:0; color:inherit; }}
 table {{ border-collapse:collapse; margin:14px 0; font-size:15px; width:100%; }}
 th, td {{ border:1px solid #e2e8f2; padding:8px 10px; text-align:left; vertical-align:top; }}
 th {{ background:#f0f4fb; }}
 blockquote {{ margin:14px 0; padding:10px 16px; border-left:4px solid #c8d6f0;
   background:#fff; color:#3c4864; border-radius:0 10px 10px 0; }}
 hr {{ border:none; border-top:1px solid #e2e8f2; margin:28px 0; }}
 footer {{ margin-top:44px; padding-top:16px; border-top:1px solid #e2e8f2;
   color:#4d5a75; font-size:13px; }}
</style></head><body><div class="wrap">
<p class="back"><a href="../index.html">← BBS SG Bank submission</a> · <a href="index.html">All documents</a></p>
{body}
<footer>BBS SG Bank is a fictional bank; all data is synthetic. Performance figures describe a
deliberately inefficient synthetic COBOL baseline, not COBOL in general.</footer>
</div></body></html>
"""


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render(md: str) -> str:
    out: list[str] = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            i += 1
            block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(html.escape(lines[i]))
                i += 1
            out.append("<pre><code>" + "\n".join(block) + "</code></pre>")
            i += 1
            continue
        if re.match(r"^\s*\|.*\|\s*$", line) and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in header) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
                       + "</tbody></table>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2).strip())}</h{level}>")
            i += 1
            continue
        if re.match(r"^\s*([-*_])\s*\1\s*\1\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        if line.strip().startswith(">"):
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(block)) + "</blockquote>")
            continue
        if re.match(r"^\s*[-*+]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        if not line.strip():
            i += 1
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*[-*+]\s|\s*\d+\.\s|>|```|\s*\|)", lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")
    return "\n".join(out)


def main() -> int:
    SITE.mkdir(exist_ok=True)
    for name in ("media", "slides", "screens", "docs", "evidence"):
        (SITE / name).mkdir(exist_ok=True)

    shutil.copy2(VIDEO / "renders" / "bbs-sg-bank-demo.mp4", SITE / "media" / "bbs-sg-bank-demo.mp4")
    for shot in sorted((VIDEO / "assets" / "screens").glob("*.png")):
        shutil.copy2(shot, SITE / "screens" / shot.name)
    for txt in sorted((ROOT / "scripts" / "evidence").glob("*.txt")):
        shutil.copy2(txt, SITE / "evidence" / txt.name)
    for md in sorted((ROOT / "docs").glob("*.md")):
        shutil.copy2(md, SITE / "docs" / md.name)
    if (ROOT / "docs" / "forge").is_dir():
        shutil.copytree(ROOT / "docs" / "forge", SITE / "docs" / "forge", dirs_exist_ok=True)
    shutil.copytree(ROOT / "slides", SITE / "slides", dirs_exist_ok=True)

    cards = []
    sources = [(ROOT / "docs", ROOT / "docs")] + (
        [(ROOT / "docs" / "forge", ROOT / "docs" / "forge")] if (ROOT / "docs" / "forge").is_dir() else []
    )
    for src_dir, _ in sources:
        for md in sorted(src_dir.glob("*.md")):
            rel = md.relative_to(ROOT / "docs")
            body = render(md.read_text())
            title = md.stem
            (SITE / "docs" / (str(rel).replace(".md", ".html"))).write_text(PAGE.format(title=title, body=body))
            label = rel.stem.replace("-", " ")
            cards.append(f'<li><a href="{str(rel).replace(".md", ".html")}">{html.escape(label)}</a></li>')
    (SITE / "docs" / "index.html").write_text(PAGE.format(
        title="Documents",
        body="<h1>Migration documents</h1>\n<ul>" + "\n".join(cards) + "</ul>",
    ))
    print(f"assembled {SITE} ({sum(1 for _ in SITE.rglob('*') if _.is_file())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
