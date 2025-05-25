"""
Models for the orchestrator module
Separate file to avoid circular imports
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class MasterResult:
    """Result from master orchestrator"""
    def __init__(self,
                 final_accuracy: float,
                 target_achieved: bool,
                 iterations_completed: int,
                 iteration_history: List[Dict],
                 needs_human_review: bool,
                 structure_analysis: Any,  # ShelfStructure - avoid circular import
                 best_planogram: Any = None,
                 total_duration: float = 0,
                 total_cost: float = 0):
        self.final_accuracy = final_accuracy
        self.target_achieved = target_achieved
        self.iterations_completed = iterations_completed
        self.iteration_history = iteration_history
        self.needs_human_review = needs_human_review
        self.structure_analysis = structure_analysis
        self.best_planogram = best_planogram
        self.total_duration = total_duration
        self.total_cost = total_cost