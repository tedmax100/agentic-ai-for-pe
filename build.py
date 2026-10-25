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

def parse_chapter_stem(stem):
    if stem in ("preface", "ch00", "ch00_preface"):
        return (0, 0)
    if stem in ("epilogue", "ch99", "conclusion"):
        return (99, 0)
    m = re.match(r"ch(\d+)(?:[_\-]ex)?", stem)
    if not m:
        return (999, 0)
    num = int(m.group(1))
    is_ex = bool(re.search(r"[_\-]ex", stem))
    return (num, 1 if is_ex else 0)

def load_chapters(dir_path):
    chapters = []
    files = [p for p in dir_path.glob("*.md") if p.stem.startswith("ch") or p.stem in ("preface", "epilogue")]
    for p in sorted(files, key=lambda p: parse_chapter_stem(p.stem)):
        num, is_ex = parse_chapter_stem(p.stem)
        text = p.read_text(encoding="utf-8")
        text = re.sub(r"\A#\s*[\d\w\-]+\s*\n", "", text).lstrip()  # drop "# 3" or "# PREFACE" or "# EPILOGUE"
        m = re.match(r"#\s+(.+)", text)
        title = m.group(1).strip()
        body = text[m.end():]
        if num == 0:
            file_name = "preface.html"
            label_zh = "全書導讀"
            label_en = "Foreword"
            num_label_zh = "導讀"
            num_label_en = "PREFACE"
            cls_name = "chap preface"
        elif num == 99:
            file_name = "epilogue.html"
            label_zh = "全書結語"
            label_en = "Epilogue"
            num_label_zh = "結語"
            num_label_en = "EPILOGUE"
            cls_name = "chap epilogue"
        else:
            file_name = f"ch{num:02d}_ex.html" if is_ex else f"ch{num:02d}.html"
            label_zh = f"第 {num} 章 延伸實踐" if is_ex else f"第 {num} 章"
            label_en = f"Chapter {num} Extension" if is_ex else f"Chapter {num}"
            num_label_zh = f"{num:02d}-EX" if is_ex else f"{num:02d}"
            num_label_en = f"{num:02d}-EX" if is_ex else f"{num:02d}"
            cls_name = "chap ex" if is_ex else "chap"

        chapters.append({
            "num": num,
            "is_ex": is_ex,
            "title": title,
            "body": body,
            "file": file_name,
            "label_zh": label_zh,
            "label_en": label_en,
            "num_label_zh": num_label_zh,
            "num_label_en": num_label_en,
            "cls_name": cls_name
        })
    return chapters

def render(body):
    def repl_mermaid(m):
        code = m.group(1).strip()
        return f'\n<pre class="mermaid">\n{code}\n</pre>\n'
    body = re.sub(r'```mermaid\s*\n(.*?)\n```', repl_mermaid, body, flags=re.DOTALL)

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
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
const isDark = document.documentElement.dataset.theme === 'dark' || 
  (!document.documentElement.dataset.theme && window.matchMedia('(prefers-color-scheme: dark)').matches);
mermaid.initialize({{
  startOnLoad: true,
  theme: isDark ? 'dark' : 'default',
  securityLevel: 'loose'
}});
</script>
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
files_zh = [c["file"] for c in chapters_zh]

