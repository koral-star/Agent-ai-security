# STRIDE Threat Model — Ella AI Banking OS

## System Overview

Ella AI Banking OS is a bank-grade operating layer that gives external apps, LLM agents (ChatGPT, Claude), partner systems, and customer-built agents governed access to financial data, banking intelligence, and safe banking action execution.

### Architecture

```
[User Apps / LLM Agents / Partner Systems / Customer-built Agents]
              │
        [Access Gateway]
              │
   [WAF + quotas + abuse controls]
              │
   [OAuth / OIDC / financial-grade auth]
              │
   [Consent + entitlements + authorization]
              │
   [PII minimization + input guard + fraud/risk]
              │
       [Capability Gateway]
      ┌───────┼────────────────┐
      │       │                │
[Deterministic  [Intelligence  [Guided journeys    [ask_ella
  reads]          APIs]         + safe actions]    agentic planner]
      │              │               │                    │
[Personal      [Features +    [Task / Action       [Approved
 Data Service]  Models]        Ledger]               Tools]
      │                            │
[Internal bank  [Workflow engine + execution adapters]
 systems / Core]
```

### Key Risk Surface
| Risk Area | Description |
|---|---|
| External LLM agent access | ChatGPT, Claude, and third-party copilots calling Ella via MCP/A2A |
| Customer-built agents | Unknown-quality agents with direct access to banking data and actions |
| ask_ella agentic planner | LLM-based planner invoking approved tools; susceptible to prompt injection |
| Personal Data JSON (PDJ) | All customer financial data in one structured object |
| Financial action execution | AI agents can propose and trigger transfers, loans, applications |
| Shared responsibility model | Ella owns data/action rails; external agents own outputs — blurred accountability |
| MCP tool-style access | LLMs call banking tools as function calls; hard to validate intent |
| A2A agent-to-agent | Agent chains where one external agent calls another via Ella |

---

## STRIDE Threat Table

