"""
Script to show how to fix LangGraph system to use real extraction
"""

print("""
=== FIXING LANGGRAPH SYSTEM TO USE REAL EXTRACTION ===

The LangGraph system currently uses mock data. Here's what needs to be changed:

1. Replace _run_structure_agents with real extraction:
   - Use self.extraction_engine.execute_with_model_id()
   - Pass actual prompts and images
   - Use dynamic models from user configuration

2. Replace mock position/quantity/detail nodes with real extraction

3. Key changes needed:
   - Import extraction engine and dynamic model builder ✓ DONE
   - Add extraction_engine to __init__ ✓ DONE
   - Replace all mock methods with real extraction calls
   - Use stage_prompts and stage_configs from configuration
   - Build dynamic models for each stage

Example implementation for _run_structure_agents:

```python
async def _run_structure_agents(self, image_data: bytes) -> List[Dict]:
    '''Run structure analysis with real AI models'''
    
    proposals = []
    models = self.stage_models.get('structure', ['gpt-4o', 'claude-3-sonnet', 'gemini-pro'])
    
    for model in models:
        try:
            # Get prompt
            prompt = self.stage_prompts.get('structure', 'Analyze shelf structure...')
            
            # Build dynamic model if configured
            output_schema = self._get_output_schema_for_stage('structure')
            
            # Real extraction
            result, cost = await self.extraction_engine.execute_with_model_id(
                model_id=model,
                prompt=prompt,
                images={'enhanced': image_data},
                output_schema=output_schema,
                agent_id=f"langgraph_structure_{model}"
            )
            
            # Add to proposals
            proposals.append({
                'result': result,
                'confidence': 0.85,  # Could be calculated from result
                'model': model,
                'cost': cost
            })
            
        except Exception as e:
            logger.error(f"Structure agent {model} failed: {e}")
    
    return proposals
```

Similar changes needed for:
- _position_consensus_node
- _quantity_consensus_node  
- _detail_consensus_node

All should use real extraction instead of mock data.
""")