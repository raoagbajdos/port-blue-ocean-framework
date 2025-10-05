# Development Guide

This guide provides comprehensive information for developers working on the Port Ocean CARG integration.

## 🏗️ Development Environment Setup

### Prerequisites

- **Python 3.12+**: Required for the integration
- **Poetry**: For dependency management
- **Docker**: For containerization and testing
- **Azure CLI**: For Azure resource management
- **Git**: For version control

### Initial Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd port-blue-ocean-framework/carg

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
make install

# Copy environment configuration
cp .env.example .env
```

### IDE Configuration

#### VS Code
Recommended extensions:
- Python
- Black Formatter
- Pylance
- Docker
- Azure Tools

#### Settings (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

## 📁 Project Structure

```
carg/
├── .github/                 # GitHub Actions workflows
├── .port/                   # Port.io configuration
│   ├── spec.yaml           # Integration specification
│   └── resources/          # Port resources
├── infra/                  # Azure infrastructure (Bicep)
├── scripts/                # Deployment and utility scripts
├── templates/              # Azure DevOps templates
├── tests/                  # Test files
├── main.py                 # Main integration logic
├── debug.py                # Debug utilities
├── Dockerfile              # Container configuration
├── azure-pipelines.yml     # Azure DevOps pipeline
└── pyproject.toml          # Python project configuration
```

## 🔧 Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

### 2. Testing

```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_specific.py

# Run with coverage
poetry run pytest --cov=. --cov-report=html

# Run integration tests
poetry run pytest tests/integration/
```

### 3. Code Quality

```bash
# Lint with Ruff
poetry run ruff check .

# Format with Black
poetry run black .

# Type checking with MyPy
poetry run mypy .

# All quality checks
make quality-check
```

## 🐳 Local Development with Docker

### Development Container

```bash
# Build development image
docker build -t port-ocean-carg:dev .

# Run with live reload
docker run -v $(pwd):/app \
           -p 8000:8000 \
           --env-file .env \
           port-ocean-carg:dev
```

### Docker Compose for Development

```yaml
version: '3.8'
services:
  port-ocean-carg:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OCEAN__LOG_LEVEL=DEBUG
    env_file:
      - .env
    volumes:
      - .:/app
    command: python main.py
```

## 🧪 Testing Strategy

### Test Categories

1. **Unit Tests** (`tests/unit/`): Test individual functions and classes
2. **Integration Tests** (`tests/integration/`): Test component interactions
3. **End-to-End Tests** (`tests/e2e/`): Test complete workflows

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from main import your_function

def test_your_function():
    """Test your_function with valid input."""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = your_function(input_data)
    
    # Assert
    assert result is not None
    assert result["processed"] is True

@patch('main.external_service')
def test_your_function_with_mock(mock_service):
    """Test your_function with mocked external dependency."""
    # Arrange
    mock_service.get_data.return_value = {"mocked": "data"}
    
    # Act & Assert
    result = your_function()
    assert result["source"] == "mocked"
```

### Test Configuration

```python
# tests/conftest.py
import pytest
from port_ocean.core.ocean_app import OceanApp

@pytest.fixture
def ocean_app():
    """Create OceanApp instance for testing."""
    return OceanApp()

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        "my_custom_id": "test_id_1",
        "my_custom_text": "test text",
        "my_special_score": 1
    }
```

## 🔌 Integration Development

### Port Ocean Framework

The integration extends the Port Ocean framework:

```python
from port_ocean.context.ocean import ocean

@ocean.on_resync()
async def on_resync(kind: str) -> list[dict]:
    """Sync data from source system to Port."""
    # Your implementation here
    return []

@ocean.on_start()
async def on_start() -> None:
    """Initialize resources on startup."""
    # Your initialization code here
    pass
```

### Adding New Resource Types

1. **Update spec.yaml**:
```yaml
features:
  - type: exporter
    resources:
      - kind: your-new-resource
```

2. **Update port-app-config.yml**:
```yaml
resources:
  - kind: your-new-resource
    selector:
      query: 'true'
    port:
      entity:
        mappings:
          identifier: .id
          title: .name
          blueprint: '"yourResourceBlueprint"'
```

3. **Implement sync logic**:
```python
@ocean.on_resync('your-new-resource')
async def resync_your_resource(kind: str) -> list[dict]:
    """Sync your new resource type."""
    # Fetch data from your source system
    return fetch_your_resources()
```

## 📊 Debugging and Monitoring

### Local Debugging

```python
# debug.py
import asyncio
from port_ocean.core.ocean_app import OceanApp

async def debug_integration():
    """Debug the integration locally."""
    app = OceanApp()
    
    # Test specific functionality
    result = await app.integration.on_resync("your-kind")
    print(f"Sync result: {result}")

if __name__ == "__main__":
    asyncio.run(debug_integration())
```

### Logging Configuration

```python
import logging
from loguru import logger

# Configure structured logging
logger.configure(
    handlers=[
        {
            "sink": sys.stdout,
            "format": "{time} | {level} | {message}",
            "level": "INFO"
        }
    ]
)
```

### Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"{func.__name__} completed in {duration:.2f}s")
        return result
    return wrapper

@monitor_performance
async def your_sync_function():
    # Your implementation
    pass
```

## 🔄 CI/CD Development

### Local Pipeline Testing

```bash
# Test Azure DevOps pipeline locally (requires Azure CLI)
az pipelines run --name "Port Ocean CARG"

# Test GitHub Actions locally (requires act)
act -j build-and-test
```

### Pipeline Configuration

- **Azure DevOps**: `azure-pipelines.yml`
- **GitHub Actions**: `.github/workflows/deploy.yml`

Both pipelines include:
- Code quality checks
- Security scanning
- Multi-environment deployment
- Rollback capabilities

## 🔐 Security Best Practices

### Code Security

1. **Never commit secrets** - Use environment variables
2. **Validate input data** - Sanitize all external inputs
3. **Use secure dependencies** - Regular security audits
4. **Implement proper error handling** - Don't expose sensitive information

### Dependency Management

```bash
# Audit dependencies for vulnerabilities
poetry audit

# Update dependencies
poetry update

# Check for outdated packages
poetry show --outdated
```

## 📚 Resources

### Documentation

- [Port Ocean Framework](https://ocean.port.io/)
- [Port.io API Documentation](https://docs.getport.io/)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)

### Tools

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Ruff Linter](https://github.com/astral-sh/ruff)
- [Black Formatter](https://black.readthedocs.io/)
- [Pytest Framework](https://pytest.org/)

### Community

- [Port.io Community](https://getport.io/community)
- [Azure Developer Community](https://techcommunity.microsoft.com/azure)
- [Python Discord](https://discord.gg/python)

## 🤝 Contributing Guidelines

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Follow code style** guidelines (Black, Ruff)
4. **Update documentation** for significant changes
5. **Submit pull request** with clear description
6. **Respond to feedback** during code review

### Code Review Checklist

- [ ] Tests pass and coverage is maintained
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Error handling implemented
- [ ] Logging added for debugging