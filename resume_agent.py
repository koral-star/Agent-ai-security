#!/usr/bin/env python3
"""
Resume Agent — Koral Shimoni
Reads current resume + career context + recent digests and produces an improved resume.
Run: python3 resume_agent.py
Dry run (no writes): python3 resume_agent.py --dry-run
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import anthropic

BASE_DIR = Path(__file__).parent
RESUME_MD = BASE_DIR / "Koral_Shimoni_Resume.md"
RESUME_HTML = BASE_DIR / "Koral_Shimoni_Resume.html"
STUDY_PLAN = BASE_DIR / "AI_Security_Study_Plan.md"
DIGEST_CODE = BASE_DIR / "daily_digest.py"
DIGESTS_DIR = BASE_DIR / "digests"
CHANGES_FILE = BASE_DIR / "resume_changes.md"

KORAL_CONTEXT = """
Koral Shimoni — Senior AI Security Architect & Manager at OneZero Bank (fintech).
- 8+ years cybersecurity, 3+ years AI security leadership
- Founded OneZero's AI security function from scratch (0→1): defined scope, KPIs, policies, AI SDLC gates
- Key production work: Ella Chat (RAG+LLM), MCP security architecture, agentic AI threat models
- Target role: Senior AI Security Architect / Principal Researcher at Nvidia-tier companies
- Nvidia feedback: "strong candidate, other better fit to lead" — gap is program ownership narrative, not technical depth
- Differentiator: one of the few practitioners who has secured AI systems end-to-end in production
- Built autonomous AI security intelligence pipeline: 25+ source monitoring, Claude API, GitHub Actions, Telegram/ntfy delivery
"""


def load_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_recent_digests(n: int = 7) -> str:
    digest_files = sorted(DIGESTS_DIR.glob("*.md"))[-n:]
    parts = []
    for f in digest_files:
        content = f.read_text(encoding="utf-8")
        if content.strip():
            parts.append(f"=== {f.name} ===\n{content[:1200]}")
    return "\n\n".join(parts)


def generate_improved_resume(
    client: anthropic.Anthropic,
    current_resume: str,
    study_plan: str,
    digests: str,
    digest_code_snippet: str,
) -> str:
    system = f"""You are an expert technical resume writer for senior cybersecurity and AI security leaders.
You are improving the resume of a senior AI security architect targeting Nvidia-level roles.

{KORAL_CONTEXT}

Rules:
1. Keep EXACTLY the same Markdown structure and section order as the original
2. Strengthen program ownership language: use "founded", "built", "designed", "own", "drive", "lead" — not "worked on", "participated in", "helped with"
3. Add the autonomous AI security intelligence pipeline under OneZero Bank's experience as a concrete portfolio deliverable — it demonstrates: Claude API integration, 25+ source monitoring, GitHub Actions CI/CD automation, multi-channel delivery (Telegram, push notifications, GitHub Pages), PostToolUse AI-generated code security hooks
4. Elevate MCP security, agentic AI, and RAG security from skills to demonstrated expertise with specifics
5. Quantify wherever possible — the 40% vulnerability reduction is good, add similar metrics
6. Make the Summary read like a leader who ships and owns programs, not someone who reviews
7. Do NOT add fluff — if something doesn't strengthen the resume, don't add it
8. Keep all contact info, education, and languages exactly as-is
9. Update the "Last updated" date to {datetime.now().strftime('%B %Y')}

Output ONLY the improved Markdown. No commentary, no preamble, no code fences."""

    user = f"""Current resume to improve:
{current_resume}

---
Career strategy and target role context:
{study_plan[:3000]}

---
Recent AI security topics she has been deeply tracking (last 7 digests):
{digests[:2000]}

---
Code evidence of the AI security pipeline she built (add this to resume under OneZero):
{digest_code_snippet[:1500]}

---
Write the improved resume now."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def generate_changes_summary(
    client: anthropic.Anthropic, old_resume: str, new_resume: str
) -> str:
    system = "You are a resume editor explaining your edits clearly to the resume owner. Be specific and direct."
    user = f"""Compare these two resume versions and write a Markdown changelog explaining exactly:
- What was ADDED (and why it strengthens the resume)
- What was CHANGED (quote old → new where helpful, explain why it's stronger)
- What was REMOVED (and why)

OLD RESUME:
{old_resume}

NEW RESUME:
{new_resume}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def generate_updated_html(
    client: anthropic.Anthropic, new_resume_md: str, current_html: str
) -> str:
    system = """You are updating an HTML resume file. The HTML has a specific two-column layout: dark navy sidebar + white main content area.
Update the HTML text content to reflect the new Markdown resume content while PRESERVING:
- Every CSS style rule exactly as-is (do not touch the <style> block)
- The sidebar structure (contact, skills sections, education)
- The main content structure (summary, experience, key achievements)
- All color scheme, layout, and design choices
- All HTML class names and element structure

Only update the visible text content. Output ONLY the complete updated HTML file. No commentary."""

    user = f"""Updated resume content (Markdown):
{new_resume_md}

---
Current HTML file to update:
{current_html}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("Resume Agent — Loading context...")
    current_resume = load_file(RESUME_MD)
    if not current_resume:
        print(f"ERROR: Resume not found at {RESUME_MD}")
        sys.exit(1)

    study_plan = load_file(STUDY_PLAN)
    digests = load_recent_digests(7)
    digest_code_lines = load_file(DIGEST_CODE).split("\n")[:200]
    digest_code_snippet = "\n".join(digest_code_lines)
    current_html = load_file(RESUME_HTML)

    print("Step 1/3 — Generating improved resume (Claude Sonnet 4.6)...")
    new_resume = generate_improved_resume(
        client, current_resume, study_plan, digests, digest_code_snippet
    )

    print("Step 2/3 — Generating changes summary...")
    changes = generate_changes_summary(client, current_resume, new_resume)

    print("Step 3/3 — Updating HTML resume...")
    new_html = generate_updated_html(client, new_resume, current_html)

    if dry_run:
        print("\n=== DRY RUN — no files written ===\n")
        print("─" * 60)
        print("NEW RESUME MARKDOWN:")
        print("─" * 60)
        print(new_resume)
        print("\n" + "─" * 60)
        print("CHANGES SUMMARY:")
        print("─" * 60)
        print(changes)
        return

    RESUME_MD.write_text(new_resume, encoding="utf-8")
    print(f"  Updated: {RESUME_MD.name}")

    RESUME_HTML.write_text(new_html, encoding="utf-8")
    print(f"  Updated: {RESUME_HTML.name}")

    changes_doc = f"# Resume Changes — {datetime.now().strftime('%B %Y')}\n\n{changes}"
    CHANGES_FILE.write_text(changes_doc, encoding="utf-8")
    print(f"  Created: {CHANGES_FILE.name}")

    print("\nDone. Review resume_changes.md before committing.")


if __name__ == "__main__":
    main()
