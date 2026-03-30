# AI Security Career Strategy & Study Plan
**Owner:** Koral Shimoni — Senior AI Security Architect & Manager
**Goal:** Next Nvidia-level interview: pass and get the role
**Last updated:** March 2026

---

## Why You're a Strong Candidate (Don't Lose This)

The Nvidia feedback was "strong candidate, other candidate better fit to lead the process." This does **not** mean your technical skills fell short. Gen AI security is ~4 years old as a discipline. You have ~3 years. No one has 10 years here.

The gap is **external visibility and program ownership narrative** — not knowledge depth.

The other candidate likely had:
- Public research (blog posts, talks, papers)
- A story told as "I built this program" not "I work on this program"
- Name recognition in the AI security community

You already have the substance. This plan turns that substance into visibility.

---

## What You're Already Doing at OneZero (Your Foundation)

| Work | Security Domain | Your Advantage |
|------|----------------|----------------|
| Ella Chat (RAG + LLM) | RAG poisoning, prompt injection, data exfiltration | End-to-end production AI product security |
| MCP Security | Tool poisoning, context injection, tool call forgery | Almost nobody has this in production |
| Code AI Extensions | AI supply chain, malicious suggestion, developer tool threats | Emerging area — few practitioners |
| AI-Driven SDLC | Secure AI pipeline, CI/CD gates for AI code | Program ownership story |
| GPT App Store / Plugins | AI marketplace security, extension trust model | Relevant to any enterprise deploying AI agents |

**MCP is your biggest differentiator.** The MCP protocol is new and virtually no security practitioner has hands-on experience. Publish first.

---

## The Leadership Narrative (Practice This Until It's Automatic)

> "At OneZero I established the AI security function from scratch. There was no program, no policy, no defined scope. I built it: defined the domain, set the KPIs, authored the policies, and designed the workflows. Today it covers every LLM product in the bank — from the RAG pipeline in Ella Chat to our MCP implementations and AI-driven developer tools. I own the roadmap and I own the risk."

That's the Nvidia answer. Say it clearly, say it confidently.

---

## Phase 1: Technical Exploitation Depth (Months 1–2)
*Goal: Go from "I understand these attacks" to "I can design novel attacks and defenses"*

### Prompt Injection (Priority — was in the Nvidia interview)
- [ ] Read: "Not What You've Signed Up For" — Perez & Ribeiro (2022) — the foundational indirect prompt injection paper
- [ ] Read: "Compromising LLM-Integrated Applications with Indirect Prompt Injection" — Greshake et al. (2023)
- [ ] Practice: Build a vulnerable RAG app yourself and exploit it with indirect injection
- [ ] Practice: Multi-turn injection, context window manipulation, system prompt extraction
- [ ] Practice: HackAPrompt competition problems (hackathon.besafe.ai)
- [ ] Practice: Lakera Gandalf (all levels including hidden levels)
- [ ] Build: A working end-to-end prompt injection exploit against an agent with tool use — document it

### Agentic AI Attacks
- [ ] Study: Tool poisoning attacks (malicious tool return values steering agent behavior)
- [ ] Study: Agent hijacking via memory/state manipulation
- [ ] Study: Multi-agent trust boundary attacks (agent-to-agent injection)
- [ ] Study: MCP-specific vectors: tool call forgery, context injection via MCP servers, server impersonation
- [ ] Practice: Build a multi-tool agent and attack it at every layer
- [ ] Document: Your MCP threat model from OneZero work (sanitize if needed — this is publishable)

### LLM/ML Security (Broader AI Red Team Skills)
- [ ] Study: Model extraction attacks (stealing model behavior via queries)
- [ ] Study: Training data extraction (Carlini et al. — "Extracting Training Data from LLMs")
- [ ] Study: Data poisoning / backdoor attacks
- [ ] Study: Membership inference attacks
- [ ] Practice: MITRE ATLAS hands-on exercises (atlas.mitre.org)
- [ ] Tool: Learn Garak (LLM vulnerability scanner) — use it and understand its probes

