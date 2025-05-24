"""
Enhanced Error Handling and Recovery System
Robust error handling with retry logic and graceful degradation
"""

import asyncio
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from datetime import datetime, timedelta
import traceback
from .logger import logger


class RecoverableError(Exception):
    """Error that can be recovered from with retry"""
    pass


class NonRecoverableError(Exception):
    """Error that cannot be recovered from"""
    pass


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(self, 
                 max_retries: int = 3, 
                 base_delay: float = 1.0,
                 exponential_backoff: bool = True,
                 max_delay: float = 60.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_backoff = exponential_backoff
        self.max_delay = max_delay
        self.jitter = jitter


class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.error_history: List[Dict] = []
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
        
        # Setup default recovery strategies
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Setup default error recovery strategies"""
        
        # API rate limit errors
        self.recovery_strategies[Exception] = self._default_recovery
        
        # Add specific strategies for different error types
        # These would be expanded based on real-world error patterns
    
    def _default_recovery(self, error: Exception, context: Dict) -> Dict:
        """Default recovery strategy"""
        return {
            'action': 'retry',
            'delay': 5.0,
            'modifications': {}
        }
    
    def record_error(self, error: Exception, context: Dict):
        """Record error for analysis"""
        error_record = {
            'timestamp': datetime.utcnow(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context,
            'agent_id': self.agent_id
        }
        
        self.error_history.append(error_record)
        
        logger.error(
            f"Error recorded: {type(error).__name__}: {error}",
            component="error_handler",
            agent_id=self.agent_id,
            error_type=type(error).__name__,
            context=context
        )
    
    def get_recovery_strategy(self, error: Exception, context: Dict) -> Dict:
        """Get recovery strategy for an error"""
        error_type = type(error)
        
        # Find most specific strategy
        for exception_type, strategy in self.recovery_strategies.items():
            if issubclass(error_type, exception_type):
                return strategy(error, context)
        
        return self._default_recovery(error, context)
    
    def should_escalate(self, error: Exception, retry_count: int) -> bool:
        """Determine if error should be escalated"""
        
        # Check for non-recoverable errors
        if isinstance(error, NonRecoverableError):
            return True
        
        # Check retry count
        if retry_count >= 3:
            return True
        
        # Check error frequency
        recent_errors = [
            e for e in self.error_history
            if e['timestamp'] > datetime.utcnow() - timedelta(minutes=5)
        ]
        
        if len(recent_errors) > 10:
            logger.warning(
                f"High error frequency detected: {len(recent_errors)} errors in 5 minutes",
                component="error_handler",
                agent_id=self.agent_id
            )
            return True
        
        return False


def with_retry(retry_config: RetryConfig = None, 
               error_handler: ErrorHandler = None):
    """Decorator for automatic retry with exponential backoff"""
    
    if retry_config is None:
        retry_config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except NonRecoverableError as e:
                    if error_handler:
                        error_handler.record_error(e, {'attempt': attempt})
                    logger.error(
                        f"Non-recoverable error in {func.__name__}: {e}",
                        component="retry_decorator"
                    )
                    raise
                    
                except Exception as e:
                    last_exception = e
                    
                    if error_handler:
                        error_handler.record_error(e, {'attempt': attempt})
                    
                    if attempt >= retry_config.max_retries:
                        logger.error(
                            f"Max retries exceeded for {func.__name__}: {e}",
                            component="retry_decorator",
                            attempt=attempt
                        )
                        break
                    
                    # Calculate delay
                    delay = retry_config.base_delay
                    if retry_config.exponential_backoff:
                        delay *= (2 ** attempt)
                    
                    delay = min(delay, retry_config.max_delay)
                    
                    if retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Retrying {func.__name__} in {delay:.1f}s (attempt {attempt + 1}/{retry_config.max_retries})",
                        component="retry_decorator",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e)
                    )
                    
                    await asyncio.sleep(delay)
            
            # If we get here, all retries failed
            if error_handler and error_handler.should_escalate(last_exception, retry_config.max_retries):
                raise NonRecoverableError(f"Failed after {retry_config.max_retries} retries: {last_exception}")
            else:
                raise RecoverableError(f"Retries exhausted: {last_exception}")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except NonRecoverableError as e:
                    if error_handler:
                        error_handler.record_error(e, {'attempt': attempt})
                    raise
                    
                except Exception as e:
                    last_exception = e
                    
                    if error_handler:
                        error_handler.record_error(e, {'attempt': attempt})
                    
                    if attempt >= retry_config.max_retries:
                        break
                    
                    # Calculate delay
                    delay = retry_config.base_delay
                    if retry_config.exponential_backoff:
                        delay *= (2 ** attempt)
                    
                    delay = min(delay, retry_config.max_delay)
                    
                    if retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Retrying {func.__name__} in {delay:.1f}s (attempt {attempt + 1}/{retry_config.max_retries})",
                        component="retry_decorator",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e)
                    )
                    
                    import time
                    time.sleep(delay)
            
            # If we get here, all retries failed
            if error_handler and error_handler.should_escalate(last_exception, retry_config.max_retries):
                raise NonRecoverableError(f"Failed after {retry_config.max_retries} retries: {last_exception}")
            else:
                raise RecoverableError(f"Retries exhausted: {last_exception}")
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class GracefulDegradation:
    """Handle graceful degradation when components fail"""
    
    @staticmethod
    def fallback_to_single_model(failed_models: List[str], available_models: List[str]) -> Optional[str]:
        """Fallback to a single model when multi-model approach fails"""
        working_models = [m for m in available_models if m not in failed_models]
        
        if not working_models:
            return None
        
        # Prefer Claude for robustness
        if 'claude-3-5-sonnet-20241022' in working_models:
            return 'claude-3-5-sonnet-20241022'
        
        # Fallback to first available
        return working_models[0]
    
    @staticmethod
    def reduce_complexity(extraction_steps: List, error_context: Dict) -> List:
        """Reduce extraction complexity on repeated failures"""
        
        # Remove optional steps
        essential_steps = []
        for step in extraction_steps:
            if step.get('required', True):
                essential_steps.append(step)
        
        return essential_steps
    
    @staticmethod
    def lower_quality_thresholds(current_thresholds: Dict) -> Dict:
        """Lower quality thresholds as fallback"""
        return {
            key: max(0.5, value - 0.1)  # Lower by 10%, minimum 50%
            for key, value in current_thresholds.items()
        } 