"""
OnShelf AI Agent Configuration
Central configuration for the revolutionary self-debugging AI extraction system
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class SystemConfig:
    """Configuration for the complete OnShelf AI system"""
    
    # Database (existing OnShelf infrastructure)
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_service_key: str = field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_KEY", ""))
    
    # AI Models
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    
    # Model assignment (configurable)
    models: Dict[str, str] = field(default_factory=lambda: {
        'structure_analysis': 'claude-3-sonnet-20240229',
        'product_extraction': 'gpt-4o-2024-11-20', 
        'ocr_enhancement': 'gemini-2.0-flash-exp',
        'image_comparison': 'gpt-4o-2024-11-20',
        'planning': 'claude-3-sonnet-20240229'
    })
    
    # Agent parameters
    max_iterations: int = 5
    target_accuracy: float = 0.95
    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'auto_approve': 0.95,
        'needs_review': 0.85,
        'escalate_human': 0.70
    })
    
    # Processing limits
    max_processing_time_seconds: int = 300  # 5 minutes
    max_api_cost_per_extraction: float = 1.00  # £1
    
    # WebSocket configuration
    websocket_host: str = "0.0.0.0"
    websocket_port: int = 8000
    
    # Dashboard configuration
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8501
    
    # Feature flags
    enable_real_time_updates: bool = True
    enable_auto_escalation: bool = True
    enable_bulk_processing: bool = True
    
    def validate(self) -> bool:
        """Validate configuration"""
        required_fields = [
            self.supabase_url,
            self.supabase_service_key,
            self.openai_api_key,
            self.anthropic_api_key,
            self.google_api_key
        ]
        
        if not all(required_fields):
            missing = []
            if not self.supabase_url:
                missing.append("SUPABASE_URL")
            if not self.supabase_service_key:
                missing.append("SUPABASE_SERVICE_KEY")
            if not self.openai_api_key:
                missing.append("OPENAI_API_KEY")
            if not self.anthropic_api_key:
                missing.append("ANTHROPIC_API_KEY")
            if not self.google_api_key:
                missing.append("GOOGLE_API_KEY")
            
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            return False
        
        return True


# Global configuration instance
config = SystemConfig() 