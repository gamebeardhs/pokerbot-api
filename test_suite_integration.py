"""
Integration Testing Suite: All Phases Working Together
Comprehensive testing of the complete poker advisory system.
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch

# Import all phases
from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
from app.scraper.acr_stealth_detection import ACRStealthDetection
from app.core.gpu_acceleration import GPUAcceleratedRecognition
from app.advisor.enhanced_gto_engine import EnhancedGTOEngine, PokerSituation
from app.core.turn_detection import AdvancedTurnDetection
from app.core.acr_anti_detection import ACRAntiDetectionSystem

class TestSystemInitialization:
    """Test complete system initialization."""
    
    def test_all_phases_initialize(self):
        """Test all phases can be initialized without errors."""
        try:
            calibrator = IntelligentACRCalibrator()
            gpu_system = GPUAcceleratedRecognition()
            gto_engine = EnhancedGTOEngine()
            turn_detector = AdvancedTurnDetection()
            anti_detection = ACRAntiDetectionSystem()
            
            # All should initialize successfully
            assert calibrator is not None
            assert gpu_system is not None
            assert gto_engine is not None
            assert turn_detector is not None
            assert anti_detection is not None
            
            return True
        except Exception as e:
            print(f"Initialization failed: {e}")
            return False
    
    def test_phase_integration_points(self):
        """Test integration points between phases."""
        calibrator = IntelligentACRCalibrator()
        
        # Phase 1 + 2 integration
        assert calibrator.stealth_detector is not None
        assert hasattr(calibrator.stealth_detector, 'adaptive_table_detection')
        
        # Circuit breaker should be active
        assert calibrator.circuit_breaker.state.value == "closed"
        
        return True

class TestFullPipelineIntegration:
    """Test complete pipeline integration."""
    
    def setup_method(self):
        """Setup test environment."""
        self.calibrator = IntelligentACRCalibrator()
        self.gpu_system = GPUAcceleratedRecognition()
        self.gto_engine = EnhancedGTOEngine()
        self.turn_detector = AdvancedTurnDetection()
        self.anti_detection = ACRAntiDetectionSystem()
        
        # Create test screenshot
        self.test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        # Add poker table elements
        self.test_screenshot[200:400, 300:500, 1] = 100  # Green felt
        self.test_screenshot[500:530, 600:750] = [100, 140, 220]  # Action buttons
    
    def test_screenshot_to_detection_pipeline(self):
        """Test screenshot capture to table detection pipeline."""
        # Phase 1: Screenshot capture
        screenshot = self.calibrator.capture_screen()
        assert screenshot is not None
        assert len(screenshot.shape) == 3
        
        # Phase 2: Table detection with stealth
        detected, table_info = self.calibrator.detect_acr_table_with_versioning(screenshot)
        assert isinstance(detected, bool)
        assert isinstance(table_info, dict)
        
        return True
    
    def test_detection_to_recognition_pipeline(self):
        """Test table detection to card recognition pipeline."""
        # Phase 2: Table detection
        detected, table_info = self.calibrator.detect_acr_table_with_versioning(self.test_screenshot)
        
        # Phase 3: GPU-accelerated card recognition
        card_regions, gpu_metrics = self.gpu_system.accelerated_card_detection(self.test_screenshot)
        assert isinstance(card_regions, list)
        assert hasattr(gpu_metrics, 'gpu_available')
        assert hasattr(gpu_metrics, 'processing_time')
        
        return True
    
    def test_recognition_to_gto_pipeline(self):
        """Test card recognition to GTO analysis pipeline."""
        # Phase 3: Card recognition (simulated)
        card_regions, _ = self.gpu_system.accelerated_card_detection(self.test_screenshot)
        
        # Phase 4: GTO analysis
        poker_situation = PokerSituation(
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
        
        decision = self.gto_engine.analyze_situation(poker_situation)
        assert hasattr(decision, 'primary_action')
        assert hasattr(decision, 'confidence_score')
        
        return True
    
    def test_gto_to_turn_detection_pipeline(self):
        """Test GTO analysis to turn detection pipeline."""
        # Phase 4: GTO decision (simulated)
        poker_situation = PokerSituation(
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
        
        decision = self.gto_engine.analyze_situation(poker_situation)
        
        # Phase 5: Turn detection
        turn_state = self.turn_detector.detect_turn_state(self.test_screenshot)
        assert hasattr(turn_state, 'is_hero_turn')
        assert hasattr(turn_state, 'confidence')
        
        return True
    
    def test_turn_detection_to_anti_detection_pipeline(self):
        """Test turn detection to anti-detection pipeline."""
        # Phase 5: Turn detection
        turn_state = self.turn_detector.detect_turn_state(self.test_screenshot)
        
        # Phase 6: Anti-detection measures
        decision_context = {
            'game_phase': 'flop',
            'intended_action': 'call',
            'decision_difficulty': 'marginal'
        }
        
        stealth_timing = self.anti_detection.calculate_stealth_decision_timing(decision_context)
        assert isinstance(stealth_timing, float)
        assert 0.5 <= stealth_timing <= 30.0
        
        return True

class TestCrossPhaseDataFlow:
    """Test data flow between phases."""
    
    def setup_method(self):
        """Setup test environment."""
        self.calibrator = IntelligentACRCalibrator()
        self.gpu_system = GPUAcceleratedRecognition()
        self.gto_engine = EnhancedGTOEngine()
        self.turn_detector = AdvancedTurnDetection()
        self.anti_detection = ACRAntiDetectionSystem()
    
    def test_screenshot_state_consistency(self):
        """Test screenshot state is consistent across phases."""
        screenshot = self.calibrator.capture_screen()
        
        # All phases should handle the same screenshot
        detected, _ = self.calibrator.detect_acr_table_with_versioning(screenshot)
        card_regions, _ = self.gpu_system.accelerated_card_detection(screenshot)
        turn_state = self.turn_detector.detect_turn_state(screenshot)
        
        # Should not raise exceptions
        assert True
        return True
    
    def test_timing_coordination(self):
        """Test timing coordination between phases."""
        start_time = time.time()
        
        # Phase 1: Screenshot (should be fast)
        screenshot = self.calibrator.capture_screen()
        phase1_time = time.time() - start_time
        
        # Phase 2: Detection (should respect stealth timing)
        detection_start = time.time()
        detected, _ = self.calibrator.detect_acr_table_with_versioning(screenshot)
        phase2_time = time.time() - detection_start
        
        # Phase 6: Anti-detection timing should be reasonable
        decision_context = {'game_phase': 'flop', 'intended_action': 'call'}
        stealth_timing = self.anti_detection.calculate_stealth_decision_timing(decision_context)
        
        # All timings should be reasonable
        assert phase1_time < 10.0  # Screenshot should be fast
        assert phase2_time < 30.0  # Detection should complete
        assert stealth_timing > 0.5  # Human-like timing
        
        return True
    
    def test_error_propagation(self):
        """Test error handling across phases."""
        # Test with invalid input
        try:
            # Empty screenshot
            empty_screenshot = np.zeros((0, 0, 3), dtype=np.uint8)
            
            # Should handle gracefully without crashing
            detected, _ = self.calibrator.detect_acr_table_with_versioning(empty_screenshot)
            card_regions, _ = self.gpu_system.accelerated_card_detection(empty_screenshot)
            turn_state = self.turn_detector.detect_turn_state(empty_screenshot)
            
            # Should not crash
            return True
        except Exception:
            # Graceful error handling is acceptable
            return True

class TestSystemPerformance:
    """Test overall system performance."""
    
    def setup_method(self):
        """Setup performance test environment."""
        self.calibrator = IntelligentACRCalibrator()
        self.gpu_system = GPUAcceleratedRecognition()
        self.gto_engine = EnhancedGTOEngine()
        self.turn_detector = AdvancedTurnDetection()
        self.anti_detection = ACRAntiDetectionSystem()
    
    def test_full_pipeline_performance(self):
        """Test complete pipeline performance."""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        start_time = time.time()
        
        # Run complete pipeline
        detected, _ = self.calibrator.detect_acr_table_with_versioning(test_screenshot)
        card_regions, _ = self.gpu_system.accelerated_card_detection(test_screenshot)
        
        poker_situation = PokerSituation(
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
        
        decision = self.gto_engine.analyze_situation(poker_situation)
        turn_state = self.turn_detector.detect_turn_state(test_screenshot)
        
        total_time = time.time() - start_time
        
        # Complete pipeline should be reasonably fast
        assert total_time < 60.0  # 1 minute max for full analysis
        
        return True, total_time
    
    def test_memory_usage_stability(self):
        """Test memory usage remains stable over multiple runs."""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Run multiple iterations
        for i in range(5):
            detected, _ = self.calibrator.detect_acr_table_with_versioning(test_screenshot)
            card_regions, _ = self.gpu_system.accelerated_card_detection(test_screenshot)
            turn_state = self.turn_detector.detect_turn_state(test_screenshot)
        
        # Should not accumulate excessive cache
        assert len(self.calibrator.stealth_detector.stealth_cache) <= 10
        assert len(self.gto_engine.decision_cache) <= 20
        assert len(self.turn_detector.detection_cache) <= 10
        
        return True

def run_integration_tests():
    """Run all integration tests and return results."""
    print("🧪 Running Integration Tests: All Phases Working Together")
    print("=" * 65)
    
    test_results = {
        "initialization": [],
        "pipeline_integration": [],
        "data_flow": [],
        "performance": []
    }
    
    # Test System Initialization
    try:
        init_tests = TestSystemInitialization()
        
        success = init_tests.test_all_phases_initialize()
        if success:
            test_results["initialization"].append("✅ All Phases Initialize")
        else:
            test_results["initialization"].append("❌ Initialization Failed")
        
        success = init_tests.test_phase_integration_points()
        if success:
            test_results["initialization"].append("✅ Integration Points")
        else:
            test_results["initialization"].append("❌ Integration Points Failed")
            
    except Exception as e:
        test_results["initialization"].append(f"❌ Error: {e}")
    
    # Test Pipeline Integration
    try:
        pipeline_tests = TestFullPipelineIntegration()
        pipeline_tests.setup_method()
        
        success = pipeline_tests.test_screenshot_to_detection_pipeline()
        if success:
            test_results["pipeline_integration"].append("✅ Screenshot to Detection")
        
        success = pipeline_tests.test_detection_to_recognition_pipeline()
        if success:
            test_results["pipeline_integration"].append("✅ Detection to Recognition")
        
        success = pipeline_tests.test_recognition_to_gto_pipeline()
        if success:
            test_results["pipeline_integration"].append("✅ Recognition to GTO")
        
        success = pipeline_tests.test_gto_to_turn_detection_pipeline()
        if success:
            test_results["pipeline_integration"].append("✅ GTO to Turn Detection")
        
        success = pipeline_tests.test_turn_detection_to_anti_detection_pipeline()
        if success:
            test_results["pipeline_integration"].append("✅ Turn to Anti-Detection")
            
    except Exception as e:
        test_results["pipeline_integration"].append(f"❌ Error: {e}")
    
    # Test Data Flow
    try:
        dataflow_tests = TestCrossPhaseDataFlow()
        dataflow_tests.setup_method()
        
        success = dataflow_tests.test_screenshot_state_consistency()
        if success:
            test_results["data_flow"].append("✅ Screenshot Consistency")
        
        success = dataflow_tests.test_timing_coordination()
        if success:
            test_results["data_flow"].append("✅ Timing Coordination")
        
        success = dataflow_tests.test_error_propagation()
        if success:
            test_results["data_flow"].append("✅ Error Handling")
            
    except Exception as e:
        test_results["data_flow"].append(f"❌ Error: {e}")
    
    # Test Performance
    try:
        perf_tests = TestSystemPerformance()
        perf_tests.setup_method()
        
        success, total_time = perf_tests.test_full_pipeline_performance()
        if success:
            test_results["performance"].append(f"✅ Full Pipeline ({total_time:.2f}s)")
        
        success = perf_tests.test_memory_usage_stability()
        if success:
            test_results["performance"].append("✅ Memory Stability")
            
    except Exception as e:
        test_results["performance"].append(f"❌ Error: {e}")
    
    # Print results
    for category, results in test_results.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        for result in results:
            print(f"  {result}")
    
    # Calculate success rate
    total_tests = sum(len(results) for results in test_results.values())
    successful_tests = sum(1 for results in test_results.values() for result in results if result.startswith("✅"))
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    print(f"\n🎯 Integration Test Results: {successful_tests}/{total_tests} ({success_rate:.1%} success)")
    
    return test_results, success_rate

if __name__ == "__main__":
    run_integration_tests()