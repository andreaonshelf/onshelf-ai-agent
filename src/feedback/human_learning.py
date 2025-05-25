"""
Human Feedback Learning System
Critical component: Learn from human corrections to improve future extractions
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..utils import logger


class CorrectionPattern(BaseModel):
    """Pattern identified from human corrections"""
    error_type: str = Field(description="Type of error being corrected")
    context: Dict[str, Any] = Field(description="Context where error occurred")
    improvement_needed: str = Field(description="What improvement is needed")
    frequency: int = Field(description="How often this pattern occurs")
    severity: str = Field(description="low/medium/high")


class PromptPerformance(BaseModel):
    """Performance tracking for prompt versions"""
    prompt_version: str
    prompt_type: str  # structure, position, quantity, detail
    accuracy_score: float
    usage_count: int = 0
    human_correction_rate: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PromptTemplate(BaseModel):
    """Evolving prompt template"""
    template_id: str
    prompt_type: str
    prompt_version: str
    prompt_content: str
    performance_score: float = 0.0
    is_active: bool = False
    created_from_feedback: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HumanFeedbackLearningSystem:
    """Critical component: Learn from human corrections to improve future extractions"""
    
    def __init__(self, config=None):
        # Initialize Supabase client for database persistence
        if config and config.supabase_url and config.supabase_service_key:
            try:
                from supabase import create_client
                self.supabase_client = create_client(config.supabase_url, config.supabase_service_key)
                self.use_database = True
                logger.info("Supabase client initialized for human learning", component="human_learning")
            except ImportError:
                logger.warning("Supabase not available - install with: pip install supabase", component="human_learning")
                self.use_database = False
                self.supabase_client = None
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}", component="human_learning")
                self.use_database = False
                self.supabase_client = None
        else:
            self.use_database = False
            self.supabase_client = None
        
        # Fallback to in-memory storage if database not available
        if not self.use_database:
            self.corrections_db = []
            self.prompt_performance_db = []
            self.prompt_templates_db = []
        
        self.prompt_optimizer = PromptOptimizer()
        
        # Initialize default prompts
        self._initialize_default_prompts()
        
        logger.info(
            "Human Feedback Learning System initialized",
            component="human_learning"
        )
    
    def _initialize_default_prompts(self):
        """Initialize default prompt templates"""
        
        default_prompts = {
            'structure_analysis': """
            Analyze this retail shelf image and identify the physical structure:
            
            1. Count horizontal shelf levels from bottom (1) to top
            2. Identify pixel boundaries for each shelf (y_start, y_end)
            3. Note any special fixtures or dividers
            
            Focus on structural elements:
            - Shelf edges and rails
            - Horizontal divisions
            - Vertical spacing patterns
            
            Return structured data with confidence scores.
            """,
            
            'position_analysis': """
            Analyze product positions on this shelf image:
            
            1. Identify distinct products visible
            2. Assign left-to-right positions (1, 2, 3, 4...)
            3. Provide product name and brand for each position
            4. Include bounding box coordinates
            
            CRITICAL RULES:
            - Only analyze products you can clearly see
            - Assign positions strictly left-to-right
            - If unsure about a product, mark confidence < 0.8
            - Focus on spatial accuracy over product details
            """,
            
            'quantity_analysis': """
            Analyze product quantities and facings:
            
            1. Count individual product units side by side (facings)
            2. Don't confuse stacked products with facings
            3. Look for product edges to determine boundaries
            4. Verify consistent product width for facing calculation
            """,
            
            'detail_analysis': """
            Extract detailed product information:
            
            1. Read product names and variants carefully
            2. Extract prices from tags, labels, or promotional materials
            3. Identify package sizes and variants
            4. Note any promotional offers or special pricing
            """
        }
        
        for prompt_type, content in default_prompts.items():
            template = PromptTemplate(
                template_id=f"default_{prompt_type}",
                prompt_type=prompt_type,
                prompt_version="1.0",
                prompt_content=content,
                performance_score=0.8,  # Default baseline
                is_active=True,
                created_from_feedback=False
            )
            self.prompt_templates_db.append(template)
    
    async def process_human_correction(self, upload_id: str, human_corrections: List[Dict]):
        """Process human feedback and update system accordingly"""
        
        logger.info(
            f"Processing human corrections for upload {upload_id}",
            component="human_learning",
            upload_id=upload_id,
            correction_count=len(human_corrections)
        )
        
        # 1. Store human corrections
        await self._store_corrections(upload_id, human_corrections)
        
        # 2. Analyze patterns in corrections
        error_patterns = await self._analyze_correction_patterns(human_corrections)
        
        # 3. Update prompts based on patterns
        for pattern in error_patterns:
            await self._update_prompts_for_pattern(pattern)
        
        # 4. Update performance tracking
        await self._update_performance_tracking(upload_id, human_corrections)
        
        logger.info(
            f"Human feedback processed: {len(error_patterns)} patterns identified",
            component="human_learning",
            patterns_found=len(error_patterns)
        )
    
    async def _store_corrections(self, upload_id: str, corrections: List[Dict]):
        """Store human corrections for analysis"""
        
        for correction in corrections:
            correction_record = {
                'upload_id': upload_id,
                'correction_type': correction.get('type', 'unknown'),
                'original_ai_result': correction.get('original', {}),
                'human_correction': correction.get('corrected', {}),
                'correction_context': correction.get('context', {}),
                'created_at': datetime.utcnow().isoformat()
            }
            
            if self.use_database and self.supabase_client:
                try:
                    # Store in Supabase
                    result = self.supabase_client.table('human_corrections').insert(correction_record).execute()
                    logger.info(f"Stored correction in database: {result.data[0]['id']}", component="human_learning")
                except Exception as e:
                    logger.error(f"Failed to store correction in database: {e}", component="human_learning")
                    # Fallback to in-memory storage
                    correction_record['correction_id'] = f"corr_{len(self.corrections_db)}"
                    self.corrections_db.append(correction_record)
            else:
                # In-memory storage
                correction_record['correction_id'] = f"corr_{len(self.corrections_db)}"
                self.corrections_db.append(correction_record)
    
    async def _analyze_correction_patterns(self, corrections: List[Dict]) -> List[CorrectionPattern]:
        """Identify what types of errors humans are correcting"""
        
        patterns = []
        error_counts = {}
        
        for correction in corrections:
            correction_type = correction.get('type', 'unknown')
            
            # Count error types
            error_counts[correction_type] = error_counts.get(correction_type, 0) + 1
            
            if correction_type == 'missed_product':
                patterns.append(CorrectionPattern(
                    error_type='missed_small_product',
                    context=correction.get('context', {}),
                    improvement_needed='enhance_small_product_detection',
                    frequency=1,
                    severity='medium'
                ))
            
            elif correction_type == 'wrong_position':
                patterns.append(CorrectionPattern(
                    error_type='spatial_positioning_error',
                    context=correction.get('context', {}),
                    improvement_needed='improve_spatial_prompts',
                    frequency=1,
                    severity='high'
                ))
            
            elif correction_type == 'wrong_price':
                patterns.append(CorrectionPattern(
                    error_type='price_extraction_error',
                    context=correction.get('context', {}),
                    improvement_needed='enhance_ocr_prompts',
                    frequency=1,
                    severity='medium'
                ))
            
            elif correction_type == 'wrong_quantity':
                patterns.append(CorrectionPattern(
                    error_type='facing_count_error',
                    context=correction.get('context', {}),
                    improvement_needed='improve_quantity_detection',
                    frequency=1,
                    severity='medium'
                ))
        
        # Aggregate patterns by type
        aggregated_patterns = {}
        for pattern in patterns:
            key = pattern.error_type
            if key in aggregated_patterns:
                aggregated_patterns[key].frequency += 1
            else:
                aggregated_patterns[key] = pattern
        
        return list(aggregated_patterns.values())
    
    async def _update_prompts_for_pattern(self, pattern: CorrectionPattern):
        """Update prompt templates based on error patterns"""
        
        logger.info(
            f"Updating prompts for pattern: {pattern.error_type}",
            component="human_learning",
            error_type=pattern.error_type,
            frequency=pattern.frequency
        )
        
        if pattern.error_type == 'missed_small_product':
            # Update structure and position prompts to look for smaller items
            await self._enhance_prompt_for_small_products('position_analysis')
        
        elif pattern.error_type == 'spatial_positioning_error':
            # Update position prompts to be more spatially precise
            await self._enhance_prompt_for_spatial_precision('position_analysis')
        
        elif pattern.error_type == 'price_extraction_error':
            # Update detail prompts for better price extraction
            await self._enhance_prompt_for_price_extraction('detail_analysis')
        
        elif pattern.error_type == 'facing_count_error':
            # Update quantity prompts for better facing detection
            await self._enhance_prompt_for_quantity_detection('quantity_analysis')
    
    async def _enhance_prompt_for_small_products(self, prompt_type: str):
        """Enhance prompt for detecting small/partially occluded products"""
        
        current_prompt = await self.get_optimized_prompt(prompt_type)
        
        enhancement = """
        
