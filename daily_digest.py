#!/usr/bin/env python3
"""
AI Security Daily Digest
Koral Shimoni — Stay at the cutting edge of AI security

Saves digest to: digests/YYYY-MM-DD.md  (raw data)
                 digests/YYYY-MM-DD.html (LinkedIn-ready presentation)
"""

import urllib.request
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "digests"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AISecurityDigest/1.0)"}

SOURCES = {
    "arXiv — AI Security Papers": {
        "url": "https://arxiv.org/search/?searchtype=all&query=prompt+injection+OR+LLM+security+OR+agentic+AI+security+OR+RAG+security+OR+adversarial+LLM&start=0",
        "type": "arxiv",
        "icon": "📄",
    },
    "arXiv — MCP & Agent Security": {
        "url": "https://arxiv.org/search/?searchtype=all&query=model+context+protocol+security+OR+agentic+AI+attack+OR+tool+poisoning&start=0",
        "type": "arxiv",
        "icon": "🤖",
    },
    "OWASP GenAI": {
        "url": "https://genai.owasp.org",
        "type": "html",
        "icon": "🛡️",
    },
    "Nvidia AI Security Blog": {
        "url": "https://developer.nvidia.com/blog/tag/security/",
        "type": "html",
        "icon": "⚡",
    },
    "Anthropic Safety": {
        "url": "https://www.anthropic.com/research",
        "type": "html",
        "icon": "🔬",
    },
    "Google DeepMind Safety": {
        "url": "https://deepmind.google/research/publications/",
        "type": "html",
        "icon": "🧠",
    },
    "HackerNews — AI Security": {
        "url": "https://hn.algolia.com/api/v1/search?query=AI+security+LLM+prompt+injection&tags=story&hitsPerPage=8",
        "type": "hn_api",
        "icon": "🔥",
    },
    "HackerNews — Agentic AI": {
        "url": "https://hn.algolia.com/api/v1/search?query=agentic+AI+MCP+security+attack&tags=story&hitsPerPage=8",
        "type": "hn_api",
        "icon": "🕵️",
    },
}

# ── Fetchers ──────────────────────────────────────────────────────────────────

def fetch(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"ERROR: {e}"

def parse_arxiv(html):
    results = []
    titles = re.findall(r'class="title[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    abstracts = re.findall(r'class="abstract-short[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    links = re.findall(r'href="(/abs/[^"]+)"', html)
    for i, title in enumerate(titles[:5]):
        title = re.sub(r'<[^>]+>', '', title).strip()
        abstract = re.sub(r'<[^>]+>', '', abstracts[i]).strip()[:200] if i < len(abstracts) else ""
        link = f"https://arxiv.org{links[i]}" if i < len(links) else ""
        if title and len(title) > 10:
            results.append({"title": title, "abstract": abstract, "link": link})
    return results

def parse_hn(json_text):
    try:
        data = json.loads(json_text)
        return [{"title": h.get("title",""), "link": h.get("url", f"https://news.ycombinator.com/item?id={h.get('objectID','')}"), "points": h.get("points",0)} for h in data.get("hits",[])[:6]]
    except:
        return []

def parse_html_headlines(html):
    tags = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.DOTALL | re.IGNORECASE)
    return [re.sub(r'<[^>]+>', '', t).strip() for t in tags if 15 < len(re.sub(r'<[^>]+>', '', t).strip()) < 150][:6]

# ── HTML Presentation Builder ─────────────────────────────────────────────────

SLIDE_COLORS = [
    ("#0f2d48", "#5bc8f5"),
    ("#1a1a2e", "#e94560"),
    ("#0d3b2e", "#00d4aa"),
    ("#2d1b4e", "#b57bee"),
    ("#2d2010", "#f5a623"),
    ("#0f2d48", "#5bc8f5"),
    ("#1a1a2e", "#e94560"),
    ("#0d3b2e", "#00d4aa"),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#111; }}

  .slide {{
    width: 1080px;
    height: 1080px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 64px;
    page-break-after: always;
    position: relative;
    overflow: hidden;
  }}

  .slide::before {{
    content: '';
    position: absolute;
    top: -200px; right: -200px;
    width: 500px; height: 500px;
    border-radius: 50%;
    opacity: 0.06;
    background: var(--accent);
  }}

  .slide-header {{ z-index: 1; }}

  .slide-tag {{
    display: inline-block;
    background: var(--accent);
    color: var(--bg);
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 2px;
    padding: 6px 14px;
    border-radius: 4px;
    margin-bottom: 20px;
  }}

  .slide-icon {{
    font-size: 48px;
    margin-bottom: 12px;
    display: block;
  }}

  .slide-title {{
    font-size: 38px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.15;
    margin-bottom: 28px;
  }}

  .slide-divider {{
    width: 60px;
    height: 3px;
    background: var(--accent);
    border-radius: 2px;
    margin-bottom: 28px;
  }}

  .items {{ z-index: 1; flex: 1; }}

  .item {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 18px;
  }}

  .item-dot {{
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
    margin-top: 7px;
  }}

  .item-text {{
    font-size: 17px;
    color: #d0e0f0;
    line-height: 1.5;
  }}

  .item-text a {{
    color: var(--accent);
    text-decoration: none;
  }}

  .item-sub {{
    font-size: 13px;
    color: #7090a0;
    margin-top: 3px;
  }}

  .no-data {{
    font-size: 16px;
    color: #4a6070;
    font-style: italic;
  }}

  .slide-footer {{
    z-index: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255,255,255,0.08);
    padding-top: 20px;
  }}

  .footer-name {{
    font-size: 15px;
    font-weight: 700;
    color: var(--accent);
  }}

  .footer-title {{
    font-size: 12px;
    color: #4a6070;
    margin-top: 2px;
  }}

  .footer-date {{
    font-size: 13px;
    color: #4a6070;
  }}

  /* Cover slide */
  .cover .slide-title {{ font-size: 52px; }}
  .cover .cover-sub {{
    font-size: 20px;
    color: #7090a0;
    margin-top: 8px;
    line-height: 1.6;
  }}
  .cover .cover-topics {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 32px;
  }}
  .cover .topic-chip {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    color: #d0e0f0;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 14px;
  }}

  @media print {{
    body {{ background: none; }}
    .slide {{ page-break-after: always; }}
  }}
