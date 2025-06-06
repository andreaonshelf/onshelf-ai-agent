import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Create Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def analyze_fields(fields, indent=0):
    """Recursively analyze field structure"""
    prefix = "  " * indent
    
    for field in fields:
        print(f"{prefix}• {field['name']} ({field['type']}){' ✓' if field.get('required') else ' ☐'}")
        
        # Show additional properties
        if field['type'] in ['enum', 'literal'] and 'allowed_values' in field:
            print(f"{prefix}  Values: {field['allowed_values']}")
            
        if field['type'] == 'list' and 'list_item_type' in field:
            print(f"{prefix}  Item type: {field['list_item_type']}")
            
        # Show nested fields
        if 'nested_fields' in field:
            print(f"{prefix}  Nested fields:")
            analyze_fields(field['nested_fields'], indent + 2)

def main():
    # Query database
    results = supabase.table('prompt_templates').select('*').execute()
    
    prompt_mapping = {
        'structure': 'Structure v1',
        'position': 'Product v1',
        'detail': 'Detail v1',
        'comparison': 'Visual v1'
    }
    
    print("Database Field Structure Analysis")
    print("=" * 80)
    print("\nLegend: ✓ = required, ☐ = optional\n")
    
    for row in results.data:
        prompt_type = row.get('prompt_type', '')
        display_name = prompt_mapping.get(prompt_type.lower())
        
        if not display_name:
            continue
            
        print(f"\n{display_name} ({prompt_type})")
        print("-" * 60)
        
        if not row.get('fields'):
            print("NO FIELDS DEFINED")
            continue
            
        try:
            if isinstance(row['fields'], str):
                fields_data = json.loads(row['fields'])
            else:
                fields_data = row['fields']
                
            print("Current structure in database:")
            analyze_fields(fields_data)
            
            print("\n✏️ Expected structure from EXTRACTION_PROMPTS_FINAL.md:")
            if display_name == "Structure v1":
                print("• structure_extraction (object) ✓")
                print("  Nested fields:")
                print("    • shelf_structure (object) ✓")
                print("      Nested fields:")
                print("        • total_shelves, fixture_id, shelf_numbers, etc.")
                
            elif display_name == "Product v1":
                print("• product_extraction (object) ✓")
                print("  Nested fields:")
                print("    • fixture_id (string) ✓")
                print("    • total_shelves (integer) ✓")
                print("    • shelves (list) ✓")
                
            elif display_name == "Detail v1":
                print("• detail_enhancement (object) ✓")
                print("  Nested fields:")
                print("    • fixture_id (string) ✓")
                print("    • total_shelves (integer) ✓")
                print("    • shelves_enhanced (list) ✓")
                
            elif display_name == "Visual v1":
                print("• visual_comparison (object) ✓")
                print("  Nested fields:")
                print("    • overview (object) ✓")
                print("    • shelf_mismatches (list) ☐")
                print("    • critical_issues (list) ☐")
                
        except Exception as e:
            print(f"Error parsing fields: {e}")

if __name__ == "__main__":
    main()