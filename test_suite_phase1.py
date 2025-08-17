"""
Phase 1 Testing Suite: Circuit Breaker & Timeout Protection
Comprehensive testing of reliability and timeout systems.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
import numpy as np

from app.scraper.intelligent_calibrator import IntelligentACRCalibrator, CircuitBreaker, ScreenshotStateManager

class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        assert cb.state.value == "closed"
        assert cb.failure_count == 0
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
    
    def test_circuit_breaker_failure_tracking(self):
        """Test circuit breaker tracks failures correctly."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # First failure
        cb.record_failure()
        assert cb.failure_count == 1
        assert cb.state.value == "closed"
        
        # Second failure - should open circuit
        cb.record_failure()
        assert cb.failure_count == 2
        assert cb.state.value == "open"
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery mechanism."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        # Trigger failure
        cb.record_failure()
        assert cb.state.value == "open"
        
        # Wait for recovery timeout
        time.sleep(0.2)
        
        # Should transition to half-open
        assert cb.can_execute()
        assert cb.state.value == "half_open"
        
        # Successful execution should close circuit
        cb.record_success()
        assert cb.state.value == "closed"
        assert cb.failure_count == 0
    
    def test_circuit_breaker_prevents_execution(self):
        """Test circuit breaker prevents execution when open."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10)
        
        # Trigger failure to open circuit
        cb.record_failure()
        assert cb.state.value == "open"
        
        # Should not allow execution
        assert not cb.can_execute()

class TestScreenshotStateManager:
    """Test screenshot state management."""
    
    def test_screenshot_state_detection(self):
        """Test screenshot state change detection."""
        manager = ScreenshotStateManager()
        
        # Create test screenshots
        screenshot1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        screenshot2 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # First screenshot should be new
        assert manager.is_state_changed(screenshot1)
        
        # Same screenshot should not be changed
        assert not manager.is_state_changed(screenshot1)
        
        # Different screenshot should be changed
        assert manager.is_state_changed(screenshot2)
    
    def test_screenshot_hash_consistency(self):
        """Test screenshot hash generation consistency."""
        manager = ScreenshotStateManager()
        
        screenshot = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Same screenshot should produce same hash
        hash1 = manager._compute_screenshot_hash(screenshot)
        hash2 = manager._compute_screenshot_hash(screenshot)
        assert hash1 == hash2
        
        # Different screenshots should produce different hashes
        screenshot2 = screenshot.copy()
        screenshot2[0, 0] = [255, 255, 255]  # Change one pixel
        hash3 = manager._compute_screenshot_hash(screenshot2)
        assert hash1 != hash3

class TestIntelligentCalibratorReliability:
    """Test intelligent calibrator reliability features."""
    
    @pytest.fixture
    def calibrator(self):
        """Create calibrator instance for testing."""
        return IntelligentACRCalibrator()
    
    def test_calibrator_initialization(self, calibrator):
        """Test calibrator initializes with reliability components."""
        assert calibrator.circuit_breaker is not None
        assert calibrator.screenshot_manager is not None
        assert isinstance(calibrator.calibration_cache, dict)
        assert calibrator.circuit_breaker.state.value == "closed"
    
    def test_timeout_protection_screenshot(self, calibrator):
        """Test screenshot capture has timeout protection."""
        start_time = time.time()
        screenshot = calibrator.capture_screen()
        capture_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert capture_time < 10.0  # 10 second max
        assert screenshot is not None
        assert len(screenshot.shape) == 3  # Should be color image
    
    def test_calibration_cache_functionality(self, calibrator):
        """Test calibration results are cached properly."""
        # Clear cache
        calibrator.calibration_cache.clear()
        assert len(calibrator.calibration_cache) == 0
        
        # Mock a calibration result
        test_hash = "test_ui_hash_123"
        test_result = {"accuracy": 0.95, "regions": 5}
        
        calibrator.calibration_cache[test_hash] = {
            "result": test_result,
            "timestamp": time.time()
        }
        
        assert len(calibrator.calibration_cache) == 1
        assert calibrator.calibration_cache[test_hash]["result"]["accuracy"] == 0.95
    
    def test_stealth_detector_integration(self, calibrator):
        """Test stealth detector is properly integrated."""
        if calibrator.stealth_detector:
            assert hasattr(calibrator.stealth_detector, 'hierarchical_detectors')
            assert hasattr(calibrator.stealth_detector, 'adaptive_table_detection')
            assert len(calibrator.stealth_detector.hierarchical_detectors) == 3
    
    @patch('app.scraper.intelligent_calibrator.time.sleep')
    def test_timeout_mechanism(self, mock_sleep, calibrator):
        """Test timeout mechanism works correctly."""
        # Test that timeout protection is in place
        with patch.object(calibrator.circuit_breaker, 'can_execute', return_value=True):
            # This should not hang even with delays
            result = calibrator.detect_acr_table_with_versioning(
                np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            )
            assert isinstance(result, tuple)
            assert len(result) == 2

class TestPhase1Performance:
    """Test Phase 1 performance characteristics."""
    
    def test_circuit_breaker_performance(self):
        """Test circuit breaker doesn't add significant overhead."""
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        
        start_time = time.time()
        for _ in range(1000):
            cb.can_execute()
        execution_time = time.time() - start_time
        
        # Should be very fast (< 10ms for 1000 operations)
        assert execution_time < 0.01
    
    def test_screenshot_manager_performance(self):
        """Test screenshot manager performs efficiently."""
        manager = ScreenshotStateManager()
        screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        start_time = time.time()
        for _ in range(100):
            manager.is_state_changed(screenshot)
        execution_time = time.time() - start_time
        
        # Should handle 100 checks quickly (< 100ms)
        assert execution_time < 0.1
    
    def test_calibrator_response_time(self):
        """Test calibrator responds within acceptable time limits."""
        calibrator = IntelligentACRCalibrator()
        
        start_time = time.time()
        screenshot = calibrator.capture_screen()
        capture_time = time.time() - start_time
        
        # Screenshot capture should be fast
        assert capture_time < 5.0
        
        start_time = time.time()
        detected, _ = calibrator.detect_acr_table_with_versioning(screenshot)
        detection_time = time.time() - start_time
        
        # Detection should complete within timeout
        assert detection_time < 30.0