</style>
</head>
<body>
{slides}
</body>
</html>"""

def make_slide(bg, accent, tag, icon, title, items_html, date, slide_num, total):
    return f"""
<div class="slide" style="background:{bg}; --bg:{bg}; --accent:{accent};">
  <div class="slide-header">
    <span class="slide-tag">{tag}</span>
    <span class="slide-icon">{icon}</span>
    <div class="slide-title">{title}</div>
    <div class="slide-divider"></div>
  </div>
  <div class="items">{items_html}</div>
  <div class="slide-footer">
    <div>
      <div class="footer-name">Koral Shimoni</div>
      <div class="footer-title">AI Security Architect & Manager</div>
    </div>
    <div class="footer-date">{date} &nbsp;·&nbsp; {slide_num}/{total}</div>
  </div>
</div>"""

def make_cover(bg, accent, date, total):
    return f"""
<div class="slide cover" style="background:{bg}; --bg:{bg}; --accent:{accent};">
  <div class="slide-header">
    <span class="slide-tag">Daily Intelligence</span>
    <div class="slide-title">🔐 AI Security<br/>Digest</div>
    <div class="cover-sub">
      What you need to know in AI security today.<br/>
      Prompt injection · Agentic AI · RAG · MCP · LLM attacks
    </div>
    <div class="cover-topics">
      <span class="topic-chip">📄 New Research Papers</span>
      <span class="topic-chip">🛡️ OWASP Updates</span>
      <span class="topic-chip">⚡ Nvidia Security</span>
      <span class="topic-chip">🔬 Anthropic Safety</span>
      <span class="topic-chip">🧠 DeepMind</span>
      <span class="topic-chip">🔥 HackerNews</span>
    </div>
  </div>
  <div class="slide-footer">
    <div>
      <div class="footer-name">Koral Shimoni</div>
      <div class="footer-title">AI Security Architect & Manager</div>
    </div>
    <div class="footer-date">{date} &nbsp;·&nbsp; 1/{total}</div>
  </div>
</div>"""

def build_items_html(source_name, config, data):
    html_items = ""
    if not data or (isinstance(data, str) and data.startswith("ERROR")):
        html_items = '<div class="no-data">No new content today — check source directly.</div>'
    elif config["type"] == "arxiv":
        papers = parse_arxiv(data)
        if papers:
            for p in papers:
                link_html = f'<a href="{p["link"]}">Read →</a>' if p["link"] else ""
                sub = f'<div class="item-sub">{p["abstract"][:120]}... {link_html}</div>' if p["abstract"] else ""
                html_items += f'<div class="item"><div class="item-dot"></div><div class="item-text">{p["title"]}{sub}</div></div>'
        else:
            html_items = '<div class="no-data">No new papers today.</div>'
    elif config["type"] == "hn_api":
        stories = parse_hn(data)
        if stories:
            for s in stories:
                html_items += f'<div class="item"><div class="item-dot"></div><div class="item-text"><a href="{s["link"]}">{s["title"]}</a><div class="item-sub">{s["points"]} points</div></div></div>'
        else:
            html_items = '<div class="no-data">No trending stories today.</div>'
    else:
        headlines = parse_html_headlines(data)
        if headlines:
            for h in headlines:
                html_items += f'<div class="item"><div class="item-dot"></div><div class="item-text">{h}</div></div>'
        else:
            html_items = '<div class="no-data">No updates today — check source directly.</div>'
    return html_items

def build_html_presentation(source_data, date):
    total_slides = len(source_data) + 2  # cover + sources + closing
    slides = [make_cover(SLIDE_COLORS[0][0], SLIDE_COLORS[0][1], date, total_slides)]

    for i, (source_name, config, data) in enumerate(source_data, start=2):
        bg, accent = SLIDE_COLORS[i % len(SLIDE_COLORS)]
        items_html = build_items_html(source_name, config, data)
        slide = make_slide(bg, accent, "AI Security Intel", config["icon"], source_name, items_html, date, i, total_slides)
        slides.append(slide)

    # Closing slide
    bg, accent = SLIDE_COLORS[1]
    closing = f"""
