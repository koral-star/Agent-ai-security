# STRIDE Threat Model — Campaigns With Coupon Redemption

## 1. System Overview

### Description
A discount-based campaign system allowing Marketing to independently create and manage promotional campaigns with generic coupon codes (not single-user codes). Customers redeem coupon codes via mobile to receive benefits.

### Components & Trust Boundaries

```
[Mobile App] ──(public internet)──> [BFF] ──(internal)──> [Benefit Service] ──> [Benefit DB]
                                                                   │
                                                                   ├──(internal)──> [Core Service]
                                                                   └──(events)────> [DWH / Analytics]

[Marketing/Prod User] ──(internal/admin)──> [Benefit Service Management APIs]
```

| Trust Boundary | Level | Notes |
|---|---|---|
| Mobile ↔ BFF | Low (public internet) | Unauthenticated channel before login |
| BFF ↔ Benefit Service | Medium (internal) | Service-to-service, should use mTLS |
| Benefit Service ↔ Benefit DB | High (internal) | Direct DB access |
| Benefit Service ↔ Core Service | Medium (internal) | Cross-service call for discount creation |
| Benefit Service ↔ DWH | Medium (event bus) | Async, event-driven |
| Marketing User ↔ Management APIs | Medium (admin) | Privileged operations |

### Key Assets
- Coupon codes (generic, shared — high value target)
- Campaign configurations (business-sensitive discount logic)
- Redemption records (PII: customer_id, portfolio_id, user plan)
- Discount records in Core Service
- Redemptions counter (enforces business limits)

### Key Data Flows
1. **Flow 1 — Campaign + Coupon Creation:** Marketing → Benefit Service → Benefit DB
2. **Flow 2 — Coupon Redemption:** Mobile → BFF → Benefit Service → validates (10 checks) → creates Redemption → creates Discount in Core → publishes events → returns success

---

## 2. STRIDE Threat Analysis

### S — Spoofing

| ID | Threat | Component | Impact | Mitigation |
|---|---|---|---|---|
| S1 | **Marketing user impersonation** — attacker authenticates as a marketing/prod user to create fraudulent campaigns or coupons | `createCampaignConfig`, `createCoupon` Management APIs | Unauthorized discount campaigns, financial loss | Strong auth (OAuth 2.0 / SSO + MFA) for admin users; RBAC enforcing marketing role |
| S2 | **Customer identity spoofing in redeemCoupon** — attacker submits another user's `customerId` or `portfolioId` to redeem coupons on their behalf | `redeemCoupon(portfolioId, customerId, couponCode)` | Fraudulent redemption linked to victim's account | Server-side assertion: JWT token claims must match `customerId` and `portfolioId` in request body; never trust client-supplied identity |
| S3 | **Service impersonation** — rogue service impersonates the BFF to call Benefit Service directly, bypassing BFF-level logic | BFF → Benefit Service channel | Bypass BFF auth/rate-limit layer, unauthorized mutations | Mutual TLS (mTLS) between internal services; service identity tokens (e.g., SPIFFE/SPIRE) |
| S4 | **Coupon code brute-force / guessing** — since codes are generic (shared across users), an attacker systematically guesses valid codes | `getCouponByCodeAndPortfolioId`, `redeemCoupon` | Unauthorized discount redemption at scale | Rate limiting per IP and per user on lookup + redemption endpoints; coupon code minimum entropy requirement; anomaly detection on failed lookups |

---

### T — Tampering

