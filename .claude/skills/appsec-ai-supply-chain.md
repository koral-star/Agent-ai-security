---
name: appsec-ai-supply-chain
description: Reviews AI/ML supply chain security. Audits model provenance, pip/conda dependencies, Hugging Face model cards, serialized model files (pickle, safetensors), requirements.txt, and CI/CD pipelines for tampering, malicious packages, and integrity gaps.
---

Perform a full AI/ML supply chain security audit on the specified files, directories, or repositories.

## Audit Scope

### 1. Python Dependency Security
- Scan `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `conda.yml` for:
  - Known CVEs in AI/ML packages (transformers, torch, langchain, openai, anthropic, etc.)
  - Typosquatted package names (e.g., `langchian`, `openai-sdk` vs `openai`)
  - Unpinned versions (`>=`, `*`) that allow silent upgrades to malicious releases
  - Packages pulled from GitHub directly without commit pinning
  - Private packages without registry authentication

### 2. Model File Integrity
- Are model weights loaded from verified, checksummed sources?
- Is `pickle` / `torch.load` used without `weights_only=True` (arbitrary code execution risk)?
- Are `.pkl`, `.pt`, `.bin` files downloaded without SHA256 verification?
- Is `safetensors` preferred over legacy pickle-based formats?
- Are Hugging Face model cards reviewed for malicious pre/post-processing hooks?

### 3. Model Provenance & Trust
- Is there a record of which model version is deployed (model card, model registry entry)?
- Are fine-tuned models stored with lineage to the base model?
- Are third-party models from untrusted organizations used without review?
- Is there a model approval workflow before production deployment?

### 4. CI/CD Pipeline Security
- Are GitHub Actions / CI steps pinned to commit SHAs (not mutable tags like `@v3`)?
- Are secrets (API keys, HuggingFace tokens) stored in vault/secrets manager — not in env files?
- Is there a dependency update bot (Dependabot, Renovate) with security policies?
- Are Docker base images for model serving pinned and scanned?

### 5. Data Pipeline Integrity
- Are training datasets downloaded with integrity checks?
- Is there input validation before data enters fine-tuning pipelines (training data poisoning)?
- Are dataset sources auditable and version-controlled?

### 6. Third-Party Integrations
- Are LLM API keys scoped to minimum permissions?
- Are third-party model inference APIs called over verified TLS?
- Is there a vendor risk assessment for each AI service used?

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **Category**: (e.g., Unpinned Dependency, Unsafe Deserialization, Missing Integrity Check)
3. **Location**: file:line or package name
4. **Risk**: Explain the specific supply chain attack vector
5. **Remediation**: Provide fixed dependency spec, code snippet, or process recommendation

End with a **Supply Chain Risk Matrix** — a table of all components (packages, models, pipelines) rated by risk level, and a prioritized remediation backlog.
