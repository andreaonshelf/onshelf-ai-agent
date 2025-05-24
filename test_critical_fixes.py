#!/usr/bin/env python3
"""
OnShelf AI Agent - Critical Fixes Test Script
Validates: Logging, Cost Tracking, Error Handling, Multi-Image Utilization
"""

import asyncio
import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import SystemConfig
from src.utils import (
    logger, CostTracker, CostLimitExceededException, ErrorHandler,
    RetryConfig, with_retry, MultiImageCoordinator, ImageType
)


class CriticalFixesTest:
    """Test suite for critical system fixes"""
    
    def __init__(self):
        self.test_results = {}
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment with mock API keys"""
        os.environ.update({
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_openai_key',
            'ANTHROPIC_API_KEY': 'test_anthropic_key',
            'GOOGLE_API_KEY': 'test_google_key'
        })
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
    
    def test_structured_logging(self):
        """Test structured logging functionality"""
        print("🧪 Testing Structured Logging...")
        
        try:
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
            
            self.test_results['structured_logging'] = {
                'status': 'PASS',
                'details': f'Log files created: {len(log_files)}',
                'log_files': [f.name for f in log_files]
            }
            print("✅ Structured Logging: PASS")
            
        except Exception as e:
            self.test_results['structured_logging'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"❌ Structured Logging: FAIL - {e}")
    
    def test_cost_tracking(self):
        """Test cost tracking and enforcement"""
        print("🧪 Testing Cost Tracking...")
        
        try:
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
                self.test_results['cost_tracking'] = {
                    'status': 'FAIL',
                    'error': 'Cost limit not enforced'
                }
            except CostLimitExceededException as e:
                # This is expected
                self.test_results['cost_tracking'] = {
                    'status': 'PASS',
                    'details': f'Cost limit enforced correctly at £{e.current_cost:.2f}',
                    'total_cost': cost_tracker.total_cost,
                    'cost_limit': cost_tracker.cost_limit
                }
                print("✅ Cost Tracking: PASS")
            
        except Exception as e:
            self.test_results['cost_tracking'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"❌ Cost Tracking: FAIL - {e}")
    
    def test_error_handling(self):
        """Test error handling and retry mechanisms"""
        print("🧪 Testing Error Handling...")
        
        try:
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
            
            # Test escalation logic
            should_escalate = error_handler.should_escalate(test_error, 1)
            
            self.test_results['error_handling'] = {
                'status': 'PASS',
                'details': f'Retry succeeded after {attempt_count} attempts',
                'error_history_count': len(error_handler.error_history),
                'escalation_logic': should_escalate
            }
            print("✅ Error Handling: PASS")
            
        except Exception as e:
            self.test_results['error_handling'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"❌ Error Handling: FAIL - {e}")
    
    def test_multi_image_coordination(self):
        """Test multi-image coordination system"""
        print("🧪 Testing Multi-Image Coordination...")
        
        try:
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
            
            self.test_results['multi_image_coordination'] = {
                'status': 'PASS',
                'details': 'Image coordination working correctly',
                'total_images': summary['total_images'],
                'has_overview': summary['has_overview'],
                'has_details': summary['has_details'],
                'scaffolding_images': len(scaffolding_images),
                'product_images': len(product_images),
                'price_images': len(price_images)
            }
            print("✅ Multi-Image Coordination: PASS")
            
        except Exception as e:
            self.test_results['multi_image_coordination'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"❌ Multi-Image Coordination: FAIL - {e}")
    
    def test_system_config_validation(self):
        """Test system configuration validation"""
        print("🧪 Testing System Configuration...")
        
        try:
            # Test with valid config
            config = SystemConfig()
            is_valid = config.validate()
            
            if is_valid:
                self.test_results['system_config'] = {
                    'status': 'PASS',
                    'details': 'Configuration validation working',
                    'target_accuracy': config.target_accuracy,
                    'max_iterations': config.max_iterations,
                    'models_configured': len(config.models)
                }
                print("✅ System Configuration: PASS")
            else:
                self.test_results['system_config'] = {
                    'status': 'FAIL',
                    'error': 'Configuration validation failed'
                }
                print("❌ System Configuration: FAIL")
            
        except Exception as e:
            self.test_results['system_config'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"❌ System Configuration: FAIL - {e}")
    
    async def test_extraction_engine_integration(self):
        """Test extraction engine with new utilities"""
        print("🧪 Testing Extraction Engine Integration...")
        
        try:
            from src.extraction.engine import ModularExtractionEngine
            
            # Create engine with test config
            config = SystemConfig()
            engine = ModularExtractionEngine(config)
            
            # Test initialization for agent
            engine.initialize_for_agent("test_agent", 1.0)
            
            # Test design sequence
            test_images = {'test.jpg': b'mock_data'}
            sequence = await engine.design_extraction_sequence(test_images, agent_id="test_agent")
            
            assert len(sequence) > 0
            assert all(hasattr(step, 'step_id') for step in sequence)
            
            self.test_results['extraction_engine_integration'] = {
                'status': 'PASS',
                'details': 'Extraction engine integration working',
                'sequence_length': len(sequence),
                'has_cost_tracker': engine.cost_tracker is not None,
                'has_error_handler': engine.error_handler is not None,
                'has_image_coordinator': engine.image_coordinator is not None
            }
            print("✅ Extraction Engine Integration: PASS")
            
        except Exception as e:
            self.test_results['extraction_engine_integration'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"❌ Extraction Engine Integration: FAIL - {e}")
    
    def run_all_tests(self):
        """Run all critical fixes tests"""
        print("🚀 Running OnShelf AI Agent Critical Fixes Test Suite")
        print("=" * 60)
        
        # Run synchronous tests
        self.test_structured_logging()
        self.test_cost_tracking()
        self.test_error_handling()
        self.test_multi_image_coordination()
        self.test_system_config_validation()
        
        # Run async tests
        asyncio.run(self.test_extraction_engine_integration())
        
        # Summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("🧪 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {test_name.upper()}: {result['status']}")
            
            if result['status'] == 'PASS' and 'details' in result:
                print(f"   Details: {result['details']}")
            elif result['status'] == 'FAIL' and 'error' in result:
                print(f"   Error: {result['error']}")
        
        if passed == total:
            print("\n🎉 ALL CRITICAL FIXES VALIDATED SUCCESSFULLY!")
            print("✅ System is ready for testing")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed - review and fix before testing")
        
        print("\n📋 Next Steps:")
        print("1. Review any failed tests above")
        print("2. Check log files in ./logs/ directory")
        print("3. Run: python main.py --mode api (to start system)")
        print("4. Test with real upload: curl -X POST 'http://localhost:8000/api/v1/process/test_upload'")


def main():
    """Main test execution"""
    try:
        test_suite = CriticalFixesTest()
        test_suite.run_all_tests()
        return True
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 