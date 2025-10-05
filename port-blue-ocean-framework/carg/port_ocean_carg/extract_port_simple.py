#!/usr/bin/env python3
"""
Simple Port Object JSON Extractor for CARG Integration

Extracts JSON objects that would be sent to Port.io from your CARG integration.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import asyncio

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import yaml
    import jq
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "pyjq"])
    import yaml
    import jq


class SimplePortExtractor:
    """Simple extractor for Port objects"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.config = self._load_config()
        print("✅ Configuration loaded successfully")
    
    def _load_config(self):
        """Load the port-app-config.yml file"""
        config_path = self.base_path / ".port" / "resources" / "port-app-config.yml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_test_data(self):
        """Import and use test data from main.py"""
        from test_integration import TestCargAPIClient
        return TestCargAPIClient()
    
    async def extract_all_objects(self):
        """Extract all Port objects"""
        client = self._get_test_data()
        
        # Get raw data
        raw_data = {
            "carg-project": await client.get_projects(),
            "carg-service": await client.get_services(),
            "carg-component": await client.get_components(),
            "carg-deployment": await client.get_deployments()
        }
        
        port_objects = {}
        
        # Process each resource type
        for resource in self.config["resources"]:
            kind = resource["kind"]
            mappings = resource["port"]["entity"]["mappings"]
            
            print(f"🔄 Processing {kind}...")
            
            port_objects[kind] = []
            items = raw_data.get(kind, [])
            
            for item in items:
                port_obj = self._transform_item(item, mappings)
                port_objects[kind].append(port_obj)
            
            print(f"   ✅ Extracted {len(items)} {kind} objects")
        
        return port_objects
    
    def _transform_item(self, item: Dict, mappings: Dict) -> Dict:
        """Transform a single item using JQ mappings"""
        result = {}
        
        for field, jq_expr in mappings.items():
            if field == "relations":
                # Handle relations
                relations = {}
                for rel_name, rel_expr in jq_expr.items():
                    try:
                        value = jq.compile(rel_expr).input(item).first()
                        if value is not None:
                            relations[rel_name] = value
                    except Exception:
                        pass  # Skip failed relations
                if relations:
                    result[field] = relations
            else:
                # Handle regular fields
                try:
                    value = jq.compile(jq_expr).input(item).first()
                    if value is not None:
                        result[field] = value
                except Exception:
                    pass  # Skip failed mappings
        
        return result
    
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


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract Port JSON objects")
    parser.add_argument("--output", "-o", default="port_objects", help="Output directory")
    parser.add_argument("--save", "-s", action="store_true", help="Save to files")
    parser.add_argument("--json-only", action="store_true", help="Output only JSON")
    
    args = parser.parse_args()
    
    if not args.json_only:
        print("🚀 Port Object JSON Extractor")
        print("=" * 30)
    
    # Create extractor and extract objects
    extractor = SimplePortExtractor()
    port_objects = await extractor.extract_all_objects()
    
    # Save if requested
    if args.save:
        extractor.save_objects(port_objects, args.output)
    
    # Show summary or JSON output
    if args.json_only:
        print(json.dumps(port_objects, indent=2))
    else:
        extractor.print_summary(port_objects)
        print("\n💡 Usage examples:")
        print(f"   Save to files: python {Path(__file__).name} --save")
        print(f"   JSON output: python {Path(__file__).name} --json-only")
        print(f"   Custom dir: python {Path(__file__).name} --save --output my_objects")


if __name__ == "__main__":
    asyncio.run(main())