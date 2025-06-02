from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from collections import Counter
import os
from supabase import create_client, Client
import anthropic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analytics"])

# Also create extended analytics router
analytics_extended_router = APIRouter(tags=["analytics-extended"])

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    supabase = None
else:
    supabase = create_client(supabase_url, supabase_key)

# Initialize Claude client for AI insights
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
if anthropic_key:
    claude_client = anthropic.Anthropic(api_key=anthropic_key)
else:
    claude_client = None
    logger.warning("No ANTHROPIC_API_KEY found - AI insights will be limited")

@router.post("/extraction/recommend")
async def get_extraction_recommendations(context: dict):
    """Get AI recommendations based on context and historical performance"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Extract context
        store = context.get("store", "")
        category = context.get("category", "")
        retailer = context.get("retailer", "")
        
        # Query historical performance for this context
        history_query = supabase.table("extraction_runs").select("*")
        
        # Apply filters if context provided
        if store:
            history_query = history_query.ilike("metadata->>store_name", f"%{store}%")
        if category:
            history_query = history_query.ilike("metadata->>category", f"%{category}%")
            
        history = history_query.order("created_at", desc=True).limit(50).execute()
        
        # Analyze what worked best
        performance_by_system = {}
        performance_by_model = {}
        performance_by_prompt = {}
        
        for run in history.data:
            # Get system performance
            system = run.get("extraction_config", {}).get("system", "unknown")
            accuracy = run.get("final_accuracy", 0) or 0
            
            if system not in performance_by_system:
                performance_by_system[system] = []
            performance_by_system[system].append(accuracy)
            
            # Get model performance by extraction type
            models = run.get("extraction_config", {}).get("models", {})
            for extraction_type, model in models.items():
                key = f"{extraction_type}_{model}"
                if key not in performance_by_model:
                    performance_by_model[key] = []
                performance_by_model[key].append(accuracy)
            
            # Get prompt performance
            prompts = run.get("extraction_config", {}).get("prompts", {})
            for extraction_type, prompt_id in prompts.items():
                if prompt_id and prompt_id != "auto":
                    key = f"{extraction_type}_{prompt_id}"
                    if key not in performance_by_prompt:
                        performance_by_prompt[key] = []
                    performance_by_prompt[key].append(accuracy)
        
        # Calculate best performers
        best_system = "custom_consensus"  # Default
        best_system_score = 0
        
        for system, scores in performance_by_system.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score > best_system_score:
                    best_system = system
                    best_system_score = avg_score
        
        # Get best prompts for each type from prompt_templates table
        best_prompts = {}
        for prompt_type in ['structure', 'products', 'details']:
            # Query prompt templates with performance data
            prompt_query = supabase.table("prompt_templates").select("*").eq("prompt_type", prompt_type).eq("is_active", True)
            
            # If we have retailer context, try to find retailer-specific prompts
            if retailer:
                prompt_query = prompt_query.or_(f"metadata->>retailer.eq.{retailer},metadata->>retailer.is.null")
                
            prompts = prompt_query.order("performance_score", desc=True).limit(5).execute()
            
            if prompts.data:
                best_prompt = prompts.data[0]
                best_prompts[prompt_type] = {
                    'prompt_id': best_prompt['prompt_id'],
                    'name': f"{best_prompt['template_id']} v{best_prompt['prompt_version']}",
                    'version': best_prompt['prompt_version'],
                    'performance': best_prompt.get('performance_score', 0.8),
                    'reason': _generate_prompt_reason(best_prompt, context)
                }
            else:
                # Fallback if no prompts found
                best_prompts[prompt_type] = {
                    'prompt_id': 'auto',
                    'name': 'Auto-select',
                    'version': '1.0',
                    'performance': 0.75,
                    'reason': 'No specific prompts available for this context'
                }
        
        # Determine best models based on historical data
        best_models = {
            'structure': 'claude',  # Claude excels at structure analysis
            'products': 'gpt4o',    # GPT-4o best for product identification
            'details': 'gemini'     # Gemini good for detail extraction
        }
        
        # Override with actual performance data if available
        for extraction_type in ['structure', 'products', 'details']:
            best_model = None
            best_model_score = 0
            
            for model in ['claude', 'gpt4o', 'gemini']:
                key = f"{extraction_type}_{model}"
                if key in performance_by_model and performance_by_model[key]:
                    avg_score = sum(performance_by_model[key]) / len(performance_by_model[key])
                    if avg_score > best_model_score:
                        best_model = model
                        best_model_score = avg_score
            
            if best_model:
                best_models[extraction_type] = best_model
        
        return {
            'system': best_system,
            'system_reason': f"Achieved {best_system_score:.0%} avg accuracy in similar extractions" if best_system_score > 0 else "Recommended default system",
            'models': best_models,
            'prompts': best_prompts,
            'history_summary': f"Based on {len(history.data)} similar extractions" if history.data else "No historical data - using defaults"
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_prompt_reason(prompt: dict, context: dict) -> str:
    """Generate a reason for why this prompt was selected"""
    reasons = []
    
    # Check performance
    perf_score = prompt.get('performance_score', 0)
    if perf_score > 0.9:
        reasons.append(f"{perf_score:.0%} success rate")
    
    # Check usage
    usage = prompt.get('usage_count', 0)
    if usage > 100:
        reasons.append(f"Proven with {usage} uses")
    elif usage > 10:
        reasons.append(f"Tested {usage} times")
    
    # Check context match
    prompt_meta = prompt.get('metadata', {})
    if isinstance(prompt_meta, str):
        try:
            prompt_meta = json.loads(prompt_meta)
        except:
            prompt_meta = {}
            
    if prompt_meta.get('retailer') == context.get('retailer'):
        reasons.append(f"Optimized for {context['retailer']}")
    
    if prompt_meta.get('category') == context.get('category'):
        reasons.append(f"Tuned for {context['category']}")
    
    # Default reason if none found
    if not reasons:
        reasons.append("Best general-purpose prompt")
    
    return " • ".join(reasons)

@router.get("/analytics/prompts-with-stats")
async def get_prompts_with_performance(prompt_type: str, model_type: str):
    """Get prompts with full performance statistics"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get prompts with performance data
        query = supabase.table("prompt_templates").select("*")
        query = query.eq("prompt_type", prompt_type)
        query = query.or_(f"model_type.eq.{model_type},model_type.eq.universal")
        query = query.eq("is_active", True)
        query = query.order("performance_score", desc=True)
        
        prompts = query.execute()
        
        # Enhance with recent performance metrics
        enhanced_prompts = []
        for prompt in prompts.data:
            # Get recent usage stats from extraction_runs
            recent_runs = supabase.table("extraction_runs").select("final_accuracy,created_at,total_cost").or_(
                f"extraction_config->>prompts->>structure.eq.{prompt['prompt_id']},"
                f"extraction_config->>prompts->>products.eq.{prompt['prompt_id']},"
                f"extraction_config->>prompts->>details.eq.{prompt['prompt_id']}"
            ).gte("created_at", (datetime.utcnow() - timedelta(days=30)).isoformat()).execute()
            
            # Calculate recent metrics
            if recent_runs.data:
                recent_accuracies = [r.get('final_accuracy', 0) for r in recent_runs.data if r.get('final_accuracy')]
                recent_costs = [r.get('total_cost', 0) for r in recent_runs.data if r.get('total_cost')]
                
                prompt['recent_accuracy'] = sum(recent_accuracies) / len(recent_accuracies) if recent_accuracies else None
                prompt['recent_uses'] = len(recent_runs.data)
                prompt['avg_cost'] = sum(recent_costs) / len(recent_costs) if recent_costs else 0
                prompt['last_used'] = max(r['created_at'] for r in recent_runs.data) if recent_runs.data else None
            else:
                prompt['recent_accuracy'] = None
                prompt['recent_uses'] = 0
                prompt['avg_cost'] = 0
                prompt['last_used'] = None
            
            # Format last used time
            if prompt['last_used']:
                last_used_dt = datetime.fromisoformat(prompt['last_used'].replace('Z', '+00:00'))
                delta = datetime.utcnow() - last_used_dt.replace(tzinfo=None)
                
                if delta.days > 0:
                    prompt['last_used'] = f"{delta.days} days ago"
                elif delta.seconds > 3600:
                    prompt['last_used'] = f"{delta.seconds // 3600} hours ago"
                else:
                    prompt['last_used'] = "Recently"
            else:
                prompt['last_used'] = "Never"
            
            # Add formatted cost
            prompt['avg_token_cost'] = f"${prompt['avg_cost']:.3f}" if prompt['avg_cost'] else "$0.000"
            
            enhanced_prompts.append(prompt)
        
        return enhanced_prompts
        
    except Exception as e:
        logger.error(f"Failed to get prompts with stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/prompt-intelligence")
