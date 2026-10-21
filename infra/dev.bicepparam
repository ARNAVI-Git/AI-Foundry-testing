// infra/dev.bicepparam
// Development environment parameters for main.bicep
//
// IMPORTANT:
//   - Do NOT put credentials, access tokens, or API keys in this file.
//   - Replace placeholder values with client-approved names and region.
//   - Validate with: az deployment group what-if --resource-group <rg> \
//       --template-file infra/main.bicep --parameters infra/dev.bicepparam

using './main.bicep'

param location = 'eastus'
param workspaceName = 'ai-agent-dev-law'
param appInsightsName = 'ai-agent-dev-appi'
param retentionInDays = 30
param environmentName = 'dev'
param foundryProjectName = 'it-support-assistant'
