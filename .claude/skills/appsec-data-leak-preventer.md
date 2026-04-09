---
name: appsec-data-leak-preventer
description: Detects and prevents data leakage in AI systems. Scans for PII/sensitive data flowing into prompts, LLM logs, vector databases, fine-tuning datasets, and model outputs. Covers GDPR/CCPA-relevant data exposure, training data memorization, and prompt-level data exfiltration paths.
---

Scan the specified code, configuration, or data pipeline for data leakage risks in AI systems.

## Scan Scope

### 1. PII & Sensitive Data in Prompts
- Is user-supplied PII (name, email, SSN, phone, address, DOB, health data) inserted into prompts raw?
- Are database query results containing sensitive fields injected into LLM context without redaction?
- Is internal business data (financials, employee records, contracts) passed to third-party LLM APIs?
- Is there a data minimization step before prompt construction?

### 2. LLM Output Leakage
- Can the model be prompted to regurgitate training data, system prompts, or other users' data?
- Are outputs scanned for PII / secrets before being returned to users?
- Is there output filtering for patterns like SSN, credit card numbers, API keys?
- Are structured outputs (JSON) validated to ensure no extra sensitive fields are included?

### 3. Logging & Observability Leakage
- Are full prompts (including user PII) written to application logs?
- Are LLM API request/response bodies logged unredacted?
- Do tracing tools (LangSmith, Langfuse, Helicone) receive sensitive data without masking?
- Are logs stored with appropriate retention limits and access controls?

### 4. Vector Database / RAG Leakage
- Are documents with different sensitivity levels stored in the same vector namespace?
- Can a user retrieve another user's embedded documents via semantic similarity queries?
- Is metadata (author, classification, customer ID) stored alongside embeddings and returned in results?
- Are embeddings reversible — could an attacker reconstruct source text from vectors?

### 5. Fine-Tuning Data Exposure
- Does the training dataset contain PII that the model could memorize and reproduce?
- Are training files (JSONL, CSV) stored with appropriate access controls?
- Is there a data anonymization / pseudonymization step before fine-tuning?
- Are synthetic data generation processes validated to not reconstruct real records?

### 6. Cross-User Data Contamination
- Is conversation history / memory isolated per user and per session?
- Can a user's data appear in another user's context through shared caches or memory stores?
- Are multi-tenant deployments namespaced correctly at the data layer?

### 7. Regulatory Compliance Signals
- GDPR: Is there a lawful basis for processing personal data through an LLM?
- CCPA: Are California residents' data sent to third-party LLM providers disclosed?
- HIPAA: Is PHI transmitted to or processed by LLMs covered under BAA agreements?

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **Data Type**: (e.g., PII — Email, PHI, Financial, API Key)
3. **Leakage Path**: Where data enters and where it can escape
4. **Location**: file:line or component name
5. **What's wrong**: The specific leakage scenario and its impact
6. **Remediation**: Code fix, redaction pattern, or architectural change

End with a **Data Flow Risk Summary** — map of sensitive data flows with SAFE / AT-RISK / LEAKING status per path, and a compliance gap list.
