#!/usr/bin/env python3
"""
AI Security Daily Digest — Koral Shimoni
Sources: arXiv API + RSS + HackerNews API
AI Layer: Claude ranks every item by relevance to your OneZero work
Output:  digests/YYYY-MM-DD.html  (morning presentation)
         digests/YYYY-MM-DD.md    (raw)
         digests/YYYY-MM-DD_ntfy.json (ranked notifications)
"""

import urllib.request
import json
import re
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "digests"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AISecurityDigest/1.0)"}

# ── Koral's context — used by Claude for ranking ──────────────────────────────

KORAL_CONTEXT = """
Koral is Senior AI Security Architect & Manager at OneZero Bank (fintech).
Daily work:
- MCP security: tool poisoning, context injection, tool call forgery in production
- RAG security: securing Ella Chat (production RAG+LLM), corpus poisoning, retrieval manipulation
- Prompt injection (direct + indirect) in agentic systems
- AI SDLC: security gates from model selection to deployment
- Code AI extensions: threat modeling Copilot, Claude Code, AI-powered dev tools
- Agentic AI attacks: agent hijacking, multi-agent trust boundaries
- Frameworks applied daily: OWASP LLM Top 10, MITRE ATLAS, NIST AI RMF

Career goal: be on cutting edge of AI security, targeting Nvidia-level architect roles.
High priority: novel attacks, new vulnerabilities, MCP/RAG/agentic AI, practical exploitation, new standards.
Low priority: general AI product news, events, conferences, non-security topics.
"""

# ── Sources ───────────────────────────────────────────────────────────────────

