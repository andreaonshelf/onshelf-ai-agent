"""
Fix monitoring integration in remaining extraction systems
"""

import os

def fix_langgraph_system():
    """Add queue_item_id support to LangGraphSystem"""
    
    file_path = "src/systems/langgraph_system.py"
    
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping...")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update __init__ method
    if "def __init__(self, config: SystemConfig):" in content:
        old_init = "def __init__(self, config: SystemConfig):"
        new_init = "def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None):"
        content = content.replace(old_init, new_init)
        
        # Add queue_item_id storage after super().__init__ if exists
        super_init = content.find("super().__init__(config)")
        if super_init > 0:
            line_end = content.find('\n', super_init)
            content = content[:line_end] + "\n        self.queue_item_id = queue_item_id" + content[line_end:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path} with queue_item_id support")

def fix_hybrid_system():
    """Add queue_item_id support to HybridSystem"""
    
    file_path = "src/systems/hybrid_system.py"
    
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping...")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update __init__ method
    if "def __init__(self, config: SystemConfig):" in content:
        old_init = "def __init__(self, config: SystemConfig):"
        new_init = "def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None):"
        content = content.replace(old_init, new_init)
        
        # Add queue_item_id storage after super().__init__ if exists
        super_init = content.find("super().__init__(config)")
        if super_init > 0:
            line_end = content.find('\n', super_init)
            content = content[:line_end] + "\n        self.queue_item_id = queue_item_id" + content[line_end:]
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path} with queue_item_id support")

def fix_custom_consensus():
    """Add queue_item_id support to CustomConsensusSystem (parent class)"""
    
    file_path = "src/systems/custom_consensus.py"
    
    if not os.path.exists(file_path):
        print(f"⚠️ {file_path} not found, skipping...")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update __init__ method if it doesn't already have queue_item_id
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

if __name__ == "__main__":
    print("🔧 Fixing monitoring integration in remaining extraction systems...")
    
    # Change to project root
    os.chdir('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram')
    
    # Apply fixes
    fix_custom_consensus()
    fix_langgraph_system() 
    fix_hybrid_system()
    
    print("\n✅ All extraction systems updated with queue_item_id support!")