| ID | Threat | Component | Impact | Mitigation |
|---|---|---|---|---|
| T1 | **Campaign config manipulation** — attacker modifies `eligiblePlans`, `discountConfigs`, `maxRedemptions`, or `stackingBehavior` to create overly generous discounts | `updateCampaignConfig` API, `campaign_config` DB table | Unauthorized discounts, financial fraud | Strict RBAC on update operations; server-side field validation; DB-level integrity constraints; immutable audit log |
| T2 | **Coupon data tampering** — attacker updates coupon's `maxRedemptions`, `redemptionWindow`, or `isActive` to extend validity or lift limits | `updateCoupon` API, `coupon` DB table | Unlimited or expired-coupon redemptions, financial loss | Authorization check on update (only coupon owner/campaign owner); field-level validation; audit log with before/after values |
| T3 | **Redemption counter manipulation** — direct DB tampering resets `redemptions_count` in `campaign_config` or `coupon` tables, bypassing max-redemption limits | `redemptions_count` fields in Benefit DB | Unlimited redemptions beyond configured cap | No direct DB write access for clients; DB user permissions restricted to application service account; counter updated only via atomic transactions |
| T4 | **Race condition / TOCTOU on redemption** — concurrent requests for the same coupon exploit the gap between "check coupon limit" and "increment counter", allowing over-redemption | `redeemCoupon` → "update redemption counter" step | Over-redemption beyond `maxRedemptions`, financial loss | Atomic compare-and-increment DB operation (e.g., `UPDATE coupon SET redemptions_count = redemptions_count + 1 WHERE redemptions_count < max_redemptions`); pessimistic/optimistic DB locking; idempotency keys |
| T5 | **Event message tampering** — `CampaignRedemption` events intercepted and modified in transit to downstream systems (DWH, Core) | Event publishing channel | Incorrect analytics, wrong discounts applied, data inconsistency | Message signing (HMAC/signatures); encrypted transport (TLS) for event bus; consumer-side signature verification |
| T6 | **GraphQL input injection** — malicious characters in `couponCode`, `campaignName`, or other string fields cause SQL/NoSQL injection or logic bypass | All GraphQL mutation inputs | Data corruption, unauthorized data access | Parameterized queries (ORM / prepared statements); strict input validation; coupon code regex enforcement (uppercase alphanumeric already specified) |

---

### R — Repudiation

| ID | Threat | Component | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Marketing user denies campaign/coupon creation** — user claims they did not create a fraudulent campaign or overly generous coupon | `createCampaignConfig`, `createCoupon` | Inability to investigate fraud, regulatory non-compliance | Immutable audit log: record actor identity (user ID), timestamp, action, full input payload; log stored separately from application DB |
| R2 | **Customer denies coupon redemption** — customer disputes a redemption for refund abuse or fraud claim | `redeemCoupon`, `redemption` table | Financial disputes, fraud | `redeemer_customer_id` already stored in redemption table (good); ensure redemption records are immutable after creation; emit signed `CampaignRedemption` event with timestamp |
| R3 | **No audit trail for campaign/coupon updates** — changes to `isEnabled`, `maxRedemptions`, `allowedTimeRange` cannot be attributed to a specific actor | `updateCampaignConfig`, `updateCoupon` | Cannot investigate unauthorized config changes | Audit log for ALL management API write operations: include actor identity, before-value, after-value, timestamp; consider event sourcing pattern for campaign config |

---

### I — Information Disclosure

| ID | Threat | Component | Impact | Mitigation |
|---|---|---|---|---|
| I1 | **Coupon code enumeration** — attacker probes `getCouponByCode` with random strings to discover valid active coupon codes | `getCouponByCodeAndPortfolioId` Mobile API | Reveals active coupon codes enabling unauthorized redemption | Consistent response time and error messages regardless of whether code exists vs. wrong portfolio vs. expired; rate limiting; monitor for enumeration patterns |
| I2 | **PII exposure in redemption data** — `redeemer_customer_id`, `portfolio_id`, `user_plan_at_redemption` are sensitive; unauthorized access leaks customer plan and identity data | `redemptionsByPortfolio`, `activeRedemptionsByPortfolio` queries, DWH | Privacy violation, GDPR/regulatory breach (doc already flags PII concern) | Strict authorization: portfolioId in query must match authenticated user's token; data masking in non-prod environments; PII field encryption at rest; DWH access controls |
| I3 | **Campaign configuration disclosure** — unauthorized access to `discountConfigs`, `eligiblePlans`, `stackingBehavior` reveals competitive business strategy | Management APIs, internal campaign config query | Competitive intelligence leak, campaign manipulation | Authentication + authorization on all management APIs; principle of least privilege; internal-only exposure of full campaign config |
| I4 | **Error message information leakage** — validation failures (10 checks in redeemCoupon) return detailed messages revealing internal logic (e.g., "campaign not found" vs. "coupon limit reached") | Error handling across all APIs (doc notes need for proper error handling) | Attacker learns system internals, facilitating targeted attacks | Return generic error codes to clients (e.g., `REDEMPTION_FAILED`); detailed errors logged server-side only; map validation errors to opaque error codes |
| I5 | **Cross-portfolio redemption history access** — user queries `redemptionsByPortfolio($portfolioId)` with a different user's `portfolioId` | `redemptionsByPortfolio`, `activeRedemptionsByPortfolio` | Privacy violation, exposure of other users' subscription/plan activity | Server-side authorization: validate that `portfolioId` in GraphQL variable matches the authenticated user's portfolio from JWT claims; never trust client-supplied portfolio ID |
| I6 | **DWH data exposure** — analytics events contain campaign + redemption data (including PII fields) accessible to broader internal audience | Event publishing → DWH | PII/business data exposure beyond need-to-know | Data minimization in events (only send required fields); anonymize/pseudonymize PII before publishing to DWH; DWH RBAC; mark PII fields per data classification |

