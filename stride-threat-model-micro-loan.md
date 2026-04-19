# STRIDE Threat Model — Micro-Loan System

## System Overview

A new micro-loan flow triggered during fund transfers. Mobile calls `getMicroLoanOffer` to check eligibility; if the transfer amount is below the offer, the customer can choose monthly installments. The rule engine is invoked with `NEW_MICRO_LOAN` application type to compute the offer, and the loan is created after installment selection.

### Components

```
[Mobile] ──> [Credit-limit-service] ──> [Credit-decisions-service]
                                                  │
                                    [Credit-limit-decision-service]
                                                  │
                                       [Blaze Communicator]
                                                  │
                                          [Rule Engine]

[DWH] ──(AutomaticCalculation event)──> [Credit-limit-service] ──> [Postgres DB]
[Loan Service] ──> [Postgres DB]
```

### Key Risk Areas
| Risk Area | Description |
|---|---|
| Removed daily loan limit | `validateAgainstRecentLoanCreationRequest` disabled |
| READY_FOR_DISBURSEMENT loans sent to rule engine | New loan state included in rule engine context |
| Idempotency key change | session-id → process-id (migration in progress, TBD with mobile) |
| Hidden microLoan purpose | `display_order < 0` hides purpose from customer; UUID exposed in API |
| Widget threshold moved to platform | 50,000₪ eligibility logic moved from rule engine to credit-limit-service |
| Bureau Derivations exposure | Fast amount in `getMicroLoanOffer` derived from credit report data |
| `recalculateAutomaticOffer` new API | Cancels previous calculation and starts new one after each loan approval |

---

## STRIDE Threat Table

