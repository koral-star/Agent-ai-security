# Open Questions — Jarvis EntraID Authorization Integration
## Security Review Meeting Preparation

**Background:** Keycloak previously managed both users AND clients (OAuth clients/service accounts).
The new design splits this: users move to EntraID, a new permission layer is added to Jarvis
(VIEWER / OPERATOR / ADMIN + fine-grained permissions). Questions below are organized by
document section so you know exactly where to raise them in the meeting.

---

## Section: Overview & Migration Scope

1. Keycloak managed both users and OAuth clients (service accounts / M2M). The design covers
   user identity migration to EntraID — but where do the **Keycloak OAuth clients** (machine-to-machine)
   go? Are they migrated to EntraID Service Principals / Managed Identities, or do they remain in
   Keycloak temporarily?

2. The doc says "minimizes IDM dependency" — what IDM functions **remain active** after the migration?
   Is IDM still authoritative for anything (e.g., employee provisioning, group sync)? If so, what
   is the trust boundary between IDM and EntraID?

3. The design introduces a new **permission layer on top of Keycloak's existing access model**.
   What did Keycloak enforce before — was it only coarse-grained role access, or were there
   fine-grained permissions too? What is the delta in what users can now do vs. before?

4. Is there a **formal threat model or security sign-off** required before the migration goes live?
   Who is the approving authority?

---

## Section: Architecture — System Context Diagram

5. **platform-auth is a single point of failure** for all token exchanges. What is its availability
   SLA? Is it deployed with redundancy (HA)? If platform-auth is down, can users authenticate at all?

6. The internal token contains a `"caller"` field (e.g., `"jarvis-service"`). How is this field
   **set and validated**? Can any service set an arbitrary caller value when calling platform-auth,
   or is it derived from authenticated service identity?

7. **app-context is unchanged and already in production.** Has it undergone a recent security review?
   Were there known vulnerabilities in the Keycloak-era implementation that this migration should
   address but currently does not?

8. Downstream services (A, B, C) verify tokens via app-context. Are these downstream services
   **aware of the token format change** (Keycloak token → internal platform token)? Is there a risk
   of a downstream service accepting both old and new token formats during migration?

---

## Section: Authentication Flows

### Flow 1 — User Login

9. MFA is shown in the login flow. Is MFA **enforced via EntraID Conditional Access Policy**, or is
   it left to each user to configure? Who owns and monitors the Conditional Access Policy?

10. The PKCE `state` parameter prevents CSRF. How is the state value **generated and validated**?
    Is it cryptographically random (min 128-bit entropy), and is it bound to the browser session?

11. Who is responsible for **enrolling and offboarding users** in EntraID App Roles? Is there a
    formal process, or is it ad-hoc? How quickly is access revoked when an employee leaves?

### Flow 3 — Silent Token Refresh

12. The silent refresh uses a **hidden iframe** (`acquireTokenSilent`). Modern browsers (Safari ITP,
    Chrome cookie partitioning) increasingly block third-party cookies required for hidden iframe
    refresh. Has this been tested? What is the fallback when silent refresh fails silently?

13. When silent refresh fails and the user is redirected to EntraID login, is there any
    **unsaved work protection** in the Jarvis UI, or does the user lose their current context?

---

## Section: Component 1 — jarvis-client (React SPA)

14. Tokens are stored in **sessionStorage**, which is still accessible to JavaScript and therefore
    to XSS. Is there a **Content Security Policy (CSP)** implemented on Jarvis to reduce XSS risk?
    Has a CSP been tested and validated?

15. The MSAL config code shows `cacheLocation: "sessionStorage" | "localStorage"` — both options
    are available in the config interface. Is **localStorage actively blocked** in the final
    implementation, or is it a developer choice? Who enforces the sessionStorage requirement?

16. The client renders pages and actions **based on role claims for UI only** — this is explicitly
    not a security boundary. Is there a risk that role information visible in the JWT or network
    traffic **reveals sensitive role assignments** to an attacker who intercepts traffic or inspects
    the browser?

17. **Employee list source for `VIEW_EMPLOYEE_DETAILS` is TBD.** This permission grants access to
    bank employee and board member personal/financial data — extremely sensitive. Who decides who
    gets this permission? What is the approval process? What is the timeline for defining this?

