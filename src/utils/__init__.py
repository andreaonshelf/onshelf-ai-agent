"""Utility Functions Package"""

from .logger import logger, OnShelfLogger
from .cost_tracker import CostTracker, CostLimitExceededException
from .error_handling import (
    ErrorHandler, RecoverableError, NonRecoverableError, 
    RetryConfig, with_retry, GracefulDegradation
)
from .image_coordinator import MultiImageCoordinator, ImageType, ImageClassifier
from .model_usage_tracker import ModelUsageTracker, get_model_usage_tracker

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
    "ImageClassifier",
    "ModelUsageTracker",
    "get_model_usage_tracker"
]

# This package can be extended with utility functions as needed 