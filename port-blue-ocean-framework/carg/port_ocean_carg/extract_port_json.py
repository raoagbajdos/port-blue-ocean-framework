#!/usr/bin/env python3
"""
Simple Port Object JSON Extractor (No JQ dependency)

Extracts JSON objects that would be sent to Port.io from your CARG integration
using basic Python data transformations instead of JQ.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import yaml
except ImportError:
    print("Installing PyYAML...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml


class SimplePortExtractor:
    """Extract Port objects without JQ dependency"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        print("✅ Simple Port Extractor initialized")
    
    def _get_test_data(self):
        """Import test data from test_integration.py"""
        from test_integration import TestCargAPIClient
        return TestCargAPIClient()
    
    async def extract_all_objects(self):
        """Extract all Port objects using simple Python transformations"""
        client = self._get_test_data()
        
        # Get raw data
        raw_data = {
            "carg-project": await client.get_projects(),
            "carg-service": await client.get_services(),
            "carg-component": await client.get_components(),
            "carg-deployment": await client.get_deployments()
        }
        
        port_objects = {}
        
        # Transform each resource type
        print("🔄 Processing projects...")
        port_objects["carg-project"] = [
            self._transform_project(project) for project in raw_data["carg-project"]
        ]
        
        print("🔄 Processing services...")
        port_objects["carg-service"] = [
            self._transform_service(service) for service in raw_data["carg-service"]
        ]
        
        print("🔄 Processing components...")
        port_objects["carg-component"] = [
            self._transform_component(component) for component in raw_data["carg-component"]
        ]
        
        print("🔄 Processing deployments...")
        port_objects["carg-deployment"] = [
            self._transform_deployment(deployment) for deployment in raw_data["carg-deployment"]
        ]
        
        return port_objects
    
    def _transform_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Transform project data to Port object"""
        return {
            "identifier": str(project.get("id", "")),
            "title": project.get("name", ""),
            "blueprint": "cargProject",
            "properties": {
                "status": project.get("status"),
                "description": project.get("description"),
                "owner": project.get("owner", {}).get("email") or project.get("owner", {}).get("username"),
                "budget": project.get("budget"),
                "startDate": project.get("start_date"),
                "endDate": project.get("end_date"),
                "tags": project.get("tags", []),
                "azureDevOpsProject": project.get("azure_devops", {}).get("project_name")
            }
        }
    
    def _transform_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Transform service data to Port object"""
        return {
            "identifier": str(service.get("id", "")),
            "title": service.get("name", ""),
            "blueprint": "cargService",
            "properties": {
                "status": service.get("status"),
                "healthStatus": service.get("health_status", "Unknown"),
                "version": service.get("version"),
                "repository": service.get("repository", {}).get("url"),
                "language": service.get("language"),
                "cpu": service.get("metrics", {}).get("cpu_usage"),
                "memory": service.get("metrics", {}).get("memory_usage_mb"),
                "lastDeployment": service.get("last_deployment", {}).get("timestamp"),
                "azurePipeline": service.get("azure_devops", {}).get("pipeline_name")
            },
            "relations": {
                "project": str(service.get("project_id", ""))
            }
        }
    
    def _transform_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Transform component data to Port object"""
        return {
            "identifier": str(component.get("id", "")),
            "title": component.get("name", ""),
            "blueprint": "cargComponent",
            "properties": {
                "type": component.get("type"),
                "status": component.get("status"),
                "description": component.get("description"),
                "maintainer": component.get("maintainer", {}).get("email") or component.get("maintainer", {}).get("username"),
                "complexity": component.get("complexity"),
                "testCoverage": component.get("test_coverage")
            },
            "relations": {
                "service": str(component.get("service_id", ""))
            }
        }
    
    def _transform_deployment(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Transform deployment data to Port object"""
        service_name = deployment.get("service_name", "")
        environment = deployment.get("environment", "")
        version = deployment.get("version", "")
        title = f"{service_name} - {environment} - {version}"
        
        return {
            "identifier": str(deployment.get("id", "")),
            "title": title,
            "blueprint": "cargDeployment",
            "properties": {
                "status": deployment.get("status"),
                "environment": deployment.get("environment"),
                "version": deployment.get("version"),
                "deployedBy": deployment.get("deployed_by", {}).get("email") or deployment.get("deployed_by", {}).get("username"),
                "deploymentTime": deployment.get("deployment_time"),
                "duration": deployment.get("duration_seconds"),
                "azurePipelineRun": deployment.get("azure_devops", {}).get("run_id"),
                "logs": deployment.get("logs")
            },
            "relations": {
                "service": str(deployment.get("service_id", ""))
            }
        }
    
    def save_objects(self, port_objects: Dict[str, List], output_dir: str = "port_objects"):
        """Save objects to JSON files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save each type separately
        for kind, objects in port_objects.items():
            filename = f"{kind.replace('-', '_')}.json"
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(objects, f, indent=2)
            
            print(f"💾 Saved {kind}: {filepath}")
        
        # Save all together
        all_path = output_path / "all_objects.json"
        with open(all_path, 'w') as f:
            json.dump(port_objects, f, indent=2)
        
        print(f"💾 Saved all objects: {all_path}")
        return output_path
    
    def print_summary(self, port_objects: Dict[str, List]):
        """Print extraction summary"""
        print("\n" + "=" * 50)
        print("📊 EXTRACTION SUMMARY")
        print("=" * 50)
        
        total = 0
        for kind, objects in port_objects.items():
            count = len(objects)
            total += count
            print(f"   {kind}: {count} objects")
            
            # Show sample object
            if objects:
                sample = objects[0]
                print(f"      Sample ID: {sample.get('identifier', 'N/A')}")
                print(f"      Sample Title: {sample.get('title', 'N/A')}")
                if 'properties' in sample:
                    props = len(sample['properties'])
                    print(f"      Properties: {props} fields")
                if 'relations' in sample:
                    rels = list(sample['relations'].keys())
                    print(f"      Relations: {rels}")
                print()
        
        print(f"📈 Total Objects: {total}")
        print("=" * 50)
    
    def show_sample_objects(self, port_objects: Dict[str, List]):
        """Show detailed sample objects"""
        print("\n" + "=" * 60)
        print("📝 SAMPLE PORT OBJECTS")
        print("=" * 60)
        
        for kind, objects in port_objects.items():
            if objects:
                print(f"\n🏷️  {kind.upper()} SAMPLE:")
                print("-" * 40)
                sample = objects[0]
                print(json.dumps(sample, indent=2))
                print()


async def main():
    """Main CLI function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract Port JSON objects (Simple version)")
    parser.add_argument("--output", "-o", default="port_objects", help="Output directory")
    parser.add_argument("--save", "-s", action="store_true", help="Save to files")
    parser.add_argument("--json-only", action="store_true", help="Output only JSON")
    parser.add_argument("--samples", action="store_true", help="Show detailed sample objects")
    
    args = parser.parse_args()
    
    if not args.json_only:
        print("🚀 Simple Port Object JSON Extractor")
        print("=" * 40)
    
    # Create extractor and extract objects
    extractor = SimplePortExtractor()
    port_objects = await extractor.extract_all_objects()
    
    # Save if requested
    if args.save:
        extractor.save_objects(port_objects, args.output)
    
    # Show output
    if args.json_only:
        print(json.dumps(port_objects, indent=2))
    elif args.samples:
        extractor.show_sample_objects(port_objects)
    else:
        extractor.print_summary(port_objects)
        print("\n💡 Usage examples:")
        print(f"   Save to files: python {Path(__file__).name} --save")
        print(f"   JSON output: python {Path(__file__).name} --json-only")
        print(f"   Show samples: python {Path(__file__).name} --samples")
        print(f"   Custom dir: python {Path(__file__).name} --save --output my_objects")


def cli_main():
    """Console script entry point"""
    import asyncio
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()