| ID | Category | Threat | Affected Component | Impact | Risk | Mitigation |
|---|---|---|---|---|---|---|
| **S1** | Spoofing | **portfolioId spoofing in getMicroLoanOffer** — attacker provides another customer's `portfolioId` to retrieve their Bureau Derivations fast amount and credit offer | `getMicroLoanOffer(portfolioId!)` | Financial data disclosure; enables higher-loan fraud | **Critical** | Server-side: `portfolioId` must match authenticated JWT token claims; reject any mismatch |
| **S2** | Spoofing | **Mobile client impersonation** — attacker calls `getMicroLoanOffer` directly (not from mobile app) with a crafted `portfolioId` | API Gateway → credit-limit-service | Unauthorized offer retrieval; credit data exposure | **High** | API key + JWT authentication; restrict endpoint to authenticated mobile sessions; consider client certificate pinning |
| **S3** | Spoofing | **Rule engine caller impersonation** — rogue internal service calls Blaze Communicator with forged `NEW_MICRO_LOAN` application type to obtain fraudulent offers | Blaze Communicator → Rule Engine | Fraudulent loan approval; financial loss | **Medium** | mTLS between services; allow-list of authorized callers; service identity tokens (SPIFFE/SPIRE) |
| **S4** | Spoofing | **DWH AutomaticCalculation event spoofing** — attacker injects fake events to credit-limit-service to trigger fraudulent offer recalculations | DWH → credit-limit-service | Incorrect credit limit stored in Postgres; higher loan amounts approved | **Medium** | Event signing (HMAC); validate event source identity; DWH-to-service authentication |
| **T1** | Tampering | **Loan amount exceeds offer amount** — customer manipulates the loan amount at creation time to exceed the fast offer returned by `getMicroLoanOffer` | Loan creation request | Over-lending beyond credit capacity; financial loss | **High** | Server stores offer server-side (not relying on client); re-validate amount ≤ stored offer at loan creation |
| **T2** | Tampering | **Race condition on multiple loans (removed daily limit)** — two concurrent requests submitted before `recalculateAutomaticOffer` fires, both approved beyond credit capacity | `LoanService` (disabled validation) | Multiple loans beyond credit limit; financial loss | **Critical** | Atomic check-and-create with DB optimistic locking; per-portfolio loan creation mutex; `recalculateAutomaticOffer` must complete before next loan is allowed |
| **T3** | Tampering | **READY_FOR_DISBURSEMENT status manipulation** — attacker delays or manipulates loan state update so loans are invisible to rule engine, making credit limit appear higher | Loan status query → rule engine | Excess credit granted; financial fraud | **High** | Authoritative loan status read from DB with row-level locking; rule engine queries via direct DB read, not client-provided state |
| **T4** | Tampering | **Idempotency key replay / manipulation** — during session-id → process-id migration, attacker reuses old session-based idempotency key to trigger duplicate loan creation | Loan creation idempotency logic | Duplicate loans; double financial commitment | **Critical** | Process-ID key tied to (portfolioId + amount + timestamp window); keys expire on loan state transition to ACTIVE; migration must be atomic (no overlap period) |
| **T5** | Tampering | **recalculateAutomaticOffer abuse** — repeated calls cancel ongoing calculations, preventing accurate credit limit from ever being set | `recalculateAutomaticOffer` in credit-limit-service | Credit limit never converges; customer offered excess amounts | **High** | Rate limit: max N calls per portfolio per hour; require caller authentication; async queue with deduplication |
| **T6** | Tampering | **Hidden microLoan purpose bypass** — attacker retrieves microLoan `purposeId` UUID (exposed in `getMicroLoanOffer` response) and uses it in a direct loan creation request, bypassing display-order filter | `getPurposesWithEligibilities`, loan-service | Unauthorized loan type; bypasses microLoan eligibility checks | **High** | Server-side purpose–flow binding: microLoan `purposeId` only valid with `NEW_MICRO_LOAN` application type; purpose eligibility enforced at loan creation, not only at display layer |
| **T7** | Tampering | **Widget threshold manipulation** — platform-side 50,000₪ threshold (moved from rule engine) configured without access control, allowing unauthorized change | credit-limit-service config (threshold) | Customers shown widget for ineligible amounts; take loans they cannot repay | **Medium** | Threshold in server-side config only; no API to modify at runtime without privileged role; audit all config changes |
| **R1** | Repudiation | **Customer denies multiple loans taken same day** — with removed daily limit, customer disputes second or third loan of the day | Loan audit records | Financial disputes; regulatory non-compliance | **High** | Immutable audit log per loan: portfolioId, amount, idempotency key, timestamp, loan status, actor; customer-facing loan history |
| **R2** | Repudiation | **No trace of recalculateAutomaticOffer caller** — internal actor cancels legitimate calculation; no record of who triggered it | credit-limit-service audit | Cannot investigate incorrect credit limit calculations; untraceable manipulation | **Medium** | Audit log every `recalculateAutomaticOffer` call: actor identity, timestamp, previous offer value, new offer value, reason |
| **R3** | Repudiation | **Rule engine NEW_MICRO_LOAN decision not persisted** — credit decisions made by rule engine for `NEW_MICRO_LOAN` not stored for regulatory traceability | Rule engine → credit-decisions-service | Regulatory breach (credit decision auditability required by law) | **High** | Persist rule engine input parameters + output + timestamp for every `NEW_MICRO_LOAN` calculation; retain for minimum regulatory retention period |
| **I1** | Information Disclosure | **Bureau Derivations fast amount exposed** — `getMicroLoanOffer` returns the fast amount derived from the customer's credit report (Bureau Derivations data), exposing internal credit assessment | `getMicroLoanOffer` response: `amount` field | Credit data exposure; GDPR / financial data regulation breach | **High** | Do not return raw Bureau Derivations amount; return only transfer-context-relevant eligibility or capped amount; consider eligibility flag + pre-approved amount, not raw credit score derivative |
| **I2** | Information Disclosure | **Internal UUIDs exposed** — `planId` and `purposeId` returned by `getMicroLoanOffer` reveal internal product configuration UUIDs | `getMicroLoanOffer` response | Internal product structure disclosure; enables T6 targeted attack | **Medium** | Use short-lived signed offer tokens instead of raw UUIDs; validate token on server-side at loan creation |
| **I3** | Information Disclosure | **Rule engine error message leakage** — failed `NEW_MICRO_LOAN` calculation returns detail exposing credit scoring thresholds or eligibility rules | Blaze Communicator / Rule Engine error responses | Customer learns internal credit criteria; enables gaming of loan applications | **Medium** | Generic error codes to client (e.g., `OFFER_UNAVAILABLE`); detailed errors logged server-side only |
| **I4** | Information Disclosure | **READY_FOR_DISBURSEMENT data over-sent to rule engine** — full loan record sent to rule engine exposes unnecessary PII across service boundary | Loan query → rule engine | Cross-service PII leak; data minimization violation | **Medium** | Send only required fields (loan amount, status) to rule engine; strip PII before cross-service calls |
| **D1** | Denial of Service | **getMicroLoanOffer spam on transfer screen** — attacker triggers many transfers to repeatedly invoke `getMicroLoanOffer`, exhausting credit-limit-service | credit-limit-service | Service unavailability for legitimate loan flows | **High** | Rate limit per portfolioId and per IP; cache offer with short TTL (e.g., 5 min per session); circuit breaker |
| **D2** | Denial of Service | **recalculateAutomaticOffer flooding** — mass calls keep canceling/restarting calculations, exhausting rule engine and DB | credit-limit-service + Rule Engine | Rule engine overload; no accurate credit limits; cascading DoS | **High** | Rate limit per portfolio; async queue with deduplication (ignore new request if one is already in-flight); circuit breaker to rule engine |
| **D3** | Denial of Service | **Concurrent loan creation storm (removed 1-loan limit)** — bot submits many micro loan requests simultaneously before recalculation fires | Loan creation endpoint + Postgres | DB lock contention; loan service exhaustion; financial loss | **Critical** | Per-portfolio in-flight loan creation lock; max concurrent micro loans per customer (e.g., 3/day); queue-based creation with concurrency control |
| **D4** | Denial of Service | **DWH event flooding** — flood of fake `AutomaticCalculation` events overwhelms credit-limit-service and Postgres write throughput | DWH → credit-limit-service → Postgres | Service degradation; incorrect credit limits saved | **Medium** | Event source authentication; rate limit event ingestion; dead-letter queue for overflow; event deduplication |
| **E1** | Elevation of Privilege | **Cross-portfolio getMicroLoanOffer** — customer substitutes another customer's `portfolioId` to retrieve a larger offer, then uses it in their own loan request | `getMicroLoanOffer(portfolioId!)` | Unauthorized loan at higher amount; financial fraud | **Critical** | JWT-bound portfolioId: server extracts portfolioId from token, ignores any client-supplied value; offer stored server-side against authenticated session |
| **E2** | Elevation of Privilege | **NEW_MICRO_LOAN without transfer context** — customer bypasses transfer-screen requirement and directly triggers `NEW_MICRO_LOAN` application type | Mobile → credit-decisions-service | Micro loan created without associated transfer; flow control bypass | **High** | Server-side: require valid pending transfer reference in loan request; transfer ID validated before `NEW_MICRO_LOAN` flow proceeds |
| **E3** | Elevation of Privilege | **Loan stacking via removed daily limit** — customer rapidly takes many micro loans before `recalculateAutomaticOffer` updates the credit limit | LoanService (disabled `validateAgainstRecentLoanCreationRequest`) | Over-leveraged customer; financial loss for bank; regulatory capital concern | **Critical** | Max micro loans per day per customer (configurable, even if > 1); total outstanding micro loan cap; synchronous offer recalculation before approving each subsequent same-day loan |
| **E4** | Elevation of Privilege | **microLoan purposeId used for regular loan** — customer uses the microLoan `purposeId` (retrieved from `getMicroLoanOffer`) to submit a large regular loan, bypassing normal eligibility | loan-service purpose validation | Higher loan than eligible; financial loss | **High** | Purpose–type binding enforced server-side: microLoan `purposeId` only accepted when `applicationType == NEW_MICRO_LOAN`; server rejects mismatched purpose/type combinations |
| **E5** | Elevation of Privilege | **Idempotency key collision during migration** — during session-id → process-id transition, attacker crafts a key matching another customer's in-flight loan | Idempotency key store | Loan linked to wrong customer; financial and data integrity breach | **High** | Idempotency key namespace includes portfolioId + customerId prefix; keys validated against authenticated session; no cross-customer key reuse possible by construction |

