"""
Strategic Multi-System Framework
Three architectural approaches for AI extraction with consensus-based processing
"""

from .base_system import BaseExtractionSystem, ExtractionSystemFactory
from .custom_consensus import CustomConsensusSystem
from .langgraph_system import LangGraphConsensusSystem
from .hybrid_system import HybridConsensusSystem

__all__ = [
    'BaseExtractionSystem',
    'ExtractionSystemFactory', 
    'CustomConsensusSystem',
    'LangGraphConsensusSystem',
    'HybridConsensusSystem'
] 