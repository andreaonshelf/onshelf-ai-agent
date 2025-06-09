#!/usr/bin/env python3
"""Debug queue item 9 model building issue specifically"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from src.extraction.dynamic_model_builder import DynamicModelBuilder

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

print("Debug: Model Building for Queue Item 9")
print("=" * 60)

# Get queue item 9 extraction_config
response = supabase.table("ai_extraction_queue").select("*").eq("id", 9).execute()
if not response.data:
    print("❌ Queue item 9 not found")
    exit(1)

item = response.data[0]
extraction_config = item.get("extraction_config", {})

print("Queue Item 9 Configuration:")
print(f"  Status: {item.get('status')}")
print(f"  Current System: {item.get('current_extraction_system')}")
print(f"  Has extraction_config: {bool(extraction_config)}")

if not extraction_config:
    print("❌ No extraction_config found")
    exit(1)

# Check stages
stages = extraction_config.get("stages", {})
print(f"  Stages in config: {list(stages.keys())}")

# Focus on structure stage
if "structure" not in stages:
    print("❌ No structure stage in configuration")
    exit(1)

structure_config = stages["structure"]
print(f"\nStructure Stage Configuration:")
print(f"  Type: {type(structure_config)}")
print(f"  Keys: {list(structure_config.keys()) if isinstance(structure_config, dict) else 'Not a dict'}")

# Check fields specifically
if "fields" in structure_config:
    fields = structure_config["fields"]
    print(f"  Fields type: {type(fields)}")
    print(f"  Fields count: {len(fields) if isinstance(fields, list) else 'Not a list'}")
    
    if isinstance(fields, list) and len(fields) > 0:
        print(f"  First field: {fields[0] if fields else 'None'}")
        print(f"  First field type: {type(fields[0]) if fields else 'None'}")
        if fields and isinstance(fields[0], dict):
            print(f"  First field keys: {list(fields[0].keys())}")
    else:
        print("  ❌ Fields is empty or not a list!")
else:
    print("  ❌ No 'fields' key in structure config!")

# Now test the dynamic model builder directly
print(f"\n" + "=" * 60)
print("Testing Dynamic Model Builder")
print("=" * 60)

try:
    print("Calling DynamicModelBuilder.build_model_from_config('structure', structure_config)")
    print(f"Structure config being passed: {json.dumps(structure_config, indent=2)[:500]}...")
    
    model = DynamicModelBuilder.build_model_from_config("structure", structure_config)
    print(f"✅ Model built successfully: {model}")
    print(f"Model name: {model.__name__}")
    print(f"Model fields: {list(model.__fields__.keys()) if hasattr(model, '__fields__') else 'No fields'}")
    
except Exception as e:
    print(f"❌ Model building failed: {e}")
    print(f"Error type: {type(e)}")
    
    # Debug the fields that are being passed
    fields = structure_config.get("fields", [])
    print(f"\nDebugging fields structure:")
    print(f"  Fields: {fields}")
    print(f"  Fields length: {len(fields)}")
    print(f"  Is empty: {not fields}")
    print(f"  Bool evaluation: {bool(fields)}")

# Let's also check what the other stages look like
print(f"\n" + "=" * 60)
print("Checking All Stages for Field Definitions")
print("=" * 60)

for stage_name, stage_config in stages.items():
    if isinstance(stage_config, dict):
        fields = stage_config.get("fields", [])
        field_count = len(fields) if isinstance(fields, list) else 0
        print(f"{stage_name}: {field_count} fields")
        
        if field_count == 0:
            print(f"  ❌ {stage_name} has no fields!")
        else:
            print(f"  ✅ {stage_name} has {field_count} fields")
            # Test model building for this stage
            try:
                test_model = DynamicModelBuilder.build_model_from_config(stage_name, stage_config)
                print(f"  ✅ {stage_name} model builds successfully")
            except Exception as e:
                print(f"  ❌ {stage_name} model building failed: {e}")

print(f"\n" + "=" * 60)
print("Analysis Complete")
print("=" * 60)