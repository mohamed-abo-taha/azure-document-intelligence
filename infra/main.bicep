// Infrastructure for the document-intelligence RAG service on Azure.
// Compile/validate locally with:  bicep build infra/main.bicep

@description('Base name for all resources')
param namePrefix string = 'docintel'

@description('Location')
param location string = resourceGroup().location

@description('Container image, e.g. <acr>.azurecr.io/docintel-api:latest')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

var suffix = uniqueString(resourceGroup().id)

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-law'
  location: location
  properties: { sku: { name: 'PerGB2018' }, retentionInDays: 30 }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namePrefix}-appi'
  location: location
  kind: 'web'
  properties: { Application_Type: 'web', WorkspaceResourceId: law.id }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower('${namePrefix}st${suffix}')
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: { minimumTlsVersion: 'TLS1_2', allowBlobPublicAccess: false }
}
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}
resource docsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'documents'
}

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: toLower('${namePrefix}-search-${suffix}')
  location: location
  sku: { name: 'basic' }
  properties: { replicaCount: 1, partitionCount: 1 }
}

resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${namePrefix}-aoai'
  location: location
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: { customSubDomainName: toLower('${namePrefix}aoai${suffix}') }
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: toLower('${namePrefix}cosmos${suffix}')
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [ { locationName: location, failoverPriority: 0 } ]
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: toLower('${namePrefix}acr${suffix}')
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: true }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }
  }
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-api'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: { external: true, targetPort: 8000 }
      secrets: [
        { name: 'storage-connection', value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=core.windows.net' }
        { name: 'search-key', value: search.listAdminKeys().primaryKey }
        { name: 'aoai-key', value: openai.listKeys().key1 }
        { name: 'cosmos-connection', value: cosmos.listConnectionStrings().connectionStrings[0].connectionString }
        { name: 'appinsights-connection', value: appInsights.properties.ConnectionString }
      ]
    }
    template: {
      containers: [
        {
          name: 'docintel-api'
          image: containerImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'VECTOR_BACKEND', value: 'azure_search' }
            { name: 'ANSWER_BACKEND', value: 'azure_openai' }
            { name: 'DOC_BACKEND', value: 'azure_blob' }
            { name: 'FEEDBACK_BACKEND', value: 'cosmos' }
            { name: 'AZURE_SEARCH_ENDPOINT', value: 'https://${search.name}.search.windows.net' }
            { name: 'AZURE_SEARCH_KEY', secretRef: 'search-key' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openai.properties.endpoint }
            { name: 'AZURE_OPENAI_KEY', secretRef: 'aoai-key' }
            { name: 'AZURE_STORAGE_CONNECTION_STRING', secretRef: 'storage-connection' }
            { name: 'COSMOS_CONNECTION_STRING', secretRef: 'cosmos-connection' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', secretRef: 'appinsights-connection' }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [ { name: 'http', http: { metadata: { concurrentRequests: '50' } } } ]
      }
    }
  }
}

output apiFqdn string = app.properties.configuration.ingress.fqdn
output searchName string = search.name
output openaiEndpoint string = openai.properties.endpoint
output cosmosName string = cosmos.name
