---
name: appsec-mcp-server-hardener
description: Full security audit of MCP (Model Context Protocol) server implementations. Reviews authentication, authorization, tool scope enforcement, input/output validation, transport security, and rate limiting. Covers the MCP 2025-03 spec authorization requirements. Replaces manual MCP security gateway configuration reviews.
---

Perform a comprehensive security audit of the MCP server implementation in the specified files or configuration.

## Audit Scope

### 1. Authentication & Identity
- Does the MCP server require authentication before exposing tools?
- Is the server identity verifiable — does it present a signed manifest or well-known endpoint?
- Are API keys / bearer tokens validated on every request, not just at connection init?
- Is there protection against server impersonation (a malicious server claiming to be a trusted one)?
- Are client identities (which agent/user is calling) verified and logged?

### 2. Authorization & Tool Scope (MCP Auth Spec — 2025-03)
- Does the server implement OAuth 2.0 authorization code flow with PKCE for user-delegated access?
- Are tool call permissions scoped — does the client need explicit consent to call each tool?
- Is there a minimal-scope principle — tools are only exposed when the session context requires them?
- Are `tools/list` responses filtered based on the caller's authorized scope?
- Is the `authorization_server` metadata endpoint present and correctly configured?
- Are refresh tokens rotated on use and invalidated on logout?

### 3. Tool Definition Security
- Are tool `inputSchema` definitions strict — no `additionalProperties: true`, no untyped fields?
- Do tool descriptions contain only functional documentation, no instructions to the LLM model?
- Are tool names unique and non-ambiguous — no shadowing of other registered tools?
- Is there a registry/allowlist of approved tool names that the server enforces?
- Are destructive tools (write, delete, execute) marked and gated behind explicit user confirmation?

### 4. Input Validation on Tool Calls
- Are all tool call arguments validated against the declared `inputSchema` before execution?
- Is there path traversal prevention on any tool that accepts file paths?
- Is there command injection prevention on any tool that wraps shell commands?
- Are numeric bounds enforced (max file size, max query length, max loop iterations)?
- Are cross-tool argument injection attacks prevented (data from tool A cannot control tool B)?

### 5. Transport Security
- Is the MCP transport using HTTPS / WSS — not plain HTTP or WS?
- Are TLS certificates validated (no `verify=False`, no self-signed in production)?
- Is CORS configured restrictively — only trusted origins allowed for HTTP transport?
- Are Streamable HTTP responses (SSE) protected against SSRF via server-initiated connections?

### 6. Rate Limiting & Abuse Prevention
- Is there per-client rate limiting on tool calls?
- Is there a maximum concurrent sessions limit?
- Are there protections against tool call flooding that could cause cost DoS on upstream LLM APIs?
- Is there a circuit breaker for tools that call expensive external services?

### 7. Secrets & Credential Handling
- Are credentials for downstream services (DB, APIs) stored in environment variables, not in tool definitions?
- Are tool call results sanitized to remove credentials before being returned to the LLM?
- Is there secret scanning on tool output to prevent accidental key leakage back to the model?

### 8. Audit Logging
- Is every tool call logged with: caller identity, tool name, input args (redacted), timestamp, result status?
- Are authorization failures (denied tool calls) alerted on?
- Is the audit log append-only and tamper-evident?

## MCP Authorization Spec Compliance Checklist

```
[ ] /.well-known/oauth-authorization-server metadata endpoint present
[ ] Authorization code flow with PKCE implemented (S256 method)
[ ] Token endpoint validates client_id and redirect_uri strictly
[ ] Access tokens are short-lived (≤1 hour)
[ ] Refresh token rotation enabled
[ ] tools/list filtered by OAuth scope
[ ] User consent screen shown before delegating tool access
[ ] Token introspection or JWT verification on every tool call
[ ] Scopes follow least-privilege (read:files not files:*)
```

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **Category**: (e.g., Missing Auth, Overpermissioned Tool, No Input Validation)
3. **Location**: file:line or endpoint path
4. **Attack Scenario**: What an attacker could do if this is exploited
5. **Remediation**: Fixed code or configuration

End with an **MCP Server Security Scorecard** — pass/fail across all 8 categories, and a hardened `server.json` / config snippet.
