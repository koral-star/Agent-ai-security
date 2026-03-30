---
name: secure-review
description: Deep security review of AI-generated code. Reviews a file or code snippet for OWASP Top 10, LLM/AI-specific vulnerabilities (prompt injection, tool poisoning, RAG injection), hardcoded secrets, and insecure patterns. Provides remediation guidance.
---

Perform a comprehensive security review of the specified file or code.

## Review Scope

### 1. AI/LLM-Specific Vulnerabilities (OWASP LLM Top 10)
- **Prompt Injection**: Is user input inserted into prompts without sanitization? Check for direct and indirect injection paths
- **Insecure Output Handling**: Are LLM outputs used in dangerous contexts (SQL, shell, HTML) without validation?
- **Training Data Poisoning**: Are there unsanitized inputs to fine-tuning pipelines?
- **Model Denial of Service**: Are there unbounded token inputs or recursive prompt patterns?
- **Supply Chain**: Are model sources, versions, and integrity checks specified?
- **Sensitive Information Disclosure**: Can the LLM be made to leak training data or system prompts?
- **Insecure Plugin Design**: If tools/plugins are registered, do they validate inputs and restrict permissions?
- **Excessive Agency**: Does the agent have more permissions/tools than it needs?
- **Overreliance**: Is LLM output used in critical decisions without human oversight or validation?
- **Model Theft**: Are inference endpoints properly authenticated and rate-limited?

### 2. RAG-Specific Threats
- Is retrieved context inserted into prompts raw, without sanitization?
- Is the vector database access authenticated and scoped?
- Can an attacker poison the knowledge base?
- Are embeddings validated before insertion?

### 3. Agentic / Tool Use Threats
- Are tool outputs validated before being acted upon (tool poisoning)?
- Is there privilege separation between tools?
- Can an agent be made to call destructive tools via injected instructions?
- Are MCP tool call inputs validated server-side?

### 4. Classic Security Issues
- **Injection**: SQL, command, LDAP, XPath injection
- **Secrets**: Hardcoded passwords, API keys, tokens
- **Crypto**: MD5/SHA1, weak random, missing TLS verification
- **Deserialization**: pickle.loads, yaml.load (unsafe), JSON with eval
- **Path Traversal**: Unvalidated file paths from user input
- **SSRF**: HTTP requests to user-controlled URLs
- **XSS**: Unescaped output in HTML context
- **CORS**: Wildcard or overly permissive origins
- **Debug flags**: debug=True, verbose logging of sensitive data

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **Vulnerability Type**: (e.g., Prompt Injection — LLM01)
3. **Location**: file:line
4. **What's wrong**: Explain the specific risk
5. **Remediation**: Provide the corrected code snippet

End with a summary table of all findings and an overall security risk rating.

If no issues are found, confirm the code is clean and note any security-positive patterns observed.