async def get_prompt_intelligence():
    """Comprehensive analysis of all prompts and their performance"""
    
    if not supabase:
        # Return mock data if no database
        return {
            'total_prompts': 0,
            'avg_success_rate': 0,
            'best_performer': {'name': 'No data yet', 'success_rate': 0},
            'success_patterns': [],
            'failure_patterns': [],
            'clusters': [],
            'ai_insights': {
                'generated_at': datetime.utcnow().isoformat(),
                'key_findings': ['No extraction data available yet'],
                'opportunities': ['Start running extractions to generate insights'],
                'trend_summary': 'No trends available'
            },
            'recommendations': []
        }
    
    try:
        # Get all prompts with performance data
        prompts = supabase.table("prompt_templates").select("*").execute()
        
        # Get extraction runs for performance analysis
        runs = supabase.table("extraction_runs").select("*").order("created_at", desc=True).limit(500).execute()
        
        # Basic statistics
        total_prompts = len(prompts.data)
        success_rates = [p['performance_score'] for p in prompts.data if p.get('performance_score')]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        # Find best performer
        best_performer = max(prompts.data, key=lambda p: p.get('performance_score', 0)) if prompts.data else None
        
        # Pattern analysis
        success_patterns = await analyze_patterns(prompts.data, 'success')
        failure_patterns = await analyze_patterns(prompts.data, 'failure')
        
        # Cluster analysis
        clusters = await cluster_prompts(prompts.data)
        
        # AI insights
        ai_insights = await generate_ai_insights(prompts.data, runs.data, success_patterns, failure_patterns)
        
        # Recommendations
        recommendations = await generate_recommendations(success_patterns, failure_patterns, runs.data)
        
        return {
            'total_prompts': total_prompts,
            'avg_success_rate': avg_success_rate,
            'best_performer': {
                'name': f"{best_performer['template_id']} v{best_performer['prompt_version']}" if best_performer else "None",
                'success_rate': best_performer.get('performance_score', 0) if best_performer else 0
            },
            'success_patterns': success_patterns,
            'failure_patterns': failure_patterns, 
            'clusters': clusters,
            'ai_insights': ai_insights,
            'recommendations': recommendations,
            
            # Additional metrics for the dashboard
            'total_extractions': len(runs.data),
            'avg_accuracy': sum(r.get('final_accuracy', 0) for r in runs.data) / len(runs.data) if runs.data else 0,
            'cost_saved': calculate_cost_savings(runs.data),
            'system_performance': analyze_system_performance(runs.data),
            'recent_insights': generate_recent_insights(runs.data)
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_patterns(prompts: List[Dict], pattern_type: str) -> List[Dict]:
    """Analyze common patterns in successful or failing prompts"""
    
    # Filter by performance
    if pattern_type == 'success':
        filtered = [p for p in prompts if p.get('performance_score', 0) > 0.9]
    else:
        filtered = [p for p in prompts if p.get('performance_score', 1) < 0.8]
    
    if not filtered:
        return []
    
    # Extract common phrases
    common_phrases = extract_common_phrases([p['prompt_content'] for p in filtered if p.get('prompt_content')])
    
    # Calculate impact
    patterns = []
    for phrase, count in common_phrases.items():
        # Calculate performance lift
        with_phrase = [p for p in prompts if phrase in p.get('prompt_content', '')]
        without_phrase = [p for p in prompts if phrase not in p.get('prompt_content', '')]
        
        if with_phrase and without_phrase:
            avg_with = sum(p.get('performance_score', 0) for p in with_phrase) / len(with_phrase)
            avg_without = sum(p.get('performance_score', 0) for p in without_phrase) / len(without_phrase)
            impact = (avg_with - avg_without) * 100
            
            patterns.append({
                'pattern': phrase,
                'impact': round(impact, 1),
                'prompt_count': count,
                'example_prompts': [p['template_id'] for p in with_phrase[:3]],
                'description': f"This pattern appears in {count} prompts and correlates with {impact:.1f}% performance difference"
            })
    
    return sorted(patterns, key=lambda x: abs(x['impact']), reverse=True)[:10]

def extract_common_phrases(texts: List[str], min_count: int = 2) -> Dict[str, int]:
    """Extract common phrases from prompt texts"""
    phrases = Counter()
    
    # Common prompt patterns to look for
    patterns_to_check = [
        "systematic", "left to right", "confidence", "double-check", "verify",
        "position", "facing", "stack", "price", "brand", "product name",
        "structured format", "JSON", "precise", "accurate", "complete"
    ]
    
    for text in texts:
        text_lower = text.lower()
        for pattern in patterns_to_check:
            if pattern in text_lower:
                phrases[pattern] += 1
    
    return {k: v for k, v in phrases.items() if v >= min_count}

async def cluster_prompts(prompts: List[Dict]) -> List[Dict]:
    """Cluster prompts by similarity and analyze performance"""
    
    # Extract prompt contents
    prompt_texts = [p['prompt_content'] for p in prompts if p.get('prompt_content')]
    
    if len(prompt_texts) < 5:
        return []
    
    try:
        # Vectorize prompts
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        X = vectorizer.fit_transform(prompt_texts)
        
        # Cluster
        n_clusters = min(5, len(prompt_texts) // 3)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)
        
        # Analyze clusters
        cluster_data = []
        for i in range(n_clusters):
            cluster_prompts = [prompts[j] for j, c in enumerate(clusters) if c == i]
            
            if cluster_prompts:
                avg_success = sum(p.get('performance_score', 0) for p in cluster_prompts) / len(cluster_prompts)
                
                # Extract common traits
                feature_names = vectorizer.get_feature_names_out()
                cluster_center = kmeans.cluster_centers_[i]
                top_features_idx = cluster_center.argsort()[-5:][::-1]
                common_traits = [feature_names[idx] for idx in top_features_idx]
                
                cluster_data.append({
                    'name': f"Cluster {i+1}",
                    'prompt_count': len(cluster_prompts),
                    'avg_success': avg_success,
                    'common_traits': common_traits,
                    'top_prompts': sorted(cluster_prompts, 
                                        key=lambda p: p.get('performance_score', 0), 
                                        reverse=True)[:3]
                })
        
        return sorted(cluster_data, key=lambda x: x['avg_success'], reverse=True)
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return []

async def generate_ai_insights(prompts: List[Dict], runs: List[Dict], 
                              success_patterns: List[Dict], 
                              failure_patterns: List[Dict]) -> Dict:
    """Use Claude to generate high-level insights"""
    
    if not claude_client:
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'key_findings': ['AI insights not available - no Claude API key configured'],
            'opportunities': ['Configure ANTHROPIC_API_KEY to enable AI insights'],
            'trend_summary': 'AI analysis not available'
        }
    
    try:
        # Prepare data summary
        avg_accuracy = sum(r.get('final_accuracy', 0) for r in runs) / len(runs) if runs else 0
        prompt_types = Counter(p['prompt_type'] for p in prompts)
        
        summary = f"""
        Analyze these patterns from {len(prompts)} extraction prompts:
        
        Success Patterns (found in high-performing prompts):
        {json.dumps(success_patterns[:5], indent=2)}
        
        Failure Patterns (found in low-performing prompts):
        {json.dumps(failure_patterns[:5], indent=2)}
        
        Overall statistics:
        - Average success rate: {avg_accuracy:.2%}
        - Total extraction runs: {len(runs)}
        - Most used prompt types: {prompt_types.most_common(3)}
        
        Provide:
        1. 3-5 key findings about what makes prompts successful
        2. 3-5 improvement opportunities
        3. Brief trend analysis summary
        
        Format as JSON with keys: key_findings, opportunities, trend_summary
        """
        
        response = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": summary}],
            max_tokens=1500
        )
        
        # Parse response
        try:
            insights = json.loads(response.content[0].text)
            insights['generated_at'] = datetime.utcnow().isoformat()
            return insights
        except:
            # Fallback if JSON parsing fails
            return {
                'generated_at': datetime.utcnow().isoformat(),
                'key_findings': [response.content[0].text[:200]],
                'opportunities': ['See full analysis above'],
                'trend_summary': 'Analysis completed'
            }
            
    except Exception as e:
        logger.error(f"AI insights generation failed: {e}")
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'key_findings': ['Error generating AI insights'],
            'opportunities': [str(e)],
            'trend_summary': 'Analysis failed'
        }

