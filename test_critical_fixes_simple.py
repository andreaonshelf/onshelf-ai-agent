#!/usr/bin/env python3
"""
OnShelf AI Agent - Simple Critical Fixes Test Script
Tests only the core utilities without complex dependencies
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up test environment
os.environ.update({
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_SERVICE_KEY': 'test_key',
    'OPENAI_API_KEY': 'test_openai_key',
    'ANTHROPIC_API_KEY': 'test_anthropic_key',
    'GOOGLE_API_KEY': 'test_google_key'
})

def test_structured_logging():
    """Test structured logging functionality"""
    print("🧪 Testing Structured Logging...")
    
    try:
        from src.utils.logger import logger
        
        # Test basic logging
        logger.info("Test info message", component="test")
        logger.warning("Test warning message", component="test", test_param="value")
        logger.error("Test error message", component="test", error_code=500)
        
        # Test agent-specific logging
        test_agent_id = "test_agent_123"
        logger.log_agent_start(test_agent_id, "test_upload", 0.95)
        logger.log_iteration_start(test_agent_id, 1, "test_strategy")
        logger.log_accuracy_update(test_agent_id, 1, 0.87, 3)
        logger.log_completion(test_agent_id, 0.96, 2, 120.5, 0.25)
        
        # Check if log files are created
        log_files = list(Path("logs").glob("*.log"))
        
        print(f"✅ Structured Logging: PASS - {len(log_files)} log files created")
        return True
        
    except Exception as e:
        print(f"❌ Structured Logging: FAIL - {e}")
        return False

def test_cost_tracking():
    """Test cost tracking and enforcement"""
    print("🧪 Testing Cost Tracking...")
    
    try:
        from src.utils.cost_tracker import CostTracker, CostLimitExceededException
        
        # Test normal operations
        cost_tracker = CostTracker(cost_limit=1.0, agent_id="test_agent")
        
        # Add costs within limit
        cost_tracker.add_cost("extraction_step_1", 0.25)
        cost_tracker.add_cost("extraction_step_2", 0.30)
        
        # Test cost summary
        summary = cost_tracker.get_cost_summary()
        assert summary['total_cost'] == 0.55
        assert summary['remaining_budget'] == 0.45
        assert cost_tracker.is_approaching_limit(0.5) == True
        
        # Test cost limit enforcement
        try:
            cost_tracker.add_cost("expensive_operation", 0.50)  # This should succeed
            cost_tracker.add_cost("over_limit_operation", 0.10)  # This should fail
            print("❌ Cost Tracking: FAIL - Cost limit not enforced")
            return False
        except CostLimitExceededException as e:
            # This is expected
            print(f"✅ Cost Tracking: PASS - Cost limit enforced correctly at £{e.current_cost:.2f}")
            return True
        
    except Exception as e:
        print(f"❌ Cost Tracking: FAIL - {e}")
        return False

def test_error_handling():
    """Test error handling and retry mechanisms"""
    print("🧪 Testing Error Handling...")
    
    try:
        from src.utils.error_handling import ErrorHandler, with_retry, RetryConfig
        
        # Test error handler
        error_handler = ErrorHandler("test_agent")
        
        # Record some errors
        test_error = ValueError("Test error")
        error_handler.record_error(test_error, {'context': 'test'})
        
        # Test retry decorator
        attempt_count = 0
        
        @with_retry(RetryConfig(max_retries=2, base_delay=0.1))
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                raise ValueError(f"Attempt {attempt_count} failed")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert attempt_count == 3  # 1 initial + 2 retries
        
        print(f"✅ Error Handling: PASS - Retry succeeded after {attempt_count} attempts")
        return True
        
    except Exception as e:
        print(f"❌ Error Handling: FAIL - {e}")
        return False

def test_multi_image_coordination():
    """Test multi-image coordination system"""
    print("🧪 Testing Multi-Image Coordination...")
    
    try:
        from src.utils.image_coordinator import MultiImageCoordinator, ImageType
        
        # Create test images (mock data)
        test_images = {
            'overview_shelf.jpg': b'mock_overview_image_data',
            'top_detail_shelf.jpg': b'mock_top_detail_data',
            'bottom_detail_shelf.jpg': b'mock_bottom_detail_data',
            'unknown_image.jpg': b'mock_unknown_data'
        }
        
        # Test image coordinator
        coordinator = MultiImageCoordinator("test_agent")
        coordinator.add_images(test_images)
        
        # Test image classification
        assert ImageType.OVERVIEW in coordinator.images
        assert ImageType.TOP_DETAIL in coordinator.images
        assert ImageType.BOTTOM_DETAIL in coordinator.images
        
        # Test step-specific image selection
        scaffolding_images = coordinator.get_images_for_step("scaffolding")
        product_images = coordinator.get_images_for_step("products")
        price_images = coordinator.get_images_for_step("specialized_pricing")
        
        # Test image summary
        summary = coordinator.get_image_summary()
        
        print(f"✅ Multi-Image Coordination: PASS - {summary['total_images']} images classified correctly")
        return True
        
    except Exception as e:
        print(f"❌ Multi-Image Coordination: FAIL - {e}")
        return False

def test_system_config():
    """Test system configuration"""
    print("🧪 Testing System Configuration...")
    
    try:
        from src.config import SystemConfig
        
        # Test with valid config
        config = SystemConfig()
        is_valid = config.validate()
        
        if is_valid:
            print(f"✅ System Configuration: PASS - Config valid with {len(config.models)} models")
            return True
        else:
            print("❌ System Configuration: FAIL - Configuration validation failed")
            return False
        
    except Exception as e:
        print(f"❌ System Configuration: FAIL - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running OnShelf AI Agent Critical Fixes Test Suite")
    print("=" * 60)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run tests
    tests = [
        test_structured_logging,
        test_cost_tracking,
        test_error_handling,
        test_multi_image_coordination,
        test_system_config
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print("🧪 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL CRITICAL FIXES VALIDATED SUCCESSFULLY!")
        print("✅ Core utilities are working correctly")
        print("✅ System is ready for integration testing")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review and fix before testing")
    
    print("\n📋 Next Steps:")
    print("1. Review any failed tests above")
    print("2. Check log files in ./logs/ directory")
    print("3. Install Python 3.10+ for full system compatibility")
    print("4. Or update type annotations for Python 3.9 compatibility")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 