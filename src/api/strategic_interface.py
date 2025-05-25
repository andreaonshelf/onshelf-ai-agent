"""
Strategic Interface API
API endpoints for strategic system selection and comparison
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import asyncio

from ..systems.base_system import ExtractionSystemFactory
from ..config import SystemConfig
from ..utils import logger

router = APIRouter(prefix="/api/strategic", tags=["Strategic Multi-System"])

# Initialize system configuration
config = SystemConfig()


@router.post("/extract-single")
async def extract_with_single_system(
    file: UploadFile = File(...),
    system_type: str = Form(..., description="custom, langgraph, or hybrid"),
    upload_id: Optional[str] = Form(None)
):
    """Extract using a single selected system"""
    
    if system_type not in ExtractionSystemFactory.AVAILABLE_SYSTEMS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid system type. Available: {list(ExtractionSystemFactory.AVAILABLE_SYSTEMS.keys())}"
        )
    
    if not upload_id:
        upload_id = str(uuid.uuid4())
    
    logger.info(
        f"Starting single system extraction: {system_type}",
        component="strategic_api",
        system_type=system_type,
        upload_id=upload_id
    )
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Get selected system
        system = ExtractionSystemFactory.get_system(system_type, config)
        
        # Run extraction
        start_time = datetime.utcnow()
        result = await system.extract_with_consensus(image_data, upload_id)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Get additional metrics
        cost_breakdown = await system.get_cost_breakdown()
        performance_metrics = await system.get_performance_metrics()
        
        response = {
            "success": True,
            "upload_id": upload_id,
            "system_type": system_type,
            "system_name": ExtractionSystemFactory.AVAILABLE_SYSTEMS[system_type],
            "processing_time": processing_time,
            
            # Core results
            "extraction_result": {
                "overall_accuracy": result.overall_accuracy,
                "consensus_reached": result.consensus_reached,
                "iteration_count": result.iteration_count,
                "products_found": len(result.positions),
                "structure": result.structure,
                "positions": result.positions,
                "quantities": result.quantities,
                "details": result.details
            },
            
            # System analysis
            "cost_breakdown": cost_breakdown.dict(),
            "performance_metrics": performance_metrics.dict(),
            "architecture_benefits": system.get_architecture_benefits(),
            "complexity_rating": system.get_complexity_rating(),
            "control_level": system.get_control_level(),
            
            # Human review
            "ready_for_human_review": result.ready_for_human_review,
            "human_review_priority": result.human_review_priority,
            
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Single system extraction completed: {system_type}",
            component="strategic_api",
            system_type=system_type,
            accuracy=result.overall_accuracy,
            processing_time=processing_time
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(
            f"Single system extraction failed: {e}",
            component="strategic_api",
            system_type=system_type,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract-comparison")
async def extract_with_strategic_comparison(
    file: UploadFile = File(...),
    systems: str = Form("custom,langgraph,hybrid", description="Comma-separated system types"),
    upload_id: Optional[str] = Form(None)
):
    """Run strategic comparison across multiple systems"""
    
    if not upload_id:
        upload_id = str(uuid.uuid4())
    
    # Parse systems
    system_list = [s.strip() for s in systems.split(",")]
    
    # Validate systems
    invalid_systems = [s for s in system_list if s not in ExtractionSystemFactory.AVAILABLE_SYSTEMS]
    if invalid_systems:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid systems: {invalid_systems}. Available: {list(ExtractionSystemFactory.AVAILABLE_SYSTEMS.keys())}"
        )
    
    logger.info(
        f"Starting strategic comparison for systems: {system_list}",
        component="strategic_api",
        systems=system_list,
        upload_id=upload_id
    )
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Run strategic comparison
        comparison_results = await ExtractionSystemFactory.run_strategic_comparison(
            image_data, upload_id, config
        )
        
        # Format response
        response = {
            "success": True,
            "upload_id": upload_id,
            "systems_compared": system_list,
            "comparison_timestamp": datetime.utcnow().isoformat(),
            
            # Individual system results
            "system_results": {},
            
            # Comparison summary
            "comparison_summary": comparison_results.get('comparison_summary', {}),
            
            # Strategic insights
            "strategic_insights": _generate_strategic_insights(comparison_results)
        }
        
        # Add individual system results
        for system_type in system_list:
            if system_type in comparison_results and comparison_results[system_type].get('success', False):
                system_data = comparison_results[system_type]
                result = system_data['result']
                
                response["system_results"][system_type] = {
                    "system_name": ExtractionSystemFactory.AVAILABLE_SYSTEMS[system_type],
                    "success": True,
                    "processing_time": system_data['processing_time'],
                    
                    # Core metrics
                    "accuracy": result.overall_accuracy,
                    "consensus_rate": result.performance_metrics.consensus_rate,
                    "products_found": len(result.positions),
                    "iteration_count": result.iteration_count,
                    
                    # Cost and performance
                    "total_cost": system_data['cost'].total_cost,
                    "cost_per_accuracy": system_data['cost'].cost_per_accuracy_point,
                    
                    # Architecture
                    "architecture_benefits": system_data['architecture_benefits'],
                    "complexity_rating": system_data['complexity_rating'],
                    "control_level": system_data['control_level'],
                    
                    # Detailed results
                    "extraction_data": {
                        "structure": result.structure,
                        "positions": result.positions,
                        "quantities": result.quantities,
                        "details": result.details
                    },
                    
                    "validation_result": result.validation_result
                }
            else:
                # System failed
                error_info = comparison_results.get(system_type, {})
                response["system_results"][system_type] = {
                    "system_name": ExtractionSystemFactory.AVAILABLE_SYSTEMS.get(system_type, system_type),
                    "success": False,
                    "error": error_info.get('error', 'Unknown error'),
                    "processing_time": 0
                }
        
        logger.info(
            f"Strategic comparison completed",
            component="strategic_api",
            successful_systems=len([r for r in response["system_results"].values() if r.get('success', False)]),
            total_systems=len(system_list)
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(
            f"Strategic comparison failed: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/systems")
async def get_available_systems():
    """Get all available extraction systems with descriptions"""
    
    systems = ExtractionSystemFactory.get_available_systems()
    
    # Add detailed information for each system
    detailed_systems = {}
    for system_type, description in systems.items():
        try:
            # Create temporary system instance to get details
            system = ExtractionSystemFactory.get_system(system_type, config)
            
            detailed_systems[system_type] = {
                "name": description,
                "architecture_benefits": system.get_architecture_benefits(),
                "complexity_rating": system.get_complexity_rating(),
                "control_level": system.get_control_level(),
                "recommended_for": _get_system_recommendations(system_type)
            }
        except Exception as e:
            detailed_systems[system_type] = {
                "name": description,
                "error": f"Failed to load system details: {str(e)}"
            }
    
    return {
        "available_systems": detailed_systems,
        "total_systems": len(detailed_systems),
        "comparison_modes": [
            "single_system",
            "strategic_comparison",
            "a_b_testing"
        ]
    }


@router.post("/human-feedback")
async def submit_human_feedback(
    upload_id: str = Form(...),
    system_type: str = Form(...),
    feedback_data: Dict[str, Any] = Form(...)
):
    """Submit human feedback for a specific system result"""
    
    logger.info(
        f"Receiving human feedback for {system_type} system",
        component="strategic_api",
        upload_id=upload_id,
        system_type=system_type
    )
    
    try:
        # Get the system to access its human feedback integration
        system = ExtractionSystemFactory.get_system(system_type, config)
        
        # Process human feedback through the system's learning component
        await system.human_feedback.process_human_correction(upload_id, [feedback_data])
        
        return {
            "success": True,
            "upload_id": upload_id,
            "system_type": system_type,
            "feedback_processed": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Human feedback processing failed: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")


@router.get("/learning-statistics")
async def get_learning_statistics(
    system_type: Optional[str] = Query(None, description="Specific system type"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get learning statistics from human feedback"""
    
    try:
        if system_type:
            # Get statistics for specific system
            system = ExtractionSystemFactory.get_system(system_type, config)
            stats = await system.human_feedback.get_learning_statistics(days)
            
            return {
                "system_type": system_type,
                "system_name": ExtractionSystemFactory.AVAILABLE_SYSTEMS[system_type],
                "statistics": stats,
                "period_days": days
            }
        else:
            # Get statistics for all systems
            all_stats = {}
            
            for sys_type in ExtractionSystemFactory.AVAILABLE_SYSTEMS.keys():
                try:
                    system = ExtractionSystemFactory.get_system(sys_type, config)
                    stats = await system.human_feedback.get_learning_statistics(days)
                    all_stats[sys_type] = {
                        "system_name": ExtractionSystemFactory.AVAILABLE_SYSTEMS[sys_type],
                        "statistics": stats
                    }
                except Exception as e:
                    all_stats[sys_type] = {
                        "system_name": ExtractionSystemFactory.AVAILABLE_SYSTEMS[sys_type],
                        "error": str(e)
                    }
            
            return {
                "all_systems": all_stats,
                "period_days": days,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(
            f"Learning statistics retrieval failed: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")


@router.get("/comparison-history/{upload_id}")
async def get_comparison_history(upload_id: str):
    """Get historical comparison results for an upload"""
    
    # TODO: Implement database retrieval of historical results
    # For now, return mock data
    
    return {
        "upload_id": upload_id,
        "historical_comparisons": [
            {
                "timestamp": "2024-01-15T10:30:00Z",
                "systems_compared": ["custom", "langgraph", "hybrid"],
                "best_system": "hybrid",
                "best_accuracy": 0.93,
                "comparison_summary": "Hybrid system achieved highest accuracy with best spatial reasoning"
            }
        ],
        "trends": {
            "accuracy_improvement": 0.05,
            "cost_optimization": 0.12,
            "processing_time_reduction": 0.08
        }
    }


def _generate_strategic_insights(comparison_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate strategic insights from comparison results"""
    
    insights = {
        "recommendations": [],
        "trade_offs": [],
        "use_case_guidance": {},
        "performance_analysis": {}
    }
    
    if 'comparison_summary' not in comparison_results:
        return insights
    
    summary = comparison_results['comparison_summary']
    
    # Generate recommendations
    best_accuracy = summary.get('best_accuracy', {})
    fastest_processing = summary.get('fastest_processing', {})
    most_cost_effective = summary.get('most_cost_effective', {})
    
    if best_accuracy.get('system'):
        insights["recommendations"].append(
            f"For highest accuracy ({best_accuracy['score']:.1%}): Use {best_accuracy['system']} system"
        )
    
    if fastest_processing.get('system'):
        insights["recommendations"].append(
            f"For fastest processing ({fastest_processing['time']:.1f}s): Use {fastest_processing['system']} system"
        )
    
    if most_cost_effective.get('system'):
        insights["recommendations"].append(
            f"For cost efficiency: Use {most_cost_effective['system']} system"
        )
    
    # Generate trade-off analysis
    architectural_comparison = summary.get('architectural_comparison', {})
    
    for system_type, data in architectural_comparison.items():
        complexity = data.get('complexity', 'Unknown')
        control = data.get('control', 'Unknown')
        accuracy = data.get('accuracy', 0)
        cost = data.get('cost', 0)
        
        insights["trade_offs"].append({
            "system": system_type,
            "complexity_vs_accuracy": f"{complexity} complexity → {accuracy:.1%} accuracy",
            "control_vs_cost": f"{control} control → ${cost:.3f} cost",
            "benefits": data.get('benefits', [])
        })
    
    # Use case guidance
    insights["use_case_guidance"] = {
        "high_volume_processing": "Custom system for maximum cost control",
        "enterprise_deployment": "LangGraph for professional workflow management",
        "research_and_development": "Hybrid system for maximum capability",
        "quick_prototyping": "Custom system for fastest iteration",
        "production_reliability": "LangGraph for proven patterns"
    }
    
    return insights


@router.post("/prompt-optimization-mode")
async def set_prompt_optimization_mode(mode: str = Form(...)):
    """Set prompt optimization mode for all systems"""
    
    valid_modes = ['automatic', 'conservative', 'experimental']
    
    if mode not in valid_modes:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid mode. Valid modes: {valid_modes}"
        )
    
    # Store user preference and configure settings
    settings = {
        'automatic': {
            'use_best_performing': True, 
            'ab_test_rate': 0.1,
            'description': 'Use best performing prompts with 10% A/B testing'
        },
        'conservative': {
            'use_best_performing': True, 
            'ab_test_rate': 0.0,
            'description': 'Always use best performing prompts, no experimentation'
        },
        'experimental': {
            'use_best_performing': False, 
            'ab_test_rate': 0.3,
            'description': 'Test new prompts frequently, 30% experimentation rate'
        }
    }
    
    logger.info(
        f"Prompt optimization mode set to: {mode}",
        component="strategic_api",
        mode=mode,
        settings=settings[mode]
    )
    
    return {
        "success": True,
        "mode": mode,
        "settings": settings[mode],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/prompt-analytics")
async def get_prompt_analytics(
    prompt_type: Optional[str] = Query(None, description="Filter by prompt type"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get prompt performance analytics"""
    
    try:
        # This would typically query the database
        # For now, return mock analytics data
        
        analytics = {
            "period_days": days,
            "prompt_performance": [
                {
                    "prompt_type": "structure_analysis",
                    "model_type": "claude",
                    "prompt_version": "2.1",
                    "performance_score": 0.94,
                    "usage_count": 156,
                    "correction_rate": 0.08,
                    "avg_accuracy": 0.92,
                    "avg_processing_time_ms": 2340,
                    "avg_cost": 0.045
                },
                {
                    "prompt_type": "position_analysis", 
                    "model_type": "gpt4o",
                    "prompt_version": "1.8",
                    "performance_score": 0.89,
                    "usage_count": 142,
                    "correction_rate": 0.12,
                    "avg_accuracy": 0.87,
                    "avg_processing_time_ms": 1890,
                    "avg_cost": 0.067
                }
            ],
            "improvement_trends": {
                "accuracy_improvement": 0.08,
                "cost_reduction": 0.15,
                "correction_rate_reduction": 0.23
            },
            "top_performing_prompts": [
                {
                    "prompt_type": "structure_analysis",
                    "model_type": "claude", 
                    "performance_score": 0.94,
                    "created_from_feedback": True
                }
            ]
        }
        
        # Apply filters if provided
        if prompt_type:
            analytics["prompt_performance"] = [
                p for p in analytics["prompt_performance"] 
                if p["prompt_type"] == prompt_type
            ]
        
        if model_type:
            analytics["prompt_performance"] = [
                p for p in analytics["prompt_performance"]
                if p["model_type"] == model_type
            ]
        
        return analytics
        
    except Exception as e:
        logger.error(
            f"Failed to get prompt analytics: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.post("/prompt/edit")
async def edit_prompt(
    prompt_type: str = Form(..., description="Type of prompt to edit"),
    model_type: str = Form(..., description="Model type (gpt4o, claude, gemini, universal)"),
    new_content: str = Form(..., description="New prompt content"),
    description: Optional[str] = Form(None, description="Description of changes made")
):
    """Allow manual prompt editing with immediate activation"""
    
    valid_prompt_types = ['structure_analysis', 'position_analysis', 'quantity_analysis', 'detail_analysis', 'validation']
    valid_model_types = ['gpt4o', 'claude', 'gemini', 'universal']
    
    if prompt_type not in valid_prompt_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid prompt type. Valid types: {valid_prompt_types}"
        )
    
    if model_type not in valid_model_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model type. Valid types: {valid_model_types}"
        )
    
    try:
        # Get human feedback system to handle prompt updates
        from ..feedback.human_learning import HumanFeedbackLearningSystem
        learning_system = HumanFeedbackLearningSystem(config)
        
        # Create new prompt version
        new_version = f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Store the new prompt
        await learning_system._save_manual_prompt(
            prompt_type=prompt_type,
            model_type=model_type,
            prompt_content=new_content,
            prompt_version=new_version,
            description=description or "Manual edit via API"
        )
        
        logger.info(
            f"Manual prompt edit completed",
            component="strategic_api",
            prompt_type=prompt_type,
            model_type=model_type,
            version=new_version
        )
        
        return {
            "success": True,
            "prompt_type": prompt_type,
            "model_type": model_type,
            "new_version": new_version,
            "content_length": len(new_content),
            "description": description,
            "activated": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Failed to edit prompt: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Prompt editing failed: {str(e)}")


@router.get("/prompt/versions")
async def get_prompt_versions(
    prompt_type: str = Query(..., description="Type of prompt to view"),
    model_type: Optional[str] = Query(None, description="Filter by model type")
):
    """View all prompt versions and their performance metrics"""
    
    try:
        from ..feedback.human_learning import HumanFeedbackLearningSystem
        learning_system = HumanFeedbackLearningSystem(config)
        
        # Get prompt versions from database or in-memory storage
        versions = await learning_system._get_prompt_versions(prompt_type, model_type)
        
        return {
            "prompt_type": prompt_type,
            "model_type_filter": model_type,
            "total_versions": len(versions),
            "versions": versions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Failed to get prompt versions: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Version retrieval failed: {str(e)}")


@router.post("/prompt/activate")
async def activate_prompt_version(
    prompt_id: str = Form(..., description="ID of prompt version to activate"),
    reason: Optional[str] = Form(None, description="Reason for activation")
):
    """Manually select which prompt version to use"""
    
    try:
        from ..feedback.human_learning import HumanFeedbackLearningSystem
        learning_system = HumanFeedbackLearningSystem(config)
        
        # Activate the specified prompt version
        result = await learning_system._activate_prompt_version(prompt_id, reason)
        
        if result['success']:
            logger.info(
                f"Prompt version activated manually",
                component="strategic_api",
                prompt_id=prompt_id,
                prompt_type=result.get('prompt_type'),
                model_type=result.get('model_type'),
                reason=reason
            )
            
            return {
                "success": True,
                "prompt_id": prompt_id,
                "prompt_type": result.get('prompt_type'),
                "model_type": result.get('model_type'),
                "prompt_version": result.get('prompt_version'),
                "reason": reason,
                "activated_at": datetime.utcnow().isoformat(),
                "previous_active": result.get('previous_active')
            }
        else:
            raise HTTPException(status_code=404, detail=result.get('error', 'Prompt not found'))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to activate prompt version: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Prompt activation failed: {str(e)}")


@router.post("/prompt/test")
async def test_prompt(
    prompt_type: str = Form(..., description="Type of prompt to test"),
    model_type: str = Form(..., description="Model to test with"),
    prompt_content: str = Form(..., description="Prompt content to test"),
    test_image: UploadFile = File(..., description="Test image for prompt evaluation")
):
    """Test a prompt without saving it - for A/B testing and experimentation"""
    
    try:
        # Read test image
        image_data = await test_image.read()
        
        # Get the appropriate system for testing
        system = ExtractionSystemFactory.get_system("custom", config)
        
        # Test the prompt (mock implementation for now)
        test_result = await system._test_prompt_performance(
            prompt_content=prompt_content,
            prompt_type=prompt_type,
            model_type=model_type,
            image_data=image_data
        )
        
        return {
            "success": True,
            "prompt_type": prompt_type,
            "model_type": model_type,
            "test_results": test_result,
            "recommendations": _generate_prompt_recommendations(test_result),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Failed to test prompt: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Prompt testing failed: {str(e)}")


@router.get("/prompt/suggestions")
async def get_prompt_suggestions(
    prompt_type: str = Query(..., description="Type of prompt to get suggestions for"),
    model_type: str = Query(..., description="Model type for suggestions"),
    based_on: str = Query("performance", description="Base suggestions on: performance, errors, feedback")
):
    """Get AI-generated suggestions for prompt improvements"""
    
    try:
        from ..feedback.human_learning import HumanFeedbackLearningSystem
        learning_system = HumanFeedbackLearningSystem(config)
        
        # Get suggestions based on historical data
        suggestions = await learning_system._generate_prompt_suggestions(
            prompt_type=prompt_type,
            model_type=model_type,
            based_on=based_on
        )
        
        return {
            "prompt_type": prompt_type,
            "model_type": model_type,
            "based_on": based_on,
            "suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Failed to get prompt suggestions: {e}",
            component="strategic_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")


def _generate_prompt_recommendations(test_result: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on prompt test results"""
    
    recommendations = []
    
    accuracy = test_result.get('accuracy', 0)
    processing_time = test_result.get('processing_time_ms', 0)
    confidence = test_result.get('confidence', 0)
    
    if accuracy < 0.8:
        recommendations.append("Consider adding more specific instructions for better accuracy")
    
    if processing_time > 3000:
        recommendations.append("Prompt may be too complex - consider simplifying for faster processing")
    
    if confidence < 0.7:
        recommendations.append("Add confidence-building instructions to improve model certainty")
    
    if accuracy > 0.95:
        recommendations.append("Excellent performance! Consider using this as a template for other prompts")
    
    return recommendations if recommendations else ["Prompt performance looks good - no specific recommendations"]


def _get_system_recommendations(system_type: str) -> List[str]:
    """Get recommendations for when to use each system"""
    
    recommendations = {
        "custom": [
            "Maximum cost control required",
            "Fast debugging and iteration needed",
            "Simple, transparent processing preferred",
            "No framework dependencies desired"
        ],
        "langgraph": [
            "Professional workflow management needed",
            "Enterprise deployment with reliability",
            "State persistence and checkpointing required",
            "Proven patterns and community support valued"
        ],
        "hybrid": [
            "Maximum accuracy and capability required",
            "Research and development projects",
            "Complex reasoning and memory needed",
            "Best-in-class performance regardless of complexity"
        ]
    }
    
    return recommendations.get(system_type, ["General purpose extraction"]) 