"""
Phase 2 Testing Suite: Advanced ACR Stealth Detection
Comprehensive testing of stealth detection and hierarchical analysis.
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch

from app.scraper.acr_stealth_detection import ACRStealthDetection, StealthMetrics

class TestACRStealthDetection:
    """Test ACR stealth detection functionality."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance for testing."""
        return ACRStealthDetection()
    
    def test_detector_initialization(self, detector):
        """Test detector initializes correctly."""
        assert detector.action_delay_range == (0.8, 2.5)
        assert detector.mouse_jitter == 3
        assert isinstance(detector.acr_ui_signatures, dict)
        assert isinstance(detector.hierarchical_detectors, dict)
        assert len(detector.hierarchical_detectors) == 3
    
    def test_acr_ui_signatures_loaded(self, detector):
        """Test ACR UI signatures are properly loaded."""
        signatures = detector.acr_ui_signatures
        
        assert "table_felt_colors" in signatures
        assert "ui_elements" in signatures
        assert "text_patterns" in signatures
        
        # Check table felt colors
        felt_colors = signatures["table_felt_colors"]
        assert "standard_green" in felt_colors
        assert "blue_variant" in felt_colors
        assert "dark_theme" in felt_colors
        
        # Check UI elements
        ui_elements = signatures["ui_elements"]
        assert "action_buttons" in ui_elements
        assert "card_regions" in ui_elements
        assert "player_seats" in ui_elements
    
    def test_hierarchical_detectors_structure(self, detector):
        """Test hierarchical detectors are properly structured."""
        detectors = detector.hierarchical_detectors
        
        # Check all levels exist
        assert "level_1_fast" in detectors
        assert "level_2_moderate" in detectors
        assert "level_3_deep" in detectors
        
        # Check timing budgets
        assert detectors["level_1_fast"]["timing"] == 0.1
        assert detectors["level_2_moderate"]["timing"] == 0.5
        assert detectors["level_3_deep"]["timing"] == 2.0
        
        # Check detector functions exist
        level1 = detectors["level_1_fast"]
        assert "green_detection" in level1
        assert "basic_shapes" in level1
    
    def test_human_behavior_delay(self, detector):
        """Test human behavior delay generation."""
        # Test multiple delays
        delays = []
        for _ in range(10):
            delay = detector.human_behavior_delay()
            delays.append(delay)
            assert 0.5 <= delay <= 5.0  # Reasonable range
        
        # Should have variance
        assert max(delays) - min(delays) > 0.5

class TestStealthDetectionMethods:
    """Test individual stealth detection methods."""
    
    @pytest.fixture
    def detector(self):
        return ACRStealthDetection()
    
    def test_fast_green_detection(self, detector):
        """Test fast green table detection."""
        # Create test image with green poker table
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Add green regions to simulate poker table
        test_image[200:400, 300:500, 1] = 120  # Green channel
        test_image[200:400, 300:500, 0] = 60   # Red channel
        test_image[200:400, 300:500, 2] = 60   # Blue channel
        
        result = detector._fast_green_detection(test_image)
        
        assert "confidence" in result
        assert "green_percentage" in result
        assert "method" in result
        assert result["method"] == "fast_sampling"
        assert 0 <= result["confidence"] <= 1.0
        assert result["green_percentage"] >= 0
    
    def test_basic_shapes_detection(self, detector):
        """Test basic shapes detection."""
        # Create test image with rectangular shapes
        test_image = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # Add some rectangular regions (simulating cards/buttons)
        test_image[100:150, 200:300] = 255  # Rectangle 1
        test_image[200:250, 400:500] = 255  # Rectangle 2
        test_image[300:350, 600:700] = 255  # Rectangle 3
        
        result = detector._detect_basic_shapes(test_image)
        
        assert "confidence" in result
        assert "rectangles" in result
        assert "circles" in result
        assert result["rectangles"] >= 0
        assert result["circles"] >= 0
        assert 0 <= result["confidence"] <= 1.0
    
    def test_ui_elements_detection(self, detector):
        """Test UI elements detection."""
        # Create test image with button-like regions
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Add button-like regions
        test_image[500:530, 600:750] = [100, 140, 220]  # Blue button
        test_image[500:530, 760:910] = [100, 140, 220]  # Another blue button
        
        result = detector._detect_ui_elements(test_image)
        
        assert "action_buttons" in result
        assert "card_regions" in result
        assert "text_elements" in result
        assert "confidence" in result
        assert result["action_buttons"] >= 0
        assert result["card_regions"] >= 0
        assert 0 <= result["confidence"] <= 1.0