### RAG-Specific Threats
- [ ] Study: Corpus poisoning / knowledge base manipulation
- [ ] Study: Embedding inversion attacks
- [ ] Study: Retrieval ranking injection (manipulating what gets retrieved)
- [ ] Practice: Run a RAG corpus poisoning attack against a test LlamaIndex setup

---

## Phase 2: Build External Visibility (Months 2–4)
*Goal: Be the person who defines AI security, not just a person who does AI security*

### Publish (Most Important Action in This Plan)
- [ ] **Blog Post 1: MCP Security Deep Dive** — attack vectors, your threat model, mitigations (publish on Medium, personal blog, or LinkedIn long-form)
- [ ] **Blog Post 2: Securing RAG Systems** — lessons from production (Ella Chat, sanitized)
- [ ] **Blog Post 3: AI SDLC Security Gates** — how to embed security into the AI development lifecycle
- [ ] **Blog Post 4: Prompt Injection in Agentic Systems** — from basic to multi-tool exploitation

Publishing even 2 of these puts you in the top 5% of AI security practitioners by external visibility.

### Conference Talks / CFPs
- [ ] Submit CFP to **DEF CON AI Village** (annual, submissions usually open March-April)
- [ ] Submit CFP to **BSides Tel Aviv** or regional BSides
- [ ] Submit to **OWASP AppSec** conference track on AI security
- [ ] Target topic: MCP security (your unique angle) — "Security of the Model Context Protocol: Attack Vectors and Defenses"

### Open Source Contributions
- [ ] Contribute to **OWASP LLM Top 10** project (GitHub: OWASP/www-project-top-10-for-large-language-model-applications)
- [ ] Contribute to **MITRE ATLAS** — submit a new technique or case study
- [ ] Publish a GitHub tool: an MCP security scanner, or a prompt injection testing harness
- [ ] Consider: open-source your AI SDLC security gates (sanitized from OneZero)

### Community Presence
- [ ] Join DEF CON AI Village Discord — be active, share research
- [ ] Join OWASP AI Security Slack/Discord
- [ ] Join MLSecOps community
- [ ] Start posting technical AI security content on LinkedIn (1-2 posts/week)

---

## Phase 3: Frameworks & Program Maturity (Months 2–4)
*Goal: Be able to architect and assess AI security programs at enterprise scale*

### NIST AI RMF (Read the Full Document)
- [ ] Read the complete NIST AI RMF (ai-100-1.pdf) — not just summaries
- [ ] Map your OneZero program to the four functions: MAP, MEASURE, MANAGE, GOVERN
- [ ] Be able to teach it in 15 minutes in an interview

### ISO/IEC 42001 (AI Management System Standard)
- [ ] Understand audit requirements and implementation controls
- [ ] Understand how it relates to ISO 27001 (you likely already know 27001 from AppSec background)

### EU AI Act (Relevant for Nvidia's European operations and clients)
- [ ] Read the risk classification framework (prohibited / high-risk / limited-risk / minimal-risk)
- [ ] Understand what "high-risk AI systems" means in practice
- [ ] Know what compliance requires for financial services AI

### OWASP LLM Top 10 (Go Deeper)
- [ ] Know every category at the "can teach it and exploit it" level, not just list it
- [ ] Map each category to real OneZero findings
- [ ] Contribute at least one update or new entry

---

## Phase 4: Nvidia-Specific Preparation (Months 3–5)
*Goal: Speak Nvidia's language fluently*

### Nvidia AI Product Portfolio (Know These)
- [ ] **Nvidia Morpheus** — their AI-powered cybersecurity platform. This is directly relevant to the role. Understand architecture, use cases, and attack surface
- [ ] **NIM (Nvidia Inference Microservices)** — their AI deployment platform. What are the security boundaries?
- [ ] **NeMo / NeMo Guardrails** — their LLM safety/guardrails framework. How does it work and where can it be bypassed?
- [ ] **Triton Inference Server** — open-source inference server. Attack surface: model loading, API exposure
- [ ] **DGX Cloud** — multi-tenant AI compute. What are the isolation and data residency concerns?

