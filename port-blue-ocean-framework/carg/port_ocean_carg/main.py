from typing import Any
from loguru import logger

from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE

# Import the proper API client
from client import create_carg_client

# Global CARG API client instance following Ocean best practices
carg_client = create_carg_client()


# Resource-specific sync handlers using the new client architecture
@ocean.on_resync("carg-project")
async def resync_projects(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    """Sync CARG projects using paginated retrieval"""
    logger.info(f"Syncing {kind} from CARG system")
    total_count = 0
    
    async for projects_batch in carg_client.get_projects():
        logger.debug(f"Processing batch of {len(projects_batch)} projects")
        total_count += len(projects_batch)
        
        for project in projects_batch:
            yield project
    
    logger.info(f"Found {total_count} projects total")


@ocean.on_resync("carg-service")
async def resync_services(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    """Sync CARG services using paginated retrieval"""
    logger.info(f"Syncing {kind} from CARG system")
    total_count = 0
    
    async for services_batch in carg_client.get_services():
        logger.debug(f"Processing batch of {len(services_batch)} services")
        total_count += len(services_batch)
        
        for service in services_batch:
            yield service
    
    logger.info(f"Found {total_count} services total")


@ocean.on_resync("carg-component")
async def resync_components(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    """Sync CARG components using paginated retrieval"""
    logger.info(f"Syncing {kind} from CARG system")
    total_count = 0
    
    async for components_batch in carg_client.get_components():
        logger.debug(f"Processing batch of {len(components_batch)} components")
        total_count += len(components_batch)
        
        for component in components_batch:
            yield component
    
    logger.info(f"Found {total_count} components total")


@ocean.on_resync("carg-deployment")
async def resync_deployments(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    """Sync CARG deployments using paginated retrieval"""
    logger.info(f"Syncing {kind} from CARG system")
    total_count = 0
    
    async for deployments_batch in carg_client.get_deployments():
        logger.debug(f"Processing batch of {len(deployments_batch)} deployments")
        total_count += len(deployments_batch)
        
        for deployment in deployments_batch:
            yield deployment
    
    logger.info(f"Found {total_count} deployments total")


# General resync handler (fallback)
@ocean.on_resync()
async def on_resync(kind: str) -> list[dict[Any, Any]]:
    """Fallback resync handler for any unhandled kinds"""
    logger.warning(f"No specific handler for kind: {kind}")
    return []


# Integration lifecycle handlers
@ocean.on_start()
async def on_start() -> None:
    """Initialize the integration with proper client architecture"""
    logger.info("Starting CARG integration with Ocean best practices")
    
    # Validate configuration
    config = ocean.integration_config
    api_url = config.get("cargApiUrl")
    api_token = config.get("cargApiToken")
    
    if not api_url or not api_token:
        logger.warning("CARG API configuration not provided. Running with mock data.")
        logger.info("To use real data, set OCEAN__INTEGRATION__CONFIG__CARG_API_URL and OCEAN__INTEGRATION__CONFIG__CARG_API_TOKEN")
    else:
        logger.info(f"CARG integration initialized with API URL: {api_url}")
        
        # Perform health check if configuration is available
        if await carg_client.health_check():
            logger.info("✅ CARG API health check passed")
        else:
            logger.warning("⚠️ CARG API health check failed - using mock data")
    
    # Log configuration settings
    sync_interval = config.get("syncInterval", 60)
    enable_health_checks = config.get("enableHealthChecks", True)
    enable_webhooks = config.get("enableWebhooks", False)
    
    logger.info("Configuration:")
    logger.info(f"  - Sync Interval: {sync_interval} minutes")
    logger.info(f"  - Health Checks: {enable_health_checks}")
    logger.info(f"  - Webhooks: {enable_webhooks}")
    
    if config.get("azureDevOpsUrl"):
        logger.info(f"  - Azure DevOps URL: {config.get('azureDevOpsUrl')}")
    
    # Setup webhooks if enabled and configured
    if enable_webhooks and api_url and api_token:
        app_host = config.get("appHost")
        if app_host:
            try:
                await carg_client.create_webhooks(app_host)
            except Exception as e:
                logger.warning(f"Failed to setup webhooks: {str(e)}")


if __name__ == "__main__":
    # For local development and testing
    logger.info("CARG Integration starting in development mode...")
    
    # You can add any initialization code here for local testing
