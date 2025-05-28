"""Field Definitions API for managing extraction field metadata."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import json
from supabase import create_client, Client

router = APIRouter()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class FieldDefinition(BaseModel):
    id: Optional[int] = None
    field_name: str
    display_name: str
    definition: str
    examples: Optional[str] = None
    data_type: str = "string"
    is_required: bool = False
    is_active: bool = True
    validation_rules: Optional[dict] = None
    category: Optional[str] = None  # For grouping fields
    sort_order: Optional[int] = None  # For custom ordering
    parent_field: Optional[str] = None  # For nested fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@router.get("/field-definitions")
async def get_field_definitions(organized: bool = False):
    """Get all active field definitions, optionally organized by category."""
    if not supabase:
        # Return mock data if no database
        return {
            "definitions": [
                {
                    "id": 1,
                    "field_name": "facings",
                    "display_name": "Facings",
                    "definition": "The number of identical products placed side by side on the shelf",
                    "examples": "If you see 3 Coca-Cola bottles next to each other, that's 3 facings",
                    "data_type": "integer",
                    "is_required": True,
                    "is_active": True,
                    "category": "Shelf Layout",
                    "sort_order": 1
                },
                {
                    "id": 2,
                    "field_name": "product_name",
                    "display_name": "Product Name",
                    "definition": "The full name of the product as shown on packaging",
                    "examples": "Coca-Cola Zero Sugar 330ml",
                    "data_type": "string",
                    "is_required": True,
                    "is_active": True,
                    "category": "Product Info",
                    "sort_order": 1
                },
                {
                    "id": 3,
                    "field_name": "brand",
                    "display_name": "Brand",
                    "definition": "The brand or manufacturer name",
                    "examples": "Coca-Cola, Pepsi, Nestle",
                    "data_type": "string",
                    "is_required": True,
                    "is_active": True,
                    "category": "Product Info",
                    "sort_order": 2
                },
                {
                    "id": 4,
                    "field_name": "shelf_position",
                    "display_name": "Shelf Position",
                    "definition": "Which shelf the product is on (counting from top)",
                    "examples": "Shelf 1 (top), Shelf 2, Shelf 3",
                    "data_type": "integer",
                    "is_required": False,
                    "is_active": True,
                    "category": "Shelf Layout",
                    "sort_order": 2
                }
            ]
        }
    
    try:
        # Try to order by new columns, fallback to display_name if they don't exist
        try:
            result = supabase.table("field_definitions").select("*").eq("is_active", True).order("category,sort_order,display_name").execute()
        except Exception:
            # Fallback if new columns don't exist yet
            result = supabase.table("field_definitions").select("*").eq("is_active", True).order("display_name").execute()
        
        definitions = []
        for row in result.data:
            if row.get('validation_rules') and isinstance(row['validation_rules'], str):
                row['validation_rules'] = json.loads(row['validation_rules'])
            definitions.append(row)
        
        if organized:
            # Group by category
            organized_defs = {}
            for def_item in definitions:
                category = def_item.get('category', 'Other')
                if category not in organized_defs:
                    organized_defs[category] = []
                organized_defs[category].append(def_item)
            
            # Sort categories and their items
            sorted_categories = sorted(organized_defs.keys())
            result = {
                "categories": [
                    {
                        "name": cat,
                        "fields": sorted(organized_defs[cat], key=lambda x: (x.get('sort_order', 999), x.get('display_name', '')))
                    }
                    for cat in sorted_categories
                ]
            }
            return result
        else:
            return {"definitions": definitions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/field-definitions/{field_name}")
async def get_field_definition(field_name: str):
    """Get a specific field definition by field name."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = supabase.table("field_definitions").select("*").eq("field_name", field_name).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Field definition not found")
        
        definition = result.data[0]
        if definition.get('validation_rules') and isinstance(definition['validation_rules'], str):
            definition['validation_rules'] = json.loads(definition['validation_rules'])
        
        return definition
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail="Field definition not found")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/field-definitions")
async def create_field_definition(definition: FieldDefinition):
    """Create a new field definition."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    validation_rules_json = json.dumps(definition.validation_rules) if definition.validation_rules else None
    
    data = {
        "field_name": definition.field_name,
        "display_name": definition.display_name,
        "definition": definition.definition,
        "examples": definition.examples,
        "data_type": definition.data_type,
        "is_required": definition.is_required,
        "is_active": definition.is_active,
        "validation_rules": validation_rules_json
    }
    
    try:
        result = supabase.table("field_definitions").insert(data).execute()
        
        if result.data:
            created_def = result.data[0]
            return {
                "message": "Field definition created successfully",
                "definition": {
                    **definition.model_dump(),
                    "id": created_def["id"],
                    "created_at": created_def["created_at"],
                    "updated_at": created_def["updated_at"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create field definition")
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Field definition for '{definition.field_name}' already exists")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/field-definitions/{field_name}")
async def update_field_definition(field_name: str, definition: FieldDefinition):
    """Update an existing field definition."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    validation_rules_json = json.dumps(definition.validation_rules) if definition.validation_rules else None
    
    data = {
        "display_name": definition.display_name,
        "definition": definition.definition,
        "examples": definition.examples,
        "data_type": definition.data_type,
        "is_required": definition.is_required,
        "is_active": definition.is_active,
        "validation_rules": validation_rules_json
    }
    
    try:
        result = supabase.table("field_definitions").update(data).eq("field_name", field_name).execute()
        
        if result.data:
            updated_def = result.data[0]
            return {
                "message": "Field definition updated successfully",
                "definition": {
                    **definition.model_dump(),
                    "field_name": field_name,
                    "id": updated_def["id"],
                    "created_at": updated_def["created_at"],
                    "updated_at": updated_def["updated_at"]
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Field definition not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/field-definitions/{field_name}")
async def delete_field_definition(field_name: str):
    """Soft delete a field definition."""
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = supabase.table("field_definitions").update({"is_active": False}).eq("field_name", field_name).execute()
        
        if result.data:
            return {"message": "Field definition deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Field definition not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/field-definitions-for-prompt")
async def get_field_definitions_for_prompt(field_names: List[str] = []):
    """Get field definitions formatted for prompt generation."""
    if not field_names:
        return {"definitions_text": ""}
    
    if not supabase:
        return {"definitions_text": "", "definitions": []}
    
    try:
        result = supabase.table("field_definitions").select("*").in_("field_name", field_names).eq("is_active", True).execute()
        
        definitions_text = []
        for row in result.data:
            text = f"**{row['display_name']} ({row['field_name']})**: {row['definition']}"
            if row.get('examples'):
                text += f"\nExamples: {row['examples']}"
            definitions_text.append(text)
        
        return {
            "definitions_text": "\n\n".join(definitions_text),
            "definitions": result.data
        }
    except Exception as e:
        # Return empty if there's an error (table might not exist)
        return {"definitions_text": "", "definitions": []}