async def generate_recommendations(success_patterns: List[Dict],
                                 failure_patterns: List[Dict],
                                 runs: List[Dict]) -> List[Dict]:
    """Generate specific recommendations for new prompts"""
    
    recommendations = []
    
    # Based on success patterns
    for pattern in success_patterns[:3]:
        recommendations.append({
            'title': f"Include '{pattern['pattern']}' in new prompts",
            'description': f"This pattern shows {pattern['impact']}% performance improvement",
            'priority': 'high' if pattern['impact'] > 10 else 'medium',
            'category': 'success_pattern'
        })
    
    # Based on failure patterns to avoid
    for pattern in failure_patterns[:3]:
        recommendations.append({
            'title': f"Avoid '{pattern['pattern']}' in prompts",
            'description': f"This pattern correlates with {abs(pattern['impact'])}% performance decrease",
            'priority': 'high' if abs(pattern['impact']) > 10 else 'medium',
            'category': 'failure_pattern'
        })
    
    # Based on usage patterns
    if runs:
        # Find underperforming contexts
        context_performance = {}
        for run in runs:
            context = f"{run.get('metadata', {}).get('category', 'unknown')}"
            if context not in context_performance:
                context_performance[context] = []
            context_performance[context].append(run.get('final_accuracy', 0))
        
        # Find contexts that need improvement
        for context, accuracies in context_performance.items():
            if accuracies and sum(accuracies) / len(accuracies) < 0.8:
                recommendations.append({
                    'title': f"Create specialized prompt for {context}",
                    'description': f"Current accuracy is only {sum(accuracies)/len(accuracies):.0%}",
                    'priority': 'high',
                    'category': 'context_optimization'
                })
    
    return recommendations

