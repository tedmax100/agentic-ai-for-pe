#!/usr/bin/env python3
"""Build static HTML reader from chN.md into site/."""
import re, shutil, html
from pathlib import Path
import markdown

ROOT = Path(__file__).parent
OUT = ROOT / "site"
BOOK = "Agentic AI for Platform Engineering"
chapters = []
for p in sorted(ROOT.glob("ch*.md"), key=lambda p: int(re.sub(r"\D", "", p.stem))):
    n = int(re.sub(r"\D", "", p.stem))
    text = p.read_text(encoding="utf-8")
    text = re.sub(r"\A#\s*\d+\s*\n", "", text).lstrip()  # drop "# 3" chapter-number line
    m = re.match(r"#\s+(.+)", text)
    title = m.group(1).strip()
    body = text[m.end():]
    chapters.append((n, title, body))

def render(body):
    md = markdown.Markdown(extensions=["tables", "fenced_code", "codehilite", "toc", "sane_lists"],
                           extension_configs={"codehilite": {"css_class": "code", "guess_lang": False, "noclasses": False},
                                              "toc": {"toc_depth": "2-3"}})
    h = md.convert(body)
    return h, md.toc_tokens

def page(title, inner, nav):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — {BOOK}</title>
<link rel="stylesheet" href="style.css"></head><body>
{nav}
<main>
{inner}
</main>
<script>
(function(){{var b=document.getElementById('theme'),r=document.documentElement;
try{{var s=localStorage.getItem('theme');if(s)r.dataset.theme=s}}catch(e){{}}
if(b)b.onclick=function(){{var d=r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
d=d==='dark'?'light':'dark';r.dataset.theme=d;try{{localStorage.setItem('theme',d)}}catch(e){{}}}};}})();
</script></body></html>"""

def nav(prev, nxt):
    a = f'<a href="{prev}">← Previous</a>' if prev else "<span></span>"
    c = f'<a href="{nxt}">Next →</a>' if nxt else "<span></span>"
    return f'<nav class="chapnav">{a}<a href="index.html">Contents</a><button id="theme" aria-label="Toggle theme">◐</button>{c}</nav>'

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
shutil.copytree(ROOT / "imgs", OUT / "imgs")
shutil.copy(ROOT / "style.css", OUT / "style.css")

files = [f"ch{n:02d}.html" for n, _, _ in chapters]
for i, (n, title, body) in enumerate(chapters):
    h, toc = render(body)
    h = re.sub(r'<img ', '<img loading="lazy" ', h)
    h = re.sub(r"<table>", '<div class="tablewrap"><table>', h).replace("</table>", "</table></div>")
    inner = f"""<header class="masthead"><span class="eyebrow">{BOOK}</span>
<h1 class="title serif">Chapter {n}<br>{html.escape(title)}</h1><div class="rule"></div></header>
{h}
<footer class="colophon"><span>{BOOK} · Chapter {n}</span><span>{html.escape(title)}</span></footer>
{nav(files[i-1] if i else None, files[i+1] if i+1 < len(files) else None).replace('class="chapnav"','class="chapnav bottom"')}"""
    (OUT / files[i]).write_text(page(f"Chapter {n}: {title}",
        inner, nav(files[i-1] if i else None, files[i+1] if i+1 < len(files) else None)), encoding="utf-8")

items = []
for (n, title, body), f in zip(chapters, files):
    _, toc = render(body)
    subs = "".join(f'<li><a href="{f}#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in (toc[0]["children"] if False else toc))
    items.append(f'<li class="chap"><a href="{f}"><span class="num">{n:02d}</span>{html.escape(title)}</a><ul>{subs}</ul></li>')
idx = f"""<header class="masthead"><span class="eyebrow">Online Reader</span>
<h1 class="title serif">{BOOK}</h1><div class="rule"></div></header>
<ol class="toc">{''.join(items)}</ol>"""
(OUT / "index.html").write_text(page("Contents", idx, nav(None, files[0])), encoding="utf-8")
print("built", len(chapters), "chapters")