| ID | Category | Threat | Affected Component | Impact | Risk | Mitigation |
|---|---|---|---|---|---|---|
| **S1** | Spoofing | **External agent impersonation** — malicious app claims to be an approved partner agent (ChatGPT/Claude tool) to gain higher-trust access tier | Access Gateway + OAuth | Unauthorized access to sensitive banking capabilities beyond approved scope | **Critical** | OAuth 2.0 client credentials with per-client scopes; signed client assertions; Exposure Profiles bound to verified client identity; no shared credentials between agents |
| **S2** | Spoofing | **Customer-built agent spoofs first-party Ella app** — customer-built agent presents itself as the bank's official app to bypass partner-tier restrictions | Access Gateway auth layer | Bypasses restrictions on sensitive actions (e.g., high-value transfers) reserved for first-party only | **High** | First-party app uses hardware-backed attestation or signed tokens; strict client_id segregation between first-party and customer-built; API gateway enforces client type |
| **S3** | Spoofing | **A2A agent identity spoofing** — one external agent impersonates another in agent-to-agent flows to gain delegated permissions | A2A integration surface | Privilege escalation via trusted agent chain; unauthorized actions in delegated context | **High** | Agent-to-agent calls require cryptographically signed agent identity tokens; receiving agent must verify caller identity before honoring delegated scope |
| **S4** | Spoofing | **OAuth token theft from compromised external agent** — attacker extracts OAuth token from a customer-built or partner agent to impersonate the customer | OAuth / OIDC layer | Full customer financial data access; unauthorized financial actions | **Critical** | Short-lived access tokens (max 15 min); refresh token rotation; token binding to client TLS certificate (DPoP); anomaly detection on token usage patterns |
| **S5** | Spoofing | **Prompt injection spoofing Ella identity** — malicious content in external data (e.g., a transaction memo) causes ask_ella to believe it received an instruction from a trusted source | ask_ella agentic planner + tool execution | ask_ella executes unauthorized actions believing they were user-approved | **Critical** | Strict separation of system prompt (trusted) vs. data plane (untrusted); input guard scans all data fetched by ask_ella before it enters the planner context; never execute instructions found in retrieved data |
| **T1** | Tampering | **Prompt injection manipulating ask_ella tool selection** — attacker embeds instructions in a document, email, or transaction description that ask_ella retrieves, causing it to invoke unauthorized tools or actions | ask_ella planner + Capability Gateway | Unauthorized action execution (e.g., transfer triggered by injected instruction) | **Critical** | Input guard on all data ingested by ask_ella; tool invocations require explicit user approval step for action-class tools; tool call logging with anomaly detection |
| **T2** | Tampering | **Capability Gateway request tampering** — attacker intercepts and modifies API requests between client and Capability Gateway to access capabilities beyond their Exposure Profile | Capability Gateway + Exposure Profiles | Unauthorized access to sensitive capabilities (e.g., intelligence APIs, action triggers) | **High** | HTTPS/TLS for all channels; Capability Gateway validates request scope against Exposure Profile server-side; signed requests for action-class APIs |
| **T3** | Tampering | **Provenance bundle falsification** — attacker or buggy external agent modifies the provenance bundle to misrepresent data source, freshness, or confidence score | Response / Delivery layer (provenance bundle) | Customer makes financial decision based on falsified data provenance; regulatory misrepresentation | **High** | Provenance bundle generated and signed by Ella OS server-side; clients MUST NOT be able to modify it; consumer-side signature verification |
| **T4** | Tampering | **Action intent parameter manipulation** — external agent modifies action intent (e.g., transfer amount, beneficiary IBAN) between ask_ella output and execution adapter | Guided journeys + Execution adapters | Unauthorized financial transaction; funds transferred to wrong beneficiary | **Critical** | Action intents cryptographically committed (signed) at ask_ella output; execution adapter verifies signature before execution; re-confirm with customer on amount + beneficiary before any transfer |
| **T5** | Tampering | **Malicious open banking data injection** — attacker injects manipulated data through open banking / external financial data feeds to corrupt the Personal Data Service | Personal Data Service + open banking feed | Incorrect customer financial model; skewed intelligence outputs; wrong loan/offer eligibility | **High** | Validate and normalize all open banking data at ingestion; schema validation + anomaly detection on external feed values; flag outliers for human review |
| **T6** | Tampering | **Policy rules store tampering** — unauthorized modification of `policy/tariff/product rules store` to change fee structures, limits, or eligibility rules | Knowledge + Policy layer | Customers given incorrect fee/policy information; regulatory non-compliance | **High** | Strict write access controls (admin role only); version-controlled policy store with immutable history; changes require approval workflow; audit log on every policy change |
| **R1** | Repudiation | **External agent denies initiating a financial action** — partner or customer-built agent triggers a transfer/loan; later denies authorization when disputed | Task / Action Ledger | Financial disputes; no proof of which agent triggered the action | **High** | Task/Action Ledger records: agent client_id, user identity, action type, parameters, timestamp, and agent OAuth token hash; records MUST be immutable |
| **R2** | Repudiation | **Customer denies approving AI-proposed action** — customer claims they never approved a transfer that an AI agent proposed and executed | Human approval flow + audit trail | Financial and legal dispute; bank liability | **Critical** | Explicit customer approval step for all action-class operations; approval event logged with: customer identity, device fingerprint, timestamp, action parameters, confirmation method (biometric/PIN); approval cannot be delegated to external agent |
| **R3** | Repudiation | **ask_ella reasoning steps not auditable** — agentic planner's tool selection and multi-step reasoning are not persisted, making it impossible to reconstruct why an action was taken | ask_ella planner | Cannot investigate wrong or harmful AI decisions; regulatory audit failure | **High** | Log all ask_ella tool calls: tool name, input parameters, output, timestamp, conversation ID; persist full planning trace for action-class outcomes; retain for regulatory minimum period |
| **R4** | Repudiation | **Consent record ambiguity for data shared with external agents** — customer disputes that they consented to sharing financial data with a third-party agent | Consent + entitlements layer | Privacy/GDPR dispute; regulatory breach | **High** | Consent records MUST be immutable, timestamped, and include: customer ID, agent client_id, scope of data shared, consent method; revocation events also logged |
| **I1** | Information Disclosure | **PDJ (Personal Data JSON) leakage to LLM context** — entire PDJ sent to external LLM (ChatGPT/Claude) context window; LLM provider stores conversation logs | Personal Data Service → LLM apps | Full financial profile exposed to third-party LLM provider; GDPR/PSD2 breach | **Critical** | Apply PII minimization before sending data to external LLMs; send only fields required to answer the specific query; never send full PDJ to external agent context; data residency controls |
| **I2** | Information Disclosure | **PII in MCP tool responses visible to external LLM** — balance, transaction history, or loan data returned by Ella MCP tool is visible in the external LLM's context and potentially logged by LLM provider | MCP tool responses | Customer PII stored/processed by external LLM provider without customer awareness | **Critical** | Field-level PII tagging; PII minimization middleware strips unnecessary fields from MCP responses; customer consent required for each data category shared via MCP; contractual data processing agreements with LLM providers |
| **I3** | Information Disclosure | **Provenance bundle reveals internal architecture** — provenance bundle exposes internal service names, data source identifiers, model versions, or system topology | Response / Delivery layer | Internal architecture disclosure; aids attacker reconnaissance | **Medium** | Sanitize provenance bundle before delivery: use external-facing labels (e.g., "banking data" not "Personal Data Service v2.3"); strip internal service names and model IDs |
| **I4** | Information Disclosure | **Intelligence API outputs expose customer behavioral scoring** — forecasting, anomaly detection, or segmentation outputs reveal sensitive internal risk/credit scoring | Intelligence APIs (E3) | Privacy breach; customer profiling data exposure; regulatory concern (GDPR automated decision-making) | **High** | Do not expose raw model scores or segment labels externally; return only actionable outputs (e.g., "your spending is above average this month" not the segment percentile); GDPR Article 22 compliance for automated decisions |
| **I5** | Information Disclosure | **Capability Catalog enumeration** — external agent probes Capability Catalog to enumerate all available banking capabilities beyond their authorized scope | Capability Catalog + Versioning | Attacker maps full banking API surface; enables targeted attacks | **Medium** | Capability Catalog returns only capabilities the caller's Exposure Profile permits; no capability metadata returned for unauthorized scopes; rate limit catalog queries |
| **I6** | Information Disclosure | **A2A agent chain over-sharing** — agent A shares data with agent B via A2A without verifying B's data entitlements; data propagates beyond original consent | A2A integration surface | Data shared with unauthorized downstream agent; consent violation | **High** | Each A2A hop must independently verify data entitlements; data MUST carry consent tags; downstream agent must re-verify consent before using tagged fields |
| **D1** | Denial of Service | **External agent API flooding** — compromised or malicious external agent floods deterministic reads (balance, transactions) exhausting Ella OS | Access Gateway + Ella service surfaces | Service unavailability for legitimate users; financial data access disruption | **High** | Per-client quotas and rate limits enforced at Access Gateway; WAF rules for abnormal request patterns; automatic client suspension on threshold breach |
| **D2** | Denial of Service | **ask_ella runaway agent loop** — external agent crafts input that causes ask_ella to enter an infinite tool-call loop, exhausting tool quota and compute | ask_ella planner | Compute exhaustion; cost escalation; service unavailability | **High** | Max tool call depth and count per ask_ella session; session timeout; circuit breaker on tool call frequency; cost cap per agent client |
| **D3** | Denial of Service | **Task/Action Ledger flooding** — malicious agent submits thousands of action intents (transfers, alerts) overwhelming the ledger and workflow engine | Task / Action Ledger + Workflow engine | Action processing delays for all customers; ledger write contention | **High** | Per-agent action submission rate limits; max pending actions per customer; action intent queue with backpressure |
| **D4** | Denial of Service | **Subscription / notification spam** — customer-built agent creates thousands of alert subscriptions, overwhelming the notification delivery system | Subscriptions / proactive notifications | Notification system unavailability; customer alert fatigue; cost | **Medium** | Max active subscriptions per customer per agent; subscription creation rate limit; admin ability to purge runaway subscriptions |
| **D5** | Denial of Service | **Intelligence API abuse for model extraction** — external agent systematically queries forecasting/scoring APIs with crafted inputs to extract model behavior | Intelligence APIs (Features + Models) | Model intellectual property theft; cost; potential model inversion attack | **Medium** | Rate limit intelligence API queries per client; detect systematic parameter sweeping patterns; add response perturbation for non-deterministic outputs |
| **E1** | Elevation of Privilege | **External agent scope escalation** — agent approved for read-only data access attempts to invoke action-class capabilities (transfers, loan applications) | Capability Gateway + Exposure Profiles | Unauthorized financial action execution | **Critical** | Capability Gateway enforces Exposure Profile on every request; action-class APIs require explicit `actions` scope in OAuth token; scope cannot be self-elevated by client |
| **E2** | Elevation of Privilege | **Cross-customer PDJ access** — customer-built or partner agent accesses the Personal Data JSON of a different customer by manipulating the customer identity parameter | Personal Data Service | Full financial profile of another customer exposed; severe privacy breach | **Critical** | All PDJ queries MUST be bound to the authenticated customer's identity from OAuth token; no client-supplied customer ID honored for data access; server-side identity binding |
| **E3** | Elevation of Privilege | **Prompt injection causes ask_ella to invoke unauthorized tools** — injected instruction in retrieved data causes ask_ella to call a tool it shouldn't (e.g., transfer tool instead of read tool) | ask_ella + Capability Gateway | Unauthorized financial action triggered without user intent | **Critical** | Tool invocation whitelist per session based on user-granted scope; action-class tools REQUIRE explicit user confirmation regardless of planner intent; input guard on all planner inputs |
| **E4** | Elevation of Privilege | **Bypassing human approval flow for high-value actions** — external agent exploits a race condition or API quirk to execute a high-value action without triggering the human approval step | Human approval / banker handoff layer | Unauthorized high-value financial transaction | **Critical** | Human approval is server-side enforced (not client-side); action limits define threshold above which approval is always required; approval cannot be skipped by any client type; re-verify approval token before execution |
| **E5** | Elevation of Privilege | **Partner agent exceeds Exposure Profile permissions** — partner agent calls capabilities not in its Static Route Pack by probing undocumented endpoints | Exposure Profiles + Static Route Packs | Partner accesses capabilities beyond contractual agreement; data/action breach | **High** | Exposure Profiles enforced at Capability Gateway (deny by default); all requests validated against route pack; alert on unauthorized capability access attempts |
| **E6** | Elevation of Privilege | **LLM output used directly as financial decision** — external agent passes LLM-generated text (not Ella-structured output) as a financial decision without provenance verification | Guided journeys + action execution | Financial action based on hallucinated or manipulated LLM output | **Critical** | Actions MUST only be executed from Ella-structured, signed action intents; free-form LLM text MUST NOT be accepted as an action trigger; output validation at execution layer |

