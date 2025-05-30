"""
Add these endpoints to src/api/prompt_management.py to support configuration management
"""

# Add these imports at the top if not already present
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add these endpoints to the prompt_management.py router

@router.get("/configurations")
async def get_saved_configurations(
    limit: int = 20,
    offset: int = 0
):
    """Get list of saved extraction configurations"""
    
    try:
        if not supabase:
            # Return mock data for testing
            return {
                "configurations": [
                    {
                        "id": "config_001",
                        "name": "High Accuracy Retail Config",
                        "description": "Optimized for retail shelf extraction with high accuracy",
                        "system": "custom_consensus",
                        "created_at": "2024-01-20T10:00:00Z",
                        "stages_count": 4,
                        "last_used": "2024-01-20T15:30:00Z",
                        "performance_score": 0.92
                    }
                ]
            }
        
        # Query saved configurations
        # Note: This assumes a 'extraction_configurations' table exists
        result = supabase.table("extraction_configurations").select("*").range(offset, offset + limit - 1).order("created_at", desc=True).execute()
        
        configurations = []
        for config in result.data:
            configurations.append({
                "id": config['id'],
                "name": config['name'],
                "description": config.get('description', ''),
                "system": config['configuration']['system'],
                "created_at": config['created_at'],
                "stages_count": len(config['configuration'].get('stages', {})),
                "last_used": config.get('last_used', config['created_at']),
                "performance_score": config.get('avg_performance_score', 0)
            })
        
        return {"configurations": configurations}
        
    except Exception as e:
        logger.error(f"Failed to get configurations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configurations: {str(e)}")


@router.get("/configurations/{config_id}")
async def get_configuration_details(config_id: str):
    """Get detailed configuration by ID"""
    
    try:
        if not supabase:
            # Return mock data for testing
            return {
                "id": config_id,
                "name": "High Accuracy Retail Config",
                "description": "Optimized for retail shelf extraction",
                "system": "custom_consensus",
                "max_budget": 2.0,
                "stages": {
                    "structure": {
                        "prompt_text": "Analyze the shelf structure...",
                        "fields": [
                            {"name": "shelf_count", "type": "integer", "required": True},
                            {"name": "sections", "type": "list", "required": True}
                        ],
                        "model_type": "claude",
                        "saved": True
                    },
                    "products": {
                        "prompt_text": "Extract all products...",
                        "fields": [
                            {"name": "product_name", "type": "string", "required": True},
                            {"name": "brand", "type": "string", "required": True}
                        ],
                        "model_type": "gpt4o",
                        "saved": True
                    }
                },
                "created_at": "2024-01-20T10:00:00Z"
            }
        
        # Get configuration from database
        result = supabase.table("extraction_configurations").select("*").eq("id", config_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        config = result.data[0]
        return {
            "id": config['id'],
            "name": config['name'],
            "description": config.get('description', ''),
            "system": config['configuration']['system'],
            "max_budget": config['configuration']['max_budget'],
            "stages": config['configuration']['stages'],
            "created_at": config['created_at'],
            "updated_at": config.get('updated_at', config['created_at'])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.post("/configurations")
async def save_configuration(request_data: Dict[str, Any]):
    """Save a new extraction configuration"""
    
    try:
        configuration = request_data.get('configuration')
        name = request_data.get('name', f'Configuration {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        description = request_data.get('description', '')
        
        if not configuration:
            raise HTTPException(status_code=400, detail="configuration is required")
        
        config_id = str(uuid.uuid4())
        
        if supabase:
            # Save to database
            config_data = {
                'id': config_id,
                'name': name,
                'description': description,
                'configuration': configuration,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('extraction_configurations').insert(config_data).execute()
            
            if result.data:
                logger.info(f"Saved configuration: {name}")
                return {
                    "success": True,
                    "config_id": config_id,
                    "message": "Configuration saved successfully"
                }
        else:
            # Save to local storage or return success
            logger.info(f"Would save configuration: {name}")
            return {
                "success": True,
                "config_id": config_id,
                "message": "Configuration saved (no database)"
            }
            
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")


@router.put("/configurations/{config_id}")
async def update_configuration(config_id: str, request_data: Dict[str, Any]):
    """Update an existing configuration"""
    
    try:
        configuration = request_data.get('configuration')
        name = request_data.get('name')
        description = request_data.get('description')
        
        if not any([configuration, name, description]):
            raise HTTPException(status_code=400, detail="At least one field to update is required")
        
        if supabase:
            # Build update data
            update_data = {'updated_at': datetime.utcnow().isoformat()}
            if configuration:
                update_data['configuration'] = configuration
            if name:
                update_data['name'] = name
            if description is not None:  # Allow empty string
                update_data['description'] = description
            
            # Update in database
            result = supabase.table('extraction_configurations').update(update_data).eq('id', config_id).execute()
            
            if result.data:
                logger.info(f"Updated configuration: {config_id}")
                return {
                    "success": True,
                    "message": "Configuration updated successfully"
                }
            else:
                raise HTTPException(status_code=404, detail="Configuration not found")
        else:
            return {
                "success": True,
                "message": "Configuration updated (no database)"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.delete("/configurations/{config_id}")
async def delete_configuration(config_id: str):
    """Delete a configuration"""
    
    try:
        if supabase:
            result = supabase.table('extraction_configurations').delete().eq('id', config_id).execute()
            
            if result.data:
                logger.info(f"Deleted configuration: {config_id}")
                return {
                    "success": True,
                    "message": "Configuration deleted successfully"
                }
            else:
                raise HTTPException(status_code=404, detail="Configuration not found")
        else:
            return {
                "success": True,
                "message": "Configuration deleted (no database)"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete configuration: {str(e)}")


# Also add this SQL to create the extraction_configurations table:
"""
CREATE TABLE extraction_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE,
    avg_performance_score FLOAT,
    usage_count INTEGER DEFAULT 0
);

-- Index for faster queries
CREATE INDEX idx_extraction_configurations_created_at ON extraction_configurations(created_at DESC);
CREATE INDEX idx_extraction_configurations_name ON extraction_configurations(name);
"""