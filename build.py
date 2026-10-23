#!/usr/bin/env python3
"""Build static HTML reader from zh/chN.md (ZH as default) and chN.md (EN) into site/."""
import re, shutil, html
from pathlib import Path
import markdown

ROOT = Path(__file__).parent
OUT = ROOT / "site"
OUT_EN = OUT / "en"
OUT_ZH = OUT / "zh"
BOOK_EN = "Agentic AI for Platform Engineering"
BOOK_ZH = "Agentic AI for Platform Engineering"

def load_chapters(dir_path):
    chapters = []
    for p in sorted(dir_path.glob("ch*.md"), key=lambda p: int(re.sub(r"\D", "", p.stem))):
        n = int(re.sub(r"\D", "", p.stem))
        text = p.read_text(encoding="utf-8")
        text = re.sub(r"\A#\s*\d+\s*\n", "", text).lstrip()  # drop "# 3" chapter-number line
        m = re.match(r"#\s+(.+)", text)
        title = m.group(1).strip()
        body = text[m.end():]
        chapters.append((n, title, body))
    return chapters

def render(body):
    md = markdown.Markdown(extensions=["tables", "fenced_code", "codehilite", "toc", "sane_lists"],
                           extension_configs={"codehilite": {"css_class": "code", "guess_lang": False, "noclasses": False},
                                              "toc": {"toc_depth": "2-3"}})
    h = md.convert(body)
    return h, md.toc_tokens

def page(title, inner, nav, lang="zh-TW", book_title=BOOK_ZH):
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — {book_title}</title>
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

def make_nav(prev, nxt, lang_link, lang_label, index_url="index.html", prev_label="← Previous", next_label="Next →", toc_label="Contents"):
    a = f'<a href="{prev}">{prev_label}</a>' if prev else "<span></span>"
    c = f'<a href="{nxt}">{next_label}</a>' if nxt else "<span></span>"
    l = f'<a href="{lang_link}" class="lang">{lang_label}</a>' if lang_link else ""
    return f'<nav class="chapnav">{a}<a href="{index_url}">{toc_label}</a>{l}<button id="theme" aria-label="Toggle theme">◐</button>{c}</nav>'

def redirect_page(target_url, message="重新導向中..."):
    return f"""<!doctype html>
<html lang="zh-TW"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={target_url}">
<link rel="canonical" href="{target_url}">
<title>{message}</title></head>
<body><p>{message} 若未自動跳轉，請<a href="{target_url}">點擊此處</a>。</p></body></html>"""

if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
OUT_EN.mkdir()
OUT_ZH.mkdir()

# Copy static assets to root (for Chinese default) and to en/ (for English)
shutil.copytree(ROOT / "imgs", OUT / "imgs")
shutil.copy(ROOT / "style.css", OUT / "style.css")

shutil.copytree(ROOT / "imgs", OUT_EN / "imgs")
shutil.copy(ROOT / "style.css", OUT_EN / "style.css")

# 1. Build Chinese site as DEFAULT at root (site/)
chapters_zh = load_chapters(ROOT / "zh")
files_zh = [f"ch{n:02d}.html" for n, _, _ in chapters_zh]

for i, (n, title, body) in enumerate(chapters_zh):
    h, toc = render(body)
    h = re.sub(r'<img ', '<img loading="lazy" ', h)
    h = re.sub(r"<table>", '<div class="tablewrap"><table>', h).replace("</table>", "</table></div>")
    
    prev_f = files_zh[i-1] if i else None
    next_f = files_zh[i+1] if i+1 < len(files_zh) else None
    lang_link = f"en/{files_zh[i]}"
    
    top_nav = make_nav(prev_f, next_f, lang_link, "English", index_url="index.html", prev_label="← 上一章", next_label="下一章 →", toc_label="目錄")
    bot_nav = make_nav(prev_f, next_f, lang_link, "English", index_url="index.html", prev_label="← 上一章", next_label="下一章 →", toc_label="目錄").replace('class="chapnav"', 'class="chapnav bottom"')
    
    inner = f"""<header class="masthead"><span class="eyebrow">{BOOK_ZH}</span>
<h1 class="title serif">第 {n} 章<br>{html.escape(title)}</h1><div class="rule"></div></header>
{h}
<footer class="colophon"><span>{BOOK_ZH} · 第 {n} 章</span><span>{html.escape(title)}</span></footer>
{bot_nav}"""
    (OUT / files_zh[i]).write_text(page(f"第 {n} 章: {title}", inner, top_nav, lang="zh-TW", book_title=BOOK_ZH), encoding="utf-8")

