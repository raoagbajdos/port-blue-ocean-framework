@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the container app.')
param containerAppName string = 'ca-port-ocean-carg'

@description('Name of the container apps environment.')
param containerAppsEnvironmentName string = 'cae-port-ocean'

@description('Name of the log analytics workspace.')
param logAnalyticsWorkspaceName string = 'law-port-ocean'

@description('Container image name.')
param containerImage string = 'your-acr.azurecr.io/port-ocean/carg-integration:latest'

@description('Port.io client ID.')
@secure()
param portClientId string

@description('Port.io client secret.')
@secure()
param portClientSecret string

@description('Environment name (dev, staging, prod).')
param environmentName string = 'dev'

@description('Target port for the container.')
param targetPort int = 8000

@description('CPU allocation for the container app.')
param cpu string = '0.25'

@description('Memory allocation for the container app.')
param memory string = '0.5Gi'

@description('Minimum number of replicas.')
param minReplicas int = 1

@description('Maximum number of replicas.')
param maxReplicas int = 3

// Tags for resource management
var commonTags = {
  Environment: environmentName
  Project: 'PortOcean'
  Component: 'Integration'
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  tags: commonTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      searchVersion: 1
      legacy: 0
    }
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  tags: commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
    zoneRedundant: false
  }
}

// Container App
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  tags: commonTags
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      secrets: [
        {
          name: 'port-client-id'
          value: portClientId
        }
        {
          name: 'port-client-secret'
          value: portClientSecret
        }
      ]
    }
    template: {
      revisionSuffix: 'v${substring(uniqueString(deployment().name), 0, 6)}'
      containers: [
        {
          name: 'port-ocean-carg'
          image: containerImage
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: [
            {
              name: 'OCEAN__PORT__CLIENT_ID'
              secretRef: 'port-client-id'
            }
            {
              name: 'OCEAN__PORT__CLIENT_SECRET'
              secretRef: 'port-client-secret'
            }
            {
              name: 'OCEAN__INTEGRATION__IDENTIFIER'
              value: 'carg'
            }
            {
              name: 'OCEAN__PORT__BASE_URL'
              value: 'https://api.getport.io'
            }
            {
              name: 'OCEAN__EVENT_LISTENER__TYPE'
              value: 'POLLING'
            }
            {
              name: 'OCEAN__INITIALIZE_PORT_RESOURCES'
              value: 'true'
            }
            {
              name: 'ENVIRONMENT'
              value: environmentName
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 5
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scale-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
@description('Container App FQDN')
output containerAppFQDN string = containerApp.properties.configuration.ingress.fqdn

@description('Container App URL')
output containerAppURL string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('Container App Resource ID')
output containerAppResourceId string = containerApp.id

@description('Container Apps Environment Resource ID')
output containerAppsEnvironmentResourceId string = containerAppsEnvironment.id

@description('Log Analytics Workspace Resource ID')
output logAnalyticsWorkspaceResourceId string = logAnalyticsWorkspace.id