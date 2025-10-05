"""
Port Ocean CARG Integration

A Port Ocean integration for CARG (Cloud Architecture Resource Graph) system that synchronizes
projects, services, components, and deployments into your Port.io catalog.

Features:
- Syncs CARG projects, services, components, and deployments
- Supports real-time updates via webhooks
- Follows Port Ocean best practices for API client implementation
- Includes comprehensive testing and validation tools
- Provides JSON extraction utilities for debugging

Usage:
    from carg import CargAPIClient, create_carg_client
    
    # Create a client
    client = create_carg_client()
    
    # Get data
    async for projects in client.get_projects():
        for project in projects:
            print(f"Project: {project['name']}")

Version: 0.1.0
Author: Richard Agbaje-Dosekun
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Richard Agbaje-Dosekun"
__email__ = "richard@example.com"

# Import main classes for easy access
from .client import CargAPIClient, create_carg_client
from .extract_port_json import SimplePortExtractor

# Define what gets imported with "from carg import *"
__all__ = [
    "CargAPIClient",
    "create_carg_client", 
    "SimplePortExtractor",
    "__version__",
    "__author__",
    "__email__"
]

# Package metadata
INTEGRATION_NAME = "carg"
INTEGRATION_DESCRIPTION = "Port Ocean integration for CARG system"
SUPPORTED_RESOURCES = [
    "carg-project",
    "carg-service", 
    "carg-component",
    "carg-deployment"
]