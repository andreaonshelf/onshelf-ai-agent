"""
Cost Tracking and Enforcement System
Hard limits on API costs with real-time monitoring
"""

from typing import Dict, Optional
from datetime import datetime
from .logger import logger


class CostLimitExceededException(Exception):
    """Raised when API cost limits are exceeded"""
    
    def __init__(self, current_cost: float, limit: float, operation: str):
        self.current_cost = current_cost
        self.limit = limit
        self.operation = operation
        super().__init__(
            f"Cost limit exceeded: £{current_cost:.3f} > £{limit:.2f} during {operation}"
        )


class CostTracker:
    """Track and enforce API cost limits during extraction"""
    
    def __init__(self, cost_limit: float, agent_id: str):
        self.cost_limit = cost_limit
        self.agent_id = agent_id
        self.total_cost = 0.0
        self.operation_costs: Dict[str, float] = {}
        self.cost_history = []
        self.started_at = datetime.utcnow()
    
    def add_cost(self, operation: str, cost: float) -> None:
        """Add cost for an operation and check limits"""
        
        # Log the cost
        logger.log_cost_tracking(
            self.agent_id, operation, cost, 
            self.total_cost + cost, self.cost_limit
        )
        
        # Check if adding this cost would exceed limit
        projected_total = self.total_cost + cost
        if projected_total > self.cost_limit:
            logger.error(
                f"Cost limit would be exceeded by operation '{operation}'",
                component="cost_tracker",
                agent_id=self.agent_id,
                operation=operation,
                operation_cost=cost,
                current_total=self.total_cost,
                projected_total=projected_total,
                limit=self.cost_limit
            )
            raise CostLimitExceededException(projected_total, self.cost_limit, operation)
        
        # Add the cost
        self.total_cost += cost
        self.operation_costs[operation] = self.operation_costs.get(operation, 0) + cost
        
        # Record in history
        self.cost_history.append({
            'timestamp': datetime.utcnow(),
            'operation': operation,
            'cost': cost,
            'total_cost': self.total_cost
        })
        
        logger.debug(
            f"Cost added: {operation} £{cost:.3f} (Total: £{self.total_cost:.3f})",
            component="cost_tracker",
            agent_id=self.agent_id
        )
    
    def check_remaining_budget(self, operation: str, estimated_cost: float) -> bool:
        """Check if there's budget for a planned operation"""
        return (self.total_cost + estimated_cost) <= self.cost_limit
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget"""
        return max(0, self.cost_limit - self.total_cost)
    
    def get_cost_summary(self) -> Dict:
        """Get comprehensive cost summary"""
        return {
            'total_cost': self.total_cost,
            'cost_limit': self.cost_limit,
            'remaining_budget': self.get_remaining_budget(),
            'utilization_percent': (self.total_cost / self.cost_limit) * 100,
            'operation_breakdown': self.operation_costs.copy(),
            'duration_minutes': (datetime.utcnow() - self.started_at).total_seconds() / 60,
            'cost_per_minute': self.total_cost / max(1, (datetime.utcnow() - self.started_at).total_seconds() / 60)
        }
    
    def is_approaching_limit(self, threshold: float = 0.8) -> bool:
        """Check if approaching cost limit"""
        return (self.total_cost / self.cost_limit) >= threshold 