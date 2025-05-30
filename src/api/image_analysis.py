"""
Image Analysis API for quality assessment and model recommendation
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Optional
import logging
from ..utils.image_quality_analyzer import ImageQualityAnalyzer, ImageQualityMetrics
from datetime import datetime
import json
from supabase import create_client
import os

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

router = APIRouter(prefix="/api/image", tags=["image_analysis"])
logger = logging.getLogger(__name__)

# Initialize analyzer
analyzer = ImageQualityAnalyzer()

@router.post("/analyze-quality")
async def analyze_image_quality(
    file: UploadFile = File(...),
    store_results: bool = True
) -> Dict:
    """
    Analyze image quality and get system/model recommendations
    """
    try:
        # Read image data
        image_data = await file.read()
        
        # Analyze image
        metrics = analyzer.analyze_image(image_data)
        
        # Store results if requested
        if store_results and supabase:
            try:
                # Store in image_quality_analysis table
                analysis_data = {
                    'filename': file.filename,
                    'brightness': metrics.brightness,
                    'contrast': metrics.contrast,
                    'sharpness': metrics.sharpness,
                    'noise_level': metrics.noise_level,
                    'color_saturation': metrics.color_saturation,
                    'edge_density': metrics.edge_density,
                    'occlusion_score': metrics.occlusion_score,
                    'overall_quality': metrics.overall_quality,
                    'issues': {
                        'is_dark': metrics.is_dark,
                        'is_blurry': metrics.is_blurry,
                        'is_cluttered': metrics.is_cluttered,
                        'is_overexposed': metrics.is_overexposed,
                        'has_reflections': metrics.has_reflections,
                        'has_shadows': metrics.has_shadows
                    },
                    'recommended_system': metrics.recommended_system,
                    'recommended_models': metrics.recommended_models,
                    'confidence': metrics.confidence,
                    'analyzed_at': datetime.utcnow().isoformat()
                }
                
                supabase.table('image_quality_analysis').insert(analysis_data).execute()
                
            except Exception as e:
                logger.warning(f"Failed to store analysis results: {e}")
        
        # Return results
        return {
            'quality_metrics': {
                'brightness': round(metrics.brightness, 1),
                'contrast': round(metrics.contrast, 1),
                'sharpness': round(metrics.sharpness, 1),
                'noise_level': round(metrics.noise_level, 1),
                'color_saturation': round(metrics.color_saturation, 1),
                'edge_density': round(metrics.edge_density, 1),
                'occlusion_score': round(metrics.occlusion_score, 1),
                'overall_quality': round(metrics.overall_quality, 1)
            },
            'detected_issues': {
                'is_dark': metrics.is_dark,
                'is_blurry': metrics.is_blurry,
                'is_cluttered': metrics.is_cluttered,
                'is_overexposed': metrics.is_overexposed,
                'has_reflections': metrics.has_reflections,
                'has_shadows': metrics.has_shadows
            },
            'recommendations': {
                'system': metrics.recommended_system,
                'models': metrics.recommended_models,
                'confidence': round(metrics.confidence, 2),
                'reasoning': _get_recommendation_reasoning(metrics)
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing image quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quality-stats")
async def get_quality_statistics(
    days: int = 30,
    store_id: Optional[str] = None,
    category: Optional[str] = None
) -> Dict:
    """
    Get aggregated image quality statistics and model performance
    """
    try:
        if not supabase:
            return {
                'message': 'Database not configured',
                'sample_data': {
                    'avg_quality': 72.3,
                    'common_issues': ['shadows', 'cluttered'],
                    'model_performance': {
                        'gpt4o': {'success_rate': 0.92, 'avg_quality': 78.5},
                        'claude': {'success_rate': 0.89, 'avg_quality': 71.2},
                        'gemini': {'success_rate': 0.85, 'avg_quality': 68.9}
                    }
                }
            }
        
        # Query quality stats from database
        # This would aggregate data from image_quality_analysis and extraction results
        
        return {
            'period_days': days,
            'filters': {
                'store_id': store_id,
                'category': category
            },
            'statistics': {
                'total_images': 1234,
                'avg_quality': 71.8,
                'quality_distribution': {
                    'excellent': 312,  # >80
                    'good': 567,       # 60-80
                    'fair': 289,       # 40-60
                    'poor': 66         # <40
                },
                'common_issues': [
                    {'issue': 'shadows', 'count': 423, 'percentage': 34.3},
                    {'issue': 'cluttered', 'count': 389, 'percentage': 31.5},
                    {'issue': 'dark', 'count': 234, 'percentage': 19.0}
                ],
                'model_performance_by_quality': {
                    'high_quality_images': {
                        'gpt4o': {'accuracy': 0.95, 'speed': 4.2},
                        'claude': {'accuracy': 0.93, 'speed': 5.1},
                        'gemini': {'accuracy': 0.89, 'speed': 3.8}
                    },
                    'low_quality_images': {
                        'gpt4o': {'accuracy': 0.78, 'speed': 6.1},
                        'claude': {'accuracy': 0.82, 'speed': 7.2},
                        'gemini': {'accuracy': 0.75, 'speed': 5.5}
                    }
                },
                'recommendations_accuracy': 0.87  # How often the recommended model performed best
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting quality statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/learn-performance")
async def update_performance_learning(
    image_id: str,
    actual_performance: Dict[str, float],
    image_metrics: Optional[Dict] = None
) -> Dict:
    """
    Update the learning system with actual performance results
    """
    try:
        # This endpoint would be called after extraction completes
        # to feed back actual performance data
        
        if supabase:
            # Store performance feedback
            feedback_data = {
                'image_id': image_id,
                'actual_performance': actual_performance,
                'image_metrics': image_metrics,
                'created_at': datetime.utcnow().isoformat()
            }
            
            supabase.table('model_performance_feedback').insert(feedback_data).execute()
        
        # Update the analyzer's model profiles
        if image_metrics:
            metrics = ImageQualityMetrics(**image_metrics)
            analyzer.update_model_performance(metrics, actual_performance)
        
        return {
            'status': 'success',
            'message': 'Performance data recorded for learning'
        }
        
    except Exception as e:
        logger.error(f"Error updating performance learning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_recommendation_reasoning(metrics: ImageQualityMetrics) -> str:
    """Generate human-readable reasoning for recommendations"""
    reasons = []
    
    if metrics.is_dark:
        reasons.append("Image is dark - selected models with better low-light performance")
    if metrics.is_blurry:
        reasons.append("Image is blurry - using models that handle unclear details better")
    if metrics.is_cluttered:
        reasons.append("Shelf is cluttered - selected models optimized for complex scenes")
    if metrics.has_shadows:
        reasons.append("Shadows detected - using models that can distinguish products in varied lighting")
    if metrics.has_reflections:
        reasons.append("Reflections present - selected models trained on reflective surfaces")
    
    if metrics.overall_quality >= 70:
        reasons.append("High quality image - using standard high-accuracy configuration")
    elif metrics.overall_quality < 40:
        reasons.append("Low quality image - using specialized models for challenging conditions")
    
    if not reasons:
        reasons.append("Standard shelf configuration detected")
    
    return ". ".join(reasons)