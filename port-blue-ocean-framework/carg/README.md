# Port Ocean CARG Integration

A [Port Ocean](https://ocean.port.io) integration for syncing data with Port.io using Python, Azure DevOps, and Azure Container Apps.

## 🚀 Overview

This integration provides a robust, cloud-native solution for connecting your systems to Port.io's developer portal. It's built with Python 3.12, deployed on Azure Container Apps, and includes complete CI/CD pipelines for both Azure DevOps and GitHub Actions.

## ✨ Features

- **Python 3.12** with Poetry for dependency management
- **Azure Container Apps** deployment for scalable, serverless hosting
- **Azure DevOps Pipelines** for CI/CD
- **GitHub Actions** alternative workflow
- **Infrastructure as Code** using Azure Bicep
- **Health checks** and monitoring
- **Multi-environment** support (dev, staging, prod)
- **Automatic scaling** based on HTTP requests

## 📋 Prerequisites

- Python 3.12+
- Poetry
- Azure CLI
- Azure subscription
- Port.io account and API credentials
- Docker (for containerization)

## 🛠️ Local Development Setup

### 1. Clone and Setup

```bash
cd carg
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
make install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file with your Port.io credentials:

```env
OCEAN__PORT__CLIENT_ID=your-port-client-id
OCEAN__PORT__CLIENT_SECRET=your-port-client-secret
OCEAN__INTEGRATION__IDENTIFIER=carg
OCEAN__PORT__BASE_URL=https://api.getport.io
OCEAN__EVENT_LISTENER__TYPE=POLLING
OCEAN__INITIALIZE_PORT_RESOURCES=true
```

### 3. Run Locally

```bash
# Start the integration
make run

# Or use Ocean CLI
ocean sail

# Or run with Python directly
source .venv/bin/activate
python main.py
```

The integration will be available at:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## ☁️ Azure Deployment

### Option 1: Using Azure Developer CLI (Recommended)

```bash
# Install azd if not already installed
curl -fsSL https://aka.ms/install-azd.sh | bash

# Initialize and deploy
azd auth login
azd up
```

### Option 2: Using Deployment Script

```bash
# Set required environment variables
export PORT_CLIENT_ID="your-port-client-id"
export PORT_CLIENT_SECRET="your-port-client-secret"

# Deploy to development
./scripts/deploy.sh dev

# Deploy to production
./scripts/deploy.sh prod rg-port-ocean-prod
```

### Option 3: Manual Bicep Deployment

```bash
# Login to Azure
az login

# Create resource group
az group create --name rg-port-ocean-dev --location eastus2

# Deploy infrastructure
az deployment group create \
    --resource-group rg-port-ocean-dev \
    --template-file infra/main.bicep \
    --parameters @infra/main.dev.parameters.json \
    --parameters portClientId="$PORT_CLIENT_ID" portClientSecret="$PORT_CLIENT_SECRET"
```

## 🔄 CI/CD Pipelines

### Azure DevOps Setup

1. **Create Azure DevOps Project**
2. **Set up Variable Groups** with these variables:
   - `PORT_CLIENT_ID` (secret)
   - `PORT_CLIENT_SECRET` (secret)
   - `azureServiceConnection`
3. **Import the pipeline** from `azure-pipelines.yml`

### GitHub Actions Setup

1. **Configure Repository Secrets**:
   ```
   AZURE_CLIENT_ID
   AZURE_TENANT_ID
   AZURE_SUBSCRIPTION_ID
   PORT_CLIENT_ID
   PORT_CLIENT_SECRET
   ACR_LOGIN_SERVER
   ACR_USERNAME
   ACR_PASSWORD
   ```

2. **Set up Environments**:
   - `development` (auto-deploy from develop branch)
   - `production` (auto-deploy from main branch)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Azure DevOps  │───▶│  Container Apps  │───▶│    Port.io      │
│   or GitHub     │    │   Environment    │    │   Platform      │
│   Actions       │    └──────────────────┘    └─────────────────┘
└─────────────────┘              │
                                │
                    ┌──────────────────┐
                    │ Log Analytics    │
                    │ Workspace        │
                    └──────────────────┘
```

### Components

- **Container App**: Hosts the Port Ocean integration
- **Container Apps Environment**: Provides the runtime environment
- **Log Analytics Workspace**: Centralized logging and monitoring
- **Application Insights**: Performance monitoring (optional)

## 🔧 Configuration

### Port Configuration

The integration includes default Port.io configuration:

- **Spec**: `.port/spec.yaml` - Integration specification
- **Blueprints**: `.port/resources/blueprints.json` - Port entity blueprints
- **Mapping**: `.port/resources/port-app-config.yml` - Data mapping configuration

### Azure Configuration

Environment-specific parameters are defined in:

- `infra/main.dev.parameters.json` - Development environment
- `infra/main.prod.parameters.json` - Production environment

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=. --cov-report=html

# Code quality checks
poetry run ruff check .
poetry run black --check .
```

## 📊 Monitoring

### Health Checks

- **Endpoint**: `/health`
- **Kubernetes**: Liveness and readiness probes configured
- **Azure**: Application Insights integration available

### Logging

- **Local**: Console output with structured logging
- **Azure**: Log Analytics Workspace integration
- **Levels**: Configurable via environment variables

### Metrics

- **Performance**: Response times, request counts
- **Business**: Data sync success rates, entity counts
- **Infrastructure**: CPU, memory, replica count

## 🚨 Troubleshooting

### Common Issues

1. **Python Version Mismatch**
   ```bash
   poetry env use python3.12
   poetry install
   ```

2. **Port.io Authentication**
   - Verify `PORT_CLIENT_ID` and `PORT_CLIENT_SECRET`
   - Check API endpoint: `OCEAN__PORT__BASE_URL`

3. **Azure Deployment Failures**
   ```bash
   # Check deployment status
   az deployment group list --resource-group rg-port-ocean-dev
   
   # View container logs
   az containerapp logs show --name ca-port-ocean-carg-dev --resource-group rg-port-ocean-dev
   ```

### Debug Mode

```bash
# Enable debug logging
export OCEAN__LOG_LEVEL=DEBUG

# Run with debug configuration
python debug.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run quality checks: `make lint` and `make test`
5. Commit changes: `git commit -m 'Add your feature'`
6. Push branch: `git push origin feature/your-feature`
7. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Port Ocean Documentation](https://ocean.port.io/)
- [Port.io Platform](https://getport.io/)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
- [Azure DevOps](https://dev.azure.com/)

## 📞 Support

For questions and support:

- **Port.io**: [Documentation](https://docs.getport.io/)
- **Azure**: [Support Center](https://azure.microsoft.com/support/)
- **Issues**: [GitHub Issues](https://github.com/your-org/port-ocean-carg/issues)