---

## Security Requirements

### SR-AUTH — Authentication & Authorization

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-AUTH-1 | All clients MUST authenticate via OAuth 2.0 / OIDC with per-client scopes. Scopes MUST be minimally privileged (read-only by default; actions scope requires explicit grant). | Critical | S1, E1 |
| SR-AUTH-2 | OAuth access tokens MUST be short-lived (max 15 minutes). Refresh tokens MUST rotate on use. Token binding to client TLS certificate (DPoP) MUST be implemented for action-class scopes. | Critical | S4 |
| SR-AUTH-3 | First-party apps MUST use hardware-backed attestation tokens. Customer-built agents MUST use a separate client_id tier with restricted capabilities. | High | S2 |
| SR-AUTH-4 | A2A agent calls MUST include a signed agent identity token. Receiving agents MUST verify the caller's identity and scope before honoring delegated permissions. | High | S3, I6 |
| SR-AUTH-5 | Customer identity for all data access MUST be extracted from the authenticated OAuth token. No client-supplied customer/portfolio ID MUST be trusted for data retrieval. | Critical | E2 |
| SR-AUTH-6 | Capability Gateway MUST validate every request against the caller's Exposure Profile and OAuth scopes. Deny by default; only explicitly permitted capabilities are accessible. | Critical | E1, E5 |

