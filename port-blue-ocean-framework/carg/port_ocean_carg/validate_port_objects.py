#!/usr/bin/env python3
"""
Port Object Validator - Validates extracted JSON objects against Port.io requirements
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


class PortObjectValidator:
    """Validates Port objects against requirements"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.blueprints = self._load_blueprints()
        print("✅ Port Object Validator initialized")
    
    def _load_blueprints(self):
        """Load blueprints from blueprints.json"""
        # Look for blueprints in the parent directory (project root)
        blueprints_path = self.base_path.parent / ".port" / "resources" / "blueprints.json"
        with open(blueprints_path, 'r') as f:
            return {bp["identifier"]: bp for bp in json.load(f)}
    
    def validate_port_objects(self, port_objects: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Validate all Port objects"""
        results = {
            "valid": True,
            "total_objects": 0,
            "validation_errors": [],
            "validation_warnings": [],
            "summary": {}
        }
        
        for kind, objects in port_objects.items():
            print(f"\n🔍 Validating {kind}...")
            
            kind_results = {
                "count": len(objects),
                "valid_objects": 0,
                "errors": [],
                "warnings": []
            }
            
            for i, obj in enumerate(objects):
                obj_id = f"{kind}[{i}]"
                obj_errors, obj_warnings = self._validate_single_object(obj, obj_id)
                
                if obj_errors:
                    kind_results["errors"].extend(obj_errors)
                    results["validation_errors"].extend(obj_errors)
                    results["valid"] = False
                else:
                    kind_results["valid_objects"] += 1
                
                if obj_warnings:
                    kind_results["warnings"].extend(obj_warnings)
                    results["validation_warnings"].extend(obj_warnings)
            
            results["total_objects"] += len(objects)
            results["summary"][kind] = kind_results
            
            if kind_results["errors"]:
                print(f"   ❌ {len(kind_results['errors'])} errors found")
            if kind_results["warnings"]:
                print(f"   ⚠️ {len(kind_results['warnings'])} warnings")
            if kind_results["valid_objects"] == kind_results["count"]:
                print(f"   ✅ All {kind_results['count']} objects are valid")
        
        return results
    
    def _validate_single_object(self, obj: Dict[str, Any], obj_id: str) -> tuple[List[str], List[str]]:
        """Validate a single Port object"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["identifier", "title", "blueprint"]
        for field in required_fields:
            if field not in obj or not obj[field]:
                errors.append(f"{obj_id}: Missing or empty required field '{field}'")
        
        # Validate blueprint exists
        blueprint_name = obj.get("blueprint")
        if blueprint_name and blueprint_name not in self.blueprints:
            errors.append(f"{obj_id}: Unknown blueprint '{blueprint_name}'")
        
        # Validate identifier format
        identifier = obj.get("identifier")
        if identifier and not isinstance(identifier, str):
            errors.append(f"{obj_id}: Identifier must be string, got {type(identifier).__name__}")
        
        # Check properties structure
        if "properties" in obj:
            if not isinstance(obj["properties"], dict):
                errors.append(f"{obj_id}: Properties must be a dictionary")
            else:
                # Check for null/None values
                for prop_name, prop_value in obj["properties"].items():
                    if prop_value is None:
                        warnings.append(f"{obj_id}: Property '{prop_name}' is null")
        
        # Check relations structure
        if "relations" in obj:
            if not isinstance(obj["relations"], dict):
                errors.append(f"{obj_id}: Relations must be a dictionary")
            else:
                for rel_name, rel_value in obj["relations"].items():
                    if not isinstance(rel_value, str):
                        errors.append(f"{obj_id}: Relation '{rel_name}' must be string identifier")
        
        return errors, warnings
    
    def print_validation_report(self, results: Dict[str, Any]):
        """Print detailed validation report"""
        print("\n" + "=" * 60)
        print("🔍 PORT OBJECT VALIDATION REPORT")
        print("=" * 60)
        
        # Overall status
        if results["valid"]:
            print("✅ VALIDATION PASSED - All objects are valid!")
        else:
            print("❌ VALIDATION FAILED - Issues found")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Objects: {results['total_objects']}")
        print(f"   Validation Errors: {len(results['validation_errors'])}")
        print(f"   Validation Warnings: {len(results['validation_warnings'])}")
        
        # Per-kind summary
        print(f"\n📋 DETAILED RESULTS:")
        for kind, kind_results in results["summary"].items():
            status = "✅" if kind_results["valid_objects"] == kind_results["count"] else "❌"
            print(f"   {status} {kind}: {kind_results['valid_objects']}/{kind_results['count']} valid")
            
            if kind_results["errors"]:
                print(f"      🚨 {len(kind_results['errors'])} errors")
            if kind_results["warnings"]:
                print(f"      ⚠️ {len(kind_results['warnings'])} warnings")
        
        # Show errors if any
        if results["validation_errors"]:
            print(f"\n❌ VALIDATION ERRORS:")
            for i, error in enumerate(results["validation_errors"][:10], 1):
                print(f"   {i:2d}. {error}")
            if len(results["validation_errors"]) > 10:
                print(f"   ... and {len(results['validation_errors']) - 10} more errors")
        
        # Show warnings if any  
        if results["validation_warnings"]:
            print(f"\n⚠️ VALIDATION WARNINGS:")
            for i, warning in enumerate(results["validation_warnings"][:5], 1):
                print(f"   {i:2d}. {warning}")
            if len(results["validation_warnings"]) > 5:
                print(f"   ... and {len(results['validation_warnings']) - 5} more warnings")
        
        print("=" * 60)


async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Port JSON objects")
    parser.add_argument("--file", "-f", help="JSON file to validate (default: extract and validate)")
    parser.add_argument("--extract", action="store_true", help="Extract fresh objects and validate")
    
    args = parser.parse_args()
    
    print("🔍 Port Object Validator")
    print("=" * 30)
    
    validator = PortObjectValidator()
    
    if args.file:
        # Load from file
        print(f"📂 Loading objects from {args.file}...")
        with open(args.file, 'r') as f:
            port_objects = json.load(f)
    else:
        # Extract fresh objects
        print("🔄 Extracting fresh objects...")
        from extract_port_json import SimplePortExtractor
        extractor = SimplePortExtractor()
        port_objects = await extractor.extract_all_objects()
    
    # Validate
    print("\n🔍 Validating objects...")
    results = validator.validate_port_objects(port_objects)
    
    # Show report
    validator.print_validation_report(results)
    
    # Exit with appropriate code
    return 0 if results["valid"] else 1


def cli_main():
    """Console script entry point"""
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


if __name__ == "__main__":
    cli_main()