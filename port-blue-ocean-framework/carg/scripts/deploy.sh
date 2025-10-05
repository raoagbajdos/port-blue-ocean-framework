#!/bin/bash

# Deployment script for Port Ocean Integration to Azure
# Usage: ./deploy.sh [environment] [resource-group]

set -e

ENVIRONMENT=${1:-dev}
RESOURCE_GROUP=${2:-rg-port-ocean-${ENVIRONMENT}}
LOCATION="eastus2"

echo "🚀 Deploying Port Ocean Integration to Azure"
echo "Environment: $ENVIRONMENT"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo "❌ Please login to Azure CLI first:"
    echo "az login"
    exit 1
fi

# Check for required environment variables
if [[ -z "$PORT_CLIENT_ID" ]]; then
    echo "❌ PORT_CLIENT_ID environment variable is required"
    exit 1
fi

if [[ -z "$PORT_CLIENT_SECRET" ]]; then
    echo "❌ PORT_CLIENT_SECRET environment variable is required"
    exit 1
fi

# Create resource group if it doesn't exist
echo "📦 Creating resource group if it doesn't exist..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy the Bicep template
echo "🏗️  Deploying infrastructure..."
DEPLOYMENT_NAME="port-ocean-deployment-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infra/main.bicep \
    --parameters @infra/main.${ENVIRONMENT}.parameters.json \
    --parameters portClientId="$PORT_CLIENT_ID" portClientSecret="$PORT_CLIENT_SECRET" \
    --name $DEPLOYMENT_NAME \
    --verbose

# Get the container app URL
echo "🔍 Getting deployment outputs..."
CONTAINER_APP_URL=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name $DEPLOYMENT_NAME \
    --query properties.outputs.containerAppURL.value \
    --output tsv)

echo "✅ Deployment completed successfully!"
echo "🌐 Container App URL: $CONTAINER_APP_URL"
echo "📊 API Documentation: $CONTAINER_APP_URL/docs"
echo "🏥 Health Check: $CONTAINER_APP_URL/health"

# Test the health endpoint
echo "🩺 Testing health endpoint..."
sleep 30  # Wait for the container to be ready
if curl -f -s "$CONTAINER_APP_URL/health" > /dev/null; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed. The application might still be starting up."
fi