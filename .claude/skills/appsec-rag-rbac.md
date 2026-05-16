---
name: appsec-rag-rbac
description: Reviews and implements Role-Based Access Control (RBAC) for RAG (Retrieval-Augmented Generation) systems. Ensures documents are scoped to authorized users/roles at ingestion and retrieval time, prevents cross-tenant leakage, and audits vector database access controls in Pinecone, Weaviate, Chroma, pgvector, and similar stores.
---

Audit and implement RBAC controls for the RAG pipeline in the specified codebase or configuration.

## Audit Scope

### 1. Document Ingestion Access Control
- Are documents tagged with access metadata (owner, role, classification, tenant_id) at ingestion time?
- Is the ingestion pipeline authenticated — only authorized services/users can add documents?
- Are document ACLs stored alongside embeddings in the vector store metadata?
- Is there a review/approval step before sensitive documents enter the knowledge base?

### 2. Retrieval-Time Access Enforcement
- Does every retrieval query include a metadata filter scoped to the requesting user's roles/tenant?
- Is the access filter applied **server-side** (in the vector DB query), not client-side (post-retrieval)?
- Can a user craft a query to bypass the metadata filter (e.g., via filter injection)?
- Are similarity search results re-validated against ACLs before being added to the prompt?

### 3. Role Hierarchy & Permission Model
- Is there a defined role hierarchy (e.g., admin > manager > user > guest)?
- Are roles assigned at the document level, collection level, and namespace level?
- Does the system support attribute-based access control (ABAC) for fine-grained document access?
- Are role assignments stored and managed in a central identity provider (LDAP, OAuth, IAM)?

### 4. Multi-Tenant Isolation
- Are different customers' documents stored in separate namespaces, collections, or indexes?
- Is namespace/collection selection done server-side based on the authenticated user's tenant?
- Can a user query a namespace other than their own by manipulating request parameters?
- Are tenant boundaries enforced at the embedding API level as well?

### 5. Vector DB-Specific Checks
- **Pinecone**: Are namespaces used per tenant? Is the API key scoped to minimum index access?
- **Weaviate**: Are class-level permissions set? Is multi-tenancy enabled for shared deployments?
- **Chroma**: Is the server running in authenticated mode (`chroma_client_auth_provider` configured)?
- **pgvector**: Are row-level security (RLS) policies enabled on the embeddings table?
- **Qdrant**: Are collections API-key scoped? Is payload filtering validated server-side?

### 6. Prompt-Level Access Leakage
- Are retrieved document titles, metadata, or IDs included in the prompt verbatim (leaking existence of restricted docs)?
- Does the LLM response reveal the contents of documents the user shouldn't know exist?
- Is there negative filtering to prevent the LLM from confirming or denying restricted content?

### 7. Audit & Compliance
- Are all retrieval queries logged with user identity, roles, and timestamp?
- Are access denials (attempted retrieval of unauthorized documents) alerted on?
- Is there a periodic review process to re-validate document ACLs (especially after role changes)?

## Implementation Patterns

When remediating, apply these patterns:

```python
# Server-side retrieval filter pattern
def retrieve_for_user(query: str, user: User, vector_store) -> list[Document]:
    # Build access filter from authenticated user context — NEVER from client input
    access_filter = {
        "$or": [
            {"roles": {"$in": user.roles}},
            {"owner_id": user.id},
            {"classification": "public"}
        ]
    }
    results = vector_store.similarity_search(
        query,
        filter=access_filter,  # enforced at DB level
        k=5
    )
    # Re-validate each result as defense-in-depth
    return [doc for doc in results if user_can_access(user, doc.metadata)]

def user_can_access(user: User, doc_metadata: dict) -> bool:
    required_roles = set(doc_metadata.get("roles", []))
    user_roles = set(user.roles)
    return (
        doc_metadata.get("owner_id") == user.id
        or doc_metadata.get("classification") == "public"
        or bool(required_roles & user_roles)
    )
```

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **Control Gap**: (e.g., Missing Retrieval Filter, Client-Side ACL, No Namespace Isolation)
3. **Vector Store Component**: Where the gap exists
4. **Attack Scenario**: How a user could access unauthorized documents
5. **Remediation**: Code fix or configuration change

End with an **RBAC Coverage Matrix** — table of each RAG component (ingest, store, retrieve, prompt) showing ENFORCED / PARTIAL / MISSING access control, plus a prioritized implementation plan.