# Chinese Table of Contents (site/index.html)
items_zh = []
for (n, title, body), f in zip(chapters_zh, files_zh):
    _, toc = render(body)
    subs = "".join(f'<li><a href="{f}#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in toc)
    items_zh.append(f'<li class="chap"><a href="{f}"><span class="num">{n:02d}</span>{html.escape(title)}</a><ul>{subs}</ul></li>')

idx_zh_nav = make_nav(None, files_zh[0] if files_zh else None, "en/index.html", "English", index_url="index.html", prev_label="← 上一章", next_label="開始閱讀 →", toc_label="目錄")
idx_zh = f"""<header class="masthead"><span class="eyebrow">線上閱讀版</span>
<h1 class="title serif">{BOOK_ZH}</h1><div class="rule"></div></header>
<ol class="toc">{''.join(items_zh)}</ol>"""
(OUT / "index.html").write_text(page("目錄", idx_zh, idx_zh_nav, lang="zh-TW", book_title=BOOK_ZH), encoding="utf-8")

# 2. Build English site (site/en/)
chapters_en = load_chapters(ROOT)
files_en = [f"ch{n:02d}.html" for n, _, _ in chapters_en]

for i, (n, title, body) in enumerate(chapters_en):
    h, toc = render(body)
    h = re.sub(r'<img ', '<img loading="lazy" ', h)
    h = re.sub(r"<table>", '<div class="tablewrap"><table>', h).replace("</table>", "</table></div>")
    
    prev_f = files_en[i-1] if i else None
    next_f = files_en[i+1] if i+1 < len(files_en) else None
    lang_link = f"../{files_en[i]}"
    
    top_nav = make_nav(prev_f, next_f, lang_link, "中文", index_url="index.html", prev_label="← Previous", next_label="Next →", toc_label="Contents")
    bot_nav = make_nav(prev_f, next_f, lang_link, "中文", index_url="index.html", prev_label="← Previous", next_label="Next →", toc_label="Contents").replace('class="chapnav"', 'class="chapnav bottom"')
    
    inner = f"""<header class="masthead"><span class="eyebrow">{BOOK_EN}</span>
<h1 class="title serif">Chapter {n}<br>{html.escape(title)}</h1><div class="rule"></div></header>
{h}
<footer class="colophon"><span>{BOOK_EN} · Chapter {n}</span><span>{html.escape(title)}</span></footer>
{bot_nav}"""
    (OUT_EN / files_en[i]).write_text(page(f"Chapter {n}: {title}", inner, top_nav, lang="en", book_title=BOOK_EN), encoding="utf-8")

# English Table of Contents (site/en/index.html)
items_en = []
for (n, title, body), f in zip(chapters_en, files_en):
    _, toc = render(body)
    subs = "".join(f'<li><a href="{f}#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in toc)
    items_en.append(f'<li class="chap"><a href="{f}"><span class="num">{n:02d}</span>{html.escape(title)}</a><ul>{subs}</ul></li>')

idx_en_nav = make_nav(None, files_en[0] if files_en else None, "../index.html", "中文", index_url="index.html", prev_label="← Previous", next_label="Start Reading →", toc_label="Contents")
idx_en = f"""<header class="masthead"><span class="eyebrow">Online Reader</span>
<h1 class="title serif">{BOOK_EN}</h1><div class="rule"></div></header>
<ol class="toc">{''.join(items_en)}</ol>"""
(OUT_EN / "index.html").write_text(page("Contents", idx_en, idx_en_nav, lang="en", book_title=BOOK_EN), encoding="utf-8")

# 3. Create backward-compatible redirects in site/zh/ -> site/
(OUT_ZH / "index.html").write_text(redirect_page("../index.html", "正在前往中文版目錄..."), encoding="utf-8")
for f in files_zh:
    (OUT_ZH / f).write_text(redirect_page(f"../{f}", "正在前往章節頁面..."), encoding="utf-8")

print(f"Built {len(chapters_zh)} Chinese chapters into site/ (default) and {len(chapters_en)} English chapters into site/en/ (with zh/ redirects)")
