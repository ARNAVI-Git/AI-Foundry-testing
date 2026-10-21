// infra/prod.bicepparam
// Production environment parameters for main.bicep
//
// IMPORTANT:
//   - Do NOT put credentials, access tokens, or API keys in this file.
//   - Replace placeholder values with client-approved names and region.
//   - Higher retention (90 days) is set for production compliance.

using './main.bicep'

param location = 'eastus'
param workspaceName = 'ai-agent-prod-law'
param appInsightsName = 'ai-agent-prod-appi'
param retentionInDays = 90
param environmentName = 'prod'
param foundryProjectName = 'it-support-assistant'