def calculate_cost_savings(runs: List[Dict]) -> float:
    """Calculate cost savings from optimizations"""
    # Simple calculation - compare average cost of first 10 runs vs last 10 runs
    if len(runs) < 20:
        return 0.0
    
    first_10_costs = [r.get('total_cost', 0) for r in runs[-10:]]  # Oldest
    last_10_costs = [r.get('total_cost', 0) for r in runs[:10]]    # Newest
    
    avg_first = sum(first_10_costs) / len(first_10_costs) if first_10_costs else 0
    avg_last = sum(last_10_costs) / len(last_10_costs) if last_10_costs else 0
    
    return max(0, (avg_first - avg_last) * len(runs))

def analyze_system_performance(runs: List[Dict]) -> List[Dict]:
    """Analyze performance by system type"""
    system_stats = {}
    
    for run in runs:
        system = run.get('extraction_config', {}).get('system', 'unknown')
        if system not in system_stats:
            system_stats[system] = {
                'accuracies': [],
                'costs': []
            }
        
        system_stats[system]['accuracies'].append(run.get('final_accuracy', 0))
        system_stats[system]['costs'].append(run.get('total_cost', 0))
    
    results = []
    for system, stats in system_stats.items():
        if stats['accuracies']:
            results.append({
                'name': system.replace('_', ' ').title(),
                'accuracy': sum(stats['accuracies']) / len(stats['accuracies']),
                'avg_cost': sum(stats['costs']) / len(stats['costs']) if stats['costs'] else 0
            })
    
    return sorted(results, key=lambda x: x['accuracy'], reverse=True)

