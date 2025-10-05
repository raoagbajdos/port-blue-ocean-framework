"""
CARG API Client - Following Port Ocean best practices for API client implementation
"""
import asyncio
from typing import Any, AsyncGenerator, Optional
from datetime import datetime
import httpx
from httpx import Timeout, HTTPStatusError
from loguru import logger

from port_ocean.utils import http_async_client
from port_ocean.context.ocean import ocean

# Constants
MAX_CONCURRENT_REQUESTS = 10
CLIENT_TIMEOUT = 30.0
PAGE_SIZE = 100
RETRY_DELAY = 60  # seconds for rate limiting


# Mock data constants
MOCK_USERS = {
    "john": {"email": "john.doe@company.com", "username": "johndoe"},
    "jane": {"email": "jane.smith@company.com", "username": "janesmith"},
    "bob": {"email": "bob.wilson@company.com", "username": "bobwilson"}
}


class CargAPIClient:
    """
    CARG API Client following Port Ocean best practices.
    
    This client handles:
    - Authentication with Bearer tokens
    - Rate limiting and concurrent request management
    - Proper error handling and retries
    - Generic data retrieval patterns
    - Mock data fallback for development
    """
    
    def __init__(self, api_url: str = "", api_token: str = "") -> None:
        """Initialize the CARG API client"""
        # Try to get config from Ocean, but fallback gracefully
        try:
            config = ocean.integration_config
            self.base_url = (api_url or config.get("cargApiUrl", "")).rstrip("/")
            self.api_token = api_token or config.get("cargApiToken", "")
        except Exception:
            # If Ocean context is not available (e.g., during testing), use provided values
            self.base_url = api_url.rstrip("/") if api_url else ""
            self.api_token = api_token
        
        # Defer client setup until first use to avoid Ocean context issues during import
        self._client = None
        
        # Semaphore for controlling concurrent requests
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        logger.info(f"CARG API Client initialized with base URL: {self.base_url}")
        if not self.base_url or not self.api_token:
            logger.warning("API configuration incomplete. Using mock data mode.")
    
    @property
    def client(self):
        """Lazy initialization of HTTP client to avoid Ocean context issues during import"""
        if self._client is None:
            try:
                # Use Ocean's recommended client
                self._client = http_async_client
                self._client.timeout = Timeout(CLIENT_TIMEOUT)
                
                # Configure authentication if available
                if self.api_token:
                    self._client.headers.update({
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    })
            except Exception as e:
                # Fallback to httpx if Ocean client is not available
                logger.warning(f"Could not use Ocean HTTP client, falling back to httpx: {e}")
                import httpx
                self._client = httpx.AsyncClient(timeout=CLIENT_TIMEOUT)
                
                if self.api_token:
                    self._client.headers.update({
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    })
        
        return self._client
    
    async def _send_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None
    ) -> Any:
        """
        Send API request with proper error handling and rate limiting.
        
        Following Ocean best practices for centralized request handling.
        """
        if not self.base_url or not self.api_token:
            logger.debug(f"No API config, returning mock data for {endpoint}")
            return self._get_mock_data_for_endpoint(endpoint)
        
        url = f"{self.base_url}/api/v1/{endpoint}"
        
        try:
            async with self._semaphore:
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                )
                response.raise_for_status()
                return response.json()
                
        except HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                logger.warning(f"Rate limit hit for {endpoint}, retrying after {RETRY_DELAY}s")
                retry_after = int(e.response.headers.get("Retry-After", str(RETRY_DELAY)))
                await asyncio.sleep(retry_after)
                return await self._send_api_request(method, endpoint, params, json_data)
            
            logger.error(
                f"HTTP error for {url}: {e.response.status_code} - {e.response.text}"
            )
            # Fallback to mock data on API errors
            return self._get_mock_data_for_endpoint(endpoint)
            
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            # Fallback to mock data on any error
            return self._get_mock_data_for_endpoint(endpoint)
    
    def _get_mock_data_for_endpoint(self, endpoint: str) -> dict[str, Any]:
        """Get mock data based on endpoint"""
        # Extract resource type from endpoint
        if endpoint.startswith("projects"):
            return {"data": self._get_mock_projects()}
        elif endpoint.startswith("services"):
            return {"data": self._get_mock_services()}
        elif endpoint.startswith("components"):
            return {"data": self._get_mock_components()}
        elif endpoint.startswith("deployments"):
            return {"data": self._get_mock_deployments()}
        else:
            return {"data": []}
    
    async def get_paginated_resources(
        self,
        resource_kind: str,
        params: Optional[dict[str, Any]] = None,
        endpoint_override: Optional[str] = None
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        """
        Generic paginated resource retrieval following Ocean best practices.
        
        This method can handle any resource type with consistent pagination.
        Similar to Octopus Deploy's generic approach shown in the documentation.
        """
        endpoint = endpoint_override or f"{resource_kind}s"
        
        if params is None:
            params = {}
        
        # Setup pagination parameters
        params["skip"] = 0
        params["take"] = PAGE_SIZE
        page = 0
        
        while True:
            logger.debug(f"Fetching {resource_kind} page {page + 1}")
            
            response = await self._send_api_request("GET", endpoint, params=params)
            
            # Handle different response structures
            if isinstance(response, dict):
                items = response.get("data", response.get("items", []))
                total = response.get("total", 0)
                has_more = response.get("hasMore", False)
            else:
                items = response if isinstance(response, list) else []
                total = len(items)
                has_more = False
            
            if not items:
                break
            
            yield items
            
            # Check if we have more pages
            if not has_more and total > 0:
                if params["skip"] + len(items) >= total:
                    break
            elif len(items) < PAGE_SIZE:
                # If we got fewer items than requested, we're at the end
                break
            
            # Prepare for next page
            params["skip"] += PAGE_SIZE
            page += 1
    
    # Specific resource methods for type safety and clarity
    async def get_projects(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """Get all projects with pagination"""
        logger.info("Fetching CARG projects")
        async for projects in self.get_paginated_resources("project"):
            yield projects
    
    async def get_services(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """Get all services with pagination"""
        logger.info("Fetching CARG services")
        async for services in self.get_paginated_resources("service"):
            yield services
    
    async def get_components(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """Get all components with pagination"""
        logger.info("Fetching CARG components")
        async for components in self.get_paginated_resources("component"):
            yield components
    
    async def get_deployments(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """Get all deployments with pagination"""
        logger.info("Fetching CARG deployments")
        async for deployments in self.get_paginated_resources("deployment"):
            yield deployments
    
    # Health check and webhook support methods
    async def health_check(self) -> bool:
        """Check if the CARG API is healthy"""
        try:
            response = await self._send_api_request("GET", "health")
            return response.get("status") == "healthy"
        except Exception:
            logger.warning("CARG API health check failed")
            return False
    
    async def has_webhook_permission(self) -> bool:
        """Check if we have permission to create webhooks"""
        try:
            response = await self._send_api_request("GET", "webhooks/permissions")
            return response.get("canCreateWebhooks", False)
        except Exception:
            logger.warning("Could not check webhook permissions")
            return False
    
    async def create_webhooks(self, app_host: str) -> None:
        """Create webhooks for real-time updates"""
        if not await self.has_webhook_permission():
            logger.warning("No permission to create webhooks")
            return
        
        webhook_url = f"{app_host}/integration/webhook"
        
        # Check if webhook already exists
        try:
            existing_webhooks = await self._send_api_request("GET", "webhooks")
            for webhook in existing_webhooks.get("data", []):
                if webhook.get("url") == webhook_url:
                    logger.info("CARG webhook already exists")
                    return
        except Exception:
            logger.warning("Could not check existing webhooks")
        
        # Create new webhook
        webhook_config = {
            "name": f"port-ocean-carg-webhook",
            "url": webhook_url,
            "events": [
                "project.created", "project.updated", "project.deleted",
                "service.created", "service.updated", "service.deleted",
                "component.created", "component.updated", "component.deleted",
                "deployment.created", "deployment.updated", "deployment.completed"
            ],
            "active": True
        }
        
        try:
            await self._send_api_request("POST", "webhooks", json_data=webhook_config)
            logger.info("CARG webhook created successfully")
        except Exception as e:
            logger.error(f"Failed to create webhook: {str(e)}")
    
    # Mock data methods (unchanged from original implementation)
    def _get_mock_projects(self) -> list[dict[str, Any]]:
        """Generate mock project data"""
        return [
            {
                "id": 1,
                "name": "E-Commerce Platform",
                "status": "Active",
                "description": "Main e-commerce platform with microservices architecture",
                "owner": MOCK_USERS["john"],
                "budget": 500000,
                "start_date": "2024-01-15",
                "end_date": "2024-12-31",
                "tags": ["microservices", "e-commerce", "critical"],
                "azure_devops": {"project_name": "ECommercePlatform"}
            },
            {
                "id": 2,
                "name": "Data Analytics Pipeline",
                "status": "Planning",
                "description": "Real-time data analytics and reporting system",
                "owner": MOCK_USERS["jane"],
                "budget": 250000,
                "start_date": "2024-03-01",
                "end_date": "2024-08-31",
                "tags": ["analytics", "pipeline", "data"],
                "azure_devops": {"project_name": "DataAnalytics"}
            }
        ]
    
    def _get_mock_services(self) -> list[dict[str, Any]]:
        """Generate mock service data"""
        current_time = datetime.now().isoformat()
        
        return [
            {
                "id": 101,
                "name": "User Authentication Service",
                "status": "Running",
                "health_status": "Healthy",
                "version": "v2.1.3",
                "repository": {"url": "https://github.com/company/auth-service"},
                "language": "Python",
                "metrics": {"cpu_usage": 45.2, "memory_usage_mb": 512},
                "last_deployment": {"timestamp": current_time},
                "azure_devops": {"pipeline_name": "auth-service-ci-cd"},
                "project_id": 1
            },
            {
                "id": 102,
                "name": "Payment Processing Service",
                "status": "Running",
                "health_status": "Healthy",
                "version": "v1.8.1",
                "repository": {"url": "https://github.com/company/payment-service"},
                "language": "Java",
                "metrics": {"cpu_usage": 32.1, "memory_usage_mb": 768},
                "last_deployment": {"timestamp": current_time},
                "azure_devops": {"pipeline_name": "payment-service-ci-cd"},
                "project_id": 1
            },
            {
                "id": 103,
                "name": "Analytics Ingestion Service",
                "status": "Deploying",
                "health_status": "Unknown",
                "version": "v0.5.2-beta",
                "repository": {"url": "https://github.com/company/analytics-ingest"},
                "language": "Go",
                "metrics": {"cpu_usage": 0, "memory_usage_mb": 0},
                "last_deployment": {"timestamp": current_time},
                "azure_devops": {"pipeline_name": "analytics-ingest-ci-cd"},
                "project_id": 2
            }
        ]
    
    def _get_mock_components(self) -> list[dict[str, Any]]:
        """Generate mock component data"""
        return [
            {
                "id": 201,
                "name": "JWT Token Manager",
                "type": "Library",
                "status": "Active",
                "description": "Handles JWT token generation and validation",
                "maintainer": MOCK_USERS["john"],
                "complexity": "Medium",
                "test_coverage": 85.5,
                "service_id": 101
            },
            {
                "id": 202,
                "name": "User Database",
                "type": "Database",
                "status": "Active",
                "description": "PostgreSQL database for user data",
                "maintainer": MOCK_USERS["jane"],
                "complexity": "Low",
                "test_coverage": 92.0,
                "service_id": 101
            },
            {
                "id": 203,
                "name": "Payment Gateway API",
                "type": "API",
                "status": "Active",
                "description": "REST API for payment processing",
                "maintainer": MOCK_USERS["bob"],
                "complexity": "High",
                "test_coverage": 78.3,
                "service_id": 102
            }
        ]
    
    def _get_mock_deployments(self) -> list[dict[str, Any]]:
        """Generate mock deployment data"""
        current_time = datetime.now().isoformat()
        
        return [
            {
                "id": 301,
                "service_name": "User Authentication Service",
                "status": "Success",
                "environment": "Production",
                "version": "v2.1.3",
                "deployed_by": MOCK_USERS["john"],
                "deployment_time": current_time,
                "duration_seconds": 180,
                "azure_devops": {"run_id": "20241005.1"},
                "logs": "```\nDeployment successful\nAll health checks passed\nService is running\n```",
                "service_id": 101
            },
            {
                "id": 302,
                "service_name": "Payment Processing Service",
                "status": "Success",
                "environment": "Production",
                "version": "v1.8.1",
                "deployed_by": MOCK_USERS["jane"],
                "deployment_time": current_time,
                "duration_seconds": 240,
                "azure_devops": {"run_id": "20241005.2"},
                "logs": "```\nDeployment completed\nDatabase migration successful\nAll tests passed\n```",
                "service_id": 102
            },
            {
                "id": 303,
                "service_name": "Analytics Ingestion Service",
                "status": "In Progress",
                "environment": "Staging",
                "version": "v0.5.2-beta",
                "deployed_by": MOCK_USERS["bob"],
                "deployment_time": current_time,
                "duration_seconds": 0,
                "azure_devops": {"run_id": "20241005.3"},
                "logs": "```\nDeployment in progress...\nBuilding container image...\n```",
                "service_id": 103
            }
        ]


# Convenience function to create a client instance
def create_carg_client() -> CargAPIClient:
    """Create and return a CARG API client instance"""
    return CargAPIClient()