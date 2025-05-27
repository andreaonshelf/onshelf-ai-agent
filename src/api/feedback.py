"""
Feedback API endpoints for human evaluation and learning
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

from ..config import SystemConfig
from ..utils.logger import logger

# Initialize router
router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackSubmission(BaseModel):
    """Feedback submission model"""
    queue_item_id: int
    upload_id: str
    extraction_rating: int  # 1-5 stars
    planogram_rating: int  # 1-5 stars
    worked_well: Optional[str] = ""
    needs_improvement: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = {}


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    success: bool
    feedback_id: Optional[str] = None
    message: str
    learning_impact: Optional[Dict[str, Any]] = None


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackSubmission
) -> FeedbackResponse:
    """Submit human feedback for an extraction"""
    
    logger.info(
        "Receiving feedback submission",
        queue_item_id=feedback.queue_item_id,
        extraction_rating=feedback.extraction_rating,
        planogram_rating=feedback.planogram_rating
    )
    
    try:
        # Get Supabase client
        config = SystemConfig()
        supabase = config.get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Create feedback record
        feedback_data = {
            "queue_item_id": feedback.queue_item_id,
            "upload_id": feedback.upload_id,
            "extraction_rating": feedback.extraction_rating,
            "planogram_rating": feedback.planogram_rating,
            "worked_well": feedback.worked_well,
            "needs_improvement": feedback.needs_improvement,
            "metadata": feedback.metadata,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "human_reviewer"  # In future, could be actual user ID
        }
        
        # Insert into database
        result = supabase.table("extraction_feedback").insert(feedback_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save feedback")
        
        feedback_id = result.data[0].get("id")
        
        # Calculate learning impact
        learning_impact = calculate_learning_impact(feedback)
        
        # Update queue item with feedback status
        try:
            queue_update = supabase.table("ai_extraction_queue").update({
                "has_feedback": True,
                "feedback_ratings": {
                    "extraction": feedback.extraction_rating,
                    "planogram": feedback.planogram_rating
                },
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", feedback.queue_item_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update queue item with feedback status: {e}")
        
        logger.info(
            "Feedback submitted successfully",
            feedback_id=feedback_id,
            learning_impact=learning_impact
        )
        
        return FeedbackResponse(
            success=True,
            feedback_id=str(feedback_id),
            message="Feedback submitted successfully",
            learning_impact=learning_impact
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{queue_item_id}")
async def get_feedback_stats(
    queue_item_id: int
) -> Dict[str, Any]:
    """Get feedback statistics for a queue item"""
    
    try:
        config = SystemConfig()
        supabase = config.get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Get all feedback for this item
        result = supabase.table("extraction_feedback").select("*").eq(
            "queue_item_id", queue_item_id
        ).execute()
        
        feedback_items = result.data or []
        
        if not feedback_items:
            return {
                "has_feedback": False,
                "feedback_count": 0,
                "average_ratings": None,
                "feedback_summary": None
            }
        
        # Calculate statistics
        extraction_ratings = [f["extraction_rating"] for f in feedback_items]
        planogram_ratings = [f["planogram_rating"] for f in feedback_items]
        
        stats = {
            "has_feedback": True,
            "feedback_count": len(feedback_items),
            "average_ratings": {
                "extraction": sum(extraction_ratings) / len(extraction_ratings),
                "planogram": sum(planogram_ratings) / len(planogram_ratings),
                "overall": (sum(extraction_ratings) + sum(planogram_ratings)) / (2 * len(feedback_items))
            },
            "feedback_summary": {
                "worked_well": [f["worked_well"] for f in feedback_items if f.get("worked_well")],
                "needs_improvement": [f["needs_improvement"] for f in feedback_items if f.get("needs_improvement")]
            },
            "latest_feedback": feedback_items[-1] if feedback_items else None
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-insights")
async def get_learning_insights() -> Dict[str, Any]:
    """Get aggregated learning insights from all feedback"""
    
    try:
        config = SystemConfig()
        supabase = config.get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Get recent feedback
        result = supabase.table("extraction_feedback").select("*").order(
            "created_at", desc=True
        ).limit(100).execute()
        
        feedback_items = result.data or []
        
        if not feedback_items:
            return {
                "total_feedback": 0,
                "insights": []
            }
        
        # Analyze patterns
        insights = analyze_feedback_patterns(feedback_items)
        
        return {
            "total_feedback": len(feedback_items),
            "insights": insights,
            "performance_trends": calculate_performance_trends(feedback_items),
            "common_issues": extract_common_issues(feedback_items),
            "improvement_areas": identify_improvement_areas(feedback_items)
        }
        
    except Exception as e:
        logger.error(f"Error getting learning insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def calculate_learning_impact(feedback: FeedbackSubmission) -> Dict[str, Any]:
    """Calculate the potential learning impact of this feedback"""
    
    # Simple impact calculation based on ratings and comments
    impact_score = 0
    impact_areas = []
    
    # Low ratings indicate high learning potential
    if feedback.extraction_rating <= 2:
        impact_score += 3
        impact_areas.append("extraction_quality")
    elif feedback.extraction_rating <= 3:
        impact_score += 1
        impact_areas.append("extraction_refinement")
    
    if feedback.planogram_rating <= 2:
        impact_score += 3
        impact_areas.append("planogram_generation")
    elif feedback.planogram_rating <= 3:
        impact_score += 1
        impact_areas.append("planogram_refinement")
    
    # Detailed comments increase impact
    if feedback.worked_well and len(feedback.worked_well) > 50:
        impact_score += 1
        impact_areas.append("positive_patterns")
    
    if feedback.needs_improvement and len(feedback.needs_improvement) > 50:
        impact_score += 2
        impact_areas.append("improvement_targets")
    
    return {
        "impact_score": impact_score,
        "impact_level": "high" if impact_score >= 5 else "medium" if impact_score >= 3 else "low",
        "impact_areas": impact_areas,
        "learning_potential": {
            "extraction": feedback.extraction_rating <= 3,
            "planogram": feedback.planogram_rating <= 3,
            "has_actionable_feedback": bool(feedback.needs_improvement)
        }
    }


def analyze_feedback_patterns(feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze patterns in feedback data"""
    
    insights = []
    
    # Rating patterns
    avg_extraction = sum(f["extraction_rating"] for f in feedback_items) / len(feedback_items)
    avg_planogram = sum(f["planogram_rating"] for f in feedback_items) / len(feedback_items)
    
    if avg_extraction < 3:
        insights.append({
            "type": "low_extraction_quality",
            "severity": "high",
            "message": f"Extraction quality averaging {avg_extraction:.1f}/5 stars",
            "recommendation": "Review extraction prompts and model selection"
        })
    
    if avg_planogram < 3:
        insights.append({
            "type": "low_planogram_quality",
            "severity": "high",
            "message": f"Planogram quality averaging {avg_planogram:.1f}/5 stars",
            "recommendation": "Improve planogram generation logic"
        })
    
    # Check for consistent issues
    improvements = [f["needs_improvement"] for f in feedback_items if f.get("needs_improvement")]
    if improvements:
        # Simple keyword analysis
        common_keywords = ["position", "missing", "wrong", "incorrect", "layout"]
        keyword_counts = {kw: sum(1 for imp in improvements if kw in imp.lower()) for kw in common_keywords}
        
        for keyword, count in keyword_counts.items():
            if count >= len(improvements) * 0.3:  # 30% threshold
                insights.append({
                    "type": f"common_issue_{keyword}",
                    "severity": "medium",
                    "message": f"'{keyword}' mentioned in {count}/{len(improvements)} feedback items",
                    "recommendation": f"Focus on improving {keyword}-related accuracy"
                })
    
    return insights