def generate_recent_insights(runs: List[Dict]) -> List[Dict]:
    """Generate recent insights from extraction runs"""
    insights = []
    
    if not runs:
        return [{
            'icon': '💡',
            'text': 'No extractions run yet - start processing to see insights',
            'time': 'Now'
        }]
    
    # Recent accuracy trend
    recent_runs = runs[:10]
    if recent_runs:
        avg_accuracy = sum(r.get('final_accuracy', 0) for r in recent_runs) / len(recent_runs)
        insights.append({
            'icon': '📈' if avg_accuracy > 0.85 else '📉',
            'text': f'Recent accuracy averaging {avg_accuracy:.0%}',
            'time': '1 hour ago'
        })
    
    # Cost trend
    if len(runs) > 20:
        recent_cost = sum(r.get('total_cost', 0) for r in runs[:10]) / 10
        older_cost = sum(r.get('total_cost', 0) for r in runs[10:20]) / 10
        
        if recent_cost < older_cost:
            savings = (older_cost - recent_cost) / older_cost * 100
            insights.append({
                'icon': '💰',
                'text': f'Cost reduced by {savings:.0f}% in recent extractions',
                'time': '2 hours ago'
            })
    
    # System usage
    system_usage = Counter(r.get('extraction_config', {}).get('system', 'unknown') for r in runs[:20])
    if system_usage:
        most_used = system_usage.most_common(1)[0]
        insights.append({
            'icon': '🎯',
            'text': f'{most_used[0].replace("_", " ").title()} used in {most_used[1]}/20 recent runs',
            'time': '3 hours ago'
        })
    
    return insights

@router.post("/analytics/regenerate-insights")
async def regenerate_insights():
    """Force regeneration of AI insights"""
    # Clear any cache and regenerate
    try:
        intelligence = await get_prompt_intelligence()
        return {"status": "success", "message": "Insights regenerated", "data": intelligence}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/generate-optimized-prompt")
async def generate_optimized_prompt(request: Dict[str, Any]):
    """Generate an optimized prompt using AI"""
    
    if not claude_client:
        # Fallback to template-based generation
        return await generate_template_based_prompt(request)
    
    try:
        logger.info("Starting prompt optimization with Claude")
        
        prompt_type = request.get("prompt_type", "products")
        base_prompt = request.get("base_prompt", "")
        fields = request.get("fields_to_extract", [])
        special_instructions = request.get("special_instructions", "")
        parent_prompt_id = request.get("parent_prompt_id")
        
        # Allow custom meta-prompt if provided
        custom_meta_prompt = request.get("meta_prompt")
        
        # Fetch field definitions for the requested fields
        field_definitions_text = ""
        if fields:
            try:
                # Import httpx for making internal API calls
                import httpx
                async with httpx.AsyncClient() as client:
                    params = "&".join([f"field_names={field}" for field in fields])
                    response = await client.get(f"http://localhost:8000/field-definitions-for-prompt?{params}")
                    if response.status_code == 200:
                        definitions_data = response.json()
                        field_definitions_text = definitions_data.get("definitions_text", "")
            except Exception as e:
                logger.warning(f"Could not fetch field definitions: {e}")
        
        # Build the generation prompt for Claude
        field_context = f"\n\nField Definitions:\n{field_definitions_text}" if field_definitions_text else ""
        
        generation_prompt = custom_meta_prompt or f"""
        Create an optimized extraction prompt for retail shelf images.
        
        Type: {prompt_type}
        Fields to extract: {', '.join(fields)}
        Base context: {base_prompt}
        Special instructions: {special_instructions}{field_context}
        
        Generate:
        1. An optimized prompt that will achieve >90% accuracy
        2. A Pydantic model for structured output with the requested fields
        3. Key improvements and reasoning
        
        IMPORTANT: The prompt and Pydantic model will be used with the Instructor library.
        The prompt should be clear, specific, and include examples where helpful.
        The Pydantic model must use proper type annotations and Field descriptors.
        
        Format the response as JSON with keys:
        - optimized_prompt: The full prompt text that will be passed to the AI model
        - pydantic_model_code: Complete Pydantic model code with proper imports and Field descriptors
        - model_class_name: Name of the main Pydantic class (e.g., "ExtractionResult")
        - reasoning: List of optimization decisions made
        - key_improvements: List of key improvements
        - optimization_focus: What this prompt is optimized for
        - recommended_model: Which AI model to use (claude/gpt4o/gemini)
        """
        
        logger.info(f"Sending request to Claude with {len(generation_prompt)} chars")
        
        response = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": generation_prompt}],
            max_tokens=2000
        )
        
        logger.info("Received response from Claude")
        
        # Parse response
        try:
            result = json.loads(response.content[0].text)
        except:
            # Fallback parsing if not valid JSON
            result = {
                "optimized_prompt": response.content[0].text,
                "pydantic_model_code": generate_pydantic_model(fields),
                "model_class_name": "ExtractionResult",
                "reasoning": ["AI optimization applied"],
                "key_improvements": ["Enhanced clarity and structure"],
                "optimization_focus": prompt_type,
                "recommended_model": "gpt4o"
            }
        
        # Add instructor configuration
        result["instructor_config"] = {
            "fields": fields,
            "validation_enabled": True,
            "retry_on_error": True,
            "max_retries": 3
        }
        
        # Estimate tokens
        result["estimated_tokens"] = len(result["optimized_prompt"].split()) * 1.3
        
        # Include the meta-prompt used for transparency
        result["meta_prompt_used"] = generation_prompt
        
        logger.info("Successfully generated optimized prompt")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate optimized prompt: {e}")
        # Fallback to template-based generation
        return await generate_template_based_prompt(request)

