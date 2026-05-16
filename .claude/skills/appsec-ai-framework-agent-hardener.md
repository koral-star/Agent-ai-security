---
name: appsec-ai-framework-agent-hardener
description: Hardens AI framework and agent configurations. Audits LangChain, AutoGen, CrewAI, LlamaIndex, OpenAI Agents SDK, and similar frameworks for excessive permissions, insecure tool registration, missing guardrails, and unsafe agent patterns. Produces a hardened configuration with remediation steps.
---

Analyze and harden the AI framework and agent configuration in the specified file(s) or codebase.

## Audit Scope

### 1. Excessive Agency (OWASP LLM08)
- Does the agent have more tools/permissions than required for its task?
- Are destructive tools (file delete, shell exec, DB write) accessible without human-in-the-loop approval?
- Is there a minimum-privilege tool set defined per agent role?
- Can an agent spawn sub-agents or clone itself without bounds?

### 2. Tool / Plugin Security
- Are all registered tools validated for input types and value ranges?
- Can tool outputs be trusted, or could a malicious tool response hijack agent flow?
- Are tool call results sanitized before being fed back into the prompt (tool poisoning)?
- Are MCP tool schemas locked down — no wildcard permissions?

### 3. Agent Loop & Recursion Limits
- Is there a maximum iteration / recursion depth configured?
- Is there a token budget enforced to prevent runaway cost and DoS?
- Can the agent be tricked into an infinite loop via injected instructions?

### 4. Memory & Context Security
- Is conversation memory (buffer, vector, entity) scoped per-user or per-session?
- Can previous conversation history leak cross-user via shared memory stores?
- Is long-term memory (vector DB) access authenticated and namespace-isolated?

### 5. System Prompt Hardening
- Is the system prompt stored securely (not client-side)?
- Does the system prompt include clear role boundaries and refusal instructions?
- Is the system prompt protected against override via user messages?
- Are sensitive instructions (API keys, internal logic) absent from the system prompt?

### 6. Framework-Specific Checks
- **LangChain**: `allow_dangerous_deserialization`, `verbose=True` leaking secrets, unguarded `PythonREPL` tool
- **AutoGen**: `human_input_mode=NEVER` on sensitive flows, unconstrained `code_execution_config`
- **CrewAI**: Agent `allow_delegation` without scope limits, `tools` with no input validation
- **LlamaIndex**: `SimpleDirectoryReader` on untrusted paths, unfiltered metadata in context
- **OpenAI Agents SDK**: Missing `output_type` schema validation, unbounded tool loops

### 7. Observability & Audit Trail
- Are all agent actions (tool calls, decisions, outputs) logged with user context?
- Is there alerting on anomalous tool call patterns?
- Are logs free of sensitive data (PII, secrets, full prompts)?

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **Category**: (e.g., Excessive Agency, Tool Poisoning, Memory Leak)
3. **Framework / Component**: Where in the agent setup the issue lives
4. **What's wrong**: Explain the specific risk and attack scenario
5. **Hardened config**: Provide the corrected code or configuration snippet

End with a **Hardening Checklist** — a table of all items showing PASS / FAIL / N/A, and an overall agent security posture rating.