---

## Security Requirements

### SR-AUTH — Authentication & Authorization

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-AUTH-1 | `portfolioId` in all API requests MUST be extracted from the authenticated JWT token claims. Client-supplied `portfolioId` values MUST be ignored or validated against token claims. | Critical | S1, E1 |
| SR-AUTH-2 | All micro-loan APIs (`getMicroLoanOffer`, `recalculateAutomaticOffer`, loan creation) MUST require a valid JWT with appropriate scope. Unauthenticated calls MUST return 401. | Critical | S2 |
| SR-AUTH-3 | Service-to-service calls (BFF → credit-limit-service, credit-decisions-service → rule engine) MUST use mutual TLS (mTLS) and service identity tokens. | High | S3 |
| SR-AUTH-4 | `NEW_MICRO_LOAN` application type MUST only be accepted from authorized internal services. An allow-list of permitted callers MUST be enforced at the rule engine interface. | High | S3, E2 |
| SR-AUTH-5 | DWH `AutomaticCalculation` events MUST be authenticated via signed payloads or mutual TLS. Unsigned/unauthenticated events MUST be rejected. | Medium | S4 |
| SR-AUTH-6 | `recalculateAutomaticOffer` MUST require caller authentication and authorization (internal service role only; not callable by customers). | High | T5, R2 |

