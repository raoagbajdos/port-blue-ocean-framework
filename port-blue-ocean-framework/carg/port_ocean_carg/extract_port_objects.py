#!/usr/bin/env python3
"""
Port Object JSON Extractor for CARG Integration

This tool extracts and validates JSON objects that would be sent to Port.io
based on your integration configuration and data mapping.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
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

try:
    import jq
except ImportError:
    print("Installing pyjq...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyjq"])
    import jq


class PortObjectExtractor:
    """Extracts and validates Port objects from CARG data"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent / ".port" / "resources" / "port-app-config.yml"
        self.blueprints_path = Path(__file__).parent / ".port" / "resources" / "blueprints.json"
        self.mapping_config = None
        self.blueprints = None
        self.load_configurations()
    
    def load_configurations(self):
        """Load Port configuration files"""
        try:
            # Load data mapping configuration
            with open(self.config_path, 'r') as f:
                self.mapping_config = yaml.safe_load(f)
            print(f"✅ Loaded mapping configuration from {self.config_path}")
            
            # Load blueprints
            with open(self.blueprints_path, 'r') as f:
                self.blueprints = json.load(f)
            print(f"✅ Loaded blueprints from {self.blueprints_path}")
            
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            sys.exit(1)
    
    def get_mock_data(self):
        """Get mock data from the main integration"""
        from main import TestCargAPIClient
        return TestCargAPIClient()
    
    async def extract_port_objects(self, kind: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Extract Port objects for all or specific entity kinds"""
        client = self.get_mock_data()
        port_objects = {}
        
        # Get raw data for each kind
        raw_data = {
            "carg-project": await client.get_projects(),
            "carg-service": await client.get_services(), 
            "carg-component": await client.get_components(),
            "carg-deployment": await client.get_deployments()
        }
        
        # Process each resource kind
        for resource in self.mapping_config.get("resources", []):
            resource_kind = resource["kind"]
            
            # Skip if specific kind requested and this isn't it
            if kind and resource_kind != kind:
                continue
            
            print(f"\n🔄 Processing {resource_kind}...")
            
            # Get raw data for this kind
            kind_data = raw_data.get(resource_kind, [])
            port_objects[resource_kind] = []
            
            # Transform each item using JQ mappings
            for item in kind_data:
                try:
                    port_object = self.transform_to_port_object(item, resource)
                    port_objects[resource_kind].append(port_object)
                    print(f"   ✅ Transformed {resource_kind} ID: {port_object.get('identifier', 'unknown')}")
                except Exception as e:
                    print(f"   ❌ Error transforming {resource_kind}: {e}")
        
        return port_objects
    
    def transform_to_port_object(self, raw_data: Dict[str, Any], resource_config: Dict) -> Dict[str, Any]:
        """Transform raw data to Port object using JQ mappings"""
        mappings = resource_config["port"]["entity"]["mappings"]
        port_object = {}
        
        # Apply each mapping
        for field, jq_expression in mappings.items():
            try:
                if field == "relations":
                    # Handle relations specially
                    relations = {}
                    for relation_name, relation_jq in jq_expression.items():
                        value = jq.compile(relation_jq).input(raw_data).first()
                        if value is not None:
                            relations[relation_name] = value
                    if relations:
                        port_object["relations"] = relations
                else:
                    # Apply JQ transformation
                    value = jq.compile(jq_expression).input(raw_data).first()
                    if value is not None:
                        port_object[field] = value
            except Exception as e:
                print(f"      ⚠️  Warning: Failed to apply JQ '{jq_expression}' for field '{field}': {e}")
        
        return port_object
    
    def validate_against_blueprints(self, port_objects: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate extracted objects against Port blueprints"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        for kind, objects in port_objects.items():
            blueprint_id = None
            
            # Find the blueprint for this kind
            if objects:
                blueprint_id = objects[0].get("blueprint")
            
            if not blueprint_id:
                validation_results["errors"].append(f"No blueprint found for kind: {kind}")
                validation_results["valid"] = False
                continue
            
            # Find blueprint definition
            blueprint = None
            for bp in self.blueprints:
                if bp["identifier"] == blueprint_id:
                    blueprint = bp
                    break
            
            if not blueprint:
                validation_results["errors"].append(f"Blueprint '{blueprint_id}' not found for kind: {kind}")
                validation_results["valid"] = False
                continue
            
            # Validate each object
            validation_results["stats"][kind] = {
                "total": len(objects),
                "valid": 0,
                "errors": 0
            }
            
            for i, obj in enumerate(objects):
                obj_errors = self.validate_object_against_blueprint(obj, blueprint, f"{kind}[{i}]")
                if obj_errors:
                    validation_results["errors"].extend(obj_errors)
                    validation_results["stats"][kind]["errors"] += 1
                    validation_results["valid"] = False
                else:
                    validation_results["stats"][kind]["valid"] += 1
        
        return validation_results
    
    def validate_object_against_blueprint(self, obj: Dict, blueprint: Dict, obj_path: str) -> List[str]:
        """Validate a single object against its blueprint"""
        errors = []
        
        # Check required fields
        required_fields = ["identifier", "title", "blueprint"]
        for field in required_fields:
            if field not in obj:
                errors.append(f"{obj_path}: Missing required field '{field}'")
        
        # Validate properties against blueprint schema
        if "properties" in obj and "schema" in blueprint and "properties" in blueprint["schema"]:
            schema_props = blueprint["schema"]["properties"]
            obj_props = obj["properties"]
            
            for prop_name, prop_value in obj_props.items():
                if prop_name in schema_props:
                    prop_schema = schema_props[prop_name]
                    prop_type = prop_schema.get("type")
                    
                    # Basic type validation
                    if prop_type == "string" and not isinstance(prop_value, str):
                        errors.append(f"{obj_path}: Property '{prop_name}' should be string, got {type(prop_value).__name__}")
                    elif prop_type == "number" and not isinstance(prop_value, (int, float)):
                        errors.append(f"{obj_path}: Property '{prop_name}' should be number, got {type(prop_value).__name__}")
                    elif prop_type == "boolean" and not isinstance(prop_value, bool):
                        errors.append(f"{obj_path}: Property '{prop_name}' should be boolean, got {type(prop_value).__name__}")
                    elif prop_type == "array" and not isinstance(prop_value, list):
                        errors.append(f"{obj_path}: Property '{prop_name}' should be array, got {type(prop_value).__name__}")
        
        # Validate relations
        if "relations" in obj and "relations" in blueprint:
            blueprint_relations = blueprint["relations"]
            obj_relations = obj["relations"]
            
            for relation_name, relation_value in obj_relations.items():
                if relation_name not in blueprint_relations:
                    errors.append(f"{obj_path}: Unknown relation '{relation_name}'")
        
        return errors
    
    def save_extracted_objects(self, port_objects: Dict[str, List[Dict]], output_dir: str = "extracted_port_objects"):
        """Save extracted objects to JSON files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save each kind to separate files
        for kind, objects in port_objects.items():
            filename = f"{kind.replace('-', '_')}_objects.json"
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(objects, f, indent=2, default=str)
            
            print(f"💾 Saved {len(objects)} {kind} objects to {filepath}")
        
        # Save combined file
        combined_path = output_path / "all_port_objects.json"
        with open(combined_path, 'w') as f:
            json.dump(port_objects, f, indent=2, default=str)
        
        print(f"💾 Saved combined objects to {combined_path}")
        
        return output_path
    
    def generate_summary_report(self, port_objects: Dict[str, List[Dict]], validation_results: Dict) -> str:
        """Generate a summary report"""
        report = []
        report.append("=" * 60)
        report.append("🔍 PORT OBJECT EXTRACTION SUMMARY")
        report.append("=" * 60)
        
        # Object counts
        report.append("\n📊 EXTRACTED OBJECTS:")
        total_objects = 0
        for kind, objects in port_objects.items():
            count = len(objects)
            total_objects += count
            report.append(f"   • {kind}: {count} objects")
        report.append(f"   📈 Total: {total_objects} objects")
        
        # Validation summary
        report.append("\n✅ VALIDATION RESULTS:")
        if validation_results["valid"]:
            report.append("   🎉 All objects are valid!")
        else:
            report.append(f"   ❌ {len(validation_results['errors'])} validation errors found")
        
        if validation_results["warnings"]:
            report.append(f"   ⚠️  {len(validation_results['warnings'])} warnings")
        
        # Per-kind validation stats
        for kind, stats in validation_results.get("stats", {}).items():
            report.append(f"   • {kind}: {stats['valid']}/{stats['total']} valid")
        
        # Sample objects
        report.append("\n📝 SAMPLE OBJECTS:")
        for kind, objects in port_objects.items():
            if objects:
                sample = objects[0]
                report.append(f"\n   {kind.upper()} SAMPLE:")
                report.append(f"      Identifier: {sample.get('identifier', 'N/A')}")
                report.append(f"      Title: {sample.get('title', 'N/A')}")
                report.append(f"      Blueprint: {sample.get('blueprint', 'N/A')}")
                
                if "properties" in sample:
                    props = sample["properties"]
                    report.append(f"      Properties: {len(props)} fields")
                    # Show first 3 properties
                    for i, (key, value) in enumerate(list(props.items())[:3]):
                        report.append(f"         - {key}: {value}")
                    if len(props) > 3:
                        report.append(f"         ... and {len(props) - 3} more")
                
                if "relations" in sample:
                    relations = sample["relations"]
                    report.append(f"      Relations: {list(relations.keys())}")
        
        # Errors (if any)
        if validation_results["errors"]:
            report.append("\n❌ VALIDATION ERRORS:")
            for error in validation_results["errors"][:10]:  # Show first 10 errors
                report.append(f"   • {error}")
            if len(validation_results["errors"]) > 10:
                report.append(f"   ... and {len(validation_results['errors']) - 10} more errors")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)