<div class="slide" style="background:{bg}; --bg:{bg}; --accent:{accent};">
  <div class="slide-header">
    <span class="slide-tag">Stay Sharp</span>
    <div class="slide-title" style="margin-top:40px;">Follow for daily<br/>AI security intel</div>
    <div class="slide-divider"></div>
    <div style="font-size:17px; color:#7090a0; line-height:2; margin-top:20px;">
      🔐 Prompt Injection &amp; Agentic AI<br/>
      📄 Latest Research Papers<br/>
      🛡️ OWASP · MITRE ATLAS · NIST AI RMF<br/>
      ⚡ Nvidia · Anthropic · DeepMind updates
    </div>
  </div>
  <div class="slide-footer">
    <div>
      <div class="footer-name">Koral Shimoni</div>
      <div class="footer-title">AI Security Architect &amp; Manager · linkedin.com/in/koral-shimoni-mor</div>
    </div>
    <div class="footer-date">{date} &nbsp;·&nbsp; {total_slides}/{total_slides}</div>
  </div>
</div>"""
    slides.append(closing)
    return HTML_TEMPLATE.format(slides="\n".join(slides))

# ── Main ──────────────────────────────────────────────────────────────────────

def build_ntfy_notifications(source_data):
    """Return list of {title, body} dicts — one per source, each with URLs."""
    notifications = []
    for source_name, config, data in source_data:
        if not data or (isinstance(data, str) and data.startswith("ERROR")):
            continue
        icon = config["icon"]
        lines = []
        if config["type"] == "arxiv":
            for p in parse_arxiv(data)[:3]:
                t = p["title"][:80] + ("…" if len(p["title"]) > 80 else "")
                lines.append(t)
                if p["link"]:
                    lines.append(p["link"])
                lines.append("")
        elif config["type"] == "hn_api":
            for s in parse_hn(data)[:3]:
                t = s["title"][:80] + ("…" if len(s["title"]) > 80 else "")
                lines.append(f"{t} ({s['points']} pts)")
                if s["link"]:
                    lines.append(s["link"])
                lines.append("")
        else:
            headlines = parse_html_headlines(data)[:3]
            for h in headlines:
                lines.append(h[:80] + ("…" if len(h) > 80 else ""))
            if config["url"]:
                lines.append("")
                lines.append(config["url"])
        body = "\n".join(lines).strip()
        if body:
            notifications.append({"title": f"{icon} {source_name}", "body": body})
    return notifications

def build_digest():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    source_data = []
    md_lines = [f"# AI Security Daily Digest — {today}\n"]

    for source_name, config in SOURCES.items():
        print(f"Fetching: {source_name}...")
        data = fetch(config["url"])
        source_data.append((source_name, config, data))
        md_lines.append(f"## {source_name}\n{config['url']}\n")
        if data.startswith("ERROR"):
            md_lines.append(f"> {data}\n")

    ntfy_notifications = build_ntfy_notifications(source_data)
    return today, "\n".join(md_lines), build_html_presentation(source_data, today), ntfy_notifications

if __name__ == "__main__":
    print("Building AI Security Daily Digest...")
    today, md_content, html_content, ntfy_notifications = build_digest()

    md_file = OUTPUT_DIR / f"{today}.md"
    html_file = OUTPUT_DIR / f"{today}.html"
    ntfy_file = OUTPUT_DIR / f"{today}_ntfy.json"

    md_file.write_text(md_content, encoding="utf-8")
    html_file.write_text(html_content, encoding="utf-8")
    ntfy_file.write_text(json.dumps(ntfy_notifications, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ Digest saved:")
    print(f"   Markdown:     {md_file}")
    print(f"   Presentation: {html_file}")
    print(f"   Notifications: {ntfy_file}")
    print(f"\nOpen the HTML in Chrome → File → Print → Save as PDF → Upload to LinkedIn")