---

### SR-INPUT — Input Validation & Business Rule Enforcement

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-INPUT-1 | Loan amount at creation time MUST be re-validated server-side against the stored offer amount. The offer MUST be stored server-side and never re-supplied by the client. | High | T1 |
| SR-INPUT-2 | The microLoan `purposeId` MUST only be accepted at loan creation when `applicationType == NEW_MICRO_LOAN`. The server MUST reject mismatched purpose/type combinations. | High | T6, E4 |
| SR-INPUT-3 | All `NEW_MICRO_LOAN` loan requests MUST include a valid pending transfer reference. The server MUST validate the transfer exists and belongs to the authenticated customer before proceeding. | High | E2 |
| SR-INPUT-4 | The widget eligibility threshold (50,000₪) MUST be enforced server-side in credit-limit-service configuration only. No client input MUST influence this value. | Medium | T7 |
| SR-INPUT-5 | A maximum micro loan count per customer per day MUST be enforced server-side (even after removing the 1-loan limit). The value MUST be configurable. | Critical | E3, D3 |
| SR-INPUT-6 | Total outstanding micro loan balance per customer MUST be capped server-side. Each loan creation MUST check this cap before approval. | Critical | E3 |

---

### SR-IDEM — Idempotency & Concurrency Control

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-IDEM-1 | Idempotency keys for loan creation MUST be scoped to (portfolioId + customerId + amount + short timestamp window). Keys MUST expire after the loan reaches ACTIVE or REJECTED state. | Critical | T4 |
| SR-IDEM-2 | The migration from session-based to process-based idempotency keys MUST be atomic. Both key schemes MUST NOT be active simultaneously. | Critical | T4, E5 |
| SR-IDEM-3 | Idempotency key namespace MUST include portfolioId prefix to prevent cross-customer key collisions. | High | E5 |
| SR-IDEM-4 | Loan creation MUST use a DB-level atomic compare-and-create operation (optimistic or pessimistic locking) to prevent race conditions under concurrent requests. | Critical | T2, D3 |
| SR-IDEM-5 | If a loan is `READY_FOR_DISBURSEMENT`, it MUST be included in the rule engine context query before any new loan is approved for the same portfolio. This query MUST use a consistent read (not eventual consistency). | High | T3 |

---

