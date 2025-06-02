#!/usr/bin/env python3
"""
Backend Model Integration Updates
This file contains the necessary changes to make the frontend model configurations functional
"""

# 1. Update queue_management.py - Add model configuration to process endpoint
QUEUE_MANAGEMENT_UPDATE = '''
# In src/api/queue_management.py

from pydantic import BaseModel
from typing import List, Optional

class ProcessRequest(BaseModel):
    system: str = "custom_consensus"
    max_budget: float = 1.50
    temperature: float = 0.7
    orchestrator_model: str = "claude-4-opus"
    orchestrator_prompt: Optional[str] = None
    stage_models: Dict[str, List[str]] = {}  # stage_id -> list of model ids

@router.post("/queue/process/{item_id}")
async def process_queue_item(item_id: int, request: ProcessRequest):
    """Process a queue item with specific model configuration"""
    
    # Update queue item with model configuration
    update_data = {
        "status": "processing",
        "selected_systems": [request.system],
        "current_extraction_system": request.system,
        "model_config": {
            "temperature": request.temperature,
            "orchestrator_model": request.orchestrator_model,
            "orchestrator_prompt": request.orchestrator_prompt,
            "stage_models": request.stage_models
        }
    }
    
    # Store in database
    await supabase.table("queue_items").update(update_data).eq("id", item_id).execute()
    
    # Continue with existing processing logic...
'''

# 2. Update extraction_orchestrator.py - Use configured models
ORCHESTRATOR_UPDATE = '''
# In src/orchestrator/extraction_orchestrator.py

class ExtractionOrchestrator:
    def __init__(self, queue_item_id: int, upload_id: str, image_url: str):
        self.queue_item_id = queue_item_id
        self.upload_id = upload_id
        self.image_url = image_url
        
        # Load model configuration from queue item
        self._load_model_config()
        
    def _load_model_config(self):
        """Load model configuration from queue item"""
        response = supabase.table("queue_items").select("model_config").eq("id", self.queue_item_id).single().execute()
        self.model_config = response.data.get("model_config", {})
        
        # Set defaults if not provided
        self.temperature = self.model_config.get("temperature", 0.7)
        self.orchestrator_model = self.model_config.get("orchestrator_model", "claude-4-opus")
        self.orchestrator_prompt = self.model_config.get("orchestrator_prompt", "")
        self.stage_models = self.model_config.get("stage_models", {})
        
    def _select_model_for_agent(self, agent_iteration: int, stage: str):
        """Select model based on configuration instead of hardcoding"""
        
        # Check if specific models are configured for this stage
        if stage in self.stage_models and self.stage_models[stage]:
            models = self.stage_models[stage]
            # Rotate through configured models for different agents
            return models[agent_iteration % len(models)]
        
        # Fallback to default behavior
        if agent_iteration == 1:
            return "gpt-4o"
        else:
            return "claude-3-5-sonnet-v2"
            
    def _create_orchestrator_prompt(self, base_prompt: str) -> str:
        """Enhance the orchestrator prompt with custom instructions"""
        if self.orchestrator_prompt:
            return f"{base_prompt}\n\nAdditional Instructions:\n{self.orchestrator_prompt}"
        return base_prompt
'''