for i, c in enumerate(chapters_zh):
    h, toc = render(c["body"])
    h = re.sub(r'<img ', '<img loading="lazy" ', h)
    h = re.sub(r"<table>", '<div class="tablewrap"><table>', h).replace("</table>", "</table></div>")
    
    prev_f = files_zh[i-1] if i else None
    next_f = files_zh[i+1] if i+1 < len(files_zh) else None
    lang_link = f"en/{c['file']}"
    
    top_nav = make_nav(prev_f, next_f, lang_link, "English", index_url="index.html", prev_label="← 上一章", next_label="下一章 →", toc_label="目錄")
    bot_nav = make_nav(prev_f, next_f, lang_link, "English", index_url="index.html", prev_label="← 上一章", next_label="下一章 →", toc_label="目錄").replace('class="chapnav"', 'class="chapnav bottom"')
    
    inner = f"""<header class="masthead"><span class="eyebrow">{BOOK_ZH}</span>
<h1 class="title serif">{c['label_zh']}<br>{html.escape(c['title'])}</h1><div class="rule"></div></header>
{h}
<footer class="colophon"><span>{BOOK_ZH} · {c['label_zh']}</span><span>{html.escape(c['title'])}</span></footer>
{bot_nav}"""
    (OUT / c['file']).write_text(page(f"{c['label_zh']}: {c['title']}", inner, top_nav, lang="zh-TW", book_title=BOOK_ZH), encoding="utf-8")

# Chinese Table of Contents (site/index.html)
items_zh = []
for c in chapters_zh:
    _, toc = render(c["body"])
    subs = "".join(f'<li><a href="{c["file"]}#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in toc)
    cls = c["cls_name"]
    items_zh.append(f'<li class="{cls}"><a href="{c["file"]}"><span class="num">{c["num_label_zh"]}</span>{html.escape(c["title"])}</a><ul>{subs}</ul></li>')

idx_zh_nav = make_nav(None, files_zh[0] if files_zh else None, "en/index.html", "English", index_url="index.html", prev_label="← 上一章", next_label="開始閱讀 →", toc_label="目錄")
idx_zh = f"""<header class="masthead"><span class="eyebrow">線上閱讀版</span>
<h1 class="title serif">{BOOK_ZH}</h1><div class="rule"></div></header>
<ol class="toc">{''.join(items_zh)}</ol>"""
(OUT / "index.html").write_text(page("目錄", idx_zh, idx_zh_nav, lang="zh-TW", book_title=BOOK_ZH), encoding="utf-8")

# 2. Build English site (site/en/)
chapters_en = load_chapters(ROOT)
files_en = [c["file"] for c in chapters_en]

for i, c in enumerate(chapters_en):
    h, toc = render(c["body"])
    h = re.sub(r'<img ', '<img loading="lazy" ', h)
    h = re.sub(r"<table>", '<div class="tablewrap"><table>', h).replace("</table>", "</table></div>")
    
    prev_f = files_en[i-1] if i else None
    next_f = files_en[i+1] if i+1 < len(files_en) else None
    lang_link = f"../{c['file']}"
    
    top_nav = make_nav(prev_f, next_f, lang_link, "中文", index_url="index.html", prev_label="← Previous", next_label="Next →", toc_label="Contents")
    bot_nav = make_nav(prev_f, next_f, lang_link, "中文", index_url="index.html", prev_label="← Previous", next_label="Next →", toc_label="Contents").replace('class="chapnav"', 'class="chapnav bottom"')
    
    inner = f"""<header class="masthead"><span class="eyebrow">{BOOK_EN}</span>
<h1 class="title serif">{c['label_en']}<br>{html.escape(c['title'])}</h1><div class="rule"></div></header>
{h}
<footer class="colophon"><span>{BOOK_EN} · {c['label_en']}</span><span>{html.escape(c['title'])}</span></footer>
{bot_nav}"""
    (OUT_EN / c['file']).write_text(page(f"{c['label_en']}: {c['title']}", inner, top_nav, lang="en", book_title=BOOK_EN), encoding="utf-8")

# English Table of Contents (site/en/index.html)
items_en = []
for c in chapters_en:
    _, toc = render(c["body"])
    subs = "".join(f'<li><a href="{c["file"]}#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in toc)
    cls = c["cls_name"]
    items_en.append(f'<li class="{cls}"><a href="{c["file"]}"><span class="num">{c["num_label_en"]}</span>{html.escape(c["title"])}</a><ul>{subs}</ul></li>')

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