---

### SR-AGENT — AI Agent Safety & Prompt Injection Prevention

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-AGENT-1 | ask_ella MUST strictly separate the system prompt (trusted, bank-controlled) from the data plane (untrusted, from retrieval). Instructions found in retrieved data MUST NEVER be executed. | Critical | S5, T1, E3 |
| SR-AGENT-2 | All data ingested by ask_ella (retrieved documents, transaction memos, external content) MUST pass through an input guard that detects prompt injection patterns before entering the planner context. | Critical | S5, T1 |
| SR-AGENT-3 | ask_ella MUST enforce a maximum tool call depth and per-session tool call count. Sessions exceeding limits MUST be terminated with an alert. | High | D2 |
| SR-AGENT-4 | Action-class tool invocations by ask_ella MUST always require an explicit customer approval step. The planner MUST NOT be able to bypass this step regardless of instruction source. | Critical | T1, E3, E4 |
| SR-AGENT-5 | All ask_ella tool calls MUST be logged (tool name, parameters, output, timestamp, session ID). Planning traces for action-class outcomes MUST be persisted for the regulatory retention period. | High | R3 |
| SR-AGENT-6 | Free-form LLM-generated text MUST NOT be accepted as a financial action trigger. Only Ella-structured, server-signed action intents MUST be executable. | Critical | E6 |

---