18. The clientId for the EntraID App Registration is embedded in the MSAL config delivered to the
    browser. Is this **clientId considered a secret**? What is the risk if it is extracted and
    abused (e.g., phishing app registration)?

---

## Section: Component 2 — jarvis-auth-lib

19. The **Role → Permission mapping is hardcoded server-side in jarvis-auth-lib.** Who has the
    authority to change this mapping? Is there a change control / security review process, or can
    any developer modify it via a pull request?

20. The **deny-by-default policy blocks unannotated endpoints.** What happens during a
    library version upgrade or rollback — is there a window where endpoints could be unprotected
    if the annotation processing fails silently? Is there a startup check that validates all
    endpoints are annotated?

21. `AuthenticatedContext` contains `internalToken: String` as a field passed to controllers.
    Is this field ever **logged, serialized to responses, or returned in error payloads**? A leaked
    internal token gives full authenticated access to all downstream services.

22. Can a developer **create a new endpoint without a `@RequiresRole` or `@RequiresPermission`
    annotation** and have it go unnoticed until production? Is there a CI/CD gate or test that
    enforces annotation coverage?

---

## Section: Component 3 — jarvis-service

23. The `/config` (PUT) endpoint requires `ADMIN` role + `MANAGE_CONFIG` permission. **How many
    users currently hold the ADMIN role?** Is there a minimum/maximum? Is ADMIN access periodically
    reviewed and recertified?

24. The `executeAction` endpoint (`EXECUTE_ACTION` permission) — **what actions can be executed?**
    Are there irreversible actions (delete records, trigger notifications, modify customer data)?
    Should these require additional confirmation or a second-factor approval beyond role check?

25. The 403 response body includes **`"requiredRole": "ADMIN"`** — this reveals internal
    permission structure to any caller who probes endpoints. Is this intentional? Should it be
    removed or restricted to internal/admin callers only?

---

## Section: Component 4 — jarvis-jql (JQL Query Service)

26. The `/query` endpoint allows VIEWER, OPERATOR, and ADMIN to execute JQL queries with
    `EXECUTE_QUERY` permission. **Is there row-level or data-level authorization within query
    results**, or can any user with EXECUTE_QUERY access all data regardless of sensitivity?

27. Can a user with `MANAGE_QUERIES` **save a query that another user with only `EXECUTE_QUERY`
    can later run**, potentially accessing data the original query creator intended to restrict?
    Is there a query ownership / sharing model?

28. **Are JQL queries sanitized and parameterized** to prevent injection attacks (SQL injection,
    NoSQL injection, or JQL-specific injection)? Is this handled in jarvis-jql, or does it rely
    on downstream data sources?

29. Can a JQL query result in **exporting or bulk-extracting sensitive data** (e.g., all customer
    records)? Are there query result size limits or data egress controls?

---

## Section: Component 5 — platform-auth (Token Exchange Service)

30. `TokenExchangeRequest` accepts `requestedScopes: List<String>`. **Can a caller request
    arbitrary scopes?** Is there validation that the requested scopes do not exceed what the
    EntraID token authorizes (scope elevation attack)?

31. **What service-to-service authentication mechanism** is used when jarvis-service calls
    platform-auth for token exchange? mTLS? API key? Service account JWT? If it is an API key,
    how is it rotated and stored?

32. Internal platform tokens are **cached keyed by EntraID token hash.** If the EntraID token is
    revoked (e.g., user terminated, password reset), does the cache get invalidated immediately,
    or does the internal token remain valid until it expires (up to 15 min)?

33. JWKS is cached with a **24-hour TTL.** During an EntraID emergency key rotation, how quickly
    does platform-auth pick up the new keys? Is there an API or mechanism to force an immediate
    JWKS refresh without a service restart?

34. The design says platform-auth verifies `issuer`, `audience`, and `expiry`. **Is the `nbf`
    (not before) claim also validated?** A token with a future `nbf` should be rejected.

---

## Section: Data Models — Roles and Permissions

35. **`VIEW_EMPLOYEE_DETAILS` is independently assigned** (not derived from VIEWER/OPERATOR/ADMIN).
    This means a VIEWER can have it, giving them access to bank employee and board member
    personal/financial data alongside read-only dashboard access. Is this **combination intentional
    and acceptable from a data privacy perspective?**

