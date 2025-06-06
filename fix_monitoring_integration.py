"""
Fix monitoring integration in extraction systems
"""

import os
import sys

def fix_custom_consensus_visual():
    """Add monitoring hooks to CustomConsensusVisualSystem"""
    
    file_path = "src/systems/custom_consensus_visual.py"
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add import for monitoring hooks if not present
    if "from ..orchestrator.monitoring_hooks import monitoring_hooks" not in content:
        # Find the imports section
        import_section_end = content.find('\nclass')
        if import_section_end > 0:
            new_import = "from ..orchestrator.monitoring_hooks import monitoring_hooks\n"
            content = content[:import_section_end] + new_import + content[import_section_end:]
    
    # Add queue_item_id parameter to __init__ if not present
    init_start = content.find("def __init__(self, config: SystemConfig):")
    if init_start > 0 and "queue_item_id" not in content[init_start:init_start + 200]:
        # Replace the __init__ signature
        old_init = "def __init__(self, config: SystemConfig):"
        new_init = "def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None):"
        content = content.replace(old_init, new_init)
        
        # Add queue_item_id storage after super().__init__
        super_init = content.find("super().__init__(config)")
        if super_init > 0:
            line_end = content.find('\n', super_init)
            content = content[:line_end] + "\n        self.queue_item_id = queue_item_id" + content[line_end:]
    
    # Add monitoring updates in extract_with_iterations
    iterations_method = content.find("async def extract_with_iterations(")
    if iterations_method > 0:
        # Find the loop start
        loop_start = content.find("for iteration in range(1, max_iterations + 1):", iterations_method)
        if loop_start > 0:
            # Add monitoring update after loop start
            loop_body_start = content.find('\n', loop_start) + 1
            indent = "            "
            monitoring_code = f'''
{indent}# Send monitoring update for iteration
{indent}if self.queue_item_id and hasattr(monitoring_hooks, 'update_iteration'):
{indent}    await monitoring_hooks.update_iteration(
{indent}        self.queue_item_id,
{indent}        iteration,
{indent}        locked_items=[]
{indent}    )
'''
            # Insert after the logger.info call
            logger_call = content.find("logger.info(", loop_body_start)
            if logger_call > 0:
                logger_end = content.find(')', logger_call)
                insert_pos = content.find('\n', logger_end) + 1
                content = content[:insert_pos] + monitoring_code + content[insert_pos:]
    
    # Add monitoring updates in _process_stage_with_visual_feedback
    stage_method = content.find("async def _process_stage_with_visual_feedback(")
    if stage_method > 0:
        # Find where we process each model
        model_loop = content.find("for i, model in enumerate(models):", stage_method)
        if model_loop > 0:
            # Add monitoring update after model processing starts
            logger_info = content.find("logger.info(", model_loop)
            if logger_info > 0:
                logger_end = content.find(')', logger_info)
                insert_pos = content.find('\n', logger_end) + 1
                indent = "            "
                monitoring_code = f'''
{indent}# Send monitoring update for stage progress
{indent}if self.queue_item_id:
{indent}    await monitoring_hooks.update_stage_progress(
{indent}        self.queue_item_id,
{indent}        stage_name=stage,
{indent}        attempt=i+1,
{indent}        total_attempts=len(models),
{indent}        model=model,
{indent}        complete=False
{indent}    )
{indent}    
{indent}    await monitoring_hooks.update_processing_detail(
{indent}        self.queue_item_id,
{indent}        f"Processing {{stage}} with model {{i+1}}/{{len(models)}}: {{model}}"
{indent}    )
'''
                content = content[:insert_pos] + monitoring_code + content[insert_pos:]
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path} with monitoring integration")

def fix_base_system():
    """Add queue_item_id support to BaseExtractionSystem"""
    
    file_path = "src/systems/base_system.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update __init__ method
    init_start = content.find("def __init__(self, config: SystemConfig):")
    if init_start > 0 and "queue_item_id" not in content[init_start:init_start + 200]:
        old_init = "def __init__(self, config: SystemConfig):"
        new_init = "def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None):"
        content = content.replace(old_init, new_init)
        
        # Add queue_item_id storage
        self_config = content.find("self.config = config")
        if self_config > 0:
            line_end = content.find('\n', self_config)
            content = content[:line_end] + "\n        self.queue_item_id = queue_item_id" + content[line_end:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path} with queue_item_id support")

def fix_system_dispatcher():
    """Update SystemDispatcher to pass queue_item_id to extraction systems"""
    
    file_path = "src/orchestrator/system_dispatcher.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find where extraction system is created
    factory_call = content.find("self.extraction_system = ExtractionSystemFactory.get_system(")
    if factory_call > 0:
        # Find the closing parenthesis
        paren_count = 1
        pos = content.find('(', factory_call) + 1
        while paren_count > 0 and pos < len(content):
            if content[pos] == '(':
                paren_count += 1
            elif content[pos] == ')':
                paren_count -= 1
            pos += 1
        
        if paren_count == 0:
            # Insert queue_item_id parameter before closing paren
            insert_pos = pos - 1
            content = content[:insert_pos] + ",\n            queue_item_id=queue_item_id" + content[insert_pos:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path} to pass queue_item_id")

def fix_extraction_system_factory():
    """Update ExtractionSystemFactory to accept queue_item_id"""
    
    file_path = "src/systems/base_system.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if factory exists, if not add it
    if "class ExtractionSystemFactory" not in content:
        factory_code = '''

class ExtractionSystemFactory:
    """Factory for creating extraction systems"""
    
    @staticmethod
    def get_system(system_type: str, config: SystemConfig, queue_item_id: Optional[int] = None) -> BaseExtractionSystem:
        """Create the appropriate extraction system"""
        
        if system_type == 'custom':
            from .custom_consensus_visual import CustomConsensusVisualSystem
            return CustomConsensusVisualSystem(config, queue_item_id)
        elif system_type == 'langgraph':
            from .langgraph_system import LangGraphSystem
            return LangGraphSystem(config, queue_item_id)
        elif system_type == 'hybrid':
            from .hybrid_system import HybridSystem
            return HybridSystem(config, queue_item_id)
        else:
            raise ValueError(f"Unknown system type: {system_type}")
'''
        content += factory_code
    else:
        # Update existing factory
        factory_method = content.find("def get_system(")
        if factory_method > 0:
            # Check if queue_item_id parameter exists
            method_end = content.find(':', factory_method)
            method_sig = content[factory_method:method_end]
            if "queue_item_id" not in method_sig:
                # Add queue_item_id parameter
                old_sig = "def get_system(system_type: str, config: SystemConfig)"
                new_sig = "def get_system(system_type: str, config: SystemConfig, queue_item_id: Optional[int] = None)"
                content = content.replace(old_sig, new_sig)
                
                # Update all system creations to pass queue_item_id
                for system in ['CustomConsensusVisualSystem', 'LangGraphSystem', 'HybridSystem']:
                    old_create = f"return {system}(config)"
                    new_create = f"return {system}(config, queue_item_id)"
                    content = content.replace(old_create, new_create)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path} with ExtractionSystemFactory")

if __name__ == "__main__":
    print("🔧 Fixing monitoring integration in extraction systems...")
    
    # Change to project root
    os.chdir('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram')
    
    # Apply fixes
    fix_base_system()
    fix_extraction_system_factory()
    fix_custom_consensus_visual()
    fix_system_dispatcher()
    
    print("\n✅ Monitoring integration fixes complete!")
    print("\nThe extraction systems will now send real-time monitoring updates during processing.")