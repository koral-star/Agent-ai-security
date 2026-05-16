---
name: appsec-ai-compliance-checker
description: Reviews AI/LLM applications for regulatory compliance. Covers GDPR (EU), CCPA (California), HIPAA (US healthcare), EU AI Act (high-risk AI systems), SOC 2 Type II (AI controls), and NIST AI RMF. Identifies compliance gaps, required documentation, and technical controls needed for each framework.
---

Review the specified AI application or codebase for regulatory and compliance gaps.

## Compliance Frameworks

### 1. GDPR (EU General Data Protection Regulation)
**Applicable when**: Processing personal data of EU residents through AI systems.

Check:
- **Lawful basis**: Is there a documented lawful basis for each AI processing activity (consent, legitimate interest, contract)?
- **Data minimization**: Is only the minimum necessary personal data sent to LLM APIs?
- **Purpose limitation**: Is personal data used only for the purpose it was collected?
- **Third-party transfers**: Are LLM API providers (OpenAI, Anthropic, Google) covered by Data Processing Agreements (DPAs)?
- **Data subject rights**: Can users request deletion of their data from vector DBs, fine-tuning datasets, and conversation logs?
- **Right to explanation**: For automated decisions made by AI, can the system explain the basis?
- **Data retention**: Are conversation histories, embeddings, and logs subject to defined retention and deletion policies?
- **DPIA**: Has a Data Protection Impact Assessment been conducted for high-risk AI processing?

### 2. CCPA / CPRA (California Consumer Privacy Act)
**Applicable when**: Processing personal data of California residents.

Check:
- **Disclosure**: Is there a privacy notice disclosing that AI/LLMs process personal data?
- **Opt-out**: Can California residents opt out of having their data processed by AI models?
- **Sale prohibition**: If user data is sent to third-party LLM providers for training, is this disclosed and consented?
- **Sensitive data**: Is sensitive personal information (health, financial, biometric) handled with heightened protection?
- **Deletion rights**: Can users request deletion across all AI-related data stores?

### 3. HIPAA (US Health Insurance Portability and Accountability Act)
**Applicable when**: Processing Protected Health Information (PHI) in AI systems.

Check:
- **BAA**: Is there a Business Associate Agreement with every LLM API provider that processes PHI?
- **PHI in prompts**: Is PHI sent to general-purpose LLM APIs, or only HIPAA-covered services?
- **De-identification**: Is PHI de-identified (Safe Harbor or Expert Determination) before LLM processing?
- **Access controls**: Is access to AI features that process PHI restricted to authorized workforce members?
- **Audit logs**: Are all AI accesses to PHI logged per HIPAA audit log requirements?
- **Encryption**: Is PHI encrypted in transit and at rest in vector DBs, logs, and fine-tuning datasets?

### 4. EU AI Act
**Applicable when**: Deploying AI systems in the EU, especially in high-risk categories.

Check:
- **Risk classification**: Is the AI system classified (Unacceptable / High-risk / Limited / Minimal)?
  - High-risk categories include: HR decisions, credit scoring, education, law enforcement, healthcare
- **Conformity assessment**: For high-risk systems, has a conformity assessment been completed?
- **Technical documentation**: Is there documentation of training data, model architecture, performance metrics, and limitations?
- **Human oversight**: Are there mechanisms for human oversight and intervention?
- **Transparency**: Are users informed they are interacting with an AI system?
- **Accuracy & robustness**: Are there measures to ensure accuracy and resistance to adversarial inputs?
- **Prohibited practices**: Does the system engage in prohibited AI practices (subliminal manipulation, social scoring, real-time biometric surveillance)?

### 5. SOC 2 Type II — AI-Relevant Controls
**Applicable when**: Serving enterprise customers who require SOC 2 compliance.

Check:
- **CC6.1 (Logical Access)**: Are LLM API keys and model endpoints access-controlled with MFA and least privilege?
- **CC6.3 (Access Removal)**: Are model API credentials revoked when employees leave?
- **CC7.2 (Monitoring)**: Is AI system behavior monitored for anomalies?
- **CC8.1 (Change Management)**: Are model version changes and prompt updates tracked in change management?
- **A1.2 (Availability)**: Are SLA commitments met despite LLM API rate limits and outages?
- **C1.1 (Confidentiality)**: Are confidential customer inputs to AI systems protected from disclosure?

### 6. NIST AI RMF (AI Risk Management Framework)
Check coverage across the four functions:
- **GOVERN**: Is there an AI policy, accountability structure, and risk tolerance defined?
- **MAP**: Are AI risks identified, contextualized, and categorized?
- **MEASURE**: Are AI risks analyzed and measured (bias testing, performance metrics, adversarial testing)?
- **MANAGE**: Are risk response plans in place and regularly reviewed?

## Output Structure

For each compliance framework:

### [Framework Name]
**Applicability**: Yes / No / Partial — reason

**Gaps Found**:
| Requirement | Status | Evidence | Gap Description | Remediation |
|---|---|---|---|---|
| [Requirement] | PASS / FAIL / N/A | [file:line or doc] | [What's missing] | [What to do] |

**Required Documentation** (not yet found in codebase):
- [ ] Item

**Technical Controls Required**:
- [ ] Item with implementation guidance

---

End with a **Compliance Readiness Dashboard** — a one-page summary of status per framework (GREEN / AMBER / RED), top 5 blocking gaps, and a compliance roadmap.
