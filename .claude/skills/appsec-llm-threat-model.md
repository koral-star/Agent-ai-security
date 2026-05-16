---
name: appsec-llm-threat-model
description: Generates a comprehensive threat model for LLM/AI applications using STRIDE and OWASP LLM Top 10. Analyzes the architecture, identifies trust boundaries, enumerates threats with risk scores, and produces a prioritized mitigation plan. Use at the start of a new AI feature or product security review.
---

Generate a full threat model for the AI/LLM application described in the specified files, architecture diagram, or description.

## Threat Modeling Process

### Step 1: System Decomposition
Identify and document:
- **Components**: LLM APIs, agent frameworks, vector stores, tool integrations, user interfaces, auth systems
- **Data flows**: How data moves between components (prompt construction, API calls, retrieval, output rendering)
- **Trust boundaries**: Where control passes between different trust zones (user → app, app → LLM API, LLM → tools)
- **Entry points**: All surfaces where external input reaches the system
- **Assets**: What is valuable to protect (user data, system prompts, model access, business logic)

### Step 2: STRIDE Threat Analysis per Component

For each component and trust boundary, enumerate threats:

| Threat | AI-Specific Examples |
|--------|---------------------|
| **S**poofing | Impersonating a user to an agent; forging tool call responses |
| **T**ampering | Poisoning RAG knowledge base; manipulating training data |
| **R**epudiation | Agent actions not logged; no audit trail for LLM decisions |
| **I**nformation Disclosure | PII in prompts sent to third-party LLMs; system prompt extraction |
| **D**enial of Service | Unbounded token loops; excessive embedding API calls |
| **E**levation of Privilege | Prompt injection granting admin tool access; jailbreak bypassing safety |

### Step 3: OWASP LLM Top 10 Coverage Check

Score the application against each LLM risk:
- **LLM01** Prompt Injection — entry points, sanitization controls
- **LLM02** Insecure Output Handling — output rendering, downstream system usage
- **LLM03** Training Data Poisoning — fine-tuning pipeline, dataset controls
- **LLM04** Model Denial of Service — rate limiting, token budgets, recursion limits
- **LLM05** Supply Chain Vulnerabilities — model provenance, dependency integrity
- **LLM06** Sensitive Information Disclosure — PII in prompts/outputs, logging
- **LLM07** Insecure Plugin Design — tool validation, least-privilege tooling
- **LLM08** Excessive Agency — permission scope, human-in-the-loop gates
- **LLM09** Overreliance — human oversight, validation of LLM decisions
- **LLM10** Model Theft — API auth, rate limiting, watermarking

### Step 4: Risk Scoring

For each identified threat, assign:
- **Likelihood**: High (3) / Medium (2) / Low (1) — based on exploitability and attacker motivation
- **Impact**: High (3) / Medium (2) / Low (1) — based on confidentiality, integrity, availability, and business impact
- **Risk Score**: Likelihood × Impact (1–9)
- **Priority**: Critical (7–9) / High (5–6) / Medium (3–4) / Low (1–2)

### Step 5: Mitigations & Security Controls

For each threat, recommend:
- **Preventive control**: What stops the attack from occurring
- **Detective control**: What would alert on an attack in progress
- **Corrective control**: What reduces impact if the attack succeeds

## Output Structure

Produce the threat model in this format:

---
### System Overview
[Brief description of the AI application, its purpose, and key components]

### Architecture Diagram (Text)
[ASCII or structured text diagram showing components, data flows, and trust boundaries]

### Asset Register
| Asset | Owner | Sensitivity | Consequence if Compromised |
|-------|-------|-------------|---------------------------|

### Threat Register
| ID | Component | Threat | STRIDE | OWASP LLM | Likelihood | Impact | Risk | Priority |
|----|-----------|--------|--------|-----------|------------|--------|------|----------|

### Detailed Threat Descriptions
[For each threat: scenario, attack vector, business impact, mitigations]

### OWASP LLM Top 10 Scorecard
| Risk | Score (1-5) | Current Controls | Gaps |
|------|-------------|-----------------|------|

### Prioritized Mitigation Roadmap
**Immediate (Critical/High risks):**
- ...

**Short-term (Medium risks):**
- ...

**Long-term (Low risks / hardening):**
- ...

### Security Requirements
[Derived security requirements for developers based on this threat model]
---
