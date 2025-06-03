"""
Adaptive Prompt System - Handles initial vs retry prompts
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PromptSection:
    initial: str
    retry: str


class AdaptivePromptBuilder:
    """Builds appropriate prompts based on extraction context"""
    
    def __init__(self):
        self.section_delimiter = "=== RETRY EXTRACTION"
        self.initial_delimiter = "=== INITIAL EXTRACTION ==="
        
    def parse_unified_prompt(self, unified_prompt: str) -> PromptSection:
        """Parse a unified prompt into initial and retry sections"""
        # Split by retry delimiter
        parts = unified_prompt.split(self.section_delimiter)
        
        if len(parts) == 1:
            # No retry section, entire prompt is initial
            return PromptSection(
                initial=unified_prompt.strip(),
                retry=""
            )
        
        # Extract initial section
        initial_part = parts[0]
        if self.initial_delimiter in initial_part:
            initial_part = initial_part.split(self.initial_delimiter)[1]
        
        # Extract retry section
        retry_part = parts[1] if len(parts) > 1 else ""
        
        return PromptSection(
            initial=initial_part.strip(),
            retry=retry_part.strip()
        )
    
    def build_adaptive_prompt(self, 
                            unified_prompt: str,
                            context: Dict,
                            attempt_number: int = 1,
                            confidence_threshold: float = 0.8) -> str:
        """Build appropriate prompt based on context"""
        
        sections = self.parse_unified_prompt(unified_prompt)
        
        # First attempt always uses initial
        if attempt_number == 1:
            return self._fill_template(sections.initial, context)
        
        # Check if we should use retry
        should_retry = self._should_use_retry(context, confidence_threshold)
        
        if should_retry and sections.retry:
            # Use retry section with context
            retry_context = self._build_retry_context(context)
            filled_retry = self._fill_template(sections.retry, retry_context)
            
            # Include successful extractions from initial for continuity
            if context.get('high_confidence_products'):
                filled_retry = f"KEEPING HIGH CONFIDENCE RESULTS:\n{context['high_confidence_products']}\n\n{filled_retry}"
                
            return filled_retry
        else:
            # Use initial prompt even on retry (confidence too low or too high)
            return self._fill_template(sections.initial, context)
    
    def _should_use_retry(self, context: Dict, threshold: float) -> bool:
        """Determine if retry prompt should be used"""
        confidence = context.get('overall_confidence', 0)
        coverage = context.get('coverage', 0)
        
        # Use retry if confidence is in the "improvable" range
        if 0.6 < confidence < threshold and coverage > 0.5:
            return True
            
        # Don't retry if too poor (start fresh) or too good (no need)
        return False
    
    def _build_retry_context(self, context: Dict) -> Dict:
        """Build specific context for retry attempts"""
        retry_context = context.copy()
        
        # Add specific problem identification
        if 'previous_extraction' in context:
            prev = context['previous_extraction']
            
            # Identify confirmed vs problematic items
            retry_context['high_confidence_products'] = self._format_high_confidence(prev)
            retry_context['low_confidence_positions'] = self._format_low_confidence(prev)
            retry_context['confidence_issues'] = self._identify_issues(prev)
            
            # Add specific focus areas
            retry_context['problem_area_1'] = self._get_primary_problem_area(prev)
            retry_context['specific_issue_1'] = self._get_specific_issue(prev)
            
        return retry_context
    
    def _fill_template(self, template: str, context: Dict) -> str:
        """Fill template variables with context"""
        filled = template
        
        # Replace all {variable} patterns
        for key, value in context.items():
            pattern = f"{{{key}}}"
            if pattern in filled:
                filled = filled.replace(pattern, str(value))
        
        # Remove any unfilled variables
        filled = re.sub(r'\{[^}]+\}', '', filled)
        
        return filled.strip()
    
    def _format_high_confidence(self, extraction) -> str:
        """Format high confidence products for retry prompt"""
        high_conf = []
        for product in extraction.get('products', []):
            if product.get('confidence', 0) > 0.85:
                high_conf.append(f"- Pos {product['position']}: {product['brand']} {product['name']}")
        
        return '\n'.join(high_conf[:10])  # Limit to prevent prompt overflow
    
    def _format_low_confidence(self, extraction) -> str:
        """Format low confidence areas for focus"""
        low_conf = []
        for product in extraction.get('products', []):
            if product.get('confidence', 0) < 0.75:
                low_conf.append(f"- Position {product['position']}: {product.get('issue', 'uncertain')}")
        
        return '\n'.join(low_conf[:5])
    
    def _identify_issues(self, extraction) -> str:
        """Identify main issues from previous extraction"""
        issues = []
        
        if extraction.get('overall_confidence', 0) < 0.8:
            issues.append("Low overall confidence")
            
        if extraction.get('missing_sections'):
            issues.append(f"Missing products in {extraction['missing_sections']}")
            
        if extraction.get('validation_flags'):
            issues.append(f"Validation issues: {', '.join(extraction['validation_flags'][:3])}")
            
        return '; '.join(issues)
    
    def _get_primary_problem_area(self, extraction) -> str:
        """Identify primary area needing attention"""
        # Analyze extraction to find worst performing area
        if 'shelf_confidences' in extraction:
            worst_shelf = min(extraction['shelf_confidences'].items(), 
                            key=lambda x: x[1])
            return f"shelf {worst_shelf[0]}"
        
        if 'section_confidences' in extraction:
            worst_section = min(extraction['section_confidences'].items(), 
                              key=lambda x: x[1])
            return f"{worst_section[0]} section"
            
        return "areas with promotional obstructions"
    
    def _get_specific_issue(self, extraction) -> str:
        """Get most specific issue to address"""
        if extraction.get('common_errors'):
            return extraction['common_errors'][0]
            
        if extraction.get('uncertainty_reasons'):
            return extraction['uncertainty_reasons'][0]
            
        return "Products may be partially obscured"