CRITICAL: Pay special attention to small products and partially visible items.
- Look for product edges that might be cut off at image boundaries
- Check for small items between larger products
- Examine areas with shadows or partial occlusion
- Don't miss single-serve or sample-size products
- Use edge detection to identify partially hidden products
        """
        
        enhanced_prompt = current_prompt + enhancement
        await self._save_enhanced_prompt(prompt_type, enhanced_prompt, 'small_product_detection')
    
    async def _enhance_prompt_for_spatial_precision(self, prompt_type: str):
        """Enhance prompt for more precise spatial positioning"""
        
        current_prompt = await self.get_optimized_prompt(prompt_type)
        
        enhancement = """
        
SPATIAL PRECISION REQUIREMENTS:
- Count positions carefully from left to right: 1, 2, 3, 4...
- If products overlap slightly, assign to primary position
- Use bounding boxes to determine exact product boundaries
- Double-check position assignments against visible shelf dividers
- Consider product width when determining position boundaries
- Account for gaps between products in position numbering
        """
        
        enhanced_prompt = current_prompt + enhancement
        await self._save_enhanced_prompt(prompt_type, enhanced_prompt, 'spatial_precision')
    
    async def _enhance_prompt_for_price_extraction(self, prompt_type: str):
        """Enhance prompt for better price extraction"""
        
        current_prompt = await self.get_optimized_prompt(prompt_type)
        
        enhancement = """
        