### SR-RATE — Rate Limiting & Abuse Prevention

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-RATE-1 | `getMicroLoanOffer` MUST be rate limited per portfolioId (e.g., max 10 calls per 5 minutes) and per IP. | High | D1 |
| SR-RATE-2 | `redeemCoupon` / `recalculateAutomaticOffer` MUST be rate limited per portfolio (e.g., max 3 calls per hour). Excess requests MUST return 429. | High | T5, D2 |
| SR-RATE-3 | Micro loan creation MUST be rate limited per customer with a configurable per-day maximum. | Critical | D3, E3 |
| SR-RATE-4 | `AutomaticCalculation` event ingestion from DWH MUST be rate limited and deduplicated (ignore duplicate events within a time window). | Medium | D4 |
| SR-RATE-5 | `getMicroLoanOffer` responses MUST be cached server-side per portfolioId with a short TTL (e.g., 5 minutes) to prevent redundant credit calculations. | High | D1 |

---

### SR-AUDIT — Audit Logging & Non-Repudiation

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-AUDIT-1 | Every loan creation event MUST be written to an immutable audit log containing: portfolioId, customerId, amount, applicationType, idempotency key, timestamp, loan status, and actor identity. | High | R1 |
| SR-AUDIT-2 | Every `recalculateAutomaticOffer` call MUST be logged with: caller identity, portfolioId, timestamp, previous offer value, new offer value. | Medium | R2 |
| SR-AUDIT-3 | All rule engine invocations for `NEW_MICRO_LOAN` MUST persist input parameters, output decision, and timestamp for the regulatory minimum retention period. | High | R3 |
| SR-AUDIT-4 | Audit logs MUST be stored in a separate, append-only store that application services cannot modify or delete. | High | R1, R2, R3 |
| SR-AUDIT-5 | All changes to the widget eligibility threshold and microLoan purpose configuration MUST be logged with actor identity and timestamp. | Medium | T7, R2 |

---

### SR-DATA — Data Protection & Privacy

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-DATA-1 | `getMicroLoanOffer` MUST NOT return the raw Bureau Derivations fast amount. It MUST return only the offer amount capped to the transfer context. Consider returning a pre-approved amount or eligibility indicator rather than the raw credit score derivative. | High | I1 |
| SR-DATA-2 | `getMicroLoanOffer` MUST use short-lived signed offer tokens instead of raw `planId` and `purposeId` UUIDs. Tokens MUST be validated server-side at loan creation time. | Medium | I2, T6 |
| SR-DATA-3 | Only the minimum required loan fields (amount, status) MUST be sent to the rule engine. PII fields MUST be stripped before cross-service calls. | Medium | I4 |
| SR-DATA-4 | Error responses to clients MUST use opaque error codes (e.g., `OFFER_UNAVAILABLE`, `LOAN_LIMIT_REACHED`). Detailed rule engine or DB errors MUST be logged server-side only. | Medium | I3 |
| SR-DATA-5 | All PII fields in the `redemption` / loan tables MUST be encrypted at rest. Access MUST be restricted to authorized service accounts. | High | I1, I4 |

---

### SR-RESIL — Resilience & Availability

| ID | Requirement | Priority | Threat(s) Addressed |
|---|---|---|---|
| SR-RESIL-1 | `recalculateAutomaticOffer` MUST be processed asynchronously via a queue. If a calculation is already in-flight for a portfolio, new requests MUST be deduplicated and not cancel the in-flight job. | High | D2, T5 |
| SR-RESIL-2 | A circuit breaker MUST be in place between credit-limit-service and the rule engine. Repeated rule engine failures MUST not cascade to the loan creation flow. | High | D2 |
| SR-RESIL-3 | DWH event ingestion MUST use a dead-letter queue (DLQ) for overflow. Failed events MUST be retried with exponential backoff and alerted on after N failures. | Medium | D4 |
| SR-RESIL-4 | Per-portfolio loan creation MUST use a queue or mutex to serialize concurrent requests. Max in-flight loan creations per portfolio MUST be 1. | Critical | T2, D3 |