async def main():
    """Main CLI function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract Port objects from CARG integration")
    parser.add_argument("--kind", help="Extract only specific kind (e.g., carg-project)")
    parser.add_argument("--output", default="extracted_port_objects", help="Output directory")
    parser.add_argument("--validate", action="store_true", help="Validate against blueprints")
    parser.add_argument("--save", action="store_true", help="Save to JSON files")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🚀 Port Object JSON Extractor")
        print("=" * 40)
    
    # Create extractor
    extractor = PortObjectExtractor()
    
    # Extract objects
    if not args.quiet:
        print(f"\n🔄 Extracting Port objects{' for ' + args.kind if args.kind else ''}...")
    
    port_objects = await extractor.extract_port_objects(args.kind)
    
    # Validate if requested
    validation_results = None
    if args.validate:
        if not args.quiet:
            print("\n🔍 Validating against blueprints...")
        validation_results = extractor.validate_against_blueprints(port_objects)
    
    # Save if requested
    if args.save:
        if not args.quiet:
            print(f"\n💾 Saving to {args.output}...")
        output_path = extractor.save_extracted_objects(port_objects, args.output)
    
    # Generate and display report
    if validation_results:
        report = extractor.generate_summary_report(port_objects, validation_results)
        print("\n" + report)
    else:
        # Simple summary without validation
        print(f"\n📊 EXTRACTION COMPLETE:")
        for kind, objects in port_objects.items():
            print(f"   • {kind}: {len(objects)} objects")
    
    # Output JSON to stdout if quiet mode
    if args.quiet:
        print(json.dumps(port_objects, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())