---

### D — Denial of Service

| ID | Threat | Component | Impact | Mitigation |
|---|---|---|---|---|
| D1 | **Management API flooding** — compromised or malicious marketing account creates thousands of campaigns/coupons exhausting DB and service resources | `createCampaignConfig`, `createCoupon` | DB exhaustion, service degradation for all users | Rate limiting on management APIs (per user/org); resource quotas (max campaigns/coupons per org); input size limits on list fields |
| D2 | **Mass redemption bot attack** — automated bots hammer `redeemCoupon` for popular coupon codes | `redeemCoupon` BFF → Benefit Service | Service unavailability for legitimate users, DB write contention (doc already flags Rate Limit) | Rate limiting per user + per IP on redemption endpoint; CAPTCHA/bot detection for high-frequency attempts; WAF rules; per-coupon redemption throttling |
| D3 | **DB lock contention on counter update** — high concurrent redemptions for the same coupon create DB write locks on `redemptions_count`, degrading all redemptions | "update redemption counter" step in `redeemCoupon` | Slow/failed redemptions globally | Atomic non-blocking increment (optimistic locking); consider Redis-based counter for high-traffic coupons; DB connection pooling; queue-based redemption for viral campaigns |
| D4 | **Large eligibility list processing** — campaign created with huge `eligiblePlans`/`eligibleSubPlans` lists causes excessive CPU/memory during eligibility validation | `createCampaignConfig` (eligiblePlans: `List<PlanType>`, eligibleSubPlans: `List<SubPlanType>`) | CPU/memory exhaustion during redemption validation | Enforce max list size limits in `createCampaignConfig`; pre-index eligible plans for O(1) lookup; pagination for large lists |
| D5 | **Event queue flooding** — mass redemptions overwhelm event bus, causing consumer lag in DWH and Core Service | "publish events" step in `redeemCoupon` | Analytics delays, downstream Core Service failures | Event queue capacity planning; dead-letter queues (DLQ) for failed events; backpressure / circuit breaker; async event publishing (don't block redemption response) |

---

### E — Elevation of Privilege

| ID | Threat | Component | Impact | Mitigation |
|---|---|---|---|---|
| E1 | **Mobile user accessing Management APIs** — end user directly calls `createCampaignConfig` or `createCoupon`, bypassing role restrictions | Management APIs | Unauthorized campaign/coupon creation, financial fraud | RBAC enforced at API gateway and Benefit Service layer; separate auth scopes for management (`admin`) vs. mobile (`customer`) APIs; deny by default |
| E2 | **Portfolio privilege escalation in redeemCoupon** — user substitutes a different `portfolioId` to claim a redemption benefit on another account | `redeemCoupon(portfolioId, customerId, couponCode)` | Fraudulent redemption on victim's portfolio | JWT must contain portfolio binding; server-side: assert `portfolioId` and `customerId` match token claims before processing |
| E3 | **Coupon stacking abuse** — user exploits `stackingBehavior` or validation rule #10 (replace existing discount → create new) to cycle through discounts and obtain unintended benefit | `stackingBehavior` in `campaign_config`; validation #10 in `redeemCoupon` | Financial loss through stacked or repeatedly replaced discounts | Atomic server-side enforcement of stacking rules; log all discount replacements; business rule review for edge cases of replace-existing; rate limit redemptions per customer per campaign |
| E4 | **Accessing other users' redemption history** — user queries `redemptionsByPortfolio` or `activeRedemptionsByPortfolio` with a victim's `portfolioId` | `redemptionsByPortfolio($portfolioId: UUID!)` | Privacy violation, enumeration of other users' activity | Authorization middleware: `portfolioId` query variable must match authenticated user's portfolio from token; return `UNAUTHORIZED` otherwise |
| E5 | **Campaign trigger validation bypass** — coupon creation skips validation #2 ("campaign is COUPON-triggered") if enforced only client-side, allowing coupons on non-coupon campaigns | `createCouponConfig` validation | Coupons created for wrong campaign type, unintended discount logic | All 6 create-coupon validations enforced server-side in Benefit Service; client cannot bypass server-side checks; unit tests for each validation path |
| E6 | **Discount replacement cycle abuse** — attacker repeatedly redeems different coupons to trigger validation #10 (remove existing discount, create new), cycling to a more favorable discount tier | `redeemCoupon` → discount management in Core Service | Unauthorized upgrade of discount tier; unintended financial impact | Log and alert on repeated redemptions per customer within a time window; business rule: limit discount replacements per customer per campaign period; review replace-existing logic for privilege implications |

---

## 3. Risk Summary Matrix

| ID | Threat | Likelihood | Impact | Risk |
|---|---|---|---|---|
| T4 | Race condition on redemption counter | High | High | **Critical** |
| S4 | Coupon code brute-force | High | High | **Critical** |
| E2 | Portfolio privilege escalation | Medium | High | **High** |
| I5 | Cross-portfolio redemption access | Medium | High | **High** |
| D2 | Mass redemption bot attack | High | Medium | **High** |
| T6 | GraphQL input injection | Medium | High | **High** |
| S2 | Customer identity spoofing | Medium | High | **High** |
| E3 | Coupon stacking abuse | Medium | High | **High** |
| E6 | Discount replacement cycle abuse | Medium | High | **High** |
| I4 | Error message information leakage | High | Medium | **Medium** |
| R1 | No audit trail for campaign creation | Low | High | **Medium** |
| R3 | No audit trail for config updates | Low | High | **Medium** |
| D3 | DB lock contention on counter | Medium | Medium | **Medium** |
| I2 | PII exposure in redemption data | Low | High | **Medium** |
| I1 | Coupon code enumeration | Medium | Medium | **Medium** |
| S1 | Marketing user impersonation | Low | High | **Medium** |
| S3 | Service impersonation | Low | High | **Medium** |
| E1 | Mobile user accessing Management APIs | Low | High | **Medium** |
| E5 | Campaign trigger bypass | Low | High | **Medium** |
| D1 | Management API flooding | Low | Medium | **Low** |
| D4 | Large eligibility list DoS | Low | Medium | **Low** |
| D5 | Event queue flooding | Low | Medium | **Low** |
| T5 | Event message tampering | Low | Medium | **Low** |
| I3 | Campaign config disclosure | Low | Medium | **Low** |
| I6 | DWH data exposure | Low | Medium | **Low** |

---

## 4. Top Priority Mitigations

### Critical (implement before launch)

1. **T4 — Race Condition:** Implement atomic DB operation for counter increment:
   ```sql
   UPDATE coupon
   SET redemptions_count = redemptions_count + 1
   WHERE coupon_code = $code AND redemptions_count < max_redemptions
   RETURNING id;
   -- If 0 rows returned → limit reached
   ```

2. **S4 — Brute-force:** Rate limit `getCouponByCode` and `redeemCoupon` per IP and per user (sliding window). Alert on > N failed attempts per coupon code per hour.

3. **E2 / I5 — Portfolio/Customer ID Trust:** Never trust `portfolioId` or `customerId` from request body alone. Always extract and verify from authenticated JWT token claims.

### High (implement in first sprint post-MVP)

4. **S2 — Identity Spoofing:** Enforce server-side binding: token subject = `customerId` = `portfolioId` owner.

5. **E3 / E6 — Stacking/Replace Abuse:** Audit log all discount replacements; rate limit redemptions per customer per campaign (e.g., max 1 redemption attempt per minute per customer).

6. **T6 — Injection:** Use ORM with parameterized queries; add integration tests for malformed inputs in all string fields.

7. **D2 — Bot Protection:** Implement rate limiting at BFF layer; add bot detection / CAPTCHA for high-frequency redemption patterns.

### Medium (backlog)

8. **R1 / R3 — Audit Trail:** Implement immutable audit log for all management API write operations (actor, timestamp, before/after values).

9. **I2 — PII Handling:** Encrypt `redeemer_customer_id` at rest; restrict `redemptionsByPortfolio` query to authenticated portfolio owner only; DWH data classification.

10. **I4 — Error Messages:** Map all 10 redemption validation failures to opaque error codes (e.g., `COUPON_INVALID`, `REDEMPTION_LIMIT_REACHED`) rather than descriptive messages.

---

## 5. Existing Security Controls (from LLD)

| Control | Coverage |
|---|---|
| Coupon code regex (uppercase) + uniqueness validation | Partial T6, partial S4 |
| 10-step redemption validation chain | Partial T1, T2, E3 |
| PII data noted as security concern | Awareness of I2 |
| Rate Limit noted as security concern | Awareness of D2, S4 |
| `redeemer_customer_id` stored in redemption table | Partial R2 |
| Coupon uniqueness enforced at DB level | Partial T2 |

**Gaps identified:** No mention of authentication/authorization mechanism, audit logging, mTLS between services, race condition handling, or error message standardization in current LLD.