class TestAdaptiveTableDetection:
    """Test adaptive table detection functionality."""
    
    @pytest.fixture
    def detector(self):
        return ACRStealthDetection()
    
    def test_adaptive_detection_basic(self, detector):
        """Test basic adaptive detection functionality."""
        # Create test screenshot
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Add poker table elements
        test_screenshot[200:400, 300:500, 1] = 100  # Green felt
        test_screenshot[500:530, 600:750] = [100, 140, 220]  # Action buttons
        
        detected, result = detector.adaptive_table_detection(test_screenshot)
        
        assert isinstance(detected, bool)
        assert isinstance(result, dict)
        
        # Check result structure
        assert "detected" in result
        assert "confidence" in result
        assert "stealth_metrics" in result
        assert "detection_layers" in result
        assert "ui_version_hash" in result
        
        # Check stealth metrics
        metrics = result["stealth_metrics"]
        assert isinstance(metrics, StealthMetrics)
        assert 0 <= metrics.detection_confidence <= 1.0
        assert 0 <= metrics.human_behavior_score <= 1.0
    
    def test_ui_hash_computation(self, detector):
        """Test UI version hash computation."""
        test_image1 = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        test_image2 = test_image1.copy()
        test_image3 = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        hash1 = detector._compute_ui_hash(test_image1)
        hash2 = detector._compute_ui_hash(test_image2)
        hash3 = detector._compute_ui_hash(test_image3)
        
        # Same images should produce same hash
        assert hash1 == hash2
        
        # Different images should produce different hashes
        assert hash1 != hash3
        
        # Hash should be reasonable length
        assert len(hash1) == 12
    
    def test_detection_caching(self, detector):
        """Test detection result caching."""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Clear cache
        detector.stealth_cache.clear()
        
        # First detection
        start_time = time.time()
        detected1, result1 = detector.adaptive_table_detection(test_screenshot)
        first_time = time.time() - start_time
        
        # Second detection (should use cache)
        start_time = time.time()
        detected2, result2 = detector.adaptive_table_detection(test_screenshot)
        second_time = time.time() - start_time
        
        # Results should be the same
        assert detected1 == detected2
        assert result1["confidence"] == result2["confidence"]
        
        # Second call should be faster (cached)
        assert second_time < first_time or second_time < 0.01

class TestStealthMetrics:
    """Test stealth metrics calculation."""
    
    @pytest.fixture
    def detector(self):
        return ACRStealthDetection()
    
    def test_stealth_metrics_structure(self, detector):
        """Test stealth metrics have correct structure."""
        # Create mock detection layers
        layers = {
            "level_1": {"confidence": 0.8, "execution_time": 0.1},
            "level_2": {"confidence": 0.9, "execution_time": 0.3}
        }
        
        metrics = detector._calculate_stealth_metrics(0.5, layers)
        
        assert isinstance(metrics, StealthMetrics)
        assert hasattr(metrics, 'detection_confidence')
        assert hasattr(metrics, 'human_behavior_score')
        assert hasattr(metrics, 'timing_variation')
        assert hasattr(metrics, 'anti_pattern_success')
        assert hasattr(metrics, 'ui_adaptation_score')
        
        # Check ranges
        assert 0 <= metrics.detection_confidence <= 1.0
        assert 0 <= metrics.human_behavior_score <= 1.0
        assert 0 <= metrics.timing_variation <= 2.0
        assert 0 <= metrics.anti_pattern_success <= 1.0
        assert 0 <= metrics.ui_adaptation_score <= 1.0

class TestPhase2Performance:
    """Test Phase 2 performance characteristics."""
    
    @pytest.fixture
    def detector(self):
        return ACRStealthDetection()
    
    def test_detection_speed(self, detector):
        """Test detection completes within time budgets."""
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        start_time = time.time()
        detected, result = detector.adaptive_table_detection(test_screenshot)
        detection_time = time.time() - start_time
        
        # Should complete within reasonable time (< 3s for all levels)
        assert detection_time < 3.0
        
        # Check individual level timings if available
        if "detection_layers" in result:
            layers = result["detection_layers"]
            
            if "level_1" in layers:
                assert layers["level_1"]["execution_time"] < 0.2  # 200ms tolerance
            
            if "level_2" in layers:
                assert layers["level_2"]["execution_time"] < 1.0  # 1s tolerance
    
    def test_memory_usage(self, detector):
        """Test memory usage is reasonable."""
        # Perform multiple detections
        for _ in range(10):
            test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
            detector.adaptive_table_detection(test_screenshot)
        
        # Cache should not grow excessively
        assert len(detector.stealth_cache) <= 20  # Reasonable cache size

