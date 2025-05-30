"""
Image Quality Analyzer for Model Selection
Analyzes image characteristics to recommend optimal extraction system and models
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional, List
from PIL import Image
import io
import base64
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ImageQualityMetrics:
    """Metrics for image quality assessment"""
    brightness: float  # 0-100
    contrast: float   # 0-100
    sharpness: float  # 0-100
    noise_level: float  # 0-100 (higher = more noise)
    color_saturation: float  # 0-100
    edge_density: float  # 0-100 (higher = more cluttered)
    occlusion_score: float  # 0-100 (higher = more occlusions)
    overall_quality: float  # 0-100
    
    # Specific issues
    is_dark: bool
    is_blurry: bool
    is_cluttered: bool
    is_overexposed: bool
    has_reflections: bool
    has_shadows: bool
    
    # Recommendations
    recommended_system: str
    recommended_models: Dict[str, str]
    confidence: float

class ImageQualityAnalyzer:
    """Analyzes image quality and recommends optimal extraction settings"""
    
    def __init__(self):
        self.quality_thresholds = {
            'brightness': {'low': 30, 'high': 80},
            'contrast': {'low': 20, 'high': 90},
            'sharpness': {'low': 30, 'high': 100},
            'noise': {'acceptable': 40},
            'edge_density': {'cluttered': 70}
        }
        
        # Model performance profiles based on historical data
        self.model_profiles = {
            'gpt4o': {
                'strengths': ['high_quality', 'clear', 'well_lit'],
                'weaknesses': ['very_dark', 'extremely_blurry'],
                'cost': 'high',
                'accuracy': 'highest'
            },
            'claude': {
                'strengths': ['complex_scenes', 'cluttered', 'shadows'],
                'weaknesses': ['low_contrast'],
                'cost': 'medium',
                'accuracy': 'high'
            },
            'gemini': {
                'strengths': ['dark_images', 'reflections', 'varied_lighting'],
                'weaknesses': ['extremely_cluttered'],
                'cost': 'low',
                'accuracy': 'good'
            }
        }
        
        # System selection rules
        self.system_rules = {
            'custom_consensus': {
                'conditions': ['high_quality', 'standard_shelf'],
                'min_quality': 60
            },
            'langgraph': {
                'conditions': ['complex_layout', 'multiple_issues'],
                'min_quality': 40
            },
            'hybrid': {
                'conditions': ['variable_quality', 'mixed_conditions'],
                'min_quality': 30
            }
        }
    
    def analyze_image(self, image_data: bytes) -> ImageQualityMetrics:
        """Analyze image quality and provide recommendations"""
        try:
            # Convert image data to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Calculate quality metrics
            brightness = self._calculate_brightness(img)
            contrast = self._calculate_contrast(img)
            sharpness = self._calculate_sharpness(img)
            noise_level = self._calculate_noise_level(img)
            color_saturation = self._calculate_saturation(img)
            edge_density = self._calculate_edge_density(img)
            occlusion_score = self._detect_occlusions(img)
            
            # Detect specific issues
            is_dark = brightness < self.quality_thresholds['brightness']['low']
            is_blurry = sharpness < self.quality_thresholds['sharpness']['low']
            is_cluttered = edge_density > self.quality_thresholds['edge_density']['cluttered']
            is_overexposed = brightness > self.quality_thresholds['brightness']['high']
            has_reflections = self._detect_reflections(img)
            has_shadows = self._detect_shadows(img)
            
            # Calculate overall quality score
            overall_quality = self._calculate_overall_quality(
                brightness, contrast, sharpness, noise_level,
                color_saturation, edge_density, occlusion_score
            )
            
            # Get recommendations
            recommended_system, recommended_models, confidence = self._get_recommendations(
                overall_quality, is_dark, is_blurry, is_cluttered,
                is_overexposed, has_reflections, has_shadows
            )
            
            return ImageQualityMetrics(
                brightness=brightness,
                contrast=contrast,
                sharpness=sharpness,
                noise_level=noise_level,
                color_saturation=color_saturation,
                edge_density=edge_density,
                occlusion_score=occlusion_score,
                overall_quality=overall_quality,
                is_dark=is_dark,
                is_blurry=is_blurry,
                is_cluttered=is_cluttered,
                is_overexposed=is_overexposed,
                has_reflections=has_reflections,
                has_shadows=has_shadows,
                recommended_system=recommended_system,
                recommended_models=recommended_models,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error analyzing image quality: {e}")
            # Return default recommendations on error
            return self._get_default_metrics()
    
    def _calculate_brightness(self, img: np.ndarray) -> float:
        """Calculate average brightness (0-100)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray) / 255 * 100)
    
    def _calculate_contrast(self, img: np.ndarray) -> float:
        """Calculate contrast using standard deviation (0-100)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return float(np.std(gray) / 255 * 100)
    
    def _calculate_sharpness(self, img: np.ndarray) -> float:
        """Calculate sharpness using Laplacian variance (0-100)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        # Normalize to 0-100 scale (empirically determined)
        return min(100, float(variance / 50))
    
    def _calculate_noise_level(self, img: np.ndarray) -> float:
        """Estimate noise level (0-100)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Calculate noise using difference between original and denoised
        denoised = cv2.fastNlMeansDenoising(gray)
        noise = np.abs(gray.astype(float) - denoised.astype(float))
        return float(np.mean(noise) / 255 * 100)
    
    def _calculate_saturation(self, img: np.ndarray) -> float:
        """Calculate color saturation (0-100)"""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        return float(np.mean(saturation) / 255 * 100)
    
    def _calculate_edge_density(self, img: np.ndarray) -> float:
        """Calculate edge density to detect clutter (0-100)"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_pixels = np.sum(edges > 0)
        total_pixels = edges.shape[0] * edges.shape[1]
        return float(edge_pixels / total_pixels * 100)
    
    def _detect_occlusions(self, img: np.ndarray) -> float:
        """Detect potential occlusions (0-100)"""
        # Simple heuristic: look for large dark regions
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        dark_pixels = np.sum(thresh == 0)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        return float(dark_pixels / total_pixels * 100)
    
    def _detect_reflections(self, img: np.ndarray) -> bool:
        """Detect potential reflections"""
        # Look for high-intensity spots
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, bright = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        bright_pixels = np.sum(bright > 0)
        total_pixels = bright.shape[0] * bright.shape[1]
        return (bright_pixels / total_pixels) > 0.05  # More than 5% very bright
    
    def _detect_shadows(self, img: np.ndarray) -> bool:
        """Detect significant shadows"""
        # Look for large dark regions with gradients
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((5, 5)))
        dark_gradient = np.logical_and(gray < 100, gradient > 20)
        return np.sum(dark_gradient) > (img.shape[0] * img.shape[1] * 0.1)
    
    def _calculate_overall_quality(self, brightness: float, contrast: float,
                                 sharpness: float, noise_level: float,
                                 saturation: float, edge_density: float,
                                 occlusion_score: float) -> float:
        """Calculate overall quality score (0-100)"""
        # Weight different factors
        weights = {
            'brightness': 0.15,
            'contrast': 0.20,
            'sharpness': 0.25,
            'noise': 0.15,
            'saturation': 0.10,
            'clutter': 0.10,
            'occlusion': 0.05
        }
        
        # Normalize scores (some need inversion)
        scores = {
            'brightness': self._normalize_brightness(brightness),
            'contrast': contrast,
            'sharpness': sharpness,
            'noise': 100 - noise_level,  # Invert: less noise is better
            'saturation': saturation,
            'clutter': 100 - min(100, edge_density),  # Invert: less clutter is better
            'occlusion': 100 - occlusion_score  # Invert: less occlusion is better
        }
        
        # Calculate weighted average
        total = sum(scores[key] * weights[key] for key in scores)
        return total
    
    def _normalize_brightness(self, brightness: float) -> float:
        """Normalize brightness to quality score"""
        # Optimal brightness is around 50-70
        if 40 <= brightness <= 70:
            return 100
        elif brightness < 40:
            return brightness * 2.5  # Scale up
        else:
            return 100 - (brightness - 70) * 1.5  # Penalize overexposure
    
    def _get_recommendations(self, overall_quality: float, is_dark: bool,
                           is_blurry: bool, is_cluttered: bool,
                           is_overexposed: bool, has_reflections: bool,
                           has_shadows: bool) -> Tuple[str, Dict[str, str], float]:
        """Get system and model recommendations based on image characteristics"""
        
        # Determine image conditions
        conditions = []
        if overall_quality >= 70:
            conditions.append('high_quality')
        if is_dark:
            conditions.append('dark')
        if is_blurry:
            conditions.append('blurry')
        if is_cluttered:
            conditions.append('cluttered')
        if is_overexposed:
            conditions.append('overexposed')
        if has_reflections:
            conditions.append('reflections')
        if has_shadows:
            conditions.append('shadows')
        
        # Complex conditions
        if len(conditions) >= 3:
            conditions.append('multiple_issues')
        if is_cluttered and (is_dark or has_shadows):
            conditions.append('complex_layout')
        
        # Select system
        recommended_system = 'custom_consensus'  # Default
        if 'multiple_issues' in conditions and overall_quality < 50:
            recommended_system = 'langgraph'
        elif 'complex_layout' in conditions:
            recommended_system = 'hybrid'
        
        # Select models based on conditions
        recommended_models = {
            'structure': self._select_model_for_conditions(conditions, 'structure'),
            'products': self._select_model_for_conditions(conditions, 'products'),
            'details': self._select_model_for_conditions(conditions, 'details')
        }
        
        # Calculate confidence
        confidence = min(100, overall_quality + 20) / 100
        
        return recommended_system, recommended_models, confidence
    
    def _select_model_for_conditions(self, conditions: List[str], 
                                   extraction_type: str) -> str:
        """Select best model for given conditions and extraction type"""
        
        # Score each model
        scores = {}
        for model, profile in self.model_profiles.items():
            score = 0
            
            # Check strengths
            for strength in profile['strengths']:
                if strength in conditions or self._matches_condition(strength, conditions):
                    score += 2
            
            # Check weaknesses
            for weakness in profile['weaknesses']:
                if weakness in conditions or self._matches_condition(weakness, conditions):
                    score -= 3
            
            # Adjust for extraction type
            if extraction_type == 'details' and model == 'gpt4o':
                score += 1  # GPT-4 excels at details
            elif extraction_type == 'structure' and model == 'claude':
                score += 1  # Claude good at understanding layout
            
            scores[model] = score
        
        # Return model with highest score
        return max(scores, key=scores.get)
    
    def _matches_condition(self, profile_condition: str, 
                          actual_conditions: List[str]) -> bool:
        """Check if profile condition matches actual conditions"""
        condition_map = {
            'high_quality': lambda c: 'high_quality' in c,
            'well_lit': lambda c: not any(x in c for x in ['dark', 'shadows']),
            'very_dark': lambda c: 'dark' in c,
            'extremely_blurry': lambda c: 'blurry' in c,
            'complex_scenes': lambda c: 'complex_layout' in c or 'cluttered' in c,
            'dark_images': lambda c: 'dark' in c or 'shadows' in c,
            'varied_lighting': lambda c: 'shadows' in c or 'reflections' in c,
            'extremely_cluttered': lambda c: 'cluttered' in c
        }
        
        if profile_condition in condition_map:
            return condition_map[profile_condition](actual_conditions)
        return False
    
    def _get_default_metrics(self) -> ImageQualityMetrics:
        """Return default metrics when analysis fails"""
        return ImageQualityMetrics(
            brightness=50.0,
            contrast=50.0,
            sharpness=50.0,
            noise_level=30.0,
            color_saturation=50.0,
            edge_density=50.0,
            occlusion_score=20.0,
            overall_quality=50.0,
            is_dark=False,
            is_blurry=False,
            is_cluttered=False,
            is_overexposed=False,
            has_reflections=False,
            has_shadows=False,
            recommended_system='custom_consensus',
            recommended_models={
                'structure': 'claude',
                'products': 'gpt4o',
                'details': 'gpt4o'
            },
            confidence=0.5
        )
    
    def update_model_performance(self, image_metrics: ImageQualityMetrics,
                               actual_performance: Dict[str, float]):
        """Update model performance profiles based on actual results"""
        # This would update a database with performance metrics
        # to improve recommendations over time
        logger.info(f"Updating model performance data: {actual_performance}")
        # TODO: Implement learning system