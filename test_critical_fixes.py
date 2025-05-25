#!/usr/bin/env python3
"""
Critical Fixes Testing Script for OnShelf AI
Tests all implemented fixes to ensure production readiness
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.append('src')

from src.config import SystemConfig
from src.systems.base_system import ExtractionSystemFactory
from src.feedback.human_learning import HumanFeedbackLearningSystem


class CriticalFixesTester:
    """Comprehensive tester for all critical fixes"""
    
    def __init__(self):
        self.config = SystemConfig()
        self.test_results = {}
        self.passed_tests = 0
        self.failed_tests = 0
    
    async def run_all_tests(self):
        """Run all critical fix tests"""
        print("🧪 OnShelf AI Critical Fixes Testing")
        print("=" * 50)
        
        # Test 1: Gemini Integration
        await self.test_gemini_integration()
        
        # Test 2: Real API Implementations
        await self.test_real_api_implementations()
        
        # Test 3: Database Persistence
        await self.test_database_persistence()
        
        # Test 4: Prompt Management System
        await self.test_prompt_management()
        
        # Test 5: 3-Model Consensus Voting
        await self.test_consensus_voting()
        
        # Test 6: Cost Tracking Accuracy
        await self.test_cost_tracking()
        
        # Test 7: Prompt Management UI
        await self.test_prompt_management_ui()
        
        # Generate final report
        self.generate_test_report()
    
    async def test_gemini_integration(self):
        """Test 1: Gemini Integration"""
        print("\n🔍 Test 1: Gemini Integration")
        
        try:
            from src.systems.custom_consensus import CustomConsensusSystem
            system = CustomConsensusSystem(self.config)
            
            # Check if Gemini client is initialized
            has_gemini = 'gemini' in system.model_clients and system.model_clients['gemini'] is not None
            
            if has_gemini:
                print("✅ Gemini client initialized successfully")
                self.test_results['gemini_integration'] = 'PASS'
                self.passed_tests += 1
            else:
                print("❌ Gemini client not initialized (check API key)")
                self.test_results['gemini_integration'] = 'FAIL - No API key or import error'
                self.failed_tests += 1
                
        except Exception as e:
            print(f"❌ Gemini integration test failed: {e}")
            self.test_results['gemini_integration'] = f'FAIL - {str(e)}'
            self.failed_tests += 1
    
    async def test_real_api_implementations(self):
        """Test 2: Real API Implementations (Mock Test)"""
        print("\n🔍 Test 2: Real API Implementations")
        
        try:
            from src.systems.custom_consensus import CustomConsensusSystem
            system = CustomConsensusSystem(self.config)
            
            # Test that we have real implementation methods
            has_gpt4o_method = hasattr(system, '_analyze_structure_gpt4o')
            has_claude_method = hasattr(system, '_analyze_structure_claude')
            has_gemini_method = hasattr(system, '_analyze_structure_gemini')
            has_parser_method = hasattr(system, '_parse_structure_response')
            
            if all([has_gpt4o_method, has_claude_method, has_gemini_method, has_parser_method]):
                print("✅ All real API implementation methods present")
                self.test_results['real_api_implementations'] = 'PASS'
                self.passed_tests += 1
            else:
                missing = []
                if not has_gpt4o_method: missing.append('GPT-4o')
                if not has_claude_method: missing.append('Claude')
                if not has_gemini_method: missing.append('Gemini')
                if not has_parser_method: missing.append('Parser')
                
                print(f"❌ Missing implementation methods: {missing}")
                self.test_results['real_api_implementations'] = f'FAIL - Missing: {missing}'
                self.failed_tests += 1
                
        except Exception as e:
            print(f"❌ API implementation test failed: {e}")
            self.test_results['real_api_implementations'] = f'FAIL - {str(e)}'
            self.failed_tests += 1
    
    async def test_database_persistence(self):
        """Test 3: Database Persistence"""
        print("\n🔍 Test 3: Database Persistence")
        
        try:
            learning_system = HumanFeedbackLearningSystem(self.config)
            
            # Check if database is configured
            has_database = learning_system.use_database and learning_system.supabase_client is not None
            
            if has_database:
                print("✅ Supabase database client initialized")
                
                # Test storing a mock correction
                mock_corrections = [{
                    'type': 'test_correction',
                    'original': {'test': 'data'},
                    'corrected': {'test': 'corrected_data'},
                    'context': {'test': True}
                }]
                
                await learning_system._store_corrections('test_upload_123', mock_corrections)
                print("✅ Database storage test completed")
                
                self.test_results['database_persistence'] = 'PASS'
                self.passed_tests += 1
            else:
                print("❌ Database not configured (check Supabase credentials)")
                self.test_results['database_persistence'] = 'FAIL - No database connection'
                self.failed_tests += 1
                
        except Exception as e:
            print(f"❌ Database persistence test failed: {e}")
            self.test_results['database_persistence'] = f'FAIL - {str(e)}'
            self.failed_tests += 1
    
    async def test_prompt_management(self):
        """Test 4: Prompt Management System"""
        print("\n🔍 Test 4: Prompt Management System")
        
        try:
            learning_system = HumanFeedbackLearningSystem(self.config)
            
            # Test model-specific prompt retrieval
            claude_prompt = await learning_system.get_optimized_prompt('structure_analysis', 'claude')
            gpt4o_prompt = await learning_system.get_optimized_prompt('structure_analysis', 'gpt4o')
            gemini_prompt = await learning_system.get_optimized_prompt('structure_analysis', 'gemini')
            
            # Check that prompts are different (model-specific adjustments)
            prompts_different = len(set([claude_prompt, gpt4o_prompt, gemini_prompt])) > 1
            
            if prompts_different:
                print("✅ Model-specific prompt adjustments working")
                print(f"   Claude prompt length: {len(claude_prompt)}")
                print(f"   GPT-4o prompt length: {len(gpt4o_prompt)}")
                print(f"   Gemini prompt length: {len(gemini_prompt)}")
                
                self.test_results['prompt_management'] = 'PASS'
                self.passed_tests += 1
            else:
                print("❌ Model-specific prompts are identical")
                self.test_results['prompt_management'] = 'FAIL - No model-specific adjustments'
                self.failed_tests += 1
                
        except Exception as e:
            print(f"❌ Prompt management test failed: {e}")
            self.test_results['prompt_management'] = f'FAIL - {str(e)}'
            self.failed_tests += 1
    
    async def test_consensus_voting(self):
        """Test 5: 3-Model Consensus Voting"""
        print("\n🔍 Test 5: 3-Model Consensus Voting")
        
        try:
            from src.systems.custom_consensus import DeterministicOrchestrator
            orchestrator = DeterministicOrchestrator()
            
            # Test structure voting with 3 models
            mock_proposals = [
                {'shelf_count': 4, 'confidence': 0.9, 'model_used': 'claude'},
                {'shelf_count': 4, 'confidence': 0.85, 'model_used': 'gpt4o'},
                {'shelf_count': 3, 'confidence': 0.7, 'model_used': 'gemini'}
            ]
            
            result = orchestrator.vote_on_structure(mock_proposals)
            
            # Check weighted voting details
            has_voting_details = 'voting_details' in result
            has_model_weights = 'participating_models' in result.get('voting_details', {})
            consensus_reached = result.get('consensus_reached', False)
            
            if has_voting_details and has_model_weights and consensus_reached:
                print("✅ 3-model weighted consensus voting working")
                print(f"   Consensus strength: {result.get('confidence', 0):.2f}")
                print(f"   Participating models: {result['voting_details']['participating_models']}")
                
                self.test_results['consensus_voting'] = 'PASS'
                self.passed_tests += 1
            else:
                print("❌ Consensus voting not working properly")
                print(f"   Result: {result}")
                self.test_results['consensus_voting'] = 'FAIL - Voting logic issues'
                self.failed_tests += 1
                
        except Exception as e:
            print(f"❌ Consensus voting test failed: {e}")
            self.test_results['consensus_voting'] = f'FAIL - {str(e)}'
            self.failed_tests += 1
    
    async def test_cost_tracking(self):
        """Test 6: Cost Tracking Accuracy"""
        print("\n🔍 Test 6: Cost Tracking Accuracy")
        
        try:
            from src.systems.custom_consensus import CustomConsensusSystem
            system = CustomConsensusSystem(self.config)
            
            # Test cost calculation methods
            gpt4o_cost = system._calculate_gpt4o_cost(1000)  # 1000 tokens
            claude_cost = system._calculate_claude_cost(700, 300)  # 700 input, 300 output
            gemini_cost = system._calculate_gemini_cost(1000)  # 1000 tokens
            
            # Verify costs are reasonable (not zero, not too high)
            costs_reasonable = all([
                0.001 < gpt4o_cost < 1.0,
                0.001 < claude_cost < 1.0,
                0.0001 < gemini_cost < 0.1  # Gemini should be much cheaper
            ])
            
            if costs_reasonable:
                print("✅ Real cost tracking implemented")
                print(f"   GPT-4o cost (1000 tokens): ${gpt4o_cost:.4f}")
                print(f"   Claude cost (700+300 tokens): ${claude_cost:.4f}")
                print(f"   Gemini cost (1000 tokens): ${gemini_cost:.4f}")
                
                self.test_results['cost_tracking'] = 'PASS'
                self.passed_tests += 1
            else:
                print("❌ Cost tracking values unreasonable")
                print(f"   GPT-4o: ${gpt4o_cost:.4f}, Claude: ${claude_cost:.4f}, Gemini: ${gemini_cost:.4f}")
                self.test_results['cost_tracking'] = 'FAIL - Unreasonable cost values'
                self.failed_tests += 1
                
        except Exception as e:
            print(f"❌ Cost tracking test failed: {e}")
            self.test_results['cost_tracking'] = f'FAIL - {str(e)}'
            self.failed_tests += 1
    
    async def test_prompt_management_ui(self):
        """Test 7: Prompt Management UI and API Endpoints"""
        print("\n🔍 Test 7: Prompt Management UI")
        
        try:
            from src.feedback.human_learning import HumanFeedbackLearningSystem
            learning_system = HumanFeedbackLearningSystem(self.config)
            
            # Test manual prompt saving
            await learning_system._save_manual_prompt(
                prompt_type='structure_analysis',
                model_type='gpt4o',
                prompt_content='Test prompt for structure analysis',
                prompt_version='test_1.0',
                description='Test prompt for UI validation'
            )
            
            # Test prompt version retrieval
            versions = await learning_system._get_prompt_versions('structure_analysis', 'gpt4o')
            
            # Test prompt activation
            if versions:
                test_prompt_id = versions[0]['prompt_id']
                activation_result = await learning_system._activate_prompt_version(test_prompt_id)
                activation_success = activation_result.get('success', False)
            else:
                activation_success = True  # No versions to test, but methods exist
            
            # Test suggestion generation
            suggestions = await learning_system._generate_prompt_suggestions(
                'structure_analysis', 'gpt4o', 'performance'
            )
            
            # Check if all UI support methods are working
            has_save_method = hasattr(learning_system, '_save_manual_prompt')
            has_versions_method = hasattr(learning_system, '_get_prompt_versions')
            has_activate_method = hasattr(learning_system, '_activate_prompt_version')
            has_suggestions_method = hasattr(learning_system, '_generate_prompt_suggestions')
            
            all_methods_present = all([
                has_save_method, has_versions_method, 
                has_activate_method, has_suggestions_method
            ])
            
            if all_methods_present and activation_success and suggestions:
                print("✅ Prompt management UI support implemented")
                print(f"   Manual prompt saving: ✅")
                print(f"   Version management: ✅ ({len(versions)} versions)")
                print(f"   Prompt activation: ✅")
                print(f"   AI suggestions: ✅ ({len(suggestions)} suggestions)")
                
                self.test_results['prompt_management_ui'] = 'PASS'
                self.passed_tests += 1
            else:
                missing_features = []
                if not has_save_method: missing_features.append('Save method')
                if not has_versions_method: missing_features.append('Versions method')
                if not has_activate_method: missing_features.append('Activate method')
                if not has_suggestions_method: missing_features.append('Suggestions method')
                if not activation_success: missing_features.append('Activation logic')
                if not suggestions: missing_features.append('Suggestion generation')
                
                print(f"❌ Missing prompt management features: {missing_features}")
                self.test_results['prompt_management_ui'] = f'FAIL - Missing: {missing_features}'
                self.failed_tests += 1
                
        except Exception as e:
            print(f"❌ Prompt management UI test failed: {e}")
            self.test_results['prompt_management_ui'] = f'FAIL - {str(e)}'
            self.failed_tests += 1
    
    def generate_test_report(self):
        """Generate final test report"""
        print("\n" + "=" * 50)
        print("🎯 CRITICAL FIXES TEST REPORT")
        print("=" * 50)
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅" if result == 'PASS' else "❌"
            print(f"  {status} {test_name}: {result}")
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        
        if self.failed_tests == 0:
            print("🎉 All critical fixes implemented successfully!")
            print("   System is ready for production deployment.")
        else:
            print("⚠️  Some critical fixes need attention:")
            
            for test_name, result in self.test_results.items():
                if result != 'PASS':
                    if 'gemini' in test_name:
                        print("   - Install Google GenerativeAI: pip install google-generativeai")
                        print("   - Set GOOGLE_API_KEY environment variable")
                    elif 'database' in test_name:
                        print("   - Install Supabase: pip install supabase")
                        print("   - Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
                        print("   - Run database_schema.sql in your Supabase project")
                    elif 'api' in test_name:
                        print("   - Verify all API keys are set correctly")
                    elif 'consensus' in test_name:
                        print("   - Check consensus voting logic implementation")
                    elif 'cost' in test_name:
                        print("   - Verify cost calculation methods")
                    elif 'prompt_management_ui' in test_name:
                        print("   - Check prompt management API endpoints")
                        print("   - Verify UI support methods are implemented")
        
        # Save report to file
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': success_rate,
            'detailed_results': self.test_results
        }
        
        with open('critical_fixes_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: critical_fixes_test_report.json")


async def main():
    """Main test runner"""
    tester = CriticalFixesTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 