### Nvidia-Unique Security Angles
- [ ] GPU/hardware security: understand CUDA security model, GPU memory isolation
- [ ] AI compute infrastructure: multi-tenant GPU clusters, HPC security at scale
- [ ] AI supply chain: model provenance, SBOM for ML models, Hugging Face model risks
- [ ] Nvidia sells AI security (Morpheus) — the role involves understanding AI security as a product, not just a practice

### Interview Scenarios to Prepare
- [ ] "Design an AI red team program for a company deploying Nvidia NIM"
- [ ] "Threat model an LLM-powered product in 30 minutes" (practice with a whiteboard)
- [ ] "Walk me through a code review of this agentic Python code" (practice with LangChain/LlamaIndex examples)
- [ ] "How would you exploit this RAG application?" (hands-on exploitation demo)
- [ ] "How do you build an AI security program from scratch?" (your OneZero story)

---

## Phase 5: Portfolio & Interview Readiness (Months 4–6)
*Goal: Have tangible proof of every skill claim*

### GitHub Portfolio (Public)
- [ ] MCP security scanner or threat modeling tool
- [ ] Prompt injection testing harness (against agentic apps)
- [ ] AI SDLC security gates (sanitized from OneZero, open-sourced)
- [ ] A write-up / proof-of-concept exploit chain against an agent

### The Interview Story (Nail This)
Three stories you must be able to tell fluently:

**Story 1 — Program Builder:**
"I established OneZero's AI security function from zero. No program, no policies, no defined scope. I built it..."

**Story 2 — Technical Depth:**
"In our Ella Chat RAG implementation, I identified an indirect prompt injection vector where [specific attack]. I designed a defense that [specific control]..."

**Story 3 — Thought Leader:**
"I published research on MCP security that [impact]. I presented at [conference]..."

---

## 6-Month Milestone Checklist

| Month | Milestone |
|-------|-----------|
| 1 | Complete HackAPrompt all levels + build own vulnerable agent for exploitation practice |
| 2 | Publish first blog post: MCP Security Deep Dive |
| 3 | Submit CFP to DEF CON AI Village |
| 4 | Publish GitHub tool (MCP scanner or prompt injection harness) |
| 5 | Complete NIST AI RMF deep study + map OneZero program to it |
| 6 | Mock interview with a peer, refine all three stories, apply to Nvidia or equivalent |

---

## Resources

### Essential Papers
- "Not what you've signed up for" — Perez & Ribeiro (2022)
- "Compromising LLM-Integrated Applications with Indirect Prompt Injection" — Greshake et al. (2023)
- "Extracting Training Data from Large Language Models" — Carlini et al. (2021)
- "Poisoning Web-Scale Training Datasets is Practical" — Carlini et al. (2023)
- "Universal and Transferable Adversarial Attacks on Aligned Language Models" — Zou et al. (2023)

### Practical Platforms
- **Lakera Gandalf** — prompt injection training (all levels)
- **HackAPrompt** — competition-style challenges
- **MITRE ATLAS** — ATT&CK for ML with hands-on playbooks (atlas.mitre.org)
- **Garak** — LLM vulnerability scanner (github.com/leondz/garak)
- **Promptfoo** — LLM red teaming framework (promptfoo.dev)

### Key Frameworks & Standards
- OWASP LLM Top 10 (genai.owasp.org)
- MITRE ATLAS (atlas.mitre.org)
- NIST AI RMF (nist.gov/artificial-intelligence)
- EU AI Act compliance guides

### Communities
- DEF CON AI Village (Discord — dc-aiv.slack.com)
- OWASP AI Security Project (GitHub)
- MLSecOps Community (Discord)

---

## Your Core Positioning Statement

> "I am one of the few practitioners who has secured AI systems end-to-end: from the model pipeline through the agentic runtime, including emerging protocols like MCP. At OneZero I built and lead the AI security function. I am now ready to scale that impact — defining AI security for an organization at Nvidia's level."

---

*Track progress by checking off items above. Revisit and update this plan monthly.*