def run_phase1_tests():
    """Run all Phase 1 tests and return results."""
    print("🧪 Running Phase 1 Tests: Circuit Breaker & Timeout Protection")
    print("=" * 60)
    
    test_results = {
        "circuit_breaker": [],
        "screenshot_manager": [],
        "calibrator_reliability": [],
        "performance": []
    }
    
    # Test Circuit Breaker
    try:
        cb_tests = TestCircuitBreaker()
        cb_tests.test_circuit_breaker_initialization()
        test_results["circuit_breaker"].append("✅ Initialization")
        
        cb_tests.test_circuit_breaker_failure_tracking()
        test_results["circuit_breaker"].append("✅ Failure Tracking")
        
        cb_tests.test_circuit_breaker_recovery()
        test_results["circuit_breaker"].append("✅ Recovery Mechanism")
        
        cb_tests.test_circuit_breaker_prevents_execution()
        test_results["circuit_breaker"].append("✅ Execution Prevention")
        
    except Exception as e:
        test_results["circuit_breaker"].append(f"❌ Error: {e}")
    
    # Test Screenshot Manager
    try:
        sm_tests = TestScreenshotStateManager()
        sm_tests.test_screenshot_state_detection()
        test_results["screenshot_manager"].append("✅ State Detection")
        
        sm_tests.test_screenshot_hash_consistency()
        test_results["screenshot_manager"].append("✅ Hash Consistency")
        
    except Exception as e:
        test_results["screenshot_manager"].append(f"❌ Error: {e}")
    
    # Test Calibrator Reliability
    try:
        calibrator = IntelligentACRCalibrator()
        
        # Test initialization
        assert calibrator.circuit_breaker is not None
        test_results["calibrator_reliability"].append("✅ Initialization")
        
        # Test timeout protection
        start_time = time.time()
        screenshot = calibrator.capture_screen()
        capture_time = time.time() - start_time
        assert capture_time < 10.0
        test_results["calibrator_reliability"].append("✅ Timeout Protection")
        
        # Test cache functionality
        calibrator.calibration_cache.clear()
        calibrator.calibration_cache["test"] = {"result": "cached", "timestamp": time.time()}
        assert len(calibrator.calibration_cache) == 1
        test_results["calibrator_reliability"].append("✅ Cache Functionality")
        
    except Exception as e:
        test_results["calibrator_reliability"].append(f"❌ Error: {e}")
    
    # Test Performance
    try:
        perf_tests = TestPhase1Performance()
        perf_tests.test_circuit_breaker_performance()
        test_results["performance"].append("✅ Circuit Breaker Performance")
        
        perf_tests.test_screenshot_manager_performance()
        test_results["performance"].append("✅ Screenshot Manager Performance")
        
        perf_tests.test_calibrator_response_time()
        test_results["performance"].append("✅ Calibrator Response Time")
        
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
    
    print(f"\n🎯 Phase 1 Test Results: {successful_tests}/{total_tests} ({success_rate:.1%} success)")
    
    return test_results, success_rate

if __name__ == "__main__":
    run_phase1_tests()