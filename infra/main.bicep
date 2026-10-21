// =============================================================
// infra/main.bicep
// Supporting monitoring infrastructure for Azure AI Foundry
// hosted agent CI/CD.
//
// SCOPE: This template manages ONLY supporting Azure resources
// (Log Analytics, Application Insights). It does NOT create or
// modify the Foundry account, Foundry project, or model
// deployments — those are managed separately by the client or
// through the Foundry/AZD workflow.
//
// PREREQUISITES:
//   - Target resource group must already exist.
//   - Deploying identity needs Contributor on the resource group.
// =============================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------

@description('Azure region for all monitoring resources. Must be a region supported by both Log Analytics and Application Insights.')
param location string = resourceGroup().location

@description('Unique name for the Log Analytics workspace. Follow client naming policy.')
@minLength(4)
@maxLength(63)
param workspaceName string

@description('Unique name for the Application Insights resource. Follow client naming policy.')
@minLength(1)
@maxLength(260)
param appInsightsName string

@description('Data retention period in days for the Log Analytics workspace.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('Environment tag to apply to all resources (e.g. dev, test, prod).')
@allowed(['dev', 'test', 'prod'])
param environmentName string

@description('Name of the AI Foundry project this monitoring instance supports. Used for resource tagging only.')
param foundryProjectName string = 'it-support-assistant'

// ---------------------------------------------------------------
// Variables
// ---------------------------------------------------------------

var commonTags = {
  environment: environmentName
  project: foundryProjectName
  managedBy: 'bicep'
  component: 'monitoring'
}

// ---------------------------------------------------------------
// Resources
// ---------------------------------------------------------------

// Log Analytics Workspace
// Provides the underlying workspace for Application Insights
// and can receive Foundry diagnostic logs via diagnostic settings.
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: commonTags
  properties: {
    retentionInDays: retentionInDays
    sku: {
      name: 'PerGB2018'
    }
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
      disableLocalAuth: false
    }
    workspaceCapping: {
      // Set to -1 for no daily cap, or a positive value (GB/day) to limit cost.
      dailyQuotaGb: -1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Application Insights (workspace-based)
// Collects telemetry from the agent runtime and any application
// instrumentation. Connect the Foundry agent to this via the
// APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: commonTags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: retentionInDays
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ---------------------------------------------------------------
// Alert Rules
// ---------------------------------------------------------------

// Alert: high failure rate (5xx errors > 5 in 5 minutes)
resource failureRateAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${appInsightsName}-failure-rate-alert'
  location: 'global'
  tags: commonTags
  properties: {
    description: 'Fires when server error count exceeds threshold — investigate agent deployment or runtime errors.'
    severity: 1
    enabled: true
    scopes: [appInsights.id]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighFailureRate'
          metricName: 'requests/failed'
          operator: 'GreaterThan'
          threshold: 5
          timeAggregation: 'Count'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    autoMitigate: true
    actions: []  // Add action group resource IDs here for email/SMS/webhook
  }
}

// Alert: high response latency (P95 > 10 seconds)
resource latencyAlert 'Microsoft.Insights/metricAlerts@2018-03-01' = {
  name: '${appInsightsName}-latency-alert'
  location: 'global'
  tags: commonTags
  properties: {
    description: 'Fires when request duration exceeds the agreed SLO threshold.'
    severity: 2
    enabled: true
    scopes: [appInsights.id]
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'HighLatency'
          metricName: 'requests/duration'
          operator: 'GreaterThan'
          threshold: 10000  // milliseconds
          timeAggregation: 'Average'
          criterionType: 'StaticThresholdCriterion'
        }
      ]
    }
    autoMitigate: true
    actions: []
  }
}

// ---------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------

@description('Resource ID of the Log Analytics workspace.')
output logAnalyticsResourceId string = logAnalytics.id

@description('Resource ID of the Application Insights resource.')
output appInsightsResourceId string = appInsights.id

@description('Application Insights connection string. Use this to configure agent telemetry. Store securely — do not log.')
output appInsightsConnectionString string = appInsights.properties.ConnectionString

@description('Application Insights instrumentation key (legacy; prefer connection string).')
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey

@description('Log Analytics workspace ID.')
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
