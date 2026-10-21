# Azure AI Foundry CI/CD — IT Support Assistant

A production-ready CI/CD pipeline for a Microsoft Azure AI Foundry hosted Python agent,
using **Bicep** for infrastructure-as-code and **Azure DevOps** for release orchestration.

---

## Architecture Overview

```
Developer / Azure Repos
    Python code, instructions, evaluations, Bicep templates
          |
          v
    CI - Azure DevOps
    Lint → Unit tests → Security → Agent evaluations → Bicep validation
          |
          v
    Infrastructure Stage
    Bicep what-if → Approved infrastructure deployment
          |
          v
    Dev → Test → Production
    Foundry agent release → Smoke tests → QA → Approval → Release
          |
          v
    Monitoring & Rollback
    Agent version, errors, latency, token usage, audit logs
```

### Division of Responsibilities

| Component | Responsibility |
|---|---|
| **Bicep** | Supporting Azure infrastructure (Log Analytics, App Insights, alerts) |
| **Azure DevOps** | CI validation, release orchestration, approvals |
| **Azure Developer CLI (azd)** | Hosted agent lifecycle: publish, version, activate |

> **Note:** The hosted agent is a Foundry data-plane resource managed by `azd deploy`.
> It is NOT declared as a native Bicep `resource` block.

---

## Repository Structure

```
ai-foundry-agent-cicd/
├── azure.yaml                     # AZD project configuration
├── azure-pipelines.yml            # Application CI/CD pipeline
├── infra-pipeline.yml             # Infrastructure-only Bicep pipeline
├── requirements.txt               # Production Python dependencies
├── requirements-dev.txt           # Dev/CI Python dependencies
├── pyproject.toml                 # Project metadata + tool config
├── README.md
├── src/
│   └── it_support_agent/
│       ├── __init__.py
│       ├── agent.py               # Agent definition and SDK calls
│       ├── main.py                # Local development entry point
│       ├── config.py              # Environment config loader
│       └── prompts/
│           └── system.md          # Version-controlled system prompt
├── tests/
│   ├── __init__.py
│   ├── test_unit.py               # Offline unit tests (no model needed)
│   ├── test_agent_evaluation.py   # Evaluation gate (offline + live)
│   └── test_smoke.py              # Post-deployment smoke tests
├── evals/
│   └── test_cases.json            # 14-case evaluation dataset
├── config/
│   ├── dev.json                   # Dev environment settings
│   ├── test.json                  # Test environment settings
│   └── prod.json                  # Production environment settings
└── infra/
    ├── main.bicep                 # Monitoring resources (Law + AppInsights)
    ├── dev.bicepparam
    ├── test.bicepparam
    └── prod.bicepparam
```

---

## Prerequisites

| Prerequisite | What to Verify |
|---|---|
| Azure subscription | Subscription ID, resource groups, Contributor access |
| Microsoft Foundry account | Dev / Test / Prod project endpoints and permissions |
| Model deployment | Model name, quota, availability per project |
| Azure DevOps org & project | Repo and pipeline creation permissions |
| Service connection `sc-ai-foundry-deploy` | Workload Identity Federation scope |
| Foundry Project Manager role | At each target project scope |
| Azure Key Vault | For secrets (API keys, connection strings) |
| Monitoring resources | Existing App Insights / Log Analytics — parameterize if existing |

---

## Initial Setup

```bash
# 1. Sign in
az login

# 2. Verify subscription
az account show

# 3. Initialize hosted-agent project (run from repo root)
azd ai agent init --infra=bicep --deploy-mode code

# 4. Compile Bicep
az bicep build --file infra/main.bicep

# 5. Preview Dev infrastructure
az deployment group what-if \
  --resource-group rg-ai-agent-dev \
  --template-file infra/main.bicep \
  --parameters infra/dev.bicepparam

# 6. Deploy Dev infrastructure
az deployment group create \
  --name "ai-agent-dev-infra" \
  --resource-group rg-ai-agent-dev \
  --template-file infra/main.bicep \
  --parameters infra/dev.bicepparam

# 7. Deploy the hosted agent
azd deploy
```

---

## Azure DevOps Setup

### Environments (Pipelines → Environments)

| Environment | Approval Required |
|---|---|
| `ai-agent-dev` | No |
| `ai-agent-test` | No |
| `ai-agent-prod` | **Yes — configure approval check** |
| `ai-infra-dev` | No |
| `ai-infra-test` | No |
| `ai-infra-prod` | **Yes — configure approval check** |

### Variable Groups (Pipelines → Library)

Each group (`ai-agent-dev`, `ai-agent-test`, `ai-agent-prod`) must contain:

| Variable | Secret? |
|---|---|
| `AZD_ENV_NAME` | No |
| `FOUNDRY_PROJECT_ENDPOINT` | No |
| `MODEL_DEPLOYMENT_NAME` | No |
| `AZURE_SUBSCRIPTION_ID` | No |
| `AZURE_LOCATION` | No |
| `TARGET_RESOURCE_GROUP` | No |
| `API_KEY` (if needed) | **Yes** |

---

## Security Controls

- Branch protection on `main` and `develop`
- Production approvals configured on Azure DevOps environments
- Secrets in Azure Key Vault / secured variable groups
- Workload Identity Federation (no client secrets)
- Agent runtime identity scoped to Foundry project only
- Dependency pinning + pip-audit vulnerability scanning
- Bicep `what-if` required before any infrastructure deployment
- No credentials in parameter files or YAML

---

## Rollback

1. Stop: Cancel further promotion on alert
2. Identify: Locate last known-good agent version + source revision
3. Restore: Route production endpoint to prior validated version
4. Verify: Run smoke tests; confirm correct version receives traffic
5. Document: Preserve all diagnostic evidence; record incident

---

## Monitoring

| Signal | Action |
|---|---|
| Agent activation failure | Fail deployment; block promotion |
| Request failures / timeouts | Alert team |
| Response latency > SLO | Compare; escalate |
| Token / model usage | Monitor cost thresholds |
| Evaluation regressions | Block release |
| Auth / permission errors | Investigate RBAC |
| Safety failures | Block + escalate immediately |

---

## References

- [Deploy a hosted agent](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent)
- [Deploy a hosted agent from source code](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/deploy-hosted-agent-code)
- [Azure YAML reference for hosted agents](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/azure-yaml-reference)
- [Integrate Bicep with Azure Pipelines](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/add-template-to-azure-pipelines)
- [Azure DevOps approvals and checks](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/checks)
