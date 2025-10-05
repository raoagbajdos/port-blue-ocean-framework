# Docker Development Guide

This guide covers Docker-based development and deployment for the Port Ocean CARG integration.

## 📦 Docker Images

### Base Image
The integration uses Python 3.12 slim as the base image for optimal size and security.

### Multi-stage Build
- **Build stage**: Installs dependencies and builds the application
- **Runtime stage**: Contains only the necessary files for production

## 🔧 Local Docker Development

### Build the Image

```bash
# Build the Docker image
docker build -t port-ocean-carg:local .

# Build with specific tag
docker build -t port-ocean-carg:$(git rev-parse --short HEAD) .
```

### Run Locally

```bash
# Run with environment file
docker run --env-file .env -p 8000:8000 port-ocean-carg:local

# Run with environment variables
docker run -e OCEAN__PORT__CLIENT_ID="your-id" \
           -e OCEAN__PORT__CLIENT_SECRET="your-secret" \
           -p 8000:8000 \
           port-ocean-carg:local

# Run in detached mode
docker run -d --name port-ocean-carg \
           --env-file .env \
           -p 8000:8000 \
           port-ocean-carg:local
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🏗️ Production Deployment

### Azure Container Registry (ACR)

```bash
# Login to ACR
az acr login --name your-acr-name

# Tag image for ACR
docker tag port-ocean-carg:local your-acr-name.azurecr.io/port-ocean/carg-integration:latest

# Push to ACR
docker push your-acr-name.azurecr.io/port-ocean/carg-integration:latest
```

### Security Best Practices

1. **Non-root User**: Container runs as non-root user
2. **Minimal Base**: Uses slim Python image
3. **Secrets Management**: Environment variables for sensitive data
4. **Health Checks**: Proper health check endpoints
5. **Resource Limits**: CPU and memory constraints

## 🔍 Debugging

### Container Logs

```bash
# View logs
docker logs port-ocean-carg

# Follow logs
docker logs -f port-ocean-carg

# View last 100 lines
docker logs --tail 100 port-ocean-carg
```

### Interactive Shell

```bash
# Execute bash in running container
docker exec -it port-ocean-carg /bin/bash

# Run a one-off command
docker exec port-ocean-carg python -c "import port_ocean; print('OK')"
```

### Debug Mode

```bash
# Run with debug configuration
docker run -e OCEAN__LOG_LEVEL=DEBUG \
           -e OCEAN__DEBUG=true \
           --env-file .env \
           -p 8000:8000 \
           port-ocean-carg:local
```

## 🧪 Testing

### Test Container Build

```bash
# Build and test in one command
docker build -t port-ocean-carg:test . && \
docker run --rm -e OCEAN__PORT__CLIENT_ID=test \
                -e OCEAN__PORT__CLIENT_SECRET=test \
                port-ocean-carg:test python -c "import main; print('Build successful')"
```

### Integration Tests

```bash
# Run tests in container
docker run --rm -v $(pwd):/app \
           -w /app \
           python:3.12-slim \
           bash -c "pip install poetry && poetry install && poetry run pytest"
```

## 🚀 CI/CD Integration

### GitHub Actions

The `.github/workflows/deploy.yml` includes:
- Multi-stage Docker builds
- Caching for faster builds
- Security scanning
- Push to ACR

### Azure DevOps

The `azure-pipelines.yml` includes:
- Docker build and push tasks
- Container registry integration
- Deployment to Azure Container Apps

## 📊 Monitoring

### Health Checks

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' port-ocean-carg

# Manual health check
curl http://localhost:8000/health
```

### Resource Usage

```bash
# Monitor resource usage
docker stats port-ocean-carg

# Get detailed container info
docker inspect port-ocean-carg
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Binding Issues**
   ```bash
   # Check if port is already in use
   lsof -i :8000
   
   # Use different port
   docker run -p 8080:8000 port-ocean-carg:local
   ```

2. **Permission Issues**
   ```bash
   # Fix Docker socket permissions (Linux)
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Memory Issues**
   ```bash
   # Increase Docker memory limit
   docker run --memory="512m" port-ocean-carg:local
   ```

4. **Environment Variable Issues**
   ```bash
   # Debug environment variables
   docker run --rm port-ocean-carg:local env | grep OCEAN
   ```

## 🔐 Security Considerations

### Image Scanning

```bash
# Scan for vulnerabilities (if using Docker Scout)
docker scout cves port-ocean-carg:local

# Scan with Trivy
trivy image port-ocean-carg:local
```

### Best Practices

1. **Use specific base image tags** (not `latest`)
2. **Regular security updates** for base images
3. **Minimal attack surface** - only necessary packages
4. **Non-root execution** for runtime security
5. **Secret management** via environment variables or Azure Key Vault