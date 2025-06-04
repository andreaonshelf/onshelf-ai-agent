#!/usr/bin/env python3
"""
Fix for the structure_extraction double nesting issue in the extraction pipeline.

This patch shows how to correctly use the dynamic model builder to avoid the
validation error: "structure_extraction Field required [type=missing, input_value={}, input_type=dict]"
"""

import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Import the correct model builder
from src.extraction.dynamic_model_builder import build_extraction_model, build_model_from_stage_config


def patch_extraction_pipeline():
    """
    Patch for the extraction pipeline to use correct model building.
    
    This should be applied wherever the extraction engine builds models from
    stage configurations with field definitions.
    """
    
    code = '''
    # In the extraction engine or orchestrator where models are built dynamically:
    
    async def execute_stage_with_dynamic_model(
        self, 
        stage_name: str, 
        stage_config: Dict[str, Any],
        prompt: str,
        images: Dict[str, bytes]
    ):
        """Execute extraction stage with dynamically built model"""
        
        # Get field definitions from stage config
        fields = stage_config.get('fields', {})
        
        # Build the model CORRECTLY (fields at root level)
        from src.extraction.dynamic_model_builder import build_extraction_model
        response_model = build_extraction_model(stage_name, fields)
        
        # Log the model structure for debugging
        logger.info(
            f"Built model for {stage_name} with schema: {response_model.model_json_schema()}",
            component="extraction_engine"
        )
        
        # Use the model with instructor
        try:
            if stage_config.get('models', ['gpt-4o'])[0].startswith('claude'):
                response = await self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "source": {...}}  # Add image
                    ]}],
                    response_model=response_model  # Uses fields at root level
                )
            else:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {...}}  # Add image
                    ]}],
                    response_model=response_model  # Uses fields at root level
                )
            
            # The response will have fields at root level, not nested
            # e.g., response.total_shelves, response.shelves, etc.
            # NOT response.structure_extraction.structure_extraction.total_shelves
            
            return response
            
        except ValidationError as e:
            logger.error(
                f"Validation error in {stage_name}: {e}",
                component="extraction_engine",
                error_detail=e.errors()
            )
            raise
    '''
    
    return code


def demonstrate_fix():
    """Demonstrate the fix for the double nesting issue"""
    
    print("DEMONSTRATION: Fixing the structure_extraction double nesting issue\n")
    print("="*70)
    
    # Example stage configuration from the UI
    stage_config = {
        "name": "structure_extraction",
        "fields": {
            "total_shelves": {
                "type": "integer",
                "description": "Total number of shelves",
                "required": True
            },
            "shelves": {
                "type": "array",
                "description": "Array of shelf objects",
                "items": {
                    "type": "object",
                    "properties": {
                        "shelf_number": {"type": "integer"},
                        "has_price_rail": {"type": "boolean"}
                    }
                }
            }
        }
    }
    
    print("1. Stage configuration from UI:")
    print(f"   Stage name: {stage_config['name']}")
    print(f"   Fields: {list(stage_config['fields'].keys())}")
    
    # Build model the WRONG way (what's causing the error)
    print("\n2. WRONG: Building model with double nesting")
    print("   This would create a model expecting:")
    print("   {")
    print("     'structure_extraction': {")
    print("       'structure_extraction': {")
    print("         'total_shelves': 5,")
    print("         'shelves': [...]")
    print("       }")
    print("     }")
    print("   }")
    
    # Build model the RIGHT way
    print("\n3. RIGHT: Building model with fields at root")
    from src.extraction.dynamic_model_builder import build_extraction_model
    
    correct_model = build_extraction_model(
        stage_config['name'], 
        stage_config['fields']
    )
    
    print("   This creates a model expecting:")
    print("   {")
    print("     'total_shelves': 5,")
    print("     'shelves': [...]")
    print("   }")
    
    # Test the correct model
    print("\n4. Testing the correct model:")
    try:
        # This is what the AI will return
        test_data = {
            "total_shelves": 5,
            "shelves": [
                {"shelf_number": 1, "has_price_rail": True},
                {"shelf_number": 2, "has_price_rail": False}
            ]
        }
        
        instance = correct_model(**test_data)
        print("   ✓ Model validation passed!")
        print(f"   Total shelves: {instance.total_shelves}")
        print(f"   Number of shelf objects: {len(instance.shelves)}")
        
    except Exception as e:
        print(f"   ✗ Model validation failed: {e}")
    
    print("\n" + "="*70)
    print("SOLUTION: Use the dynamic_model_builder.build_extraction_model() function")
    print("This ensures fields are at the root level, matching what the AI returns.")
    

if __name__ == "__main__":
    demonstrate_fix()
    
    print("\n\nPATCH CODE:")
    print(patch_extraction_pipeline())