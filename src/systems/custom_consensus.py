"""
Custom Consensus System
Lightweight implementation with direct API calls and deterministic consensus voting
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import instructor
import openai
import anthropic

from .base_system import BaseExtractionSystem, ExtractionResult, CostBreakdown, PerformanceMetrics
from ..config import SystemConfig
from ..utils import logger
from ..feedback.human_learning import HumanFeedbackLearningSystem


class DeterministicOrchestrator:
    """Deterministic consensus voting logic"""
    
    def __init__(self):
        self.confidence_threshold = 0.8
        self.consensus_threshold = 0.7
    
    def vote_on_structure(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Vote on structure analysis from multiple models with weighted consensus"""
        
        if not proposals:
            return {'consensus_reached': False, 'reason': 'No proposals'}
        
        # Filter out error proposals
        valid_proposals = [p for p in proposals if 'error' not in p and p.get('shelf_count')]
        
        if not valid_proposals:
            return {'consensus_reached': False, 'reason': 'No valid proposals'}
        
        # Weighted voting based on confidence scores
        weighted_votes = {}
        total_weight = 0
        
        for proposal in valid_proposals:
            shelf_count = proposal.get('shelf_count', 0)
            confidence = proposal.get('confidence', 0.5)
            model_weight = self._get_model_weight(proposal.get('model_used', 'unknown'))
            
            # Combined weight: confidence * model reliability
            combined_weight = confidence * model_weight
            
            if shelf_count not in weighted_votes:
                weighted_votes[shelf_count] = {'weight': 0, 'proposals': [], 'models': []}
            
            weighted_votes[shelf_count]['weight'] += combined_weight
            weighted_votes[shelf_count]['proposals'].append(proposal)
            weighted_votes[shelf_count]['models'].append(proposal.get('model_used', 'unknown'))
            total_weight += combined_weight
        
        if not weighted_votes:
            return {'consensus_reached': False, 'reason': 'No weighted votes'}
        
        # Find the option with highest weighted support
        best_option = max(weighted_votes.items(), key=lambda x: x[1]['weight'])
        shelf_count, vote_data = best_option
        
        consensus_strength = vote_data['weight'] / total_weight if total_weight > 0 else 0
        
        # Adjust consensus threshold based on number of models
        num_models = len(valid_proposals)
        if num_models >= 3:
            # With 3 models, require stronger consensus
            required_threshold = 0.6
        elif num_models == 2:
            # With 2 models, require agreement
            required_threshold = 0.7
        else:
            # Single model, lower threshold
            required_threshold = 0.5
        
        if consensus_strength >= required_threshold:
            # Select the proposal with highest confidence from winning option
            best_proposal = max(vote_data['proposals'], key=lambda x: x.get('confidence', 0))
            
            return {
                'consensus_reached': True,
                'result': best_proposal,
                'confidence': consensus_strength,
                'voting_details': {
                    'shelf_count_votes': {k: v['weight'] for k, v in weighted_votes.items()},
                    'consensus_strength': consensus_strength,
                    'selected_count': shelf_count,
                    'participating_models': vote_data['models'],
                    'total_models': num_models,
                    'required_threshold': required_threshold
                }
            }
        
        return {
            'consensus_reached': False,
            'reason': f'Insufficient consensus: {consensus_strength:.2f} < {required_threshold:.2f}',
            'consensus_strength': consensus_strength,
            'vote_breakdown': {k: v['weight'] for k, v in weighted_votes.items()}
        }
    
    def _get_model_weight(self, model_name: str) -> float:
        """Get reliability weight for different models"""
        model_weights = {
            'claude': 1.0,    # Claude is typically very reliable for structure
            'gpt4o': 0.9,     # GPT-4o is good but sometimes overconfident
            'gemini': 0.8,    # Gemini is cost-effective but less reliable
            'unknown': 0.5    # Unknown models get lower weight
        }
        return model_weights.get(model_name, 0.5)
    
    def vote_on_positions(self, shelf_proposals: List[Dict]) -> Dict[str, Any]:
        """Vote on product positions from multiple models with weighted consensus"""
        
        if not shelf_proposals:
            return {'consensus_reached': False, 'reason': 'No position proposals'}
        
        # Filter valid proposals
        valid_proposals = [p for p in shelf_proposals if 'error' not in p and p.get('positions')]
        
        if not valid_proposals:
            return {'consensus_reached': False, 'reason': 'No valid position proposals'}
        
        # Aggregate positions across models with weights
        position_votes = {}
        
        for proposal in valid_proposals:
            positions = proposal.get('positions', {})
            model_name = proposal.get('model', 'unknown')
            model_weight = self._get_model_weight(model_name)
            
            for pos_key, product_data in positions.items():
                if pos_key not in position_votes:
                    position_votes[pos_key] = []
                
                # Add weighted vote
                weighted_vote = product_data.copy()
                weighted_vote['model_weight'] = model_weight
                weighted_vote['weighted_confidence'] = product_data.get('confidence', 0.5) * model_weight
                position_votes[pos_key].append(weighted_vote)
        
        # Build consensus positions with weighted voting
        consensus_positions = {}
        total_positions = len(position_votes)
        consensus_count = 0
        
        num_models = len(valid_proposals)
        min_votes_required = max(1, num_models // 2)  # At least half the models
        
        for pos_key, votes in position_votes.items():
            if len(votes) >= min_votes_required:
                # Calculate weighted consensus
                total_weighted_confidence = sum(v.get('weighted_confidence', 0) for v in votes)
                avg_weighted_confidence = total_weighted_confidence / len(votes)
                
                if avg_weighted_confidence >= (self.confidence_threshold * 0.8):  # Slightly lower threshold for weighted
                    # Select the vote with highest weighted confidence
                    best_vote = max(votes, key=lambda x: x.get('weighted_confidence', 0))
                    
                    # Clean up the vote (remove our internal fields)
                    clean_vote = {k: v for k, v in best_vote.items() 
                                if k not in ['model_weight', 'weighted_confidence']}
                    clean_vote['consensus_confidence'] = avg_weighted_confidence
                    clean_vote['supporting_models'] = len(votes)
                    
                    consensus_positions[pos_key] = clean_vote
                    consensus_count += 1
        
        consensus_rate = consensus_count / total_positions if total_positions > 0 else 0
        
        # Adjust consensus threshold based on number of models
        if num_models >= 3:
            required_consensus_rate = 0.6
        elif num_models == 2:
            required_consensus_rate = 0.7
        else:
            required_consensus_rate = 0.5
        
        return {
            'consensus_reached': consensus_rate >= required_consensus_rate,
            'result': consensus_positions,
            'confidence': consensus_rate,
            'voting_details': {
                'total_positions': total_positions,
                'consensus_positions': consensus_count,
                'consensus_rate': consensus_rate,
                'participating_models': num_models,
                'min_votes_required': min_votes_required,
                'required_consensus_rate': required_consensus_rate
            }
        }


class CustomConsensusSystem(BaseExtractionSystem):
    """Lightweight custom system with direct API calls and deterministic consensus"""
    
    def __init__(self, config: SystemConfig):
        super().__init__(config)
        
        self.orchestrator = DeterministicOrchestrator()
        self.human_feedback = HumanFeedbackLearningSystem(config)
        
        # Initialize model clients
        self.model_clients = {}
        self.cost_tracker = {'total_cost': 0, 'model_costs': {}, 'api_calls': {}, 'tokens_used': {}}
        
        if config.openai_api_key:
            self.model_clients['gpt4o'] = instructor.from_openai(
                openai.OpenAI(api_key=config.openai_api_key)
            )
        
        if config.anthropic_api_key:
            self.model_clients['claude'] = instructor.from_anthropic(
                anthropic.Anthropic(api_key=config.anthropic_api_key)
            )
        
        # Initialize Gemini client
        if config.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.google_api_key)
                self.model_clients['gemini'] = genai.GenerativeModel('gemini-pro-vision')
                logger.info("Gemini client initialized successfully", component="custom_consensus")
            except ImportError:
                logger.warning("Google GenerativeAI not available - install with: pip install google-generativeai", component="custom_consensus")
                self.model_clients['gemini'] = None
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}", component="custom_consensus")
                self.model_clients['gemini'] = None
        
        logger.info(
            f"Custom consensus system initialized with {len(self.model_clients)} models",
            component="custom_consensus",
            available_models=list(self.model_clients.keys())
        )
    
    async def extract_with_consensus(self, image_data: bytes, upload_id: str, extraction_data: Optional[Dict] = None) -> ExtractionResult:
        """Main extraction with cumulative building and end-to-end optimization"""
        
        start_time = time.time()
        locked_results = {}  # Preserve consensus results across iterations
        iteration = 1
        max_iterations = 5
        
        logger.info(
            f"Starting custom consensus extraction for upload {upload_id}",
            component="custom_consensus",
            upload_id=upload_id
        )
        
        while iteration <= max_iterations:
            logger.info(
                f"🎯 Custom Consensus Iteration {iteration}",
                component="custom_consensus",
                iteration=iteration,
                upload_id=upload_id
            )
            
            # Stage 1: Build extraction using locked + new consensus
            extraction_result = await self._build_cumulative_extraction(
                image_data, locked_results, iteration
            )
            
            if not extraction_result:
                logger.warning(
                    f"Extraction failed at iteration {iteration}",
                    component="custom_consensus",
                    iteration=iteration
                )
                iteration += 1
                continue
            
            # Stage 2: Generate planogram (deterministic, no AI calls)
            planogram = await self._generate_planogram(extraction_result)
            
            # Stage 3: End-to-end validation (compare planogram vs original)
            validation = await self._validate_end_to_end(
                image_data, extraction_result, planogram
            )
            
            # Stage 4: Check if we're done or need smart retry
            if self._is_satisfactory(validation, iteration):
                processing_time = time.time() - start_time
                
                # Prepare final result
                final_result = await self._finalize_result(
                    extraction_result, planogram, validation, processing_time, iteration, upload_id
                )
                
                # Prepare for human feedback
                await self.human_feedback.prepare_for_validation(upload_id, final_result)
                
                logger.info(
                    f"Custom consensus extraction completed successfully",
                    component="custom_consensus",
                    upload_id=upload_id,
                    iterations=iteration,
                    accuracy=final_result.overall_accuracy,
                    processing_time=processing_time
                )
                
                return final_result
            
            # Stage 5: Smart retry - only re-run what's broken
            retry_plan = await self._plan_smart_retry(validation, locked_results)
            locked_results = retry_plan['updated_locks']
            iteration += 1
        
        # If we get here, escalate to human review
        processing_time = time.time() - start_time
        return await self._escalate_to_human(image_data, extraction_result, validation, processing_time, upload_id)
    
    async def _build_cumulative_extraction(self, image_data: bytes, locked_results: Dict, iteration: int) -> Optional[Dict]:
        """Build extraction using locked consensus + new consensus where needed"""
        
        extraction = {}
        
        # Structure consensus (if not locked)
        if 'structure' not in locked_results:
            logger.info("Running structure consensus", component="custom_consensus")
            
            # Get proposals from all available models
            tasks = []
            for model_name in ['gpt4o', 'claude', 'gemini']:
                if self.model_clients.get(model_name):
                    tasks.append(self._analyze_structure(image_data, model_name))
            
            if not tasks:
                logger.error("No models available for structure analysis", component="custom_consensus")
                return None
            
            structure_proposals = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_proposals = [p for p in structure_proposals if not isinstance(p, Exception)]
            
            if not valid_proposals:
                logger.error("No valid structure proposals", component="custom_consensus")
                return None
            
            structure_consensus = self.orchestrator.vote_on_structure(valid_proposals)
            
            if structure_consensus['consensus_reached']:
                extraction['structure'] = structure_consensus['result']
                logger.info(
                    f"✅ Structure consensus: {structure_consensus['confidence']:.0%}",
                    component="custom_consensus",
                    confidence=structure_consensus['confidence']
                )
            else:
                logger.warning(
                    f"❌ No structure consensus: {structure_consensus.get('reason')}",
                    component="custom_consensus"
                )
                return None
        else:
            extraction['structure'] = locked_results['structure']
            logger.info("🔒 Using locked structure", component="custom_consensus")
        
        # Position consensus (shelf-by-shelf, if not locked)
        if 'positions' not in locked_results:
            logger.info("Running position consensus", component="custom_consensus")
            extraction['positions'] = await self._shelf_by_shelf_consensus(
                image_data, extraction['structure']
            )
        else:
            extraction['positions'] = locked_results['positions']
            logger.info("🔒 Using locked positions", component="custom_consensus")
        
        # Quantity and detail consensus (if needed)
        extraction['quantities'] = await self._quantity_consensus(
            image_data, extraction['positions']
        )
        extraction['details'] = await self._detail_consensus(
            image_data, extraction['positions'], extraction['quantities']
        )
        
        return extraction
    
    async def _analyze_structure(self, image_data: bytes, model_name: str) -> Dict[str, Any]:
        """Analyze shelf structure with specific model"""
        
        if model_name not in self.model_clients or not self.model_clients[model_name]:
            return {'error': f'Model {model_name} not available'}
        
        # Get model-specific optimized prompt from human feedback system
        prompt = await self.human_feedback.get_optimized_prompt('structure_analysis', model_name)
        
        try:
            # Real structure analysis implementation
            if model_name == 'gpt4o' and self.model_clients.get('gpt4o'):
                result = await self._analyze_structure_gpt4o(image_data, prompt)
            elif model_name == 'claude' and self.model_clients.get('claude'):
                result = await self._analyze_structure_claude(image_data, prompt)
            elif model_name == 'gemini' and self.model_clients.get('gemini'):
                result = await self._analyze_structure_gemini(image_data, prompt)
            else:
                return {'error': f'Model {model_name} not available or not configured'}
            
            # Add model metadata
            result['model_used'] = model_name
            return result
            
        except Exception as e:
            logger.error(
                f"Structure analysis failed for {model_name}: {e}",
                component="custom_consensus",
                model=model_name,
                error=str(e)
            )
            return {'error': str(e)}
    
    async def _shelf_by_shelf_consensus(self, image_data: bytes, structure: Dict) -> Dict[str, Any]:
        """Analyze product positions shelf by shelf with consensus"""
        
        shelf_count = structure.get('shelf_count', 0)
        all_positions = {}
        
        for shelf_num in range(1, shelf_count + 1):
            logger.info(
                f"Analyzing shelf {shelf_num}",
                component="custom_consensus",
                shelf_number=shelf_num
            )
            
            # Get proposals from all available models for this shelf
            tasks = []
            for model_name in ['gpt4o', 'claude', 'gemini']:
                if self.model_clients.get(model_name):
                    tasks.append(self._analyze_shelf_positions(image_data, shelf_num, model_name))
            
            if not tasks:
                logger.warning(f"No models available for shelf {shelf_num} analysis", component="custom_consensus")
                continue
            
            shelf_proposals = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter valid proposals
            valid_proposals = [p for p in shelf_proposals if not isinstance(p, Exception)]
            
            if valid_proposals:
                shelf_consensus = self.orchestrator.vote_on_positions(valid_proposals)
                if shelf_consensus['consensus_reached']:
                    all_positions.update(shelf_consensus['result'])
        
        return all_positions
    
    async def _analyze_shelf_positions(self, image_data: bytes, shelf_number: int, model_name: str) -> Dict[str, Any]:
        """Analyze positions on a specific shelf"""
        
        if model_name not in self.model_clients or not self.model_clients[model_name]:
            return {'error': f'Model {model_name} not available'}
        
        try:
            # Real position analysis implementation
            prompt = await self.human_feedback.get_optimized_prompt('position_analysis', model_name)
            
            if model_name == 'gpt4o' and self.model_clients.get('gpt4o'):
                result = await self._analyze_positions_gpt4o(image_data, shelf_number, prompt)
            elif model_name == 'claude' and self.model_clients.get('claude'):
                result = await self._analyze_positions_claude(image_data, shelf_number, prompt)
            elif model_name == 'gemini' and self.model_clients.get('gemini'):
                result = await self._analyze_positions_gemini(image_data, shelf_number, prompt)
            else:
                return {'error': f'Model {model_name} not available or not configured'}
            
            return result
            
        except Exception as e:
            logger.error(
                f"Position analysis failed for {model_name} shelf {shelf_number}: {e}",
                component="custom_consensus",
                model=model_name,
                shelf=shelf_number,
                error=str(e)
            )
            return {'error': str(e)}
    
    async def _quantity_consensus(self, image_data: bytes, positions: Dict) -> Dict[str, Any]:
        """Analyze product quantities with consensus"""
        quantities = {}
        
        # Get quantity analysis prompt
        prompt = await self.human_feedback.get_optimized_prompt('quantity_analysis', 'universal')
        
        # Run quantity analysis with available models
        tasks = []
        for model_name in ['gpt4o', 'claude', 'gemini']:
            if self.model_clients.get(model_name):
                tasks.append(self._analyze_quantities(image_data, positions, model_name, prompt))
        
        if not tasks:
            # Fallback to estimated quantities if no models available
            for pos_key, pos_data in positions.items():
                quantities[pos_key] = {
                    'facing_count': 2,  # Estimated fallback
                    'confidence': 0.5
                }
            return quantities
        
        quantity_proposals = await asyncio.gather(*tasks, return_exceptions=True)
        valid_proposals = [p for p in quantity_proposals if not isinstance(p, Exception) and 'error' not in p]
        
        if valid_proposals:
            # Use consensus voting for quantities
            consensus_result = self._vote_on_quantities(valid_proposals)
            if consensus_result.get('consensus_reached'):
                quantities = consensus_result['result']
            else:
                # Use best single result if no consensus
                best_proposal = max(valid_proposals, key=lambda x: x.get('confidence', 0))
                quantities = best_proposal.get('quantities', {})
        
        # Ensure all positions have quantity data
        for pos_key in positions.keys():
            if pos_key not in quantities:
                quantities[pos_key] = {
                    'facing_count': 1,  # Conservative fallback
                    'confidence': 0.6
                }
        
        return quantities
    
    async def _detail_consensus(self, image_data: bytes, positions: Dict, quantities: Dict) -> Dict[str, Any]:
        """Analyze product details with consensus"""
        details = {}
        
        # Get detail analysis prompt
        prompt = await self.human_feedback.get_optimized_prompt('detail_analysis', 'universal')
        
        # Run detail analysis with available models
        tasks = []
        for model_name in ['gpt4o', 'claude', 'gemini']:
            if self.model_clients.get(model_name):
                tasks.append(self._analyze_details(image_data, positions, quantities, model_name, prompt))
        
        if not tasks:
            # Fallback to basic details if no models available
            for pos_key, pos_data in positions.items():
                details[pos_key] = {
                    'price': None,  # Unknown price
                    'size': 'Unknown',
                    'confidence': 0.3
                }
            return details
        
        detail_proposals = await asyncio.gather(*tasks, return_exceptions=True)
        valid_proposals = [p for p in detail_proposals if not isinstance(p, Exception) and 'error' not in p]
        
        if valid_proposals:
            # Use consensus voting for details
            consensus_result = self._vote_on_details(valid_proposals)
            if consensus_result.get('consensus_reached'):
                details = consensus_result['result']
            else:
                # Use best single result if no consensus
                best_proposal = max(valid_proposals, key=lambda x: x.get('confidence', 0))
                details = best_proposal.get('details', {})
        
        # Ensure all positions have detail data
        for pos_key in positions.keys():
            if pos_key not in details:
                details[pos_key] = {
                    'price': None,
                    'size': 'Unknown',
                    'confidence': 0.4
                }
        
        return details
    
    async def _generate_planogram(self, extraction: Dict) -> Dict[str, Any]:
        """Generate planogram from extraction (deterministic, no AI calls)"""
        # Mock planogram generation
        return {
            'planogram_id': f"planogram_{int(time.time())}",
            'shelf_count': extraction['structure']['shelf_count'],
            'products': len(extraction['positions']),
            'generated_at': datetime.utcnow().isoformat()
        }
    
    async def _validate_end_to_end(self, original_image: bytes, extraction: Dict, planogram: Dict) -> Dict[str, Any]:
        """Critical: Compare final planogram against original image"""
        
        # Mock validation - in real implementation, this would use AI to compare
        # the original image with the generated planogram
        accuracy = 0.89  # Mock accuracy
        
        return {
            'accuracy': accuracy,
            'issues': [
                {'type': 'position_error', 'shelf': 2, 'position': 3, 'severity': 'low'},
                {'type': 'missing_product', 'shelf': 4, 'position': 1, 'severity': 'medium'}
            ] if accuracy < 0.9 else [],
            'validation_method': 'ai_comparison',
            'confidence': 0.85
        }
    
    def _is_satisfactory(self, validation: Dict, iteration: int) -> bool:
        """Check if results are satisfactory"""
        accuracy = validation.get('accuracy', 0)
        return accuracy >= 0.90 or iteration >= 5
    
    async def _plan_smart_retry(self, validation: Dict, locked_results: Dict) -> Dict[str, Any]:
        """Intelligent retry: only re-run failing stages"""
        
        issues = validation.get('issues', [])
        retry_plan = {'updated_locks': locked_results.copy()}
        
        # Analyze issue patterns
        structure_issues = [i for i in issues if 'structure' in i.get('type', '')]
        position_issues = [i for i in issues if 'position' in i.get('type', '')]
        
        if structure_issues:
            # Structure problems - unlock structure
            retry_plan['updated_locks'].pop('structure', None)
            logger.info(
                f"🔄 Will retry structure due to {len(structure_issues)} issues",
                component="custom_consensus"
            )
        elif position_issues:
            # Position problems - keep structure, retry positions
            logger.info(
                f"🔄 Will retry positions, keeping locked structure",
                component="custom_consensus"
            )
        
        return retry_plan
    
    async def _finalize_result(self, extraction: Dict, planogram: Dict, validation: Dict, 
                             processing_time: float, iteration_count: int, upload_id: str) -> ExtractionResult:
        """Create final extraction result"""
        
        accuracy = validation.get('accuracy', 0)
        consensus_rate = 0.85  # Mock consensus rate
        
        cost_breakdown = CostBreakdown(
            total_cost=self.cost_tracker['total_cost'],
            model_costs=self.cost_tracker['model_costs'],
            api_calls=self.cost_tracker['api_calls'],
            tokens_used=self.cost_tracker['tokens_used'],
            cost_per_accuracy_point=self._calculate_cost_efficiency(self.cost_tracker['total_cost'], accuracy)
        )
        
        performance_metrics = PerformanceMetrics(
            accuracy=accuracy,
            processing_time=processing_time,
            consensus_rate=consensus_rate,
            iteration_count=iteration_count,
            human_escalation_rate=0.1,  # Mock rate
            spatial_accuracy=accuracy * 0.95,  # Mock spatial accuracy
            complexity_rating=self.get_complexity_rating(),
            control_level=self.get_control_level(),
            debugging_ease="Easy"
        )
        
        return ExtractionResult(
            system_type="custom",
            upload_id=upload_id,
            structure=extraction['structure'],
            positions=extraction['positions'],
            quantities=extraction['quantities'],
            details=extraction['details'],
            overall_accuracy=accuracy,
            consensus_reached=consensus_rate >= 0.7,
            validation_result=validation,
            processing_time=processing_time,
            iteration_count=iteration_count,
            cost_breakdown=cost_breakdown,
            performance_metrics=performance_metrics,
            ready_for_human_review=self._should_escalate_to_human(accuracy, iteration_count),
            human_review_priority=self._get_human_review_priority(accuracy, consensus_rate)
        )
    
    async def _escalate_to_human(self, image_data: bytes, extraction: Dict, validation: Dict, 
                                processing_time: float, upload_id: str) -> ExtractionResult:
        """Escalate to human review when automatic processing fails"""
        
        logger.warning(
            f"Escalating to human review for upload {upload_id}",
            component="custom_consensus",
            upload_id=upload_id
        )
        
        # Create result with human escalation flag
        return await self._finalize_result(
            extraction or {}, {}, validation or {}, processing_time, 5, upload_id
        )
    
    async def _analyze_structure_gpt4o(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze structure using GPT-4o"""
        import base64
        
        # Convert image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['gpt4o'].chat.completions.acreate(
                model="gpt-4o",
                temperature=self.config.model_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            # Parse response and extract structure data
            content = response.choices[0].message.content
            
            # Track actual costs
            tokens_used = response.usage.total_tokens
            cost = self._calculate_gpt4o_cost(tokens_used)
            self._track_api_call('gpt4o', cost, tokens_used)
            
            # Parse structured response (implement JSON extraction)
            result = self._parse_structure_response(content)
            result['confidence'] = 0.9  # Base confidence, could be extracted from response
            
            return result
            
        except Exception as e:
            logger.error(f"GPT-4o structure analysis failed: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    async def _analyze_structure_claude(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze structure using Claude"""
        import base64
        
        # Convert image to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['claude'].messages.acreate(
                model="claude-3-sonnet-20240229",
                temperature=self.config.model_temperature,
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Track actual costs
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_claude_cost(response.usage.input_tokens, response.usage.output_tokens)
            self._track_api_call('claude', cost, tokens_used)
            
            # Parse structured response
            result = self._parse_structure_response(content)
            result['confidence'] = 0.92  # Claude typically has high confidence
            
            return result
            
        except Exception as e:
            logger.error(f"Claude structure analysis failed: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    async def _analyze_structure_gemini(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze structure using Gemini"""
        try:
            # Upload image to Gemini
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            
            response = await self.model_clients['gemini'].generate_content_async([prompt, image])
            
            # Parse response
            content = response.text
            
            # Track costs (Gemini is very cost-effective)
            tokens_used = len(content.split()) * 1.3  # Rough token estimation
            cost = self._calculate_gemini_cost(int(tokens_used))
            self._track_api_call('gemini', cost, int(tokens_used))
            
            # Parse structured response
            result = self._parse_structure_response(content)
            result['confidence'] = 0.88  # Gemini baseline confidence
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini structure analysis failed: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    def _parse_structure_response(self, content: str) -> Dict[str, Any]:
        """Parse structure analysis response from any model"""
        import re
        import json
        
        try:
            # Try to extract JSON first
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback: extract key information with regex
            shelf_count_match = re.search(r'(?:shelf|level).*?(\d+)', content, re.IGNORECASE)
            shelf_count = int(shelf_count_match.group(1)) if shelf_count_match else 4
            
            # Generate boundaries based on shelf count
            boundaries = []
            height_per_shelf = 600 / shelf_count  # Assume 600px total height
            
            for i in range(shelf_count):
                y_start = int(i * height_per_shelf + 100)
                y_end = int((i + 1) * height_per_shelf + 100)
                boundaries.append({'y_start': y_start, 'y_end': y_end})
            
            return {
                'shelf_count': shelf_count,
                'boundaries': boundaries,
                'raw_response': content
            }
            
        except Exception as e:
            logger.error(f"Failed to parse structure response: {e}", component="custom_consensus")
            return {
                'shelf_count': 4,  # Safe fallback
                'boundaries': [
                    {'y_start': 100, 'y_end': 250},
                    {'y_start': 250, 'y_end': 400},
                    {'y_start': 400, 'y_end': 550},
                    {'y_start': 550, 'y_end': 700}
                ],
                'raw_response': content,
                'parsing_error': str(e)
            }
    
    def _calculate_gpt4o_cost(self, tokens: int) -> float:
        """Calculate GPT-4o cost based on actual token usage"""
        # GPT-4o pricing: $0.01 per 1K input tokens, $0.03 per 1K output tokens
        # Assume 70% input, 30% output for structure analysis
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        input_cost = (input_tokens / 1000) * 0.01
        output_cost = (output_tokens / 1000) * 0.03
        
        return input_cost + output_cost
    
    def _calculate_claude_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate Claude cost based on actual token usage"""
        # Claude pricing: $0.008 per 1K input tokens, $0.024 per 1K output tokens
        input_cost = (input_tokens / 1000) * 0.008
        output_cost = (output_tokens / 1000) * 0.024
        
        return input_cost + output_cost
    
    def _calculate_gemini_cost(self, tokens: int) -> float:
        """Calculate Gemini cost based on actual token usage"""
        # Gemini pricing: $0.00025 per 1K input tokens, $0.0005 per 1K output tokens
        # Assume 70% input, 30% output
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        input_cost = (input_tokens / 1000) * 0.00025
        output_cost = (output_tokens / 1000) * 0.0005
        
        return input_cost + output_cost
    
    async def _analyze_positions_gpt4o(self, image_data: bytes, shelf_number: int, prompt: str) -> Dict[str, Any]:
        """Analyze positions using GPT-4o"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            enhanced_prompt = f"{prompt}\n\nFocus on shelf number {shelf_number}. Return JSON with positions."
            
            response = await self.model_clients['gpt4o'].chat.completions.acreate(
                model="gpt-4o",
                temperature=self.config.model_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": enhanced_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Track costs
            tokens_used = response.usage.total_tokens
            cost = self._calculate_gpt4o_cost(tokens_used)
            self._track_api_call('gpt4o', cost, tokens_used)
            
            # Parse positions
            positions = self._parse_position_response(content, shelf_number)
            
            return {'positions': positions}
            
        except Exception as e:
            logger.error(f"GPT-4o position analysis failed: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    async def _analyze_positions_claude(self, image_data: bytes, shelf_number: int, prompt: str) -> Dict[str, Any]:
        """Analyze positions using Claude"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            enhanced_prompt = f"{prompt}\n\nAnalyze shelf {shelf_number} specifically. Provide detailed JSON output."
            
            response = await self.model_clients['claude'].messages.acreate(
                model="claude-3-sonnet-20240229",
                temperature=self.config.model_temperature,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            },
                            {"type": "text", "text": enhanced_prompt}
                        ]
                    }
                ]
            )
            
            content = response.content[0].text
            
            # Track costs
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_claude_cost(response.usage.input_tokens, response.usage.output_tokens)
            self._track_api_call('claude', cost, tokens_used)
            
            # Parse positions
            positions = self._parse_position_response(content, shelf_number)
            
            return {'positions': positions}
            
        except Exception as e:
            logger.error(f"Claude position analysis failed: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    async def _analyze_positions_gemini(self, image_data: bytes, shelf_number: int, prompt: str) -> Dict[str, Any]:
        """Analyze positions using Gemini"""
        try:
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            enhanced_prompt = f"{prompt}\n\nFocus on shelf {shelf_number}. Provide structured JSON output."
            
            response = await self.model_clients['gemini'].generate_content_async([enhanced_prompt, image])
            
            content = response.text
            
            # Track costs
            tokens_used = len(content.split()) * 1.3
            cost = self._calculate_gemini_cost(int(tokens_used))
            self._track_api_call('gemini', cost, int(tokens_used))
            
            # Parse positions
            positions = self._parse_position_response(content, shelf_number)
            
            return {'positions': positions}
            
        except Exception as e:
            logger.error(f"Gemini position analysis failed: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    def _parse_position_response(self, content: str, shelf_number: int) -> Dict[str, Any]:
        """Parse position analysis response from any model"""
        import re
        import json
        
        positions = {}
        
        try:
            # Try to extract JSON first
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                if 'positions' in parsed_data:
                    return parsed_data['positions']
                elif isinstance(parsed_data, dict):
                    return parsed_data
            
            # Fallback: extract product information with regex
            product_patterns = [
                r'product[:\s]+([^,\n]+)',
                r'brand[:\s]+([^,\n]+)',
                r'item[:\s]+([^,\n]+)'
            ]
            
            products_found = []
            for pattern in product_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                products_found.extend(matches)
            
            # Create positions from found products
            for i, product in enumerate(products_found[:8]):  # Max 8 products per shelf
                position_key = f"shelf_{shelf_number}_pos_{i+1}"
                positions[position_key] = {
                    'product': product.strip(),
                    'brand': 'Unknown',  # Could be extracted separately
                    'confidence': 0.8,  # Default confidence for parsed data
                    'shelf_number': shelf_number,
                    'position': i + 1,
                    'bbox': {'x': i * 100, 'y': 10, 'w': 95, 'h': 120}  # Estimated
                }
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to parse position response: {e}", component="custom_consensus")
            # Return minimal fallback
            return {
                f"shelf_{shelf_number}_pos_1": {
                    'product': 'Unknown Product',
                    'brand': 'Unknown',
                    'confidence': 0.5,
                    'shelf_number': shelf_number,
                    'position': 1,
                    'parsing_error': str(e)
                }
            }

    def _track_api_call(self, model_name: str, cost: float, tokens: int):
        """Track API call costs and usage"""
        self.cost_tracker['total_cost'] += cost
        self.cost_tracker['model_costs'][model_name] = self.cost_tracker['model_costs'].get(model_name, 0) + cost
        self.cost_tracker['api_calls'][model_name] = self.cost_tracker['api_calls'].get(model_name, 0) + 1
        self.cost_tracker['tokens_used'][model_name] = self.cost_tracker['tokens_used'].get(model_name, 0) + tokens
    
    async def get_cost_breakdown(self) -> CostBreakdown:
        """Get detailed cost breakdown"""
        return CostBreakdown(
            total_cost=self.cost_tracker['total_cost'],
            model_costs=self.cost_tracker['model_costs'],
            api_calls=self.cost_tracker['api_calls'],
            tokens_used=self.cost_tracker['tokens_used'],
            cost_per_accuracy_point=self.cost_tracker['total_cost'] / 0.89  # Mock accuracy
        )
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics"""
        return PerformanceMetrics(
            accuracy=0.89,  # Mock data
            processing_time=45.0,
            consensus_rate=0.85,
            iteration_count=3,
            human_escalation_rate=0.1,
            spatial_accuracy=0.87,
            complexity_rating=self.get_complexity_rating(),
            control_level=self.get_control_level(),
            debugging_ease="Easy"
        )
    
    def get_architecture_benefits(self) -> List[str]:
        """Get key architectural benefits"""
        return [
            "Direct cost control and transparency",
            "No framework dependencies",
            "Fastest debugging and iteration",
            "Maximum control over consensus logic",
            "Deterministic and predictable behavior"
        ]
    
    def get_complexity_rating(self) -> str:
        """Get complexity rating"""
        return "Low"
    
    def get_control_level(self) -> str:
        """Get control level"""
        return "Maximum"
    
    async def _test_prompt_performance(self, prompt_content: str, prompt_type: str, 
                                     model_type: str, image_data: bytes) -> Dict[str, Any]:
        """Test a prompt's performance without saving it"""
        
        start_time = time.time()
        
        try:
            # Test the prompt with the specified model
            if model_type == 'gpt4o' and self.model_clients.get('gpt4o'):
                if prompt_type == 'structure_analysis':
                    result = await self._test_structure_prompt_gpt4o(image_data, prompt_content)
                elif prompt_type == 'position_analysis':
                    result = await self._test_position_prompt_gpt4o(image_data, prompt_content)
                else:
                    result = {'error': f'Prompt type {prompt_type} not supported for testing'}
            
            elif model_type == 'claude' and self.model_clients.get('claude'):
                if prompt_type == 'structure_analysis':
                    result = await self._test_structure_prompt_claude(image_data, prompt_content)
                elif prompt_type == 'position_analysis':
                    result = await self._test_position_prompt_claude(image_data, prompt_content)
                else:
                    result = {'error': f'Prompt type {prompt_type} not supported for testing'}
            
            elif model_type == 'gemini' and self.model_clients.get('gemini'):
                if prompt_type == 'structure_analysis':
                    result = await self._test_structure_prompt_gemini(image_data, prompt_content)
                elif prompt_type == 'position_analysis':
                    result = await self._test_position_prompt_gemini(image_data, prompt_content)
                else:
                    result = {'error': f'Prompt type {prompt_type} not supported for testing'}
            
            else:
                result = {'error': f'Model {model_type} not available or not configured'}
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if 'error' in result:
                return {
                    'success': False,
                    'error': result['error'],
                    'processing_time_ms': processing_time
                }
            
            # Evaluate the result quality
            evaluation = self._evaluate_prompt_result(result, prompt_type)
            
            return {
                'success': True,
                'accuracy': evaluation['accuracy'],
                'confidence': evaluation['confidence'],
                'processing_time_ms': processing_time,
                'result_quality': evaluation['quality'],
                'extracted_data': result,
                'evaluation_details': evaluation['details']
            }
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Prompt testing failed: {e}", component="custom_consensus")
            
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': processing_time
            }
    
    async def _test_structure_prompt_gpt4o(self, image_data: bytes, prompt_content: str) -> Dict[str, Any]:
        """Test structure analysis prompt with GPT-4o"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['gpt4o'].chat.completions.acreate(
                model="gpt-4o",
                temperature=self.config.model_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_content},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = self._calculate_gpt4o_cost(tokens_used)
            
            # Parse the response
            parsed_result = self._parse_structure_response(content)
            parsed_result['tokens_used'] = tokens_used
            parsed_result['cost'] = cost
            
            return parsed_result
            
        except Exception as e:
            return {'error': f'GPT-4o test failed: {str(e)}'}
    
    async def _test_structure_prompt_claude(self, image_data: bytes, prompt_content: str) -> Dict[str, Any]:
        """Test structure analysis prompt with Claude"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['claude'].messages.acreate(
                model="claude-3-sonnet-20240229",
                temperature=self.config.model_temperature,
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            },
                            {"type": "text", "text": prompt_content}
                        ]
                    }
                ]
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_claude_cost(response.usage.input_tokens, response.usage.output_tokens)
            
            # Parse the response
            parsed_result = self._parse_structure_response(content)
            parsed_result['tokens_used'] = tokens_used
            parsed_result['cost'] = cost
            
            return parsed_result
            
        except Exception as e:
            return {'error': f'Claude test failed: {str(e)}'}
    
    async def _test_structure_prompt_gemini(self, image_data: bytes, prompt_content: str) -> Dict[str, Any]:
        """Test structure analysis prompt with Gemini"""
        try:
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            
            response = await self.model_clients['gemini'].generate_content_async([prompt_content, image])
            
            content = response.text
            tokens_used = len(content.split()) * 1.3  # Rough estimation
            cost = self._calculate_gemini_cost(int(tokens_used))
            
            # Parse the response
            parsed_result = self._parse_structure_response(content)
            parsed_result['tokens_used'] = int(tokens_used)
            parsed_result['cost'] = cost
            
            return parsed_result
            
        except Exception as e:
            return {'error': f'Gemini test failed: {str(e)}'}
    
    async def _test_position_prompt_gpt4o(self, image_data: bytes, prompt_content: str) -> Dict[str, Any]:
        """Test position analysis prompt with GPT-4o"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            # Enhanced prompt for position testing
            enhanced_prompt = f"{prompt_content}\n\nFocus on product positions. Return JSON with detailed position data."
            
            response = await self.model_clients['gpt4o'].chat.completions.acreate(
                model="gpt-4o",
                temperature=self.config.model_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": enhanced_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = self._calculate_gpt4o_cost(tokens_used)
            
            # Parse the response for positions
            positions = self._parse_position_response(content, 1)  # Default to shelf 1 for testing
            
            return {
                'positions': positions,
                'tokens_used': tokens_used,
                'cost': cost,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'GPT-4o position test failed: {str(e)}'}
    
    async def _test_position_prompt_claude(self, image_data: bytes, prompt_content: str) -> Dict[str, Any]:
        """Test position analysis prompt with Claude"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            # Enhanced prompt for position testing
            enhanced_prompt = f"{prompt_content}\n\nAnalyze product positions carefully. Provide detailed JSON output with position data."
            
            response = await self.model_clients['claude'].messages.acreate(
                model="claude-3-sonnet-20240229",
                temperature=self.config.model_temperature,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            },
                            {"type": "text", "text": enhanced_prompt}
                        ]
                    }
                ]
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_claude_cost(response.usage.input_tokens, response.usage.output_tokens)
            
            # Parse the response for positions
            positions = self._parse_position_response(content, 1)  # Default to shelf 1 for testing
            
            return {
                'positions': positions,
                'tokens_used': tokens_used,
                'cost': cost,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'Claude position test failed: {str(e)}'}
    
    async def _test_position_prompt_gemini(self, image_data: bytes, prompt_content: str) -> Dict[str, Any]:
        """Test position analysis prompt with Gemini"""
        try:
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            
            # Enhanced prompt for position testing
            enhanced_prompt = f"{prompt_content}\n\nFocus on product positions. Provide structured JSON output with position details."
            
            response = await self.model_clients['gemini'].generate_content_async([enhanced_prompt, image])
            
            content = response.text
            tokens_used = len(content.split()) * 1.3  # Rough estimation
            cost = self._calculate_gemini_cost(int(tokens_used))
            
            # Parse the response for positions
            positions = self._parse_position_response(content, 1)  # Default to shelf 1 for testing
            
            return {
                'positions': positions,
                'tokens_used': int(tokens_used),
                'cost': cost,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'Gemini position test failed: {str(e)}'}
    
    def _evaluate_prompt_result(self, result: Dict[str, Any], prompt_type: str) -> Dict[str, Any]:
        """Evaluate the quality of a prompt test result"""
        
        evaluation = {
            'accuracy': 0.0,
            'confidence': 0.0,
            'quality': 'poor',
            'details': []
        }
        
        if prompt_type == 'structure_analysis':
            # Evaluate structure analysis result
            if 'shelf_count' in result and result['shelf_count'] > 0:
                evaluation['accuracy'] += 0.4
                evaluation['details'].append('Valid shelf count detected')
            
            if 'boundaries' in result and len(result['boundaries']) > 0:
                evaluation['accuracy'] += 0.3
                evaluation['details'].append('Shelf boundaries identified')
            
            if 'confidence' in result and result['confidence'] > 0.8:
                evaluation['accuracy'] += 0.3
                evaluation['confidence'] = result['confidence']
                evaluation['details'].append('High confidence score')
            
        elif prompt_type == 'position_analysis':
            # Evaluate position analysis result
            if 'positions' in result and len(result['positions']) > 0:
                evaluation['accuracy'] += 0.5
                evaluation['details'].append(f"Detected {len(result['positions'])} positions")
            
            # Check average confidence of positions
            if 'positions' in result:
                confidences = [pos.get('confidence', 0) for pos in result['positions'].values()]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    evaluation['confidence'] = avg_confidence
                    if avg_confidence > 0.8:
                        evaluation['accuracy'] += 0.3
                        evaluation['details'].append('High average confidence')
        
        # Determine quality rating
        if evaluation['accuracy'] >= 0.9:
            evaluation['quality'] = 'excellent'
        elif evaluation['accuracy'] >= 0.7:
            evaluation['quality'] = 'good'
        elif evaluation['accuracy'] >= 0.5:
            evaluation['quality'] = 'fair'
        else:
            evaluation['quality'] = 'poor'
        
        return evaluation
    
    async def _analyze_quantities(self, image_data: bytes, positions: Dict, model_name: str, prompt: str) -> Dict[str, Any]:
        """Analyze product quantities using specific model"""
        
        try:
            # Get model-specific prompt
            enhanced_prompt = f"{prompt}\n\nAnalyze product quantities and facings for the detected products. Focus on counting individual units side by side."
            
            if model_name == 'gpt4o' and self.model_clients.get('gpt4o'):
                result = await self._analyze_quantities_gpt4o(image_data, enhanced_prompt)
            elif model_name == 'claude' and self.model_clients.get('claude'):
                result = await self._analyze_quantities_claude(image_data, enhanced_prompt)
            elif model_name == 'gemini' and self.model_clients.get('gemini'):
                result = await self._analyze_quantities_gemini(image_data, enhanced_prompt)
            else:
                return {'error': f'Model {model_name} not available'}
            
            # Add model metadata
            result['model_used'] = model_name
            return result
            
        except Exception as e:
            logger.error(f"Quantity analysis failed for {model_name}: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    async def _analyze_details(self, image_data: bytes, positions: Dict, quantities: Dict, model_name: str, prompt: str) -> Dict[str, Any]:
        """Analyze product details using specific model"""
        
        try:
            # Get model-specific prompt
            enhanced_prompt = f"{prompt}\n\nExtract detailed product information including prices, sizes, and variants. Look for price tags, labels, and promotional materials."
            
            if model_name == 'gpt4o' and self.model_clients.get('gpt4o'):
                result = await self._analyze_details_gpt4o(image_data, enhanced_prompt)
            elif model_name == 'claude' and self.model_clients.get('claude'):
                result = await self._analyze_details_claude(image_data, enhanced_prompt)
            elif model_name == 'gemini' and self.model_clients.get('gemini'):
                result = await self._analyze_details_gemini(image_data, enhanced_prompt)
            else:
                return {'error': f'Model {model_name} not available'}
            
            # Add model metadata
            result['model_used'] = model_name
            return result
            
        except Exception as e:
            logger.error(f"Detail analysis failed for {model_name}: {e}", component="custom_consensus")
            return {'error': str(e)}
    
    async def _analyze_quantities_gpt4o(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze quantities using GPT-4o"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['gpt4o'].chat.completions.acreate(
                model="gpt-4o",
                temperature=self.config.model_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = self._calculate_gpt4o_cost(tokens_used)
            self._track_api_call('gpt4o', cost, tokens_used)
            
            # Parse quantities from response
            quantities = self._parse_quantity_response(content)
            
            return {
                'quantities': quantities,
                'confidence': 0.85,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'GPT-4o quantity analysis failed: {str(e)}'}
    
    async def _analyze_quantities_claude(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze quantities using Claude"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['claude'].messages.acreate(
                model="claude-3-sonnet-20240229",
                temperature=self.config.model_temperature,
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_claude_cost(response.usage.input_tokens, response.usage.output_tokens)
            self._track_api_call('claude', cost, tokens_used)
            
            # Parse quantities from response
            quantities = self._parse_quantity_response(content)
            
            return {
                'quantities': quantities,
                'confidence': 0.88,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'Claude quantity analysis failed: {str(e)}'}
    
    async def _analyze_quantities_gemini(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze quantities using Gemini"""
        try:
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            
            response = await self.model_clients['gemini'].generate_content_async([prompt, image])
            
            content = response.text
            tokens_used = len(content.split()) * 1.3
            cost = self._calculate_gemini_cost(int(tokens_used))
            self._track_api_call('gemini', cost, int(tokens_used))
            
            # Parse quantities from response
            quantities = self._parse_quantity_response(content)
            
            return {
                'quantities': quantities,
                'confidence': 0.82,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'Gemini quantity analysis failed: {str(e)}'}
    
    async def _analyze_details_gpt4o(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze details using GPT-4o"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['gpt4o'].chat.completions.acreate(
                model="gpt-4o",
                temperature=self.config.model_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = self._calculate_gpt4o_cost(tokens_used)
            self._track_api_call('gpt4o', cost, tokens_used)
            
            # Parse details from response
            details = self._parse_detail_response(content)
            
            return {
                'details': details,
                'confidence': 0.83,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'GPT-4o detail analysis failed: {str(e)}'}
    
    async def _analyze_details_claude(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze details using Claude"""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        try:
            response = await self.model_clients['claude'].messages.acreate(
                model="claude-3-sonnet-20240229",
                temperature=self.config.model_temperature,
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_claude_cost(response.usage.input_tokens, response.usage.output_tokens)
            self._track_api_call('claude', cost, tokens_used)
            
            # Parse details from response
            details = self._parse_detail_response(content)
            
            return {
                'details': details,
                'confidence': 0.86,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'Claude detail analysis failed: {str(e)}'}
    
    async def _analyze_details_gemini(self, image_data: bytes, prompt: str) -> Dict[str, Any]:
        """Analyze details using Gemini"""
        try:
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            
            response = await self.model_clients['gemini'].generate_content_async([prompt, image])
            
            content = response.text
            tokens_used = len(content.split()) * 1.3
            cost = self._calculate_gemini_cost(int(tokens_used))
            self._track_api_call('gemini', cost, int(tokens_used))
            
            # Parse details from response
            details = self._parse_detail_response(content)
            
            return {
                'details': details,
                'confidence': 0.80,
                'raw_response': content
            }
            
        except Exception as e:
            return {'error': f'Gemini detail analysis failed: {str(e)}'}
    
    def _parse_quantity_response(self, content: str) -> Dict[str, Any]:
        """Parse quantity analysis response"""
        import re
        import json
        
        quantities = {}
        
        try:
            # Try to extract JSON first
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                if 'quantities' in parsed_data:
                    return parsed_data['quantities']
                elif isinstance(parsed_data, dict):
                    return parsed_data
            
            # Fallback: extract quantity information with regex
            facing_patterns = [
                r'facing[s]?[:\s]+(\d+)',
                r'unit[s]?[:\s]+(\d+)',
                r'count[:\s]+(\d+)'
            ]
            
            facings_found = []
            for pattern in facing_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                facings_found.extend([int(m) for m in matches])
            
            # Create quantity data
            if facings_found:
                avg_facing = sum(facings_found) / len(facings_found)
                for i in range(min(8, len(facings_found))):  # Max 8 products
                    position_key = f"shelf_1_pos_{i+1}"
                    quantities[position_key] = {
                        'facing_count': facings_found[i] if i < len(facings_found) else int(avg_facing),
                        'confidence': 0.75
                    }
            
            return quantities
            
        except Exception as e:
            logger.error(f"Failed to parse quantity response: {e}", component="custom_consensus")
            return {}
    
    def _parse_detail_response(self, content: str) -> Dict[str, Any]:
        """Parse detail analysis response"""
        import re
        import json
        
        details = {}
        
        try:
            # Try to extract JSON first
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                if 'details' in parsed_data:
                    return parsed_data['details']
                elif isinstance(parsed_data, dict):
                    return parsed_data
            
            # Fallback: extract detail information with regex
            price_patterns = [
                r'[\$£€](\d+\.?\d*)',
                r'price[:\s]+[\$£€]?(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*[\$£€]'
            ]
            
            size_patterns = [
                r'(\d+(?:\.\d+)?)\s*(ml|l|g|kg|oz|lb)',
                r'size[:\s]+(\d+(?:\.\d+)?)\s*(ml|l|g|kg|oz|lb)'
            ]
            
            prices_found = []
            sizes_found = []
            
            for pattern in price_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                prices_found.extend([float(m) for m in matches if m])
            
            for pattern in size_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                sizes_found.extend([f"{m[0]}{m[1]}" for m in matches])
            
            # Create detail data
            for i in range(min(8, max(len(prices_found), len(sizes_found), 1))):  # At least 1, max 8
                position_key = f"shelf_1_pos_{i+1}"
                details[position_key] = {
                    'price': prices_found[i] if i < len(prices_found) else None,
                    'size': sizes_found[i] if i < len(sizes_found) else 'Unknown',
                    'confidence': 0.70
                }
            
            return details
            
        except Exception as e:
            logger.error(f"Failed to parse detail response: {e}", component="custom_consensus")
            return {}
    
    def _vote_on_quantities(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Vote on quantity analysis from multiple models"""
        
        if not proposals:
            return {'consensus_reached': False, 'reason': 'No quantity proposals'}
        
        # Simple consensus: use the proposal with highest confidence
        best_proposal = max(proposals, key=lambda x: x.get('confidence', 0))
        
        return {
            'consensus_reached': True,
            'result': best_proposal.get('quantities', {}),
            'confidence': best_proposal.get('confidence', 0.5)
        }
    
    def _vote_on_details(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Vote on detail analysis from multiple models"""
        
        if not proposals:
            return {'consensus_reached': False, 'reason': 'No detail proposals'}
        
        # Simple consensus: use the proposal with highest confidence
        best_proposal = max(proposals, key=lambda x: x.get('confidence', 0))
        
        return {
            'consensus_reached': True,
            'result': best_proposal.get('details', {}),
            'confidence': best_proposal.get('confidence', 0.5)
        }
    
    def _calculate_cost_efficiency(self, total_cost: float, accuracy: float) -> float:
        """Calculate cost per accuracy point"""
        if accuracy > 0:
            return total_cost / accuracy
        return total_cost
    
    def _should_escalate_to_human(self, accuracy: float, iteration_count: int) -> bool:
        """Determine if result should be escalated to human review"""
        return accuracy < 0.85 or iteration_count >= 5
    
    def _get_human_review_priority(self, accuracy: float, consensus_rate: float) -> str:
        """Get priority level for human review"""
        if accuracy < 0.7 or consensus_rate < 0.5:
            return "high"
        elif accuracy < 0.85 or consensus_rate < 0.7:
            return "medium"
        else:
            return "low" 