### SR-DATA — Data Protection & PII Minimization

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-DATA-1 | PII minimization MUST be applied before sending any customer data to external LLMs via MCP. Only fields required to answer the specific query MUST be included. The full PDJ MUST NEVER be sent to an external LLM context. | Critical | I1, I2 |
| SR-DATA-2 | All PII fields in API responses MUST be tagged at the schema level. PII minimization middleware MUST strip untagged/unauthorized fields per client Exposure Profile. | Critical | I1, I2 |
| SR-DATA-3 | Data shared via A2A MUST carry consent tags. Downstream agents MUST re-verify consent for each tagged field before use. | High | I6, R4 |
| SR-DATA-4 | Intelligence API outputs MUST return actionable insights only (e.g., "above average spending") — never raw model scores, segment labels, or percentiles. | High | I4 |
| SR-DATA-5 | Provenance bundles MUST be sanitized before delivery: internal service names, model IDs, and system topology MUST be replaced with external-facing labels. | Medium | I3 |
| SR-DATA-6 | Customer consent for each data category shared with external agents MUST be explicitly collected, stored immutably, and revocable at any time. | Critical | R4, I1, I2 |

---

### SR-ACTION — Safe Financial Action Execution

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-ACTION-1 | Action intents MUST be cryptographically signed by Ella OS at the point of generation. Execution adapters MUST verify the signature before executing any action. | Critical | T4, E6 |
| SR-ACTION-2 | Human approval MUST be server-side enforced for all action-class operations. The approval threshold (e.g., transfer amount) MUST be configurable. No client MUST be able to skip this step. | Critical | E4, R2 |
| SR-ACTION-3 | Customer approval events MUST be logged with: customer identity, device fingerprint, timestamp, action parameters, and confirmation method (biometric/PIN). These logs MUST be immutable. | Critical | R2 |
| SR-ACTION-4 | Action policy + limits MUST define per-action-type daily/monthly maximums. Limits MUST be enforced server-side and not overridable by external agents. | High | E1, D3 |
| SR-ACTION-5 | The Task/Action Ledger MUST record: agent client_id, user identity, action type, parameters, timestamp, and approval reference for every action. Records MUST be immutable. | High | R1 |

---

### SR-AUDIT — Audit, Logging & Non-Repudiation

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-AUDIT-1 | All management API write operations (policy changes, Exposure Profile changes, agent registration) MUST be logged with actor identity, before-value, after-value, and timestamp. | High | T6, R1 |
| SR-AUDIT-2 | Consent records MUST be immutable and include: customer ID, agent client_id, data scope, consent method, and timestamp. Revocation events MUST also be logged. | High | R4 |
| SR-AUDIT-3 | All audit logs MUST be stored in a separate, append-only store inaccessible to application services. | High | R1, R2, R3 |
| SR-AUDIT-4 | Unauthorized capability access attempts MUST generate security alerts in real time. Repeated attempts MUST trigger automatic client suspension. | High | E5 |

---

### SR-RATE — Rate Limiting & Abuse Prevention

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-RATE-1 | Per-client API quotas MUST be enforced at the Access Gateway. Quotas MUST be differentiated by client type (first-party vs. partner vs. customer-built). | High | D1 |
| SR-RATE-2 | Intelligence API queries MUST be rate limited per client. Systematic parameter-sweep patterns MUST trigger anomaly alerts. | Medium | D5 |
| SR-RATE-3 | Per-customer subscription/alert creation MUST be capped (max N active subscriptions per agent). | Medium | D4 |
| SR-RATE-4 | Action intent submission MUST be rate limited per agent client and per customer. | High | D3 |

---

### SR-SUPPLY — Third-Party Agent Supply Chain

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-SUPPLY-1 | All external agents accessing Ella via MCP, API, or A2A MUST be registered and approved. Unregistered agents MUST be rejected at the Access Gateway. | Critical | S1, S2 |
| SR-SUPPLY-2 | LLM provider contracts (e.g., OpenAI, Anthropic) MUST include data processing agreements that prohibit training on customer financial data and require data deletion after session. | Critical | I1, I2 |
| SR-SUPPLY-3 | Customer-built agents MUST be sandboxed: they MUST only access data and capabilities their Exposure Profile explicitly grants; no lateral access to other customers' data. | Critical | E2 |
| SR-SUPPLY-4 | Ella MUST publish a Trust & Safety policy for external agents, defining prohibited behaviors and the consequences (suspension, revocation). | High | S1, S3 |
