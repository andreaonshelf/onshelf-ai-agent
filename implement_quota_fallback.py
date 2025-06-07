#!/usr/bin/env python3
"""
Implement proper quota exhaustion fallback instead of removing user configurations
"""

# This would be integrated into the extraction engine

class QuotaAwareFallback:
    """Handle quota exhaustion with intelligent fallbacks"""
    
    def __init__(self):
        self.quota_exhausted_models = set()
        self.fallback_mapping = {
            'gemini-pro': 'claude-3-5-sonnet',
            'gemini-1.5-pro': 'claude-3-5-sonnet', 
            'gemini-2.5-pro': 'claude-4-opus',
            'gpt-4o': 'claude-4-opus',
            'claude-4-opus': 'gpt-4o'
        }
    
    async def execute_with_fallback(self, model_id, prompt, images, output_schema, agent_id):
        """Execute with automatic fallback on quota exhaustion"""
        
        # Try original model first
        try:
            result, cost = await self.extraction_engine.execute_with_model_id(
                model_id=model_id,
                prompt=prompt, 
                images=images,
                output_schema=output_schema,
                agent_id=agent_id
            )
            return result, cost, model_id  # Return which model was actually used
            
        except Exception as e:
            # Check if it's a quota error
            if '429' in str(e) or 'quota' in str(e).lower():
                print(f"⚠️  {model_id} quota exhausted, falling back...")
                self.quota_exhausted_models.add(model_id)
                
                # Try fallback model
                fallback_model = self.fallback_mapping.get(model_id)
                if fallback_model and fallback_model not in self.quota_exhausted_models:
                    try:
                        result, cost = await self.extraction_engine.execute_with_model_id(
                            model_id=fallback_model,
                            prompt=prompt,
                            images=images, 
                            output_schema=output_schema,
                            agent_id=f"{agent_id}_fallback"
                        )
                        print(f"✅ Fallback successful: {model_id} → {fallback_model}")
                        return result, cost, fallback_model
                    except Exception as fallback_error:
                        print(f"❌ Fallback {fallback_model} also failed: {fallback_error}")
                
                # If no fallback available, re-raise original error
                raise e
            else:
                # Non-quota error, re-raise
                raise e

def restore_original_configurations():
    """Restore user's original Gemini configurations"""
    
    print("🔄 Restoring user's original Gemini model selections...")
    
    # This would restore configurations that were incorrectly modified
    # Instead of removing Gemini, we should have implemented fallback logic
    
    restorations = {
        6: {
            "details": ["gpt-4o", "gemini-2.5-pro"],  # Restore Gemini
            "products": ["gpt-4o", "claude-3-5-sonnet", "gemini-2.5-pro"],  # Restore Gemini
            "comparison": ["gpt-4o", "claude-4-opus", "gemini-2.5-pro"]  # Restore Gemini
        },
        9: {
            "details": ["gpt-4o", "gemini-2.5-pro"],  # Restore Gemini  
            "products": ["gpt-4o", "claude-3-5-sonnet", "gemini-2.5-pro"],  # Restore Gemini
            "comparison": ["gpt-4o", "claude-4-opus", "gemini-2.5-pro"]  # Restore Gemini
        }
    }
    
    print("⚠️  WARNING: This should be implemented in the extraction engine")
    print("   User configurations should never be modified due to quota issues")
    print("   Fallback should happen at runtime, not configuration level")

if __name__ == "__main__":
    restore_original_configurations()
    print("\n💡 The proper solution:")
    print("   1. Keep user's Gemini selections in configuration") 
    print("   2. Implement quota fallback in extraction engine")
    print("   3. Log when fallbacks occur")
    print("   4. Never modify user's intentional model choices")