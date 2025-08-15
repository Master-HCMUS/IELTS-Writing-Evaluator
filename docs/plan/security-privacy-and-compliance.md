# Plan: Security, Privacy & Compliance

Objective
- Secure-by-default implementation for PoC.

Controls
- Secrets in Azure Key Vault; MSI for access; no secrets in code.
- TLS enforced; minimal public exposure; optional IP allowlist.
- Data minimization: do not collect demographics; store only needed fields.
- PII/essay handling: redact in logs where possible; user-provided ID hashed.
- Least-privileged RBAC for resources; separate dev/test containers.

Acceptance
- Static checks: no secrets committed; dependency vulnerability scan passes.
- Runtime: secrets resolved from KV; access logs verified.

Notes
- Document data retention and deletion on request for PoC scope.