def run_phase2_tests():
    """Run all Phase 2 tests and return results."""
    print("🧪 Running Phase 2 Tests: Advanced ACR Stealth Detection")
    print("=" * 60)
    
    test_results = {
        "stealth_detection": [],
        "detection_methods": [],
        "adaptive_detection": [],
        "metrics": [],
        "performance": []
    }
    
    # Test Stealth Detection
    try:
        detector = ACRStealthDetection()
        
        # Test initialization
        assert len(detector.hierarchical_detectors) == 3
        test_results["stealth_detection"].append("✅ Initialization")
        
        # Test UI signatures
        assert "table_felt_colors" in detector.acr_ui_signatures
        test_results["stealth_detection"].append("✅ UI Signatures")
        
        # Test human behavior delay
        delay = detector.human_behavior_delay()
        assert 0.5 <= delay <= 5.0
        test_results["stealth_detection"].append("✅ Human Behavior Simulation")
        
    except Exception as e:
        test_results["stealth_detection"].append(f"❌ Error: {e}")
    
    # Test Detection Methods
    try:
        detector = ACRStealthDetection()
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Test green detection
        result = detector._fast_green_detection(test_image)
        assert "confidence" in result
        test_results["detection_methods"].append("✅ Green Detection")
        
        # Test shapes detection
        result = detector._detect_basic_shapes(test_image)
        assert "confidence" in result
        test_results["detection_methods"].append("✅ Shapes Detection")
        
        # Test UI elements detection
        result = detector._detect_ui_elements(test_image)
        assert "confidence" in result
        test_results["detection_methods"].append("✅ UI Elements Detection")
        
    except Exception as e:
        test_results["detection_methods"].append(f"❌ Error: {e}")
    
    # Test Adaptive Detection
    try:
        detector = ACRStealthDetection()
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Test adaptive detection
        detected, result = detector.adaptive_table_detection(test_screenshot)
        assert isinstance(detected, bool)
        assert "confidence" in result
        test_results["adaptive_detection"].append("✅ Adaptive Detection")
        
        # Test UI hash computation
        ui_hash = detector._compute_ui_hash(test_screenshot)
        assert len(ui_hash) == 12
        test_results["adaptive_detection"].append("✅ UI Hash Computation")
        
        # Test caching
        detector.stealth_cache.clear()
        detector.adaptive_table_detection(test_screenshot)
        assert len(detector.stealth_cache) == 1
        test_results["adaptive_detection"].append("✅ Detection Caching")
        
    except Exception as e:
        test_results["adaptive_detection"].append(f"❌ Error: {e}")
    
    # Test Metrics
    try:
        detector = ACRStealthDetection()
        
        # Test metrics calculation
        layers = {"level_1": {"confidence": 0.8, "execution_time": 0.1}}
        metrics = detector._calculate_stealth_metrics(0.5, layers)
        assert isinstance(metrics, StealthMetrics)
        test_results["metrics"].append("✅ Stealth Metrics")
        
    except Exception as e:
        test_results["metrics"].append(f"❌ Error: {e}")
    
    # Test Performance
    try:
        detector = ACRStealthDetection()
        test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        
        # Test detection speed
        start_time = time.time()
        detector.adaptive_table_detection(test_screenshot)
        detection_time = time.time() - start_time
        assert detection_time < 3.0
        test_results["performance"].append("✅ Detection Speed")
        
        # Test memory usage
        for _ in range(5):
            detector.adaptive_table_detection(test_screenshot)
        assert len(detector.stealth_cache) <= 10
        test_results["performance"].append("✅ Memory Usage")
        
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
    
    print(f"\n🎯 Phase 2 Test Results: {successful_tests}/{total_tests} ({success_rate:.1%} success)")
    
    return test_results, success_rate

if __name__ == "__main__":
    run_phase2_tests()