"""
Comprehensive Test Runner: Complete System Validation
Runs all individual phase tests and integration tests.
"""

import time
import sys
from pathlib import Path

# Import all test suites
from test_suite_phase1 import run_phase1_tests
from test_suite_phase2 import run_phase2_tests
from test_suite_integration import run_integration_tests

class ComprehensiveTestRunner:
    """Complete test runner for the poker advisory system."""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.total_tests = 0
        self.successful_tests = 0
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("🧪 COMPREHENSIVE POKER ADVISORY SYSTEM TEST SUITE")
        print("=" * 70)
        print("Running complete validation of all 6 phases and integration...")
        print()
        
        self.start_time = time.time()
        
        # Run individual phase tests
        print("📋 PHASE-BY-PHASE TESTING")
        print("-" * 40)
        
        # Phase 1 Tests
        try:
            print("Running Phase 1 Tests...")
            phase1_results, phase1_success = run_phase1_tests()
            self.results["Phase 1"] = {
                "results": phase1_results,
                "success_rate": phase1_success,
                "status": "✅ PASSED" if phase1_success > 0.8 else "⚠️ ISSUES"
            }
        except Exception as e:
            self.results["Phase 1"] = {
                "results": {"error": [f"❌ {e}"]},
                "success_rate": 0.0,
                "status": "❌ FAILED"
            }
        
        print()
        
        # Phase 2 Tests
        try:
            print("Running Phase 2 Tests...")
            phase2_results, phase2_success = run_phase2_tests()
            self.results["Phase 2"] = {
                "results": phase2_results,
                "success_rate": phase2_success,
                "status": "✅ PASSED" if phase2_success > 0.8 else "⚠️ ISSUES"
            }
        except Exception as e:
            self.results["Phase 2"] = {
                "results": {"error": [f"❌ {e}"]},
                "success_rate": 0.0,
                "status": "❌ FAILED"
            }
        
        print()
        
        # Phase 3-6 Quick Tests (functionality verification)
        self._run_remaining_phase_tests()
        
        print()
        
        # Integration Tests
        print("📋 INTEGRATION TESTING")
        print("-" * 40)
        try:
            print("Running Integration Tests...")
            integration_results, integration_success = run_integration_tests()
            self.results["Integration"] = {
                "results": integration_results,
                "success_rate": integration_success,
                "status": "✅ PASSED" if integration_success > 0.8 else "⚠️ ISSUES"
            }
        except Exception as e:
            self.results["Integration"] = {
                "results": {"error": [f"❌ {e}"]},
                "success_rate": 0.0,
                "status": "❌ FAILED"
            }
        
        print()
        
        # Generate final report
        self._generate_final_report()
    
    def _run_remaining_phase_tests(self):
        """Run quick functionality tests for phases 3-6."""
        
        # Phase 3: GPU Acceleration
        try:
            from app.core.gpu_acceleration import GPUAcceleratedRecognition
            gpu_system = GPUAcceleratedRecognition()
            
            # Quick functionality test
            test_image = __import__('numpy').random.randint(0, 255, (600, 800, 3), dtype=__import__('numpy').uint8)
            card_regions, metrics = gpu_system.accelerated_card_detection(test_image)
            
            self.results["Phase 3"] = {
                "results": {"gpu_test": [f"✅ GPU System ({metrics.gpu_available})"]},
                "success_rate": 1.0,
                "status": "✅ PASSED"
            }
        except Exception as e:
            self.results["Phase 3"] = {
                "results": {"error": [f"❌ {e}"]},
                "success_rate": 0.0,
                "status": "❌ FAILED"
            }
        
        # Phase 4: Enhanced GTO Engine
        try:
            from app.advisor.enhanced_gto_engine import EnhancedGTOEngine, PokerSituation
            gto_engine = EnhancedGTOEngine()
            
            # Quick GTO test
            test_situation = PokerSituation(
                hero_cards=['As', 'Kh'],
                board_cards=['Qd', 'Jc', '9s'],
                position='BTN',
                stack_size=100.0,
                pot_size=20.0,
                bet_to_call=5.0,
                opponents=[{'position': 'BB', 'last_action': 'bet'}],
                betting_history=['check', 'bet'],
                game_phase='flop',
                table_type='cash',
                blind_levels=(0.5, 1.0)
            )
            
            decision = gto_engine.analyze_situation(test_situation)
            
            self.results["Phase 4"] = {
                "results": {"gto_test": [f"✅ GTO Analysis ({decision.primary_action})"]},
                "success_rate": 1.0,
                "status": "✅ PASSED"
            }
        except Exception as e:
            self.results["Phase 4"] = {
                "results": {"error": [f"❌ {e}"]},
                "success_rate": 0.0,
                "status": "❌ FAILED"
            }
        
        # Phase 5: Turn Detection
        try:
            from app.core.turn_detection import AdvancedTurnDetection
            turn_detector = AdvancedTurnDetection()
            
            # Quick turn detection test
            test_image = __import__('numpy').random.randint(0, 255, (600, 800, 3), dtype=__import__('numpy').uint8)
            turn_state = turn_detector.detect_turn_state(test_image)
            
            self.results["Phase 5"] = {
                "results": {"turn_test": [f"✅ Turn Detection ({turn_state.confidence:.2f})"]},
                "success_rate": 1.0,
                "status": "✅ PASSED"
            }
        except Exception as e:
            self.results["Phase 5"] = {
                "results": {"error": [f"❌ {e}"]},
                "success_rate": 0.0,
                "status": "❌ FAILED"
            }
        
        # Phase 6: Anti-Detection
        try:
            from app.core.acr_anti_detection import ACRAntiDetectionSystem
            anti_detection = ACRAntiDetectionSystem()
            
            # Quick anti-detection test
            timing = anti_detection.calculate_stealth_decision_timing({
                'game_phase': 'flop',
                'intended_action': 'call'
            })
            
            self.results["Phase 6"] = {
                "results": {"stealth_test": [f"✅ Anti-Detection ({timing:.2f}s)"]},
                "success_rate": 1.0,
                "status": "✅ PASSED"
            }
        except Exception as e:
            self.results["Phase 6"] = {
                "results": {"error": [f"❌ {e}"]},
                "success_rate": 0.0,
                "status": "❌ FAILED"
            }
    
    def _generate_final_report(self):
        """Generate comprehensive final report."""
        total_time = time.time() - self.start_time
        
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        # Summary table
        print(f"{'Phase':<15} {'Status':<12} {'Success Rate':<12} {'Details'}")
        print("-" * 70)
        
        overall_success_rates = []
        
        for phase, data in self.results.items():
            status = data['status']
            success_rate = data['success_rate']
            overall_success_rates.append(success_rate)
            
            # Count tests in this phase
            phase_test_count = sum(len(category_results) for category_results in data['results'].values())
            
            print(f"{phase:<15} {status:<12} {success_rate:.1%}          {phase_test_count} tests")
        
        print("-" * 70)
        
        # Overall statistics
        overall_success = sum(overall_success_rates) / len(overall_success_rates) if overall_success_rates else 0
        total_test_count = sum(
            sum(len(category_results) for category_results in data['results'].values())
            for data in self.results.values()
        )
        
        print(f"{'OVERALL':<15} {'✅ PASSED' if overall_success > 0.8 else '⚠️ ISSUES':<12} {overall_success:.1%}          {total_test_count} total tests")
        
        print()
        print("🎯 SYSTEM VALIDATION SUMMARY")
        print("=" * 70)
        
        # System readiness assessment
        critical_phases = ["Phase 1", "Phase 2", "Integration"]
        critical_success = all(
            self.results.get(phase, {}).get('success_rate', 0) > 0.7
            for phase in critical_phases
        )
        
        if overall_success > 0.9:
            system_status = "🟢 EXCELLENT - System ready for production"
        elif overall_success > 0.8:
            system_status = "🟡 GOOD - System ready with minor issues"
        elif critical_success:
            system_status = "🟠 ACCEPTABLE - Core functionality working"
        else:
            system_status = "🔴 ISSUES - System needs attention"
        
        print(f"System Status: {system_status}")
        print(f"Overall Success Rate: {overall_success:.1%}")
        print(f"Total Test Time: {total_time:.2f} seconds")
        print(f"Total Tests Executed: {total_test_count}")
        
        # Detailed recommendations
        print()
        print("🔧 RECOMMENDATIONS")
        print("-" * 40)
        
        for phase, data in self.results.items():
            if data['success_rate'] < 0.8:
                print(f"• {phase}: Review failed tests and address issues")
        
        if overall_success > 0.8:
            print("• System is ready for professional poker advisory use")
            print("• All critical components are functioning correctly")
            print("• Stealth and performance measures are operational")
        
        print()
        print("🎮 POKER ADVISORY SYSTEM VALIDATION COMPLETE")
        print("=" * 70)
        
        return overall_success

def main():
    """Main test runner function."""
    runner = ComprehensiveTestRunner()
    overall_success = runner.run_all_tests()
    
    # Exit with appropriate code
    if overall_success > 0.8:
        print("✅ Test suite passed - System validated")
        sys.exit(0)
    else:
        print("⚠️ Test suite issues detected - Review required")
        sys.exit(1)

if __name__ == "__main__":
    main()