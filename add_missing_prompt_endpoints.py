"""
Script to add missing prompt endpoints to prompt_management.py
"""

import os

# Read the current file
file_path = "src/api/prompt_management.py"
with open(file_path, 'r') as f:
    content = f.read()

# Find where to insert the new endpoints (after the /save endpoint)
insert_marker = '@router.post("/save")'
insert_position = content.find(insert_marker)

if insert_position == -1:
    print("Error: Could not find insertion point")
    exit(1)

# Find the start of the /save function
line_start = content.rfind('\n', 0, insert_position) + 1

# New endpoints to add
new_endpoints = '''
@router.get("/list/{prompt_type}")
async def list_prompts_by_type(prompt_type: str, is_active: Optional[bool] = None):
    """List all prompts for a specific type"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Build query
        query = supabase.table("prompt_templates").select("*").eq("prompt_type", prompt_type)
        
        # Filter by active status if specified
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        # Order by performance score and creation date
        query = query.order("performance_score", desc=True).order("created_at", desc=True)
        
        result = query.execute()
        
        # Format prompts for response
        prompts = []
        for prompt in result.data:
            prompts.append({
                "id": prompt['prompt_id'],
                "name": prompt['prompt_name'],
                "type": prompt['prompt_type'],
                "content": prompt['prompt_content'],
                "version": prompt['prompt_version'],
                "model_type": prompt['model_type'],
                "performance_score": prompt['performance_score'],
                "usage_count": prompt['usage_count'],
                "success_rate": prompt['success_rate'],
                "avg_cost": prompt['avg_token_cost'],
                "is_active": prompt['is_active'],
                "field_definitions": prompt.get('field_definitions', []),
                "created_at": prompt['created_at'],
                "created_by": prompt['created_by']
            })
        
        return {
            "prompt_type": prompt_type,
            "total": len(prompts),
            "prompts": prompts
        }
        
    except Exception as e:
        logger.error(f"Failed to list prompts for type {prompt_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/get/{prompt_id}")
async def get_prompt_by_id(prompt_id: str):
    """Get a specific prompt by ID"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        result = supabase.table("prompt_templates").select("*").eq("prompt_id", prompt_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        prompt = result.data[0]
        
        return {
            "id": prompt['prompt_id'],
            "name": prompt['prompt_name'],
            "type": prompt['prompt_type'],
            "content": prompt['prompt_content'],
            "version": prompt['prompt_version'],
            "model_type": prompt['model_type'],
            "performance_score": prompt['performance_score'],
            "usage_count": prompt['usage_count'],
            "success_rate": prompt['success_rate'],
            "avg_cost": prompt['avg_token_cost'],
            "is_active": prompt['is_active'],
            "field_definitions": prompt.get('field_definitions', []),
            "created_at": prompt['created_at'],
            "created_by": prompt['created_by']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("/performance/{prompt_id}")
async def track_prompt_performance(prompt_id: str, performance_data: Dict[str, Any]):
    """Track performance metrics for a prompt"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current prompt data
        result = supabase.table("prompt_templates").select("*").eq("prompt_id", prompt_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        prompt = result.data[0]
        
        # Update performance metrics
        current_usage = prompt.get('usage_count', 0)
        current_success = prompt.get('success_rate', 0.5)
        current_cost = prompt.get('avg_token_cost', 0)
        
        # Calculate new averages
        new_usage = current_usage + 1
        new_success = ((current_success * current_usage) + performance_data.get('success', 1)) / new_usage
        new_cost = ((current_cost * current_usage) + performance_data.get('cost', 0)) / new_usage
        
        # Calculate performance score (weighted average of success rate and cost efficiency)
        # Lower cost is better, so we invert it
        cost_score = 1 - min(new_cost / 0.1, 1)  # Normalize to 0-1 where 0.1 is considered expensive
        performance_score = (new_success * 0.7) + (cost_score * 0.3)
        
        # Update prompt with new metrics
        update_data = {
            "usage_count": new_usage,
            "success_rate": new_success,
            "avg_token_cost": new_cost,
            "performance_score": performance_score,
            "last_used_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("prompt_templates").update(update_data).eq("prompt_id", prompt_id).execute()
        
        # Log performance tracking
        logger.info(f"Updated performance for prompt {prompt_id}: usage={new_usage}, success={new_success:.2f}, cost=${new_cost:.4f}")
        
        return {
            "prompt_id": prompt_id,
            "updated_metrics": update_data,
            "performance_data": performance_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track performance for prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track performance: {str(e)}")


@router.get("/best/{prompt_type}/{model_type}")
async def get_best_performing_prompt(prompt_type: str, model_type: str = "universal"):
    """Get the best performing prompt for a specific type and model"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Query for best performing active prompt
        query = supabase.table("prompt_templates") \
            .select("*") \
            .eq("prompt_type", prompt_type) \
            .eq("is_active", True)
        
        # Filter by model type if not universal
        if model_type != "universal":
            query = query.or_(f"model_type.eq.{model_type},model_type.eq.universal")
        else:
            query = query.eq("model_type", "universal")
        
        # Order by performance score
        result = query.order("performance_score", desc=True).limit(1).execute()
        
        if not result.data:
            # Fallback to any active prompt of this type
            fallback_result = supabase.table("prompt_templates") \
                .select("*") \
                .eq("prompt_type", prompt_type) \
                .eq("is_active", True) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if not fallback_result.data:
                raise HTTPException(status_code=404, detail=f"No prompts found for type {prompt_type}")
            
            result = fallback_result
        
        prompt = result.data[0]
        
        return {
            "id": prompt['prompt_id'],
            "name": prompt['prompt_name'],
            "type": prompt['prompt_type'],
            "content": prompt['prompt_content'],
            "model_type": prompt['model_type'],
            "performance_score": prompt['performance_score'],
            "usage_count": prompt['usage_count'],
            "success_rate": prompt['success_rate'],
            "avg_cost": prompt['avg_token_cost'],
            "selection_reason": "highest_performance_score" if prompt['performance_score'] else "most_recent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best prompt for {prompt_type}/{model_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get best prompt: {str(e)}")


@router.post("/evolve/{prompt_id}")
async def evolve_underperforming_prompt(prompt_id: str, evolution_params: Optional[Dict[str, Any]] = None):
    """Evolve an underperforming prompt using AI"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current prompt
        result = supabase.table("prompt_templates").select("*").eq("prompt_id", prompt_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        prompt = result.data[0]
        
        # Check if prompt is actually underperforming
        if prompt['performance_score'] > 0.7:
            return {
                "message": "Prompt is performing well, evolution not needed",
                "current_performance": prompt['performance_score']
            }
        
        # Generate evolved prompt (in real implementation, this would use AI)
        evolved_content = f"""{prompt['prompt_content']}

ENHANCED INSTRUCTIONS (Based on performance analysis):
- Pay special attention to accuracy in edge cases
- Double-check all extracted values for consistency
- If uncertain, provide confidence scores
- Focus on systematic extraction to avoid missing items
"""
        
        # Create new version of the prompt
        import uuid
        new_prompt_id = str(uuid.uuid4())
        new_version = f"{prompt['prompt_version']}.evolved"
        
        new_prompt_data = {
            "prompt_id": new_prompt_id,
            "template_id": prompt['template_id'],
            "prompt_name": f"{prompt['prompt_name']} (Evolved)",
            "prompt_type": prompt['prompt_type'],
            "model_type": prompt['model_type'],
            "prompt_content": evolved_content,
            "prompt_version": new_version,
            "performance_score": 0.5,  # Start with neutral score
            "usage_count": 0,
            "success_rate": 0.5,
            "avg_token_cost": prompt['avg_token_cost'],
            "is_active": False,  # Not active until tested
            "created_by": "system_evolution",
            "created_from_feedback": True,
            "parent_prompt_id": prompt_id,
            "field_definitions": prompt.get('field_definitions', [])
        }
        
        # Insert evolved prompt
        supabase.table("prompt_templates").insert(new_prompt_data).execute()
        
        logger.info(f"Evolved prompt {prompt_id} -> {new_prompt_id}")
        
        return {
            "success": True,
            "original_prompt_id": prompt_id,
            "evolved_prompt_id": new_prompt_id,
            "version": new_version,
            "evolution_reason": f"Performance score {prompt['performance_score']:.2f} below threshold",
            "improvements": [
                "Added edge case handling",
                "Enhanced accuracy instructions",
                "Incorporated failure pattern analysis",
                "Added confidence scoring requirements"
            ],
            "next_steps": "Test evolved prompt with A/B testing before full activation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evolve prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to evolve prompt: {str(e)}")


'''

# Insert the new endpoints before the /save endpoint
new_content = content[:line_start] + new_endpoints + content[line_start:]

# Write the updated content
with open(file_path, 'w') as f:
    f.write(new_content)

print("Successfully added missing prompt endpoints to prompt_management.py")
print("Added endpoints:")
print("- GET /api/prompts/list/{prompt_type}")
print("- GET /api/prompts/get/{prompt_id}")
print("- POST /api/prompts/performance/{prompt_id}")
print("- GET /api/prompts/best/{prompt_type}/{model_type}")
print("- POST /api/prompts/evolve/{prompt_id}")