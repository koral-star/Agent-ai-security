---
name: appsec-mcp-oauth-reviewer
description: Reviews OAuth 2.0 authorization flows in MCP server and client implementations against the MCP 2025-03 auth specification. Checks PKCE enforcement, token lifecycle, scope validation, redirect URI binding, and consent flows. Identifies auth bypasses, token leakage, and spec non-compliance that allow unauthorized tool access.
---

Review the OAuth 2.0 / authorization implementation in the MCP server or client code specified.

## Review Scope

### 1. Authorization Code Flow + PKCE (Required by MCP Spec)
- Is the authorization code flow implemented (not implicit flow or client_credentials for user-delegated access)?
- Is PKCE enforced with `code_challenge_method=S256` — not plain, not optional?
- Is the `code_verifier` generated with sufficient entropy (≥32 bytes of random data)?
- Is the `code_challenge` bound to the authorization request and verified at token exchange?
- Is the `state` parameter used and validated to prevent CSRF on the authorization callback?

### 2. Token Security
- Are access tokens short-lived (recommended ≤1 hour for MCP sessions)?
- Are refresh tokens rotated on every use (rotation prevents token replay)?
- Are tokens stored securely on the client — not in localStorage, not in URL params, not in logs?
- Are tokens transmitted only over HTTPS?
- Is token revocation supported and called on session end / logout?
- Are JWT access tokens validated for signature, expiry, issuer, and audience on every tool call?

### 3. Client Registration & Redirect URI Security
- Is Dynamic Client Registration (DCR) used, and if so, are client metadata validated server-side?
- Are redirect URIs strictly bound to registered values — no open redirectors, no wildcard matching?
- Is `client_id` validated on the token endpoint to prevent client impersonation?
- For public clients (CLI agents), is PKCE the sole proof-of-possession mechanism?

### 4. Scope & Consent
- Are scopes granular — one scope per tool or tool category (e.g., `files:read`, `calendar:write`)?
- Is a user consent screen shown for each scope being requested?
- Are previously granted scopes cached and re-shown on scope upgrade requests?
- Can a client request broader scopes than the user has consented to?
- Are admin/privileged scopes protected by step-up authentication?

### 5. Authorization Server Security
- Is the `/.well-known/oauth-authorization-server` or `/.well-known/openid-configuration` endpoint present and correct?
- Are authorization server metadata values (issuer, endpoints) validated by the client before use?
- Is there protection against authorization server metadata injection (attacker replaces the well-known document)?
- Is the issuer `iss` claim in tokens verified against the expected authorization server?

### 6. Common OAuth Attack Patterns
- **Authorization Code Interception**: Is PKCE enforced end-to-end with no fallback to no-PKCE?
- **Token Leakage via Referrer**: Is the `Referrer-Policy: no-referrer` header set on auth pages?
- **Mix-Up Attack**: Does the client verify the `iss` parameter on the authorization response?
- **CSRF on Callback**: Is the `state` parameter validated before processing the auth code?
- **Open Redirect**: Are redirect URIs exact-matched, not prefix-matched?
- **Token Substitution**: Are tokens bound to the session that requested them?

### 7. MCP-Specific Auth Patterns
- Is the authorization flow triggered before any `tools/call` request?
- Does the MCP client include the access token in the `Authorization: Bearer` header on each request?
- Is there a mechanism for the MCP server to trigger re-authorization when a token expires mid-session?
- Are tool-specific scopes checked per call, not just at session initiation?

## Vulnerable Code Patterns to Find

```python
# VULNERABLE: No PKCE
requests.get(auth_url + f"?client_id={id}&redirect_uri={uri}&response_type=code")

# VULNERABLE: state not validated
def callback(code, state):
    token = exchange_code(code)  # state ignored!

# VULNERABLE: Token in URL
redirect_uri = f"https://app.example.com/callback?token={access_token}"

# VULNERABLE: No expiry check
def call_tool(token, tool_name, args):
    headers = {"Authorization": f"Bearer {token}"}
    # No check if token is expired

# SAFER: Full PKCE flow
import secrets, hashlib, base64
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()
auth_url = build_auth_url(
    code_challenge=code_challenge,
    code_challenge_method="S256",
    state=secrets.token_urlsafe(16),
    scope="tools:read files:read"
)
```

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **OAuth Weakness**: (e.g., Missing PKCE, Open Redirect, No Token Rotation)
3. **Location**: file:line
4. **Attack**: How an attacker exploits this to gain unauthorized tool access
5. **Fix**: Corrected code or configuration

End with an **OAuth Compliance Matrix** — table showing compliance with MCP auth spec requirements, and a hardened authorization flow diagram (text).