SOURCES = {
    # ── Research Papers ───────────────────────────────────────────────────────
    "arXiv — AI Security": {
        "url": "https://export.arxiv.org/api/query?search_query=all:prompt+injection+OR+LLM+security+OR+agentic+AI+security+OR+RAG+security+OR+adversarial+LLM&sortBy=submittedDate&sortOrder=descending&max_results=8",
        "type": "arxiv_api",
        "icon": "📄",
    },
    "arXiv — MCP & Agents": {
        "url": "https://export.arxiv.org/api/query?search_query=all:model+context+protocol+security+OR+agentic+AI+attack+OR+tool+poisoning+OR+LLM+agent+attack&sortBy=submittedDate&sortOrder=descending&max_results=8",
        "type": "arxiv_api",
        "icon": "🤖",
    },
    # ── Hands-on Research Blogs ───────────────────────────────────────────────
    "Simon Willison": {
        "url": "https://simonwillison.net/atom/everything/",
        "type": "rss",
        "icon": "🔍",
        "fallback": "https://simonwillison.net",
    },
    "Embrace The Red": {
        "url": "https://embracethered.com/blog/index.xml",
        "type": "rss",
        "icon": "🎯",
        "fallback": "https://embracethered.com/blog",
    },
    "Lakera AI": {
        "url": "https://www.lakera.ai/blog/rss.xml",
        "type": "rss",
        "icon": "🛡️",
        "fallback": "https://www.lakera.ai/blog",
    },
    "Invariant Labs": {
        "url": "https://invariantlabs.ai/blog",
        "type": "html",
        "icon": "🔬",
    },
    "Hidden Layer Research": {
        "url": "https://hiddenlayer.com/research/feed/",
        "type": "rss",
        "icon": "👁️",
        "fallback": "https://hiddenlayer.com/research/",
    },
    "Protect AI": {
        "url": "https://protectai.com/blog",
        "type": "html",
        "icon": "🔒",
    },
    "Trail of Bits": {
        "url": "https://blog.trailofbits.com/feed/",
        "type": "rss",
        "icon": "⚗️",
        "fallback": "https://blog.trailofbits.com",
    },
    # ── Standards & Frameworks ────────────────────────────────────────────────
    "OWASP GenAI": {
        "url": "https://genai.owasp.org",
        "type": "html",
        "icon": "📋",
    },
    "OWASP Agentic AI": {
        "url": "https://owasp.org/www-project-agentic-ai-threats/",
        "type": "html",
        "icon": "🤖",
    },
    # ── Vendor Security Teams ─────────────────────────────────────────────────
    "Microsoft Security Blog": {
        "url": "https://www.microsoft.com/en-us/security/blog/feed/",
        "type": "rss",
        "icon": "🪟",
        "fallback": "https://www.microsoft.com/en-us/security/blog/",
    },
    "Palo Alto Unit 42": {
        "url": "https://unit42.paloaltonetworks.com/feed/",
        "type": "rss",
        "icon": "🔭",
        "fallback": "https://unit42.paloaltonetworks.com",
    },
    "Wiz Research": {
        "url": "https://www.wiz.io/blog/tag/research",
        "type": "html",
        "icon": "☁️",
    },
    "Anthropic Safety": {
        "url": "https://www.anthropic.com/rss.xml",
        "type": "rss",
        "icon": "🧬",
        "fallback": "https://www.anthropic.com/research",
    },
    "Google DeepMind": {
        "url": "https://blog.google/technology/google-deepmind/rss/",
        "type": "rss",
        "icon": "🧠",
        "fallback": "https://deepmind.google/research/publications/",
    },
    "Nvidia AI Security": {
        "url": "https://developer.nvidia.com/blog/tag/security/feed/",
        "type": "rss",
        "icon": "⚡",
        "fallback": "https://developer.nvidia.com/blog/tag/security/",
    },
    # ── News & Aggregators ────────────────────────────────────────────────────
    "The Weather Report — AI": {
        "url": "https://theweatherreport.ai",
        "type": "html",
        "icon": "🌐",
    },
    "tl;dr sec": {
        "url": "https://tldrsec.com/feed/",
        "type": "rss",
        "icon": "📰",
        "fallback": "https://tldrsec.com",
    },
    "HackerNews — AI Security": {
        "url": "https://hn.algolia.com/api/v1/search?query=AI+security+LLM+prompt+injection&tags=story&hitsPerPage=10",
        "type": "hn_api",
        "icon": "🔥",
    },
    "HackerNews — Agentic AI": {
        "url": "https://hn.algolia.com/api/v1/search?query=agentic+AI+MCP+security+attack&tags=story&hitsPerPage=10",
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

# ── Parsers — all return [{title, desc, link}] ────────────────────────────────

def parse_arxiv_api(xml_text):
    results = []
    try:
        root = ET.fromstring(xml_text)
        ns = "http://www.w3.org/2005/Atom"
        for entry in root.findall(f"{{{ns}}}entry")[:6]:
            title_el = entry.find(f"{{{ns}}}title")
            summary_el = entry.find(f"{{{ns}}}summary")
            id_el = entry.find(f"{{{ns}}}id")
            title = re.sub(r'\s+', ' ', title_el.text or "").strip() if title_el is not None else ""
            desc = re.sub(r'\s+', ' ', summary_el.text or "").strip()[:300] if summary_el is not None else ""
            if desc and not desc.endswith("."):
                desc = desc.rsplit(" ", 1)[0] + "…"
            link = (id_el.text or "").strip() if id_el is not None else ""
            if title:
                results.append({"title": title, "desc": desc, "link": link})
    except Exception as e:
        print(f"arXiv parse error: {e}")
    return results

def parse_rss(xml_text):
    results = []
    try:
        root = ET.fromstring(xml_text)
        atom_ns = "http://www.w3.org/2005/Atom"
        entries = root.findall(f".//{{{atom_ns}}}entry")
        if entries:
            for entry in entries[:5]:
                title_el = entry.find(f"{{{atom_ns}}}title")
                summary_el = entry.find(f"{{{atom_ns}}}summary") or entry.find(f"{{{atom_ns}}}content")
                link_el = entry.find(f"{{{atom_ns}}}link")
                t = (title_el.text or "").strip() if title_el is not None else ""
                d = re.sub(r'<[^>]+>', '', summary_el.text or "").strip()[:280] if summary_el is not None else ""
                l = link_el.get("href", "") if link_el is not None else ""
                if t:
                    results.append({"title": t, "desc": d, "link": l})
        else:
            for item in root.findall(".//item")[:5]:
                def gt(tag):
                    el = item.find(tag)
                    return (el.text or "").strip() if el is not None else ""
                t = gt("title")
                d = re.sub(r'<[^>]+>', '', gt("description")).strip()[:280]
                l = gt("link")
                if t:
                    results.append({"title": t, "desc": d, "link": l})
    except Exception as e:
        print(f"RSS parse error: {e}")
    return results

EVENT_SKIP = {"webinar", "conference", "meetup", "register", "summit", "workshop",
              "join us", "sign up", "free event", "live session", "agenda", "speaker"}

def parse_html_content(html):
    results = []
    blocks = re.split(r'(<h[1-4][^>]*>.*?</h[1-4]>)', html, flags=re.DOTALL | re.IGNORECASE)
    for i, block in enumerate(blocks):
        if not re.match(r'<h[1-4]', block, re.IGNORECASE):
            continue
        title = re.sub(r'<[^>]+>', '', block).strip()
        if not (15 < len(title) < 200):
            continue
        if any(kw in title.lower() for kw in EVENT_SKIP):
            continue
        following = blocks[i + 1] if i + 1 < len(blocks) else ""
        desc = ""
        for p in re.findall(r'<p[^>]*>(.*?)</p>', following[:1000], re.DOTALL | re.IGNORECASE):
            p_text = re.sub(r'<[^>]+>', '', p).strip()
            if len(p_text) > 40:
                desc = p_text[:250]
                if not desc.endswith("."):
                    desc = desc.rsplit(" ", 1)[0] + "…"
                break
        link_match = re.search(r'href="(https?://[^"]+)"', block)
        link = link_match.group(1) if link_match else ""
        results.append({"title": title, "desc": desc, "link": link})
        if len(results) >= 4:
            break
    return results

def parse_hn(json_text):
    try:
        data = json.loads(json_text)
        return [{"title": h.get("title", ""),
                 "desc": f"{h.get('points', 0)} points on Hacker News",
                 "link": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID', '')}"}
                for h in data.get("hits", [])[:6] if h.get("title")]
    except:
        return []

def extract_items(config, data):
    if not data or (isinstance(data, str) and data.startswith("ERROR")):
        fallback = config.get("fallback")
        if fallback:
            fd = fetch(fallback)
            if not fd.startswith("ERROR"):
                return parse_html_content(fd)
        return []
    t = config["type"]
    if t == "arxiv_api":
        return parse_arxiv_api(data)
    elif t == "rss":
        items = parse_rss(data)
        if not items:
            fallback = config.get("fallback")
            if fallback:
                fd = fetch(fallback)
                if not fd.startswith("ERROR"):
                    return parse_html_content(fd)
        return items
    elif t == "hn_api":
        return parse_hn(data)
    else:
        return parse_html_content(data)

# ── Claude ranking ─────────────────────────────────────────────────────────────

def rank_with_claude(flat_items):
    """
    flat_items: list of {source, icon, title, desc, link}
    Returns same list enriched with {score, summary, badge} and sorted high→low.
    Falls back gracefully if no API key.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not flat_items:
        for item in flat_items:
            item["score"] = 5
            item["summary"] = item.get("desc", "")
            item["badge"] = "🟡"
        return flat_items

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        items_text = "\n".join(
            f'[{i}] {it["source"]}\nTitle: {it["title"]}\nDesc: {it.get("desc","")[:180]}'
            for i, it in enumerate(flat_items)
        )

        prompt = f"""You are briefing a Senior AI Security Architect. Here is her context:
{KORAL_CONTEXT}

For each news item below, return a JSON array with:
- idx: item index
- score: 1-10 relevance to her daily work (10=directly hits MCP/RAG/agentic/prompt injection)
- summary: ONE sentence max 160 chars — why THIS matters to HER specifically, practical and direct

Return ONLY a JSON array, no markdown, no explanation.

Items:
{items_text}"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        rankings = json.loads(json_match.group()) if json_match else []

        rank_map = {r["idx"]: r for r in rankings}
        for i, item in enumerate(flat_items):
            r = rank_map.get(i, {})
            item["score"] = r.get("score", 5)
            item["summary"] = r.get("summary", item.get("desc", ""))
            item["badge"] = "🔴" if item["score"] >= 7 else ("🟡" if item["score"] >= 4 else "🟢")

        flat_items.sort(key=lambda x: x["score"], reverse=True)
        print(f"Claude ranked {len(flat_items)} items")

    except Exception as e:
        print(f"Claude ranking error (falling back): {e}")
        for item in flat_items:
            item.setdefault("score", 5)
            item.setdefault("summary", item.get("desc", ""))
            item.setdefault("badge", "🟡")

    return flat_items


def generate_morning_brief(ranked_items, date):
    """
    Claude Sonnet writes a proper analyst-style morning brief.
    Falls back to plain markdown if no API key.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    reds    = [it for it in ranked_items if it.get("badge") == "\U0001f534"][:5]
    yellows = [it for it in ranked_items if it.get("badge") == "\U0001f7e1"][:4]

    def plain_brief():
        out = [f"# \U0001f510 AI Security Brief \u2014 {date}\n"]
        for badge, items in [("\U0001f534 Must Read", reds), ("\U0001f7e1 Worth Knowing", yellows)]:
            if items:
                out.append(f"## {badge}\n")
                for it in items:
                    out.append(f"**{it['title']}**  \n{it.get('summary', it.get('desc',''))}  \n{it.get('link','')}\n")
        return "\n".join(out)

    if not api_key:
        return plain_brief()

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        def fmt(items):
            return "\n".join(
                f'- {it["badge"]} {it["title"]}\n  Source: {it["source"]}\n  Desc: {it.get("desc","")[:250]}\n  Link: {it.get("link","")}'
                for it in items
            )

        prompt = f"""You are writing a daily intelligence brief for a Senior AI Security Architect.

Her context:
{KORAL_CONTEXT}

Today is {date}. Here are today's ranked items:

RED (high priority):
{fmt(reds) if reds else "None today"}

YELLOW (medium priority):
{fmt(yellows) if yellows else "None today"}

Write a morning brief in this exact format:

# \U0001f510 AI Security Morning Brief \u2014 {date}

## \U0001f534 Act On These
For each red item: bold title, then 2-3 sentences — what it is, what the specific risk is for her MCP/RAG/agentic work at OneZero, what she should do. Link on its own line.

## \U0001f7e1 Worth Knowing
For each yellow item: bold title, 1-2 sentences why it matters to her. Link on its own line.

## Today's Signal
4-6 sentences: what pattern do today's items show together? What does it mean for AI security direction and for her OneZero work and Nvidia-level ambitions?

Be direct. No vague phrases. Say exactly what the risk is and what she should do."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        print("Morning brief generated")
        return response.content[0].text.strip()

    except Exception as e:
        print(f"Brief generation error: {e}")
        return plain_brief()

# ── HTML Presentation ─────────────────────────────────────────────────────────

SLIDE_COLORS = [
    ("#0f2d48", "#5bc8f5"),
    ("#1a1a2e", "#e94560"),
    ("#0d3b2e", "#00d4aa"),
    ("#2d1b4e", "#b57bee"),
    ("#2d2010", "#f5a623"),
    ("#0f2d48", "#5bc8f5"),
    ("#1a1a2e", "#e94560"),
    ("#0d3b2e", "#00d4aa"),
    ("#2d1b4e", "#b57bee"),
    ("#2d2010", "#f5a623"),
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
    min-height: 1080px;
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
    font-size: 36px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.15;
    margin-bottom: 24px;
  }}

  .slide-divider {{
    width: 60px;
    height: 3px;
    background: var(--accent);
    border-radius: 2px;
    margin-bottom: 24px;
  }}

  .items {{ z-index: 1; flex: 1; }}

  .item {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 20px;
    border-left: 2px solid rgba(255,255,255,0.06);
    padding-left: 14px;
  }}

  .item-badge {{
    font-size: 16px;
    flex-shrink: 0;
    margin-top: 2px;
  }}

  .item-body {{ flex: 1; }}

  .item-title {{
    font-size: 16px;
    font-weight: 700;
    color: #e8f0f7;
    line-height: 1.4;
  }}

  .item-title a {{
    color: #e8f0f7;
    text-decoration: none;
  }}

  .item-summary {{
    font-size: 13px;
    color: #8aa8bc;
    margin-top: 5px;
    line-height: 1.55;
  }}

  .item-link {{
    font-size: 12px;
    margin-top: 4px;
  }}

  .item-link a {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
  }}

  .item-source {{
    font-size: 11px;
    color: #4a6070;
    margin-top: 3px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  .no-data {{
    font-size: 15px;
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
    margin-top: 24px;
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

def make_cover(bg, accent, date, total):
    return f"""
<div class="slide cover" style="background:{bg}; --bg:{bg}; --accent:{accent};">
  <div class="slide-header">
    <span class="slide-tag">Daily Intelligence</span>
    <div class="slide-title">🔐 AI Security<br/>Digest</div>
    <div class="cover-sub">
      Ranked by relevance to your work at OneZero.<br/>
      🔴 Must read &nbsp;·&nbsp; 🟡 Worth knowing &nbsp;·&nbsp; 🟢 Background
    </div>
    <div class="cover-topics">
      <span class="topic-chip">📄 arXiv Papers</span>
      <span class="topic-chip">🛡️ OWASP GenAI</span>
      <span class="topic-chip">⚡ Nvidia Security</span>
      <span class="topic-chip">🔬 Anthropic</span>
      <span class="topic-chip">🧠 DeepMind</span>
      <span class="topic-chip">🌐 Weather Report</span>
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

def item_html(it):
    link_html = f'<div class="item-link"><a href="{it["link"]}">Read → {it["link"][:60]}{"…" if len(it["link"]) > 60 else ""}</a></div>' if it.get("link") else ""
    summary = it.get("summary") or it.get("desc", "")
    summary_html = f'<div class="item-summary">{summary}</div>' if summary else ""
    source_html = f'<div class="item-source">{it.get("source", "")}</div>'
    title_content = f'<a href="{it["link"]}">{it["title"]}</a>' if it.get("link") else it["title"]
    return f"""<div class="item">
  <div class="item-badge">{it.get("badge", "🟡")}</div>
  <div class="item-body">
    <div class="item-title">{title_content}</div>
    {summary_html}
    {source_html}
    {link_html}
  </div>
</div>"""

def make_top_slide(bg, accent, date, total, ranked_items):
    top5 = [it for it in ranked_items if it.get("badge") == "🔴"][:5]
    if not top5:
        top5 = ranked_items[:5]
    items_html = "\n".join(item_html(it) for it in top5) or '<div class="no-data">No high-priority items today.</div>'
    return f"""
<div class="slide" style="background:{bg}; --bg:{bg}; --accent:{accent};">
  <div class="slide-header">
    <span class="slide-tag">🔴 Must Read Today</span>
    <div class="slide-title">Top Priorities</div>
    <div class="slide-divider"></div>
  </div>
  <div class="items">{items_html}</div>
  <div class="slide-footer">
    <div>
      <div class="footer-name">Koral Shimoni</div>
      <div class="footer-title">AI Security Architect & Manager</div>
    </div>
    <div class="footer-date">{date} &nbsp;·&nbsp; 2/{total}</div>
  </div>
</div>"""

def make_source_slide(bg, accent, date, slide_num, total, source_name, icon, items):
    if not items:
        items_html = '<div class="no-data">No new content today.</div>'
    else:
        items_html = "\n".join(item_html(it) for it in items[:4])
    return f"""
<div class="slide" style="background:{bg}; --bg:{bg}; --accent:{accent};">
  <div class="slide-header">
    <span class="slide-tag">AI Security Intel</span>
    <span class="slide-icon">{icon}</span>
    <div class="slide-title">{source_name}</div>
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

def build_html_presentation(source_items, ranked_items, date):
    # cover + top slide + one per source + closing
    total = 2 + len(source_items) + 1
    slides = [make_cover(SLIDE_COLORS[0][0], SLIDE_COLORS[0][1], date, total)]

    # Top priorities slide
    bg, accent = SLIDE_COLORS[1]
    slides.append(make_top_slide(bg, accent, date, total, ranked_items))

    # Per-source slides
    for i, (source_name, icon, items) in enumerate(source_items, start=3):
        bg, accent = SLIDE_COLORS[i % len(SLIDE_COLORS)]
        slides.append(make_source_slide(bg, accent, date, i, total, source_name, icon, items))

    # Closing
    bg, accent = SLIDE_COLORS[2]
    closing = f"""
<div class="slide" style="background:{bg}; --bg:{bg}; --accent:{accent};">
  <div class="slide-header">
    <span class="slide-tag">Stay Sharp</span>
    <div class="slide-title" style="margin-top:40px;">Follow for daily<br/>AI security intel</div>
    <div class="slide-divider"></div>
    <div style="font-size:17px; color:#7090a0; line-height:2.2; margin-top:20px;">
      🔐 MCP · RAG · Agentic AI · Prompt Injection<br/>
      📄 Latest Research Papers<br/>
      🛡️ OWASP · MITRE ATLAS · NIST AI RMF<br/>
      ⚡ Nvidia · Anthropic · DeepMind
    </div>
  </div>
  <div class="slide-footer">
    <div>
      <div class="footer-name">Koral Shimoni</div>
      <div class="footer-title">AI Security Architect &amp; Manager · linkedin.com/in/koral-shimoni-mor</div>
    </div>
    <div class="footer-date">{date} &nbsp;·&nbsp; {total}/{total}</div>
  </div>
</div>"""
    slides.append(closing)
    return HTML_TEMPLATE.format(slides="\n".join(slides))

# ── ntfy notifications ────────────────────────────────────────────────────────

def build_ntfy_notifications(ranked_items, date):
    """
    Max 2 notifications per day:
    1. 🔴 Must Read — top red items
    2. 🟡 Worth Knowing — top yellow items
    Each item: title + one-line summary + link
    """
    notifications = []

    reds = [it for it in ranked_items if it.get("badge") == "🔴"][:4]
    yellows = [it for it in ranked_items if it.get("badge") == "🟡"][:4]

    def format_items(items):
        lines = []
        for it in items:
            summary = it.get("summary") or it.get("desc", "")
            link = it.get("link", "")
            lines.append(f'• {it["title"][:70]}')
            if summary:
                lines.append(f'  {summary[:130]}')
            if link:
                lines.append(f'  {link}')
            lines.append("")
        return "\n".join(lines).strip()

    if reds:
        notifications.append({
            "title": f"🔴 AI Security — Must Read ({date})",
            "body": format_items(reds)
        })

    if yellows:
        notifications.append({
            "title": f"🟡 AI Security — Worth Knowing ({date})",
            "body": format_items(yellows)
        })

    return notifications

# ── Main ──────────────────────────────────────────────────────────────────────

def discover_new_sources(flat_items, existing_sources):
    """
    Ask Claude to identify new AI security sources worth tracking
    based on links and domains appearing in today's content.
    Returns markdown string appended to the brief.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not flat_items:
        return ""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Collect all links from today's items
        links = [it.get("link", "") for it in flat_items if it.get("link")]
        existing_domains = set()
        for cfg in existing_sources.values():
            try:
                from urllib.parse import urlparse
                existing_domains.add(urlparse(cfg["url"]).netloc)
            except:
                pass

        links_text = "\n".join(links[:60])
        existing_text = "\n".join(sorted(existing_domains))

        prompt = f"""You are helping maintain an AI security intelligence feed for a Senior AI Security Architect.

Currently tracked domains:
{existing_text}

Links appearing in today's content:
{links_text}

Identify up to 3 new domains/blogs NOT already tracked that:
1. Focus on AI security, LLM attacks, agentic AI, MCP, RAG security, or ML security
2. Publish technical content (not just news aggregation)
3. Are credible sources (research labs, security companies, known researchers)

For each suggestion return:
- Name: short descriptive name
- URL: the blog/research URL
- RSS: RSS feed URL if you know it (or "unknown")
- Why: one sentence why it's relevant to AI security practitioners

If no new relevant sources found, return "NONE".
Format as a simple markdown list."""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.content[0].text.strip()
        if result and result != "NONE":
            return f"\n\n---\n## 🔎 New Sources Discovered Today\n{result}"
        return ""
    except Exception as e:
        print(f"Source discovery error: {e}")
        return ""


def build_digest():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    source_items = []
    flat_items = []
    md_lines = [f"# AI Security Daily Digest — {today}\n"]

    for source_name, config in SOURCES.items():
        print(f"Fetching: {source_name}...")
        data = fetch(config["url"])
        items = extract_items(config, data)
        for it in items:
            it["source"] = source_name
            it["icon"] = config["icon"]
        source_items.append((source_name, config["icon"], items))
        flat_items.extend(items)
        md_lines.append(f"## {source_name}\n{config['url']}\n")
        if isinstance(data, str) and data.startswith("ERROR"):
            md_lines.append(f"> {data}\n")

    print(f"Ranking {len(flat_items)} items with Claude...")
    ranked_items = rank_with_claude(flat_items)

    print("Generating morning brief...")
    brief = generate_morning_brief(ranked_items, today)

    print("Discovering new sources...")
    new_sources = discover_new_sources(flat_items, SOURCES)
    brief += new_sources

    html = build_html_presentation(source_items, ranked_items, today)
    ntfy = build_ntfy_notifications(ranked_items, today)
    return today, "\n".join(md_lines), html, ntfy, brief

if __name__ == "__main__":
    print("Building AI Security Daily Digest...")
    today, md_content, html_content, ntfy_notifications, brief = build_digest()

    md_file   = OUTPUT_DIR / f"{today}.md"
    html_file = OUTPUT_DIR / f"{today}.html"
    ntfy_file = OUTPUT_DIR / f"{today}_ntfy.json"
    brief_file= OUTPUT_DIR / f"{today}_brief.md"

    md_file.write_text(md_content, encoding="utf-8")
    html_file.write_text(html_content, encoding="utf-8")
    ntfy_file.write_text(json.dumps(ntfy_notifications, ensure_ascii=False, indent=2), encoding="utf-8")
    brief_file.write_text(brief, encoding="utf-8")

    print(f"\n✅ Digest saved:")
    print(f"   Brief:         {brief_file}")
    print(f"   Presentation:  {html_file}")
    print(f"   Markdown:      {md_file}")
    print(f"   Notifications: {ntfy_file} ({len(ntfy_notifications)} items)")
    print(f"\nOpen the HTML in Chrome → Print → Save as PDF")
