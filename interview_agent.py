#!/usr/bin/env python3
"""
Interview Coach Agent — Koral Shimoni
Interactive CLI chat for senior AI security architect interview preparation.
Run: python3 interview_agent.py
"""

import os
import sys
from pathlib import Path
import anthropic

BASE_DIR = Path(__file__).parent
RESUME_MD = BASE_DIR / "Koral_Shimoni_Resume.md"
STUDY_PLAN = BASE_DIR / "AI_Security_Study_Plan.md"
DIGESTS_DIR = BASE_DIR / "digests"


def load_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_recent_digests(n: int = 5) -> str:
    digest_files = sorted(DIGESTS_DIR.glob("*.md"))[-n:]
    parts = []
    for f in digest_files:
        content = f.read_text(encoding="utf-8")
        if content.strip():
            parts.append(f"[{f.name}]\n{content[:700]}")
    return "\n\n".join(parts)


def build_system_prompt(resume: str, study_plan: str, digests: str) -> str:
    return f"""You are Koral Shimoni's personal AI security interview coach.
You know her background in detail and your job is to help her land senior AI security architect roles.

## Who Koral Is

Koral is Senior AI Security Architect & Manager at OneZero Bank (fintech/banking).
8+ years cybersecurity, 3+ years leading enterprise AI security programs.
She founded OneZero's AI security function from scratch — 0 to 1.

Key work at OneZero:
- Ella Chat: secured a production RAG+LLM conversational banking product end-to-end
- MCP security: designed security architecture for production MCP implementations (tool poisoning, context injection, tool call forgery) — one of very few practitioners with this in production
- Agentic AI: threat modeling for multi-agent systems, trust boundaries, privilege escalation via tool chaining
- AI SDLC: security gates from model selection through deployment, CI/CD pipeline AI code scanning
- Built autonomous AI security intelligence pipeline: 25+ sources, Claude API, GitHub Actions, multi-channel delivery

Target: Senior AI Security Architect / Principal AI Security Researcher at companies like Nvidia.
Nvidia feedback: "strong candidate, other better fit to lead the process" → gap is ownership narrative, not technical depth.

Key narrative to own: "I am one of the few practitioners who has secured AI systems end-to-end in production — RAG, agentic, MCP — and I built and own the program."

## Her Full Resume
{resume}

## Career Strategy & Target Role Context
{study_plan[:2500]}

## Recent AI Security Topics She's Been Tracking
{digests}

## Your Coaching Style

Be direct and specific. Never give generic interview advice.
- Always anchor coaching to her REAL experience (OneZero, MCP, Ella Chat, RAG, AI SDLC)
- Push back on vague language immediately — if she says "I worked on AI security" help her say "I founded and lead the AI security function at OneZero Bank"
- For behavioral questions: always use STAR format (Situation, Task, Action, Result) with her actual stories
- For technical questions: reference real examples from her work
- Interview answers should be 90–120 seconds when spoken — flag anything longer
- If she pastes a draft answer, critique it specifically: what's weak, what's missing, what to cut
- Be honest about gaps and give her concrete strategies to handle them

## Modes

When she says "mock interview" — ask her questions one at a time and give feedback on her answers.
When she asks "top questions" or "question bank" — give the real top 10-15 for her target role.
When she says "star [story/topic]" — help her build a tight STAR answer using her real experience.
When she says "pitch" — help her refine her 60-second elevator pitch.
When she says "how do I explain [topic]" — coach her on explaining it to technical and non-technical audiences.
Otherwise — answer naturally as her coach.
"""


def print_banner(resume_loaded: bool, study_plan_loaded: bool, digests_count: int) -> None:
    print("\n" + "─" * 62)
    print("  Interview Coach — AI Security  (powered by Claude Sonnet)")
    print("─" * 62)
    print("  Context loaded:")
    print(f"    Resume:     {'✓' if resume_loaded else '✗ not found'}")
    print(f"    Study plan: {'✓' if study_plan_loaded else '✗ not found'}")
    print(f"    Digests:    {digests_count} recent files")
    print("─" * 62)
    print("  Suggested openers:")
    print("    • What are the top questions for a senior AI security role?")
    print("    • mock interview")
    print("    • help me with my elevator pitch")
    print("    • star: building the AI security program from scratch")
    print("    • how do I explain MCP security to a non-technical interviewer?")
    print("─" * 62)
    print("  Type 'quit' to exit.\n")


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    resume = load_file(RESUME_MD)
    study_plan = load_file(STUDY_PLAN)
    digests_text = load_recent_digests(5)
    digests_count = len(list(DIGESTS_DIR.glob("*.md")))

    system_prompt = build_system_prompt(resume, study_plan, digests_text)
    conversation_history: list[dict] = []

    print_banner(bool(resume), bool(study_plan), digests_count)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Good luck!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Good luck in the interview!")
            break

        conversation_history.append({"role": "user", "content": user_input})

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=system_prompt,
                messages=conversation_history,
            )
            reply = response.content[0].text
        except anthropic.APIError as e:
            print(f"\nAPI error: {e}\n")
            conversation_history.pop()
            continue

        conversation_history.append({"role": "assistant", "content": reply})
        print(f"\nCoach: {reply}\n")


if __name__ == "__main__":
    main()
