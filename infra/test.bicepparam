// infra/test.bicepparam
// Test / QA environment parameters for main.bicep
//
// IMPORTANT:
//   - Do NOT put credentials, access tokens, or API keys in this file.
//   - Replace placeholder values with client-approved names and region.

using './main.bicep'

param location = 'eastus'
param workspaceName = 'ai-agent-test-law'
param appInsightsName = 'ai-agent-test-appi'
param retentionInDays = 60
param environmentName = 'test'
param foundryProjectName = 'it-support-assistant'
