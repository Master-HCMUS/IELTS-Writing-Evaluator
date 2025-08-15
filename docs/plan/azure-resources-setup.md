# Plan: Azure Resources Setup

Objective
- Provision minimal, cost-efficient Azure resources for one-week PoC.

Resources
- Azure OpenAI: deployments for gpt-4o-mini (primary), gpt-4o (vision fallback).
- Storage account: Blob (runs, prompts, calibration artifacts), Table/ADLS optional.
- Azure Container Apps or App Service: host FastAPI.
- Azure Key Vault: secrets (API keys, connection strings).
- Azure Monitor / Application Insights: logs, metrics, traces.
- Optional: Azure Container Registry (for CI/CD images), Log Analytics workspace.

Key Tasks
- Choose region with both models available and favorable pricing.
- Create RBAC assignments; restrict keys via Key Vault; disable public endpoints where feasible (egress rules).
- Configure network and minimal IP restrictions; HTTPS only.
- Establish alerts: latency, error rate, cost budgets.

Acceptance
- End-to-end call from Container App to Azure OpenAI succeeds.
- Secrets resolved from Key Vault; no secrets in code.
- Basic dashboards in App Insights show requests, latency, token usage.

Notes
- Keep SKU minimal; stop non-prod resources off-hours to meet cost goals.