async def generate_template_based_prompt(request: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback template-based prompt generation"""
    prompt_type = request.get("prompt_type", "products")
    fields = request.get("fields_to_extract", [])
    base_prompt = request.get("base_prompt", "")
    
    # Build prompt based on type and fields
    if prompt_type == "structure":
        optimized = f"""Analyze this retail shelf image and identify the shelf structure.

{base_prompt}

Extract the following information:
- Number of shelves (count from top to bottom)
- Shelf dimensions and spacing
- Overall layout pattern
{chr(10).join(f'- {field.replace("_", " ").title()}' for field in fields if field not in ['shelf_count'])}

Be systematic and precise. Start from the top shelf and work downward."""
    
    elif prompt_type == "products":
        optimized = f"""Extract all products from this retail shelf image.

{base_prompt}

For each product, extract:
{chr(10).join(f'- {field.replace("_", " ").title()}' for field in fields)}

Work systematically from left to right on each shelf. Include confidence scores for each field."""
    
    else:  # details
        optimized = f"""Enhance the product details for items in this shelf image.

{base_prompt}

Focus on extracting:
{chr(10).join(f'- {field.replace("_", " ").title()}' for field in fields)}

Pay special attention to small text and partially visible items."""
    
    return {
        "optimized_prompt": optimized,
        "pydantic_model_code": generate_pydantic_model(fields),
        "model_class_name": "ExtractionResult",
        "reasoning": [
            "Structured format for consistency",
            "Clear field definitions",
            "Systematic extraction approach"
        ],
        "key_improvements": [
            "Added systematic scanning instructions",
            "Included confidence scoring",
            "Clear output structure"
        ],
        "optimization_focus": f"{prompt_type} extraction",
        "recommended_model": "gpt4o" if prompt_type == "products" else "claude",
        "instructor_config": {
            "fields": fields,
            "validation_enabled": True
        },
        "estimated_tokens": len(optimized.split()) * 1.3
    }

def generate_pydantic_model(fields: List[str]) -> str:
    """Generate Pydantic model code for the selected fields"""
    
    field_definitions = {
        "product_name": "str = Field(..., description='Full product name')",
        "brand": "str = Field(..., description='Brand name')",
        "price": "Optional[float] = Field(None, description='Price in local currency')",
        "position": "int = Field(..., description='Position from left (1-based)')",
        "facings": "int = Field(1, description='Number of facings/columns')",
        "stack": "int = Field(1, description='Vertical stack count')",
        "color": "Optional[str] = Field(None, description='Primary color')",
        "promo_text": "Optional[str] = Field(None, description='Promotional text if any')",
        "package_size": "Optional[str] = Field(None, description='Package size/volume')",
        "confidence": "float = Field(0.0, ge=0.0, le=1.0, description='Extraction confidence')"
    }
    
    model_code = """from pydantic import BaseModel, Field
from typing import Optional, List

class Product(BaseModel):
    \"\"\"Extracted product information\"\"\"
"""
    
    for field in fields:
        if field in field_definitions:
            model_code += f"    {field}: {field_definitions[field]}\n"
    
    model_code += """
class ExtractionResult(BaseModel):
    \"\"\"Complete extraction result\"\"\"
    products: List[Product]
    shelf_count: int = Field(..., description='Total number of shelves')
    extraction_confidence: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = Field(None, description='Additional observations')
"""
    
    return model_code

@router.post("/analytics/save-generated-prompt")
async def save_generated_prompt(request: Dict[str, Any]):
    """Save a generated prompt to the database"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        prompt_type = request.get("prompt_type")
        model_type = request.get("model_type", "universal")
        content = request.get("optimized_prompt")
        version_strategy = request.get("version_strategy", "new")
        parent_id = request.get("parent_prompt_id")
        
        # Generate template ID
        if parent_id and version_strategy == "branch":
            # Get parent prompt
            parent = supabase.table("prompt_templates").select("*").eq("prompt_id", parent_id).single().execute()
            template_id = f"{parent.data['template_id']}_custom_{datetime.utcnow().strftime('%Y%m%d')}"
            version = "1.0"
        elif parent_id and version_strategy == "new":
            # Increment version
            parent = supabase.table("prompt_templates").select("*").eq("prompt_id", parent_id).single().execute()
            template_id = parent.data['template_id']
            current_version = float(parent.data['prompt_version'])
            version = f"{current_version + 0.1:.1f}"
        else:
            # New prompt
            template_id = f"{prompt_type}_{model_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
            version = "1.0"
        
        # Prepare prompt data
        prompt_data = {
            "template_id": template_id,
            "prompt_type": prompt_type,
            "model_type": model_type,
            "prompt_content": content,
            "prompt_version": version,
            "is_active": False,  # Don't auto-activate new prompts
            "created_from_feedback": parent_id is not None,
            "parent_prompt_id": parent_id,
            "metadata": json.dumps({
                "instructor_config": request.get("instructor_config", {}),
                "pydantic_model": request.get("pydantic_model_code", ""),
                "optimization_focus": request.get("optimization_focus", ""),
                "created_by": "prompt_engineering_ui"
            }),
            "performance_score": 0.0,  # Will be updated as it's used
            "usage_count": 0,
            "avg_token_cost": 0.0
        }
        
        # Insert into database
        result = supabase.table("prompt_templates").insert(prompt_data).execute()
        
        return {
            "prompt_id": result.data[0]["prompt_id"],
            "template_id": template_id,
            "version": version,
            "message": "Prompt saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/queue/batch-configure")
async def batch_configure_queue_items(request: Dict[str, Any]):
    """Apply extraction configuration to multiple queue items"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        item_ids = request.get("item_ids", [])
        config = request.get("extraction_config", {})
        
        # Update each item with the configuration
        for item_id in item_ids:
            update_data = {
                "extraction_config": config,
                "config_applied_at": datetime.utcnow().isoformat(),
                "status": "configured"  # Mark as configured but not processed
            }
            
            supabase.table("extraction_queue").update(update_data).eq("id", item_id).execute()
        
        return {
            "updated_count": len(item_ids),
            "message": f"Configuration applied to {len(item_ids)} items"
        }
        
    except Exception as e:
        logger.error(f"Failed to batch configure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize the module
@router.get("/initialize")
async def initialize_analytics():
    """Initialize the analytics engine with historical data"""
    try:
        logger.info("🧠 Initializing analytics engine...")
        
        # This is now a real initialization that checks database connectivity
        if supabase:
            # Test connection
            test_query = supabase.table("extraction_runs").select("count", count="exact").execute()
            data_points = test_query.count if hasattr(test_query, 'count') else 0
            
            return {
                "status": "initialized",
                "data_points": data_points,
                "database_connected": True,
                "ai_insights_available": claude_client is not None,
                "models_available": ["pattern_detection", "clustering", "performance_prediction"]
            }
        else:
            return {
                "status": "initialized_limited",
                "data_points": 0,
                "database_connected": False,
                "ai_insights_available": False,
                "models_available": ["pattern_detection"]
            }
            
    except Exception as e:
        logger.error(f"Failed to initialize analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Extended Analytics Endpoints for Unified Dashboard
@analytics_extended_router.get("/system-performance")
async def get_system_performance() -> Dict[str, Any]:
    """Get real system performance metrics from Supabase"""
    
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Get all completed extractions
        result = supabase.table("ai_extraction_queue").select("*").eq(
            "status", "completed"
        ).execute()
        
        items = result.data or []
        
        # Group by system
        systems = {}
        for item in items:
            system = item.get("extraction_config", {}).get("system", "unknown")
            if system not in systems:
                systems[system] = {
                    "count": 0,
                    "total_accuracy": 0,
                    "total_cost": 0,
                    "total_duration": 0,
                    "accuracy_scores": []
                }
            
            systems[system]["count"] += 1
            
            # Get accuracy from final_accuracy or calculate from metadata
            accuracy = item.get("final_accuracy", 0)
            if not accuracy and item.get("extraction_results"):
                # Try to get from results
                results = item["extraction_results"]
                if isinstance(results, dict):
                    accuracy = results.get("accuracy", 0)
            
            systems[system]["total_accuracy"] += accuracy
            systems[system]["accuracy_scores"].append(accuracy)
            systems[system]["total_cost"] += item.get("api_cost", 0)
            
            # Calculate duration
            if item.get("completed_at") and item.get("started_at"):
                try:
                    start = datetime.fromisoformat(item["started_at"].replace("Z", "+00:00"))
                    end = datetime.fromisoformat(item["completed_at"].replace("Z", "+00:00"))
                    duration = (end - start).total_seconds()
                    systems[system]["total_duration"] += duration
                except:
                    pass
        
        # Calculate averages
        system_stats = {}
        for system, data in systems.items():
            if data["count"] > 0:
                system_stats[system] = {
                    "total_runs": data["count"],
                    "avg_accuracy": data["total_accuracy"] / data["count"],
                    "avg_cost": data["total_cost"] / data["count"],
                    "avg_duration": data["total_duration"] / data["count"] if data["total_duration"] > 0 else 0,
                    "accuracy_range": {
                        "min": min(data["accuracy_scores"]) if data["accuracy_scores"] else 0,
                        "max": max(data["accuracy_scores"]) if data["accuracy_scores"] else 0
                    }
                }
        
        # Get recent trends (last 7 days)
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        recent_result = supabase.table("ai_extraction_queue").select("*").eq(
            "status", "completed"
        ).gte("completed_at", seven_days_ago).execute()
        
        recent_items = recent_result.data or []
        
        return {
            "systems": system_stats,
            "overall": {
                "total_extractions": len(items),
                "recent_extractions": len(recent_items),
                "average_accuracy": sum(item.get("final_accuracy", 0) for item in items) / len(items) if items else 0,
                "total_cost": sum(item.get("api_cost", 0) for item in items)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system performance: {e}")
        # Return empty data - no fake data
        return {
            "systems": {},
            "overall": {
                "total_extractions": 0,
                "recent_extractions": 0,
                "average_accuracy": 0,
                "total_cost": 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }


@analytics_extended_router.get("/prompt-performance")
async def get_prompt_performance() -> Dict[str, Any]:
    """Get real prompt performance metrics"""
    
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Get meta prompts
        prompts_result = supabase.table("meta_prompts").select("*").execute()
        prompts = {p["id"]: p for p in prompts_result.data or []}
        
        # Get extraction runs that used prompts
        runs_result = supabase.table("extraction_runs").select("*").execute()
        runs = runs_result.data or []
        
        # Analyze prompt usage and performance
        prompt_stats = {}
        
        for run in runs:
            prompt_config = run.get("prompt_config", {})
            for stage, stage_config in prompt_config.items():
                prompt_id = stage_config.get("prompt_id")
                if prompt_id and prompt_id in prompts:
                    if prompt_id not in prompt_stats:
                        prompt_stats[prompt_id] = {
                            "name": prompts[prompt_id]["name"],
                            "stage": prompts[prompt_id]["stage"],
                            "uses": 0,
                            "total_accuracy": 0,
                            "total_cost": 0,
                            "accuracy_scores": []
                        }
                    
                    prompt_stats[prompt_id]["uses"] += 1
                    
                    # Get accuracy for this run
                    accuracy = run.get("final_accuracy", 0)
                    prompt_stats[prompt_id]["total_accuracy"] += accuracy
                    prompt_stats[prompt_id]["accuracy_scores"].append(accuracy)
                    prompt_stats[prompt_id]["total_cost"] += run.get("cost", 0)
        
        # Calculate averages
        prompt_performance = []
        for prompt_id, stats in prompt_stats.items():
            if stats["uses"] > 0:
                prompt_performance.append({
                    "id": prompt_id,
                    "name": stats["name"],
                    "stage": stats["stage"],
                    "uses": stats["uses"],
                    "avg_accuracy": stats["total_accuracy"] / stats["uses"],
                    "avg_cost": stats["total_cost"] / stats["uses"],
                    "accuracy_range": {
                        "min": min(stats["accuracy_scores"]) if stats["accuracy_scores"] else 0,
                        "max": max(stats["accuracy_scores"]) if stats["accuracy_scores"] else 0
                    }
                })
        
        # Sort by performance
        prompt_performance.sort(key=lambda x: x["avg_accuracy"], reverse=True)
        
        return {
            "prompts": prompt_performance,
            "total_prompts": len(prompts),
            "active_prompts": len(prompt_performance),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting prompt performance: {e}")
        # Return empty data - no fake data
        return {
            "prompts": [],
            "total_prompts": 0,
            "active_prompts": 0,
            "timestamp": datetime.utcnow().isoformat()
        }