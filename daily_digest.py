#!/usr/bin/env python3
"""
AI Security Daily Digest
Koral Shimoni — Stay at the cutting edge of AI security

Run manually:     python3 daily_digest.py
Run daily (cron): 0 7 * * * /usr/bin/python3 /home/user/Agent-ai-security/daily_digest.py

Saves digest to: digests/YYYY-MM-DD.md
"""

import urllib.request
import urllib.parse
import json
import re
import os
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent / "digests"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AISecurityDigest/1.0)"
}

SOURCES = {
    "arXiv — AI Security Papers": {
        "url": "https://arxiv.org/search/?searchtype=all&query=prompt+injection+OR+LLM+security+OR+agentic+AI+security+OR+RAG+security+OR+adversarial+LLM&start=0",
        "type": "arxiv"
    },
    "arXiv — MCP & Agent Security": {
        "url": "https://arxiv.org/search/?searchtype=all&query=model+context+protocol+security+OR+agentic+AI+attack+OR+tool+poisoning&start=0",
        "type": "arxiv"
    },
    "OWASP GenAI": {
        "url": "https://genai.owasp.org",
        "type": "html"
    },
    "Nvidia AI Security Blog": {
        "url": "https://developer.nvidia.com/blog/tag/security/",
        "type": "html"
    },
    "Anthropic Safety": {
        "url": "https://www.anthropic.com/research",
        "type": "html"
    },
    "Google DeepMind Safety": {
        "url": "https://deepmind.google/research/publications/",
        "type": "html"
    },
    "HackerNews — AI Security": {
        "url": "https://hn.algolia.com/api/v1/search?query=AI+security+LLM+prompt+injection&tags=story&hitsPerPage=10",
        "type": "hn_api"
    },
    "HackerNews — Agentic AI": {
        "url": "https://hn.algolia.com/api/v1/search?query=agentic+AI+MCP+security+attack&tags=story&hitsPerPage=10",
        "type": "hn_api"
    },
}

# ── Fetchers ──────────────────────────────────────────────────────────────────

def fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"ERROR: {e}"


def parse_arxiv(html: str) -> list[dict]:
    results = []
    # Find paper entries
    titles = re.findall(r'class="title[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    abstracts = re.findall(r'class="abstract-short[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    links = re.findall(r'href="(/abs/[^"]+)"', html)

    for i, title in enumerate(titles[:8]):
        title = re.sub(r'<[^>]+>', '', title).strip()
        abstract = ""
        if i < len(abstracts):
            abstract = re.sub(r'<[^>]+>', '', abstracts[i]).strip()[:300]
        link = f"https://arxiv.org{links[i]}" if i < len(links) else ""
        if title and len(title) > 10:
            results.append({"title": title, "abstract": abstract, "link": link})
    return results


def parse_hn(json_text: str) -> list[dict]:
    try:
        data = json.loads(json_text)
        results = []
        for hit in data.get("hits", [])[:8]:
            results.append({
                "title": hit.get("title", ""),
                "link": hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID','')}"),
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
            })
        return results
    except Exception:
        return []


def parse_html_headlines(html: str) -> list[str]:
    headlines = []
    # Extract h1/h2/h3/h4 tags
    tags = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.DOTALL | re.IGNORECASE)
    for tag in tags:
        text = re.sub(r'<[^>]+>', '', tag).strip()
        if len(text) > 15 and len(text) < 200:
            headlines.append(text)
    return headlines[:10]


# ── Digest builder ────────────────────────────────────────────────────────────

def build_digest() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# AI Security Daily Digest — {today}",
        f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "---",
        "",
    ]

    for source_name, config in SOURCES.items():
        print(f"Fetching: {source_name}...")
        html = fetch(config["url"])

        lines.append(f"## {source_name}")
        lines.append(f"*{config['url']}*")
        lines.append("")

        if html.startswith("ERROR"):
            lines.append(f"> Could not fetch: {html}")
            lines.append("")
            continue

        if config["type"] == "arxiv":
            papers = parse_arxiv(html)
            if papers:
                for p in papers:
                    lines.append(f"**{p['title']}**")
                    if p["abstract"]:
                        lines.append(f"{p['abstract']}...")
                    if p["link"]:
                        lines.append(f"[Read →]({p['link']})")
                    lines.append("")
            else:
                lines.append("No results found today.")
                lines.append("")

        elif config["type"] == "hn_api":
            stories = parse_hn(html)
            if stories:
                for s in stories:
                    lines.append(f"**{s['title']}** — {s['points']} points, {s['comments']} comments")
                    lines.append(f"[Read →]({s['link']})")
                    lines.append("")
            else:
                lines.append("No results found today.")
                lines.append("")

        else:
            headlines = parse_html_headlines(html)
            if headlines:
                for h in headlines:
                    lines.append(f"- {h}")
                lines.append("")
            else:
                lines.append("No headlines extracted — check source manually.")
                lines.append("")

        lines.append("---")
        lines.append("")

    lines += [
        "## Quick Links — Always Check These",
        "",
        "- [arXiv cs.CR (new today)](https://arxiv.org/list/cs.CR/new)",
        "- [OWASP GenAI](https://genai.owasp.org)",
        "- [MITRE ATLAS](https://atlas.mitre.org)",
        "- [Nvidia AI Security Blog](https://developer.nvidia.com/blog/tag/security/)",
        "- [Anthropic Research](https://www.anthropic.com/research)",
        "- [Google DeepMind](https://deepmind.google/research/)",
        "- [OpenAI Safety](https://openai.com/safety)",
        "- [HackerNews — AI Security](https://news.ycombinator.com/)",
        "",
    ]

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Building AI Security Daily Digest...")
    digest = build_digest()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = OUTPUT_DIR / f"{today}.md"
    output_file.write_text(digest, encoding="utf-8")

    print(f"\nDigest saved to: {output_file}")
    print(f"Lines: {len(digest.splitlines())}")
    print("\nOpen the file to read today's AI security updates.")