# 3. Update extraction engine to use temperature and model names
ENGINE_UPDATE = '''
# In src/extraction/engine.py

class ExtractionEngine:
    def __init__(self, temperature: float = 0.7):
        self.temperature = temperature
        self._initialize_clients()
        
    def extract_with_model(self, image_url: str, prompt: str, schema, model_id: str):
        """Extract using specific model ID"""
        
        # Map model IDs to actual implementations
        model_mapping = {
            # OpenAI models
            "gpt-4.1": ("openai", "gpt-4-turbo-preview"),
            "gpt-4.1-mini": ("openai", "gpt-4-turbo-mini"),
            "gpt-4.1-nano": ("openai", "gpt-4-turbo-nano"),
            "gpt-4o": ("openai", "gpt-4o"),
            "gpt-4o-mini": ("openai", "gpt-4o-mini"),
            "o3": ("openai", "o3-preview"),
            "o4-mini": ("openai", "o4-mini"),
            
            # Anthropic models
            "claude-3-5-sonnet-v2": ("anthropic", "claude-3-5-sonnet-20241022"),
            "claude-3-7-sonnet": ("anthropic", "claude-3-sonnet-20240229"),
            "claude-4-sonnet": ("anthropic", "claude-4-sonnet"),
            "claude-4-opus": ("anthropic", "claude-4-opus"),
            
            # Google models
            "gemini-2.5-flash": ("google", "gemini-2.0-flash-exp"),
            "gemini-2.5-flash-thinking": ("google", "gemini-2.0-flash-thinking-exp"),
            "gemini-2.5-pro": ("google", "gemini-2.0-pro-exp"),
        }
        
        provider, actual_model = model_mapping.get(model_id, ("openai", "gpt-4o"))
        
        if provider == "openai":
            return self._extract_with_openai(image_url, prompt, schema, actual_model)
        elif provider == "anthropic":
            return self._extract_with_anthropic(image_url, prompt, schema, actual_model)
        elif provider == "google":
            return self._extract_with_gemini(image_url, prompt, schema, actual_model)
            
    def _extract_with_openai(self, image_url: str, prompt: str, schema, model: str):
        """OpenAI extraction with temperature"""
        response = self.openai_client.chat.completions.create(
            model=model,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            response_model=schema
        )
        return response
        
    def _extract_with_anthropic(self, image_url: str, prompt: str, schema, model: str):
        """Anthropic extraction with temperature"""
        # Download and encode image
        image_data = self._download_image(image_url)
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        response = self.anthropic_client.messages.create(
            model=model,
            temperature=self.temperature,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        
        # Parse with instructor
        return self._parse_with_instructor(response.content[0].text, schema)
        
    def _extract_with_gemini(self, image_url: str, prompt: str, schema, model: str):
        """Google Gemini extraction with temperature"""
        # Configure generation with temperature
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature,
            top_p=1,
            top_k=1,
            max_output_tokens=2048,
        )
        
        model = genai.GenerativeModel(model, generation_config=generation_config)
        
        # Download image
        image_data = self._download_image(image_url)
        image = Image.open(io.BytesIO(image_data))
        
        response = model.generate_content([prompt, image])
        return self._parse_with_instructor(response.text, schema)
'''

# 4. Update the master orchestrator to pass configuration
MASTER_UPDATE = '''
# In src/orchestrator/master_orchestrator.py

class MasterOrchestrator:
    def process_queue_item(self, queue_item_id: int):
        """Process a queue item with model configuration"""
        
        # Get queue item details
        queue_item = self._get_queue_item(queue_item_id)
        
        # Extract model configuration
        model_config = queue_item.get("model_config", {})
        temperature = model_config.get("temperature", 0.7)
        
        # Create extraction orchestrator with configuration
        orchestrator = ExtractionOrchestrator(
            queue_item_id=queue_item_id,
            upload_id=queue_item["upload_id"],
            image_url=queue_item["image_url"]
        )
        
        # Set temperature for all extractions
        orchestrator.engine = ExtractionEngine(temperature=temperature)
        
        # Run extraction
        results = orchestrator.run()
        
        return results
'''

# 5. Update the system implementations to respect model choices
SYSTEM_UPDATE = '''
# In src/systems/custom_consensus.py

class CustomConsensusSystem:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        
    async def run_stage(self, stage: str, image_url: str, prompt: str, schema):
        """Run a stage with configured models"""
        
        # Get models for this stage
        models = self.orchestrator.stage_models.get(stage, [])
        if not models:
            # Fallback to defaults
            models = ["gpt-4o", "claude-3-5-sonnet-v2", "gemini-2.5-pro"]
            
        # Run extraction with each model
        results = []
        for i, model_id in enumerate(models):
            try:
                result = await self.orchestrator.engine.extract_with_model(
                    image_url=image_url,
                    prompt=prompt,
                    schema=schema,
                    model_id=model_id
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Model {model_id} failed: {e}")
                
        # Consensus logic
        return self._build_consensus(results)
'''

if __name__ == "__main__":
    print("Backend Model Integration Plan")
    print("=" * 60)
    print("\nThis script outlines the necessary backend changes to support:")
    print("1. Model selection per stage")
    print("2. Temperature (creativity) control")
    print("3. Orchestrator model selection")
    print("4. Orchestrator prompt customization")
    print("5. Mapping frontend model IDs to actual API model names")
    print("\nKey files to update:")
    print("- src/api/queue_management.py")
    print("- src/orchestrator/extraction_orchestrator.py")
    print("- src/extraction/engine.py")
    print("- src/orchestrator/master_orchestrator.py")
    print("- src/systems/custom_consensus.py")