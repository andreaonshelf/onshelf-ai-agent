from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["settings"])

# Settings file path
SETTINGS_FILE = "config/settings.json"

def load_settings():
    """Load settings from file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    # Return default settings
    return {
        "general": {
            "company_name": "OnShelf AI",
            "contact_email": "admin@onshelf.ai",
            "language": "en_US",
            "timezone": "UTC",
            "currency": "USD"
        },
        "api_keys": {
            "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "google": os.getenv("GOOGLE_API_KEY", "")
        },
        "models": {
            "default_structure": "claude",
            "default_products": "gpt4o",
            "default_details": "gemini",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "database": {
            "connection_pool_size": 10,
            "query_timeout": 30,
            "auto_backup": True,
            "backup_frequency": "daily"
        },
        "notifications": {
            "email_enabled": True,
            "slack_enabled": False,
            "webhook_url": "",
            "notify_on_failure": True,
            "notify_on_completion": False
        },
        "advanced": {
            "parallel_processing": True,
            "max_concurrent_jobs": 5,
            "retry_attempts": 3,
            "cache_ttl": 3600,
            "debug_mode": False
        }
    }

def save_settings(settings: Dict[str, Any]):
    """Save settings to file"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return False

@router.get("/settings")
async def get_settings():
    """Get all settings"""
    return load_settings()

@router.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update settings"""
    try:
        # Merge with existing settings
        current_settings = load_settings()
        
        # Deep merge
        for category, values in settings.items():
            if category in current_settings and isinstance(values, dict):
                current_settings[category].update(values)
            else:
                current_settings[category] = values
        
        # Add metadata
        current_settings["_metadata"] = {
            "last_updated": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
        
        # Save
        if save_settings(current_settings):
            return {
                "status": "success",
                "message": "Settings updated successfully",
                "settings": current_settings
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
            
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/{category}")
async def get_settings_category(category: str):
    """Get settings for a specific category"""
    settings = load_settings()
    
    if category in settings:
        return settings[category]
    else:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

@router.post("/settings/{category}")
async def update_settings_category(category: str, values: Dict[str, Any]):
    """Update settings for a specific category"""
    try:
        settings = load_settings()
        settings[category] = values
        settings["_metadata"] = {
            "last_updated": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
        
        if save_settings(settings):
            return {
                "status": "success",
                "message": f"Settings for '{category}' updated successfully",
                "settings": settings[category]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save settings")
            
    except Exception as e:
        logger.error(f"Failed to update settings category {category}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/reset")
async def reset_settings():
    """Reset settings to defaults"""
    try:
        # Remove settings file
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        
        # Return defaults
        default_settings = load_settings()
        return {
            "status": "success",
            "message": "Settings reset to defaults",
            "settings": default_settings
        }
        
    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/export")
async def export_settings():
    """Export settings as JSON file"""
    settings = load_settings()
    
    return {
        "filename": f"onshelf_settings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
        "content": settings
    }

@router.post("/settings/import")
async def import_settings(imported_settings: Dict[str, Any]):
    """Import settings from JSON"""
    try:
        # Validate basic structure
        required_categories = ["general", "api_keys", "models", "database", "notifications", "advanced"]
        
        for category in required_categories:
            if category not in imported_settings:
                raise ValueError(f"Missing required category: {category}")
        
        # Add metadata
        imported_settings["_metadata"] = {
            "last_updated": datetime.utcnow().isoformat(),
            "imported_at": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
        
        # Save
        if save_settings(imported_settings):
            return {
                "status": "success",
                "message": "Settings imported successfully",
                "settings": imported_settings
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save imported settings")
            
    except Exception as e:
        logger.error(f"Failed to import settings: {e}")
        raise HTTPException(status_code=400, detail=str(e))