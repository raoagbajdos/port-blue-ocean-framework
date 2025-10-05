#!/usr/bin/env python3
"""
Setup script for Port Ocean CARG Integration

This setup.py provides compatibility for environments that don't use Poetry.
The primary build configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Port Ocean integration for CARG system"

# Read version from __init__.py
def get_version():
    init_path = os.path.join(os.path.dirname(__file__), "port_ocean_carg", "__init__.py")
    with open(init_path, "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="port-ocean-carg",
    version=get_version(),
    description="Port Ocean integration for CARG (Cloud Architecture Resource Graph) system",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Richard Agbaje-Dosekun",
    author_email="richard@example.com",
    url="https://github.com/your-org/port-ocean-carg",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "carg": [
            ".port/**/*",
            "templates/**/*",
            "scripts/**/*",
            "*.md",
            "*.yml",
            "*.yaml"
        ]
    },
    python_requires=">=3.12",
    install_requires=[
        "port-ocean[cli]>=0.28.12",
        "aiohttp>=3.9.0",
        "loguru>=0.7.0",
        "pyyaml>=6.0",
        "httpx>=0.27.0"
    ],
    extras_require={
        "dev": [
            "black>=24.4.2",
            "mypy>=1.3.0", 
            "pylint>=2.17.4,<4.0.0",
            "pytest>=8.2,<9.0",
            "pytest-asyncio>=0.24.0",
            "pytest-httpx>=0.30.0",
            "pytest-xdist>=3.6.1",
            "ruff>=0.6.3",
            "towncrier>=23.6.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "carg-extract-json=port_ocean_carg.extract_port_json:cli_main",
            "carg-validate=port_ocean_carg.validate_port_objects:cli_main", 
            "carg-test=port_ocean_carg.test_integration:cli_main"
        ],
        "port_ocean.integrations": [
            "carg=port_ocean_carg.main"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License", 
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration"
    ],
    keywords="port ocean integration carg devops infrastructure",
    project_urls={
        "Homepage": "https://github.com/your-org/port-ocean-carg",
        "Repository": "https://github.com/your-org/port-ocean-carg", 
        "Documentation": "https://github.com/your-org/port-ocean-carg#readme",
        "Bug Reports": "https://github.com/your-org/port-ocean-carg/issues"
    }
)