# Port Ocean CARG Integration Package

## 📦 Package Information

- **Name**: `port-ocean-carg`
- **Version**: `0.1.0`
- **Python**: `>=3.12`
- **License**: MIT

## 🚀 Installation

### Using Poetry (Recommended)
```bash
poetry add port-ocean-carg
```

### Using pip
```bash
pip install port-ocean-carg
```

### Development Installation
```bash
git clone <repository-url>
cd carg
poetry install
```

## 🔧 Console Scripts

The package provides several command-line tools:

### JSON Extraction
```bash
# Extract and display sample Port objects
carg-extract-json --samples

# Extract and save to files
carg-extract-json --save

# Extract raw JSON only
carg-extract-json --json-only
```

### Validation
```bash
# Validate extracted objects against Port.io requirements
carg-validate

# Validate specific JSON file
carg-validate --file path/to/objects.json
```

### Integration Testing
```bash
# Run comprehensive integration tests
carg-test
```

## 📚 Python API

### Basic Usage
```python
from port_ocean_carg import CargAPIClient, create_carg_client

# Create a client
client = create_carg_client()

# Or with explicit configuration
client = CargAPIClient(
    api_url="https://your-carg-api.com",
    api_token="your_token"
)

# Get paginated data
async for projects in client.get_projects():
    for project in projects:
        print(f"Project: {project['name']}")
```

### JSON Extraction
```python
from port_ocean_carg import SimplePortExtractor

extractor = SimplePortExtractor()
port_objects = await extractor.extract_all_objects()
print(f"Extracted {len(port_objects)} object types")
```

## 🏗️ Package Structure

```
port_ocean_carg/
├── __init__.py              # Package initialization and exports
├── client.py                # API client (Ocean best practices)
├── main.py                  # Ocean integration handlers
├── extract_port_json.py     # JSON extraction utilities
├── validate_port_objects.py # Object validation tools
├── test_integration.py      # Integration testing
└── py.typed                 # Type hint support
```

## 🔌 Port Ocean Integration

This package is designed as a Port Ocean integration and can be used with the Port Ocean framework:

```bash
# Using Ocean CLI (when integrated)
ocean sail --integration carg

# With configuration
OCEAN__INTEGRATION__CONFIG__CARG_API_URL=https://api.carg.com \
OCEAN__INTEGRATION__CONFIG__CARG_API_TOKEN=your_token \
ocean sail --integration carg
```

## ⚙️ Configuration

### Environment Variables
```bash
# API Configuration
OCEAN__INTEGRATION__CONFIG__CARG_API_URL=https://your-carg-api.com
OCEAN__INTEGRATION__CONFIG__CARG_API_TOKEN=your_api_token

# Optional Settings
OCEAN__INTEGRATION__CONFIG__SYNC_INTERVAL=60
OCEAN__INTEGRATION__CONFIG__ENABLE_HEALTH_CHECKS=true
OCEAN__INTEGRATION__CONFIG__ENABLE_WEBHOOKS=false
OCEAN__INTEGRATION__CONFIG__APP_HOST=https://your-ocean-instance.com
```

### Configuration File (.env)
```env
CARG_API_URL=https://your-carg-api.com
CARG_API_TOKEN=your_api_token
SYNC_INTERVAL=60
ENABLE_HEALTH_CHECKS=true
ENABLE_WEBHOOKS=false
```

## 🧪 Testing

### Run Package Tests
```bash
# Using poetry
poetry run pytest

# Using the test console script
carg-test

# Run specific test
python -m port_ocean_carg.test_integration
```

### Validate Installation
```bash
# Check package imports
python -c "from port_ocean_carg import CargAPIClient; print('✅ Package installed correctly')"

# Test console scripts
carg-extract-json --samples
carg-validate
```

## 🚀 Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install port-ocean-carg

CMD ["ocean", "sail", "--integration", "carg"]
```

### Azure Container Instance
```yaml
# Use provided Azure deployment files
az deployment group create \
  --resource-group rg-port-ocean-carg \
  --template-file infra/main.bicep \
  --parameters containerImage=your-registry/port-ocean-carg:latest
```

## 📊 Supported Resources

The integration synchronizes the following CARG resources:

- **Projects** (`carg-project`)
  - Status, description, owner, budget
  - Azure DevOps integration
  - Tags and metadata

- **Services** (`carg-service`)
  - Health status, version, language
  - Repository information
  - Performance metrics
  - Project relationships

- **Components** (`carg-component`)
  - Type, status, complexity
  - Test coverage metrics
  - Service relationships

- **Deployments** (`carg-deployment`)
  - Status, environment, version
  - Deployment logs and metrics
  - Service relationships

## 🔗 Related Links

- [Port Ocean Documentation](https://ocean.port.io/)
- [API Client Best Practices](https://ocean.port.io/developing-an-integration/implementing-an-api-client)
- [Port.io Platform](https://getport.io/)

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

For development setup, see [DEVELOPMENT.md](DEVELOPMENT.md).