36. Who in the organization has the **EntraID admin rights to assign App Roles** (VIEWER, OPERATOR,
    ADMIN, EMPLOYEE_DETAILS_VIEWER) to users in production? Is there separation of duties — i.e.,
    can a Jarvis user assign their own role?

37. Is there a **periodic access recertification process** for all Jarvis role holders? How often
    are role assignments reviewed? Who is notified when a new ADMIN or EMPLOYEE_DETAILS_VIEWER is
    assigned?

38. The `MANAGE_USERS` permission is ADMIN-only. **What does user management entail in Jarvis** —
    can an ADMIN in Jarvis assign EntraID App Roles to other users, or is role assignment purely
    in EntraID? If Jarvis can trigger role assignments, this is a critical privilege escalation path.

---

## Section: EntraID App Registration Configuration

39. The App Registration requests **Microsoft Graph: User.Read (delegated).** Why is this needed?
    What data is fetched from Microsoft Graph, and where is it used in the flow?

40. The redirect URI is `https://jarvis.company.com/auth/callback`. **Are wildcard redirect URIs
    disabled?** A wildcard (e.g., `https://*.company.com/*`) would allow open redirect attacks.
    Is the redirect URI list strictly pinned to exact values?

41. **Groups claim is NOT used** — App Roles are used instead. Is there any legacy code or
    configuration in jarvis-service / jarvis-auth-lib that still reads a `groups` claim? If so,
    could it be abused if a token happens to contain group claims?

---

## Section: Migration Period (Keycloak → EntraID)

42. **Migration step 7 runs both Keycloak and EntraID auth in parallel.** During this period,
    can a user authenticate via Keycloak (with potentially weaker or different access controls)
    to bypass the new EntraID permission layer? How is this prevented?

43. **How long is the parallel auth period?** Is there a hard deadline for cutting over to
    EntraID-only? Who is responsible for enforcing the cutover?

44. The old Keycloak setup managed OAuth clients (M2M / service accounts). During the transition,
    **are Keycloak-issued tokens still accepted by platform-auth or downstream services?** If yes,
    this could allow tokens issued for decommissioned clients to still work.

45. **What is the rollback plan** if a critical security issue is found post-migration? Can the
    system revert to Keycloak within an RTO (Recovery Time Objective)? Is the Keycloak
    configuration being preserved or decommissioned immediately?

46. The design says "Assign existing agents to appropriate EntraID App Roles" (migration step 2).
    **How are existing Keycloak roles mapped to the new VIEWER/OPERATOR/ADMIN roles?** Is there
    a risk that users are over-provisioned during migration (e.g., everyone gets OPERATOR)?

---

## Section: Security Considerations (already in document)

47. The doc says "Never log full JWT tokens — log only `oid` and `exp` for debugging." **Are
    existing logging frameworks (e.g., Spring Boot default request logging, API gateway access
    logs) audited to ensure they do not capture Authorization headers?** Has this been verified
    across all services?

48. Token Exchange Security states "Token exchange requests are authenticated
    (service-to-service auth with platform-auth)" — but the **specific mechanism is not defined
    in the HLD.** What is it? If it is not implemented yet, this is a gap.

49. The design mentions "Validate token signature, issuer, audience, and expiry on every request
    server-side" — **is this validation done before or after the token exchange cache lookup?**
    If a cached internal token is returned without re-validating the EntraID token, a revoked
    user could continue to access the system until the cache expires.

---

## Section: Audit and Logging

50. The doc says "Log all authorization failures (401, 403) with user ID, endpoint, and required
    role." **Where are these logs stored, and who has access?** Are they protected from
    modification? Is there alerting on repeated 403s from the same user (potential privilege
    escalation probe)?

51. **Are successful privileged actions logged?** Specifically: ADMIN config changes
    (`MANAGE_CONFIG`), user management (`MANAGE_USERS`), and employee detail access
    (`VIEW_EMPLOYEE_DETAILS`) — these should have their own audit trail beyond generic auth logs.

52. The `trace_id` in the internal token enables distributed tracing. **Are trace logs secured
    appropriately?** Trace logs could expose internal service topology and request payloads
    containing sensitive data.