def calculate_performance_trends(feedback_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate performance trends over time"""
    
    # Sort by date
    sorted_items = sorted(feedback_items, key=lambda x: x["created_at"])
    
    # Calculate rolling averages
    window_size = min(10, len(sorted_items) // 3)
    if window_size < 3:
        return {"trend": "insufficient_data"}
    
    recent_items = sorted_items[-window_size:]
    older_items = sorted_items[:window_size]
    
    recent_avg = sum(f["extraction_rating"] + f["planogram_rating"] for f in recent_items) / (2 * len(recent_items))
    older_avg = sum(f["extraction_rating"] + f["planogram_rating"] for f in older_items) / (2 * len(older_items))
    
    improvement = recent_avg - older_avg
    
    return {
        "trend": "improving" if improvement > 0.2 else "declining" if improvement < -0.2 else "stable",
        "recent_average": recent_avg,
        "older_average": older_avg,
        "improvement_percentage": (improvement / older_avg) * 100 if older_avg > 0 else 0
    }


def extract_common_issues(feedback_items: List[Dict[str, Any]]) -> List[str]:
    """Extract common issues from feedback"""
    
    issues = []
    improvements = [f["needs_improvement"] for f in feedback_items if f.get("needs_improvement")]
    
    # Simple pattern matching for common issues
    patterns = {
        "Product positioning": ["position", "placement", "location", "shifted"],
        "Missing products": ["missing", "not detected", "skipped", "omitted"],
        "Wrong products": ["wrong", "incorrect", "misidentified", "confused"],
        "Layout issues": ["layout", "structure", "shelf", "arrangement"],
        "Accuracy problems": ["accuracy", "precision", "exact", "precise"]
    }
    
    for issue_type, keywords in patterns.items():
        count = sum(1 for imp in improvements if any(kw in imp.lower() for kw in keywords))
        if count >= len(improvements) * 0.2:  # 20% threshold
            issues.append(f"{issue_type} ({count} occurrences)")
    
    return issues


def identify_improvement_areas(feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify specific areas for improvement"""
    
    areas = []
    
    # Analyze ratings distribution
    extraction_low = sum(1 for f in feedback_items if f["extraction_rating"] <= 2)
    planogram_low = sum(1 for f in feedback_items if f["planogram_rating"] <= 2)
    
    if extraction_low > len(feedback_items) * 0.3:
        areas.append({
            "area": "extraction_accuracy",
            "priority": "high",
            "affected_percentage": (extraction_low / len(feedback_items)) * 100,
            "suggested_action": "Review and improve extraction prompts"
        })
    
    if planogram_low > len(feedback_items) * 0.3:
        areas.append({
            "area": "planogram_visualization",
            "priority": "high",
            "affected_percentage": (planogram_low / len(feedback_items)) * 100,
            "suggested_action": "Enhance planogram generation algorithm"
        })
    
    # Check for specific feedback patterns
    worked_well = [f["worked_well"] for f in feedback_items if f.get("worked_well")]
    if worked_well:
        # Identify what's working to preserve it
        if any("structure" in w.lower() for w in worked_well):
            areas.append({
                "area": "structure_detection",
                "priority": "maintain",
                "affected_percentage": 100,
                "suggested_action": "Maintain current structure detection approach"
            })
    
    return areas