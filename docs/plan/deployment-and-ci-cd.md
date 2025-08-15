# Plan: Deployment & CI/CD

Objective
- Containerize FastAPI and deploy to Azure Container Apps (or App Service) with CI/CD.

Deliverables
- Dockerfile (slim, non-root), health endpoints, readiness checks.
- GitHub Actions: build, scan, push to ACR; deploy to Container Apps.
- Env config via Key Vault and App Settings.

Key Tasks
- Build-time: pin Python and SDK versions; cache wheels; run tests.
- Runtime: gunicorn/uvicorn settings; graceful timeouts; structured logs.
- Deployment: blue/green or revision-based; rollbacks; smoke tests.

Acceptance
- One-click pipeline from main branch to dev environment.
- Post-deploy smoke test calls /score successfully.

Risks/Mitigations
- Cold starts → minimal worker count; pre-warm ping if needed.
