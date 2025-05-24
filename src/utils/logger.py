"""
OnShelf AI Agent Logging System
Structured logging with levels, formatting, and persistence
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class OnShelfFormatter(logging.Formatter):
    """Custom formatter for OnShelf AI Agent logs"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'component': getattr(record, 'component', 'unknown'),
            'agent_id': getattr(record, 'agent_id', None),
            'upload_id': getattr(record, 'upload_id', None),
            'iteration': getattr(record, 'iteration', None),
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry['extra'] = log_entry.get('extra', {})
                log_entry['extra'][key] = value
        
        return json.dumps(log_entry, default=str)


class OnShelfLogger:
    """Centralized logging for OnShelf AI Agent"""
    
    def __init__(self, name: str = "onshelf_ai"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Console formatter (human readable)
        console_format = "%(asctime)s | %(levelname)-8s | %(component)-15s | %(message)s"
        console_formatter = logging.Formatter(console_format, datefmt="%H:%M:%S")
        console_handler.setFormatter(console_formatter)
        
        # File handler (structured JSON)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"onshelf_ai_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(OnShelfFormatter())
        
        # Error file handler
        error_handler = logging.FileHandler(
            log_dir / f"onshelf_ai_errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(OnShelfFormatter())
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
    
    def _log(self, level: int, message: str, component: str = "unknown", 
             agent_id: str = None, upload_id: str = None, iteration: int = None, 
             **kwargs):
        """Internal logging method with context"""
        extra = {
            'component': component,
            'agent_id': agent_id,
            'upload_id': upload_id,
            'iteration': iteration,
            **kwargs
        }
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, component: str = "unknown", **kwargs):
        """Debug level logging"""
        self._log(logging.DEBUG, message, component, **kwargs)
    
    def info(self, message: str, component: str = "unknown", **kwargs):
        """Info level logging"""
        self._log(logging.INFO, message, component, **kwargs)
    
    def warning(self, message: str, component: str = "unknown", **kwargs):
        """Warning level logging"""
        self._log(logging.WARNING, message, component, **kwargs)
    
    def error(self, message: str, component: str = "unknown", **kwargs):
        """Error level logging"""
        self._log(logging.ERROR, message, component, **kwargs)
    
    def critical(self, message: str, component: str = "unknown", **kwargs):
        """Critical level logging"""
        self._log(logging.CRITICAL, message, component, **kwargs)
    
    def log_agent_start(self, agent_id: str, upload_id: str, target_accuracy: float):
        """Log agent start event"""
        self.info(
            f"AI Agent started for upload {upload_id}",
            component="agent",
            agent_id=agent_id,
            upload_id=upload_id,
            target_accuracy=target_accuracy,
            event_type="agent_start"
        )
    
    def log_iteration_start(self, agent_id: str, iteration: int, strategy: str):
        """Log iteration start"""
        self.info(
            f"Starting iteration {iteration} with strategy: {strategy}",
            component="agent",
            agent_id=agent_id,
            iteration=iteration,
            strategy=strategy,
            event_type="iteration_start"
        )
    
    def log_extraction_step(self, agent_id: str, step_id: str, model: str, 
                           duration: float = None, cost: float = None):
        """Log extraction step completion"""
        self.info(
            f"Extraction step '{step_id}' completed using {model}",
            component="extraction",
            agent_id=agent_id,
            step_id=step_id,
            model=model,
            duration_seconds=duration,
            api_cost=cost,
            event_type="extraction_step"
        )
    
    def log_accuracy_update(self, agent_id: str, iteration: int, accuracy: float, 
                           issues_found: int):
        """Log accuracy improvement"""
        self.info(
            f"Accuracy: {accuracy:.2%} (Issues: {issues_found})",
            component="agent",
            agent_id=agent_id,
            iteration=iteration,
            accuracy=accuracy,
            issues_found=issues_found,
            event_type="accuracy_update"
        )
    
    def log_cost_tracking(self, agent_id: str, operation: str, cost: float, 
                         total_cost: float, limit: float):
        """Log cost tracking"""
        self.info(
            f"API cost: {operation} £{cost:.3f} (Total: £{total_cost:.3f}/£{limit:.2f})",
            component="cost_tracker",
            agent_id=agent_id,
            operation=operation,
            operation_cost=cost,
            total_cost=total_cost,
            cost_limit=limit,
            event_type="cost_tracking"
        )
    
    def log_escalation(self, agent_id: str, reason: str, final_accuracy: float):
        """Log human escalation"""
        self.warning(
            f"Escalating to human review: {reason} (Final accuracy: {final_accuracy:.2%})",
            component="agent",
            agent_id=agent_id,
            escalation_reason=reason,
            final_accuracy=final_accuracy,
            event_type="escalation"
        )
    
    def log_completion(self, agent_id: str, accuracy: float, iterations: int, 
                      duration: float, total_cost: float):
        """Log successful completion"""
        self.info(
            f"Agent completed successfully: {accuracy:.2%} in {iterations} iterations",
            component="agent",
            agent_id=agent_id,
            final_accuracy=accuracy,
            iterations_completed=iterations,
            processing_duration=duration,
            total_api_cost=total_cost,
            event_type="completion"
        )


# Global logger instance
logger = OnShelfLogger() 