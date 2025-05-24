"""
OnShelf AI Agent System
Revolutionary self-debugging AI extraction system for retail shelf analysis

Version: 1.0.0
"""

__version__ = "1.0.0"

# Import main components
from .config import SystemConfig
from .system import OnShelfAISystem, process_upload
from .agent.models import AgentResult
from .extraction.models import CompleteShelfExtraction
from .planogram.models import VisualPlanogram

# Export main API
__all__ = [
    "SystemConfig",
    "OnShelfAISystem", 
    "process_upload",
    "AgentResult",
    "CompleteShelfExtraction",
    "VisualPlanogram"
] 