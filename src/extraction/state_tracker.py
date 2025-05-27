"""
State Tracker for Extraction Pipeline
Tracks the state and progress of extraction runs through various stages.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field, asdict
import asyncio
from supabase import Client

logger = logging.getLogger(__name__)


class ExtractionStage(Enum):
    """Stages in the extraction pipeline"""
    QUEUED = "queued"
    INITIALIZING = "initializing"
    STRUCTURE_EXTRACTION = "structure_extraction"
    PRODUCT_EXTRACTION = "product_extraction"
    DETAIL_EXTRACTION = "detail_extraction"
    VALIDATION = "validation"
    HUMAN_REVIEW = "human_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionStatus(Enum):
    """Overall status of extraction"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class StageMetrics:
    """Metrics for a single extraction stage"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    tokens_used: int = 0
    cost: float = 0.0
    errors: List[str] = field(default_factory=list)
    retries: int = 0
    model_used: Optional[str] = None
    prompt_version: Optional[str] = None


@dataclass
class ExtractionRun:
    """Represents a single extraction run"""
    run_id: str
    queue_item_id: int
    upload_id: str
    status: ExtractionStatus
    current_stage: ExtractionStage
    system: str
    configuration: Dict[str, Any]
    stages: Dict[str, StageMetrics] = field(default_factory=dict)
    overall_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class StateTracker:
    """Tracks state of extraction runs"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase = supabase_client
        self.active_runs: Dict[str, ExtractionRun] = {}
        self._lock = asyncio.Lock()
        logger.info("StateTracker initialized")
    
    async def create_run(self, 
                        run_id: str,
                        queue_item_id: int,
                        upload_id: str,
                        system: str,
                        configuration: Dict[str, Any]) -> ExtractionRun:
        """Create a new extraction run"""
        async with self._lock:
            run = ExtractionRun(
                run_id=run_id,
                queue_item_id=queue_item_id,
                upload_id=upload_id,
                status=ExtractionStatus.PENDING,
                current_stage=ExtractionStage.QUEUED,
                system=system,
                configuration=configuration
            )
            
            self.active_runs[run_id] = run
            
            # Persist to database if available
            if self.supabase:
                await self._persist_run(run)
            
            logger.info(f"Created extraction run {run_id} for queue item {queue_item_id}")
            return run
    
    async def update_stage(self,
                          run_id: str,
                          stage: ExtractionStage,
                          metrics: Optional[Dict[str, Any]] = None) -> Optional[ExtractionRun]:
        """Update the current stage of an extraction run"""
        async with self._lock:
            run = self.active_runs.get(run_id)
            if not run:
                logger.warning(f"Run {run_id} not found")
                return None
            
            # End previous stage if exists
            if run.current_stage != stage:
                prev_stage_key = run.current_stage.value
                if prev_stage_key in run.stages and run.stages[prev_stage_key].start_time:
                    run.stages[prev_stage_key].end_time = datetime.utcnow()
                    run.stages[prev_stage_key].duration_seconds = (
                        run.stages[prev_stage_key].end_time - 
                        run.stages[prev_stage_key].start_time
                    ).total_seconds()
            
            # Start new stage
            run.current_stage = stage
            run.status = ExtractionStatus.IN_PROGRESS
            run.updated_at = datetime.utcnow()
            
            # Initialize stage metrics
            stage_key = stage.value
            if stage_key not in run.stages:
                run.stages[stage_key] = StageMetrics(start_time=datetime.utcnow())
            
            # Update metrics if provided
            if metrics:
                stage_metrics = run.stages[stage_key]
                for key, value in metrics.items():
                    if hasattr(stage_metrics, key):
                        setattr(stage_metrics, key, value)
            
            # Persist to database
            if self.supabase:
                await self._persist_run(run)
            
            logger.info(f"Updated run {run_id} to stage {stage.value}")
            return run
    
    async def record_stage_metrics(self,
                                  run_id: str,
                                  stage: ExtractionStage,
                                  metrics: Dict[str, Any]) -> Optional[ExtractionRun]:
        """Record metrics for a specific stage"""
        async with self._lock:
            run = self.active_runs.get(run_id)
            if not run:
                logger.warning(f"Run {run_id} not found")
                return None
            
            stage_key = stage.value
            if stage_key not in run.stages:
                run.stages[stage_key] = StageMetrics()
            
            stage_metrics = run.stages[stage_key]
            for key, value in metrics.items():
                if hasattr(stage_metrics, key):
                    if key in ['tokens_used', 'cost', 'retries']:
                        # Accumulate these metrics
                        current = getattr(stage_metrics, key)
                        setattr(stage_metrics, key, current + value)
                    else:
                        setattr(stage_metrics, key, value)
            
            run.updated_at = datetime.utcnow()
            
            # Update overall metrics
            run.overall_metrics['total_tokens'] = sum(
                s.tokens_used for s in run.stages.values()
            )
            run.overall_metrics['total_cost'] = sum(
                s.cost for s in run.stages.values()
            )
            
            # Persist to database
            if self.supabase:
                await self._persist_run(run)
            
            return run
    
    async def complete_run(self,
                          run_id: str,
                          result_data: Optional[Dict[str, Any]] = None,
                          status: ExtractionStatus = ExtractionStatus.COMPLETED) -> Optional[ExtractionRun]:
        """Mark a run as completed"""
        async with self._lock:
            run = self.active_runs.get(run_id)
            if not run:
                logger.warning(f"Run {run_id} not found")
                return None
            
            # End current stage
            stage_key = run.current_stage.value
            if stage_key in run.stages and run.stages[stage_key].start_time:
                run.stages[stage_key].end_time = datetime.utcnow()
                run.stages[stage_key].duration_seconds = (
                    run.stages[stage_key].end_time - 
                    run.stages[stage_key].start_time
                ).total_seconds()
            
            run.status = status
            run.current_stage = ExtractionStage.COMPLETED if status == ExtractionStatus.COMPLETED else ExtractionStage.FAILED
            run.completed_at = datetime.utcnow()
            run.updated_at = datetime.utcnow()
            run.result_data = result_data
            
            # Calculate total duration
            run.overall_metrics['total_duration_seconds'] = (
                run.completed_at - run.created_at
            ).total_seconds()
            
            # Persist to database
            if self.supabase:
                await self._persist_run(run)
            
            # Remove from active runs
            del self.active_runs[run_id]
            
            logger.info(f"Completed run {run_id} with status {status.value}")
            return run
    
    async def fail_run(self,
                      run_id: str,
                      error_message: str,
                      stage: Optional[ExtractionStage] = None) -> Optional[ExtractionRun]:
        """Mark a run as failed"""
        async with self._lock:
            run = self.active_runs.get(run_id)
            if not run:
                logger.warning(f"Run {run_id} not found")
                return None
            
            run.error_message = error_message
            
            # Record error in stage metrics
            if stage:
                stage_key = stage.value
                if stage_key not in run.stages:
                    run.stages[stage_key] = StageMetrics()
                run.stages[stage_key].errors.append(error_message)
            
            return await self.complete_run(run_id, status=ExtractionStatus.FAILED)
    
    async def get_run(self, run_id: str) -> Optional[ExtractionRun]:
        """Get a specific run by ID"""
        async with self._lock:
            return self.active_runs.get(run_id)
    
    async def get_active_runs(self) -> List[ExtractionRun]:
        """Get all active runs"""
        async with self._lock:
            return list(self.active_runs.values())
    
    async def _persist_run(self, run: ExtractionRun):
        """Persist run data to database"""
        if not self.supabase:
            return
        
        try:
            run_data = {
                "run_id": run.run_id,
                "queue_item_id": run.queue_item_id,
                "upload_id": run.upload_id,
                "status": run.status.value,
                "current_stage": run.current_stage.value,
                "system": run.system,
                "configuration": run.configuration,
                "stages": {k: asdict(v) for k, v in run.stages.items()},
                "overall_metrics": run.overall_metrics,
                "created_at": run.created_at.isoformat(),
                "updated_at": run.updated_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_message": run.error_message,
                "result_data": run.result_data
            }
            
            # Convert datetime objects to strings for JSON serialization
            for stage_data in run_data["stages"].values():
                for field in ['start_time', 'end_time']:
                    if field in stage_data and stage_data[field]:
                        stage_data[field] = stage_data[field].isoformat()
            
            # Try to insert or update
            result = self.supabase.table("extraction_runs").upsert(
                run_data,
                on_conflict="run_id"
            ).execute()
            
        except Exception as e:
            logger.error(f"Failed to persist run {run.run_id}: {e}")
            # Don't fail the operation if persistence fails


# Singleton instance
_state_tracker: Optional[StateTracker] = None


def get_state_tracker(supabase_client: Optional[Client] = None) -> StateTracker:
    """Get or create the singleton StateTracker instance"""
    global _state_tracker
    if _state_tracker is None:
        _state_tracker = StateTracker(supabase_client)
    return _state_tracker