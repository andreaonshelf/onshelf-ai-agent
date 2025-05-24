"""Utility Functions Package"""

from .logger import logger, OnShelfLogger
from .cost_tracker import CostTracker, CostLimitExceededException
from .error_handling import (
    ErrorHandler, RecoverableError, NonRecoverableError, 
    RetryConfig, with_retry, GracefulDegradation
)
from .image_coordinator import MultiImageCoordinator, ImageType, ImageClassifier

__all__ = [
    "logger",
    "OnShelfLogger",
    "CostTracker", 
    "CostLimitExceededException",
    "ErrorHandler",
    "RecoverableError",
    "NonRecoverableError", 
    "RetryConfig",
    "with_retry",
    "GracefulDegradation",
    "MultiImageCoordinator",
    "ImageType",
    "ImageClassifier"
]

# This package can be extended with utility functions as needed 