PRICE EXTRACTION FOCUS:
- Look specifically for price tags, shelf tags, promotional stickers
- Use OCR enhancement for small text
- Check for promotional pricing (was/now prices)
- Verify currency symbols and decimal places
- Consider multi-buy offers (2 for £3, etc.)
- Look for electronic price displays
- Check for handwritten price labels
        """
        
        enhanced_prompt = current_prompt + enhancement
        await self._save_enhanced_prompt(prompt_type, enhanced_prompt, 'price_extraction')
    
    async def _enhance_prompt_for_quantity_detection(self, prompt_type: str):
        """Enhance prompt for better quantity/facing detection"""
        
        current_prompt = await self.get_optimized_prompt(prompt_type)
        
        enhancement = """
        
FACING COUNT FOCUS:
- Count individual product units side by side
- Look for product edges to determine boundaries
- Don't confuse stacked products with facings
- Check if products are pushed back on shelf
- Verify consistent product width for facing calculation
- Account for products at different depths
- Consider partial facings at shelf edges
        """
        
        enhanced_prompt = current_prompt + enhancement
        await self._save_enhanced_prompt(prompt_type, enhanced_prompt, 'quantity_detection')
    
    async def _save_enhanced_prompt(self, prompt_type: str, enhanced_content: str, enhancement_reason: str):
        """Save enhanced prompt as new version"""
        
        # Deactivate current prompt
        for template in self.prompt_templates_db:
            if template.prompt_type == prompt_type and template.is_active:
                template.is_active = False
        
        # Create new enhanced version
        new_version = f"{len([t for t in self.prompt_templates_db if t.prompt_type == prompt_type]) + 1}.0"
        
        enhanced_template = PromptTemplate(
            template_id=f"enhanced_{prompt_type}_{enhancement_reason}",
            prompt_type=prompt_type,
            prompt_version=new_version,
            prompt_content=enhanced_content,
            performance_score=0.0,  # Will be updated based on usage
            is_active=True,
            created_from_feedback=True
        )
        
        if self.use_database and self.supabase_client:
            try:
                # Store in Supabase
                template_data = enhanced_template.dict()
                template_data['created_at'] = datetime.utcnow().isoformat()
                result = self.supabase_client.table('prompt_templates').insert(template_data).execute()
                logger.info(f"Stored enhanced prompt in database: {result.data[0]['prompt_id']}", component="human_learning")
            except Exception as e:
                logger.error(f"Failed to store prompt template in database: {e}", component="human_learning")
                # Fallback to in-memory storage
                self.prompt_templates_db.append(enhanced_template)
        else:
            # In-memory storage
            self.prompt_templates_db.append(enhanced_template)
        
        logger.info(
            f"Enhanced prompt saved: {prompt_type} v{new_version}",
            component="human_learning",
            prompt_type=prompt_type,
            version=new_version,
            reason=enhancement_reason
        )
    
    async def _update_performance_tracking(self, upload_id: str, corrections: List[Dict]):
        """Update performance tracking for current prompts"""
        
        # Calculate correction rate for each prompt type
        prompt_types = ['structure_analysis', 'position_analysis', 'quantity_analysis', 'detail_analysis']
        
        for prompt_type in prompt_types:
            # Count corrections related to this prompt type
            related_corrections = [
                c for c in corrections 
                if self._is_correction_related_to_prompt_type(c, prompt_type)
            ]
            
            correction_rate = len(related_corrections) / len(corrections) if corrections else 0
            
            # Update performance record
            performance = PromptPerformance(
                prompt_version=await self._get_current_prompt_version(prompt_type),
                prompt_type=prompt_type,
                accuracy_score=1.0 - correction_rate,  # Simple accuracy calculation
                usage_count=1,
                human_correction_rate=correction_rate
            )
            
            self.prompt_performance_db.append(performance)
    
    def _is_correction_related_to_prompt_type(self, correction: Dict, prompt_type: str) -> bool:
        """Determine if a correction is related to a specific prompt type"""
        
        correction_type = correction.get('type', '')
        
        if prompt_type == 'structure_analysis':
            return 'structure' in correction_type or 'shelf' in correction_type
        elif prompt_type == 'position_analysis':
            return 'position' in correction_type or 'location' in correction_type
        elif prompt_type == 'quantity_analysis':
            return 'quantity' in correction_type or 'facing' in correction_type
        elif prompt_type == 'detail_analysis':
            return 'price' in correction_type or 'name' in correction_type or 'detail' in correction_type
        
        return False
    
    async def _get_current_prompt_version(self, prompt_type: str) -> str:
        """Get current active prompt version"""
        
        for template in self.prompt_templates_db:
            if template.prompt_type == prompt_type and template.is_active:
                return template.prompt_version
        
        return "1.0"  # Default
    
    async def get_optimized_prompt(self, prompt_type: str, model_type: str = 'universal', context: Dict = None) -> str:
        """Get the best performing prompt for model and context"""
        
        if self.use_database and self.supabase_client:
            try:
                # Use database function to get best prompt
                context_array = []
                if context:
                    if 'retailer' in context:
                        context_array.append(context['retailer'])
                    if 'category' in context:
                        context_array.append(context['category'])
                
                # Call the database function
                result = self.supabase_client.rpc('get_best_prompt', {
                    'p_prompt_type': prompt_type,
                    'p_model_type': model_type,
                    'p_context': context_array if context_array else None
                }).execute()
                
                if result.data and len(result.data) > 0:
                    prompt_content = result.data[0]['prompt_content']
                    
                    # Apply model-specific adjustments
                    return self._apply_model_adjustments(prompt_content, model_type)
                
            except Exception as e:
                logger.error(f"Failed to get optimized prompt from database: {e}", component="human_learning")
        
        # Fallback to in-memory or default prompts
        return await self._get_fallback_prompt(prompt_type, model_type)
    
    def _apply_model_adjustments(self, prompt_content: str, model_type: str) -> str:
        """Apply model-specific prompt adjustments"""
        
        if model_type == 'claude':
            # Claude prefers step-by-step reasoning
            return f"Think step-by-step:\n\n{prompt_content}\n\nProvide your analysis in a structured, logical manner."
        
        elif model_type == 'gpt4o':
            # GPT-4 responds well to role-playing
            return f"You are an expert retail analyst with years of experience in shelf analysis.\n\n{prompt_content}\n\nUse your expertise to provide accurate, detailed analysis."
        
        elif model_type == 'gemini':
            # Gemini likes structured output
            return f"{prompt_content}\n\nProvide structured JSON output with clear field names and confidence scores."
        
        return prompt_content
    
    async def _get_fallback_prompt(self, prompt_type: str, model_type: str) -> str:
        """Get fallback prompt from in-memory templates or defaults"""
        
        # Try in-memory templates first
        if hasattr(self, 'prompt_templates_db'):
            for template in self.prompt_templates_db:
                if template.prompt_type == prompt_type and template.is_active:
                    return self._apply_model_adjustments(template.prompt_content, model_type)
        
        # Ultimate fallback to default prompts
        default_prompts = {
            'structure_analysis': """
            Analyze this retail shelf image and identify the physical structure:
            
            1. Count horizontal shelf levels from bottom (1) to top
            2. Identify pixel boundaries for each shelf (y_start, y_end)
            3. Note any special fixtures or dividers
            
            Focus on structural elements:
            - Shelf edges and rails
            - Horizontal divisions
            - Vertical spacing patterns
            
            Return structured data with confidence scores.
            """,
            
            'position_analysis': """
            Analyze product positions on this shelf image:
            
            1. Identify distinct products visible
            2. Assign left-to-right positions (1, 2, 3, 4...)
            3. Provide product name and brand for each position
            4. Include bounding box coordinates
            
            CRITICAL RULES:
            - Only analyze products you can clearly see
            - Assign positions strictly left-to-right
            - If unsure about a product, mark confidence < 0.8
            - Focus on spatial accuracy over product details
            """,
            
            'quantity_analysis': """
            Analyze product quantities and facings:
            
            1. Count individual product units side by side (facings)
            2. Don't confuse stacked products with facings
            3. Look for product edges to determine boundaries
            4. Verify consistent product width for facing calculation
            """,
            
            'detail_analysis': """
            Extract detailed product information:
            
            1. Read product names and variants carefully
            2. Extract prices from tags, labels, or promotional materials
            3. Identify package sizes and variants
            4. Note any promotional offers or special pricing
            """
        }
        
        base_prompt = default_prompts.get(prompt_type, f"Analyze the image for {prompt_type}")
        return self._apply_model_adjustments(base_prompt, model_type)
    
    async def prepare_for_validation(self, upload_id: str, extraction_result: Any):
        """Prepare extraction result for human validation"""
        
        logger.info(
            f"Preparing extraction result for human validation: {upload_id}",
            component="human_learning",
            upload_id=upload_id
        )
        
        # This would typically store the result in a database for human review
        # For now, we'll just log it
        
        validation_data = {
            'upload_id': upload_id,
            'extraction_result': extraction_result,
            'prepared_at': datetime.utcnow(),
            'status': 'pending_human_review'
        }
        
        # In production, store in Supabase for human review interface
        logger.info(
            f"Extraction result prepared for validation",
            component="human_learning",
            upload_id=upload_id
        )
    
    async def get_learning_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get statistics on learning from human feedback"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_corrections = [
            c for c in self.corrections_db 
            if c['created_at'] >= cutoff_date
        ]
        
        # Calculate statistics
        total_corrections = len(recent_corrections)
        correction_types = {}
        
        for correction in recent_corrections:
            correction_type = correction['correction_type']
            correction_types[correction_type] = correction_types.get(correction_type, 0) + 1
        
        # Calculate improvement trends
        prompt_improvements = len([
            t for t in self.prompt_templates_db 
            if t.created_from_feedback and t.created_at >= cutoff_date
        ])
        
        return {
            'period_days': days,
            'total_corrections': total_corrections,
            'correction_types': correction_types,
            'prompt_improvements': prompt_improvements,
            'active_prompts': len([t for t in self.prompt_templates_db if t.is_active]),
            'learning_rate': prompt_improvements / max(total_corrections, 1),
            'most_common_errors': sorted(correction_types.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    async def _save_manual_prompt(self, prompt_type: str, model_type: str, prompt_content: str, 
                                 prompt_version: str, description: str):
        """Save manually edited prompt and activate it"""
        
        # Deactivate current prompts of this type and model
        if self.use_database and self.supabase_client:
            try:
                # Deactivate existing prompts
                self.supabase_client.table('prompt_templates').update({
                    'is_active': False
                }).eq('prompt_type', prompt_type).eq('model_type', model_type).execute()
                
                # Create new manual prompt
                new_prompt = {
                    'template_id': f"manual_{prompt_type}_{model_type}_{prompt_version}",
                    'prompt_type': prompt_type,
                    'model_type': model_type,
                    'prompt_version': prompt_version,
                    'prompt_content': prompt_content,
                    'performance_score': 0.0,
                    'usage_count': 0,
                    'correction_rate': 0.0,
                    'is_active': True,
                    'created_from_feedback': False,  # Manual edit, not from feedback
                    'retailer_context': [],
                    'category_context': [],
                    'created_at': datetime.utcnow().isoformat()
                }
                
                result = self.supabase_client.table('prompt_templates').insert(new_prompt).execute()
                logger.info(f"Manual prompt saved to database: {result.data[0]['prompt_id']}", component="human_learning")
                
            except Exception as e:
                logger.error(f"Failed to save manual prompt to database: {e}", component="human_learning")
                # Fallback to in-memory
                await self._save_manual_prompt_memory(prompt_type, model_type, prompt_content, prompt_version, description)
        else:
            # In-memory storage
            await self._save_manual_prompt_memory(prompt_type, model_type, prompt_content, prompt_version, description)
    
    async def _save_manual_prompt_memory(self, prompt_type: str, model_type: str, prompt_content: str, 
                                        prompt_version: str, description: str):
        """Save manual prompt to in-memory storage"""
        
        # Deactivate existing prompts
        for template in self.prompt_templates_db:
            if template.prompt_type == prompt_type and template.model_type == model_type:
                template.is_active = False
        
        # Create new manual prompt
        manual_template = PromptTemplate(
            template_id=f"manual_{prompt_type}_{model_type}_{prompt_version}",
            prompt_type=prompt_type,
            prompt_version=prompt_version,
            prompt_content=prompt_content,
            performance_score=0.0,
            is_active=True,
            created_from_feedback=False
        )
        
        self.prompt_templates_db.append(manual_template)
        logger.info(f"Manual prompt saved to memory: {manual_template.template_id}", component="human_learning")
    
    async def _get_prompt_versions(self, prompt_type: str, model_type: Optional[str] = None) -> List[Dict]:
        """Get all versions of a prompt type with performance data"""
        
        versions = []
        
        if self.use_database and self.supabase_client:
            try:
                query = self.supabase_client.table('prompt_templates').select('*').eq('prompt_type', prompt_type)
                
                if model_type:
                    query = query.eq('model_type', model_type)
                
                result = query.order('created_at', desc=True).execute()
                
                for template in result.data:
                    versions.append({
                        'prompt_id': template['prompt_id'],
                        'template_id': template['template_id'],
                        'prompt_type': template['prompt_type'],
                        'model_type': template['model_type'],
                        'prompt_version': template['prompt_version'],
                        'prompt_content': template['prompt_content'][:200] + '...' if len(template['prompt_content']) > 200 else template['prompt_content'],
                        'full_content': template['prompt_content'],
                        'performance_score': float(template['performance_score']) if template['performance_score'] else 0.0,
                        'usage_count': template['usage_count'],
                        'correction_rate': float(template['correction_rate']) if template['correction_rate'] else 0.0,
                        'is_active': template['is_active'],
                        'created_from_feedback': template['created_from_feedback'],
                        'created_at': template['created_at']
                    })
                
            except Exception as e:
                logger.error(f"Failed to get prompt versions from database: {e}", component="human_learning")
                # Fallback to in-memory
                versions = self._get_prompt_versions_memory(prompt_type, model_type)
        else:
            # In-memory storage
            versions = self._get_prompt_versions_memory(prompt_type, model_type)
        
        return versions
    
    def _get_prompt_versions_memory(self, prompt_type: str, model_type: Optional[str] = None) -> List[Dict]:
        """Get prompt versions from in-memory storage"""
        
        versions = []
        
        for template in self.prompt_templates_db:
            if template.prompt_type == prompt_type:
                if model_type is None or template.model_type == model_type:
                    versions.append({
                        'prompt_id': template.template_id,
                        'template_id': template.template_id,
                        'prompt_type': template.prompt_type,
                        'model_type': getattr(template, 'model_type', 'universal'),
                        'prompt_version': template.prompt_version,
                        'prompt_content': template.prompt_content[:200] + '...' if len(template.prompt_content) > 200 else template.prompt_content,
                        'full_content': template.prompt_content,
                        'performance_score': template.performance_score,
                        'usage_count': getattr(template, 'usage_count', 0),
                        'correction_rate': getattr(template, 'correction_rate', 0.0),
                        'is_active': template.is_active,
                        'created_from_feedback': template.created_from_feedback,
                        'created_at': template.created_at.isoformat() if hasattr(template.created_at, 'isoformat') else str(template.created_at)
                    })
        
        # Sort by creation date, newest first
        versions.sort(key=lambda x: x['created_at'], reverse=True)
        return versions
    
    async def _activate_prompt_version(self, prompt_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Activate a specific prompt version"""
        
        if self.use_database and self.supabase_client:
            try:
                # Get the prompt to activate
                prompt_result = self.supabase_client.table('prompt_templates').select('*').eq('prompt_id', prompt_id).execute()
                
                if not prompt_result.data:
                    return {'success': False, 'error': 'Prompt not found'}
                
                prompt_data = prompt_result.data[0]
                
                # Deactivate all prompts of the same type and model
                self.supabase_client.table('prompt_templates').update({
                    'is_active': False
                }).eq('prompt_type', prompt_data['prompt_type']).eq('model_type', prompt_data['model_type']).execute()
                
                # Activate the selected prompt
                self.supabase_client.table('prompt_templates').update({
                    'is_active': True
                }).eq('prompt_id', prompt_id).execute()
                
                return {
                    'success': True,
                    'prompt_type': prompt_data['prompt_type'],
                    'model_type': prompt_data['model_type'],
                    'prompt_version': prompt_data['prompt_version']
                }
                
            except Exception as e:
                logger.error(f"Failed to activate prompt in database: {e}", component="human_learning")
                return {'success': False, 'error': str(e)}
        else:
            # In-memory activation
            return self._activate_prompt_version_memory(prompt_id, reason)
    
    def _activate_prompt_version_memory(self, prompt_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Activate prompt version in memory"""
        
        target_template = None
        
        # Find the template to activate
        for template in self.prompt_templates_db:
            if template.template_id == prompt_id:
                target_template = template
                break
        
        if not target_template:
            return {'success': False, 'error': 'Prompt not found'}
        
        # Deactivate all prompts of the same type and model
        for template in self.prompt_templates_db:
            if (template.prompt_type == target_template.prompt_type and 
                getattr(template, 'model_type', 'universal') == getattr(target_template, 'model_type', 'universal')):
                template.is_active = False
        
        # Activate the target template
        target_template.is_active = True
        
        return {
            'success': True,
            'prompt_type': target_template.prompt_type,
            'model_type': getattr(target_template, 'model_type', 'universal'),
            'prompt_version': target_template.prompt_version
        }
    
    async def _generate_prompt_suggestions(self, prompt_type: str, model_type: str, based_on: str) -> List[Dict]:
        """Generate AI-powered suggestions for prompt improvements"""
        
        suggestions = []
        
        if based_on == "performance":
            # Get current performance data
            current_performance = await self._get_current_performance(prompt_type, model_type)
            
            if current_performance['accuracy'] < 0.8:
                suggestions.append({
                    'type': 'accuracy_improvement',
                    'suggestion': 'Add more specific examples and step-by-step instructions',
                    'priority': 'high',
                    'expected_improvement': '10-15% accuracy increase'
                })
            
            if current_performance['processing_time'] > 3000:
                suggestions.append({
                    'type': 'efficiency_improvement',
                    'suggestion': 'Simplify prompt structure and reduce unnecessary instructions',
                    'priority': 'medium',
                    'expected_improvement': '20-30% faster processing'
                })
        
        elif based_on == "errors":
            # Get common error patterns
            error_patterns = await self._get_error_patterns(prompt_type)
            
            for pattern in error_patterns:
                if pattern['type'] == 'missed_product':
                    suggestions.append({
                        'type': 'detection_improvement',
                        'suggestion': 'Add instructions to look for partially visible or small products',
                        'priority': 'high',
                        'addresses_error': pattern['type']
                    })
                elif pattern['type'] == 'wrong_position':
                    suggestions.append({
                        'type': 'spatial_improvement',
                        'suggestion': 'Include more detailed spatial positioning instructions',
                        'priority': 'high',
                        'addresses_error': pattern['type']
                    })
        
        elif based_on == "feedback":
            # Get recent human feedback
            feedback_patterns = await self._get_feedback_patterns(prompt_type)
            
            for pattern in feedback_patterns:
                suggestions.append({
                    'type': 'feedback_based',
                    'suggestion': f"Based on human feedback: {pattern['suggestion']}",
                    'priority': pattern['priority'],
                    'feedback_frequency': pattern['frequency']
                })
        
        # Add model-specific suggestions
        if model_type == 'claude':
            suggestions.append({
                'type': 'model_optimization',
                'suggestion': 'Add step-by-step reasoning prompts - Claude responds well to structured thinking',
                'priority': 'medium',
                'model_specific': True
            })
        elif model_type == 'gpt4o':
            suggestions.append({
                'type': 'model_optimization',
                'suggestion': 'Use role-playing prompts - GPT-4 performs better with expert personas',
                'priority': 'medium',
                'model_specific': True
            })
        elif model_type == 'gemini':
            suggestions.append({
                'type': 'model_optimization',
                'suggestion': 'Request structured JSON output - Gemini excels with clear output formats',
                'priority': 'medium',
                'model_specific': True
            })
        
        return suggestions
    
    async def _get_current_performance(self, prompt_type: str, model_type: str) -> Dict[str, Any]:
        """Get current performance metrics for a prompt type and model"""
        
        # Mock implementation - in production, would query actual performance data
        return {
            'accuracy': 0.85,
            'processing_time': 2500,
            'confidence': 0.82,
            'usage_count': 45,
            'correction_rate': 0.12
        }
    
    async def _get_error_patterns(self, prompt_type: str) -> List[Dict]:
        """Get common error patterns for a prompt type"""
        
        # Mock implementation - in production, would analyze actual error data
        return [
            {'type': 'missed_product', 'frequency': 15, 'severity': 'high'},
            {'type': 'wrong_position', 'frequency': 8, 'severity': 'medium'},
            {'type': 'wrong_price', 'frequency': 5, 'severity': 'low'}
        ]
    
    async def _get_feedback_patterns(self, prompt_type: str) -> List[Dict]:
        """Get patterns from human feedback"""
        
        # Mock implementation - in production, would analyze actual feedback
        return [
            {
                'suggestion': 'Add more context about product boundaries',
                'priority': 'high',
                'frequency': 12
            },
            {
                'suggestion': 'Include examples of edge cases',
                'priority': 'medium',
                'frequency': 8
            }
        ]


class PromptOptimizer:
    """Optimizes prompts based on human feedback patterns"""
    
    def __init__(self):
        logger.info(
            "Prompt Optimizer initialized",
            component="prompt_optimizer"
        )
    
    def enhance_for_small_products(self, current_prompt: str) -> str:
        """Add instructions for detecting small/partially occluded products"""
        
        enhancement = """
        
CRITICAL: Pay special attention to small products and partially visible items.
- Look for product edges that might be cut off at image boundaries
- Check for small items between larger products
- Examine areas with shadows or partial occlusion
- Don't miss single-serve or sample-size products
        """
        
        return current_prompt + enhancement
    
    def enhance_spatial_precision(self, current_prompt: str) -> str:
        """Add more precise spatial positioning instructions"""
        
        enhancement = """
        
SPATIAL PRECISION REQUIREMENTS:
- Count positions carefully from left to right: 1, 2, 3, 4...
- If products overlap slightly, assign to primary position
- Use bounding boxes to determine exact product boundaries
- Double-check position assignments against visible shelf dividers
        """
        
        return current_prompt + enhancement
    
    def enhance_price_extraction(self, current_prompt: str) -> str:
        """Add better price extraction instructions"""
        
        enhancement = """
        
PRICE EXTRACTION FOCUS:
- Look specifically for price tags, shelf tags, promotional stickers
- Use OCR enhancement for small text
- Check for promotional pricing (was/now prices)
- Verify currency symbols and decimal places
- Consider multi-buy offers (2 for £3, etc.)
        """
        
        return current_prompt + enhancement
    
    def enhance_quantity_detection(self, current_prompt: str) -> str:
        """Add better quantity/facing detection instructions"""
        
        enhancement = """
        
FACING COUNT FOCUS:
- Count individual product units side by side
- Look for product edges to determine boundaries
- Don't confuse stacked products with facings
- Check if products are pushed back on shelf
- Verify consistent product width for facing calculation
        """
        
        return current_prompt + enhancement 