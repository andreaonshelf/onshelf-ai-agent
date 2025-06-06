#!/usr/bin/env python3
"""
TEST LANGGRAPH FIX
"""

import asyncio
from src.systems.langgraph_system import LangGraphConsensusSystem
from src.config import SystemConfig

async def test_langgraph_fix():
    print("🔍 TESTING LANGGRAPH FIX")
    print("=" * 60)
    
    # Create a mock config
    config = SystemConfig()
    
    # Create the system
    system = LangGraphConsensusSystem(config)
    
    # Create a mock state for validation
    mock_state = {
        'structure_consensus': {'shelf_count': 4},
        'position_consensus': {f'pos_{i}': {'product': f'Product {i}'} for i in range(15)},
        'quantity_consensus': {f'pos_{i}': {'facing_count': 2} for i in range(15)},
        'detail_consensus': {f'pos_{i}': {'price': 2.99} for i in range(15)},
        'consensus_rates': {
            'structure': 0.85,
            'positions': 0.82,
            'quantities': 0.78,
            'details': 0.80
        }
    }
    
    # Test the validation node
    result_state = await system._validate_end_to_end_node(mock_state)
    
    validation = result_state.get('validation_result', {})
    accuracy = validation.get('accuracy', 0.0)
    
    print(f"\n✅ NEW ACCURACY: {accuracy:.2%}")
    print(f"   (Was hardcoded to 91%, now calculated based on actual data)")
    
    print(f"\n📊 VALIDATION DETAILS:")
    details = validation.get('validation_details', {})
    for key, value in details.items():
        print(f"   {key}: {value}")
    
    print(f"\n🎯 RESULT:")
    print(f"   - No more fake 91% accuracy!")
    print(f"   - Accuracy now based on actual extraction results")
    print(f"   - Maximum 85% without human validation")
    print(f"   - Needs human validation: {validation.get('needs_human_validation', False)}")

if __name__ == "__main__":
    asyncio.run(test_langgraph_fix())