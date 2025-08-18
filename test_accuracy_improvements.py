# Cross-platform test script
"""
Test the improved ACR calibration accuracy with realistic scenarios.
This script verifies the enhanced accuracy calculations and region detection.
"""

import sys
import time
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
from app.scraper.acr_scraper import TableRegion
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_improved_accuracy():
    """Test the improved accuracy calculation system."""
    print("🎯 Testing Improved ACR Calibration Accuracy")
    print("=" * 50)
    
    # Initialize calibrator
    calibrator = IntelligentACRCalibrator()
    
    # Test 1: Mock regions with realistic ACR table layout
    print("\n📋 Test 1: Realistic ACR Table Regions")
    mock_regions = {
        "card_region_0": TableRegion(x=500, y=600, width=50, height=70, confidence=0.7, element_type="card"),
        "card_region_1": TableRegion(x=560, y=600, width=50, height=70, confidence=0.7, element_type="card"),
        "button_0": TableRegion(x=800, y=650, width=80, height=30, confidence=0.6, element_type="button"),
        "button_1": TableRegion(x=890, y=650, width=80, height=30, confidence=0.6, element_type="button"),
        "circular_0": TableRegion(x=650, y=400, width=30, height=30, confidence=0.5, element_type="circular"),
    }
    
    # Create mock screenshot
    mock_screenshot = np.zeros((800, 1200, 3), dtype=np.uint8)
    
    # Test validation
    validation_results = calibrator.validate_regions(mock_screenshot, mock_regions)
    accuracy = calibrator.calculate_accuracy_score(validation_results)
    
    print(f"Regions created: {len(mock_regions)}")
    print(f"Validation results: {validation_results}")
    print(f"Calculated accuracy: {accuracy:.1%}")
    
    # Analyze what passed/failed
    passed_tests = [test for test, result in validation_results.items() if result]
    failed_tests = [test for test, result in validation_results.items() if not result]
    
    print(f"✅ Passed tests ({len(passed_tests)}): {passed_tests}")
    print(f"❌ Failed tests ({len(failed_tests)}): {failed_tests}")
    
    # Test 2: Auto-calibration with fallback regions
    print("\n📋 Test 2: Auto-Calibration with Fallbacks")
    try:
        result = calibrator.auto_calibrate_table()
        print(f"Auto-calibration success: {result.table_detected}")
        print(f"Accuracy score: {result.accuracy_score:.1%}")
        print(f"Regions found: {len(result.regions)}")
        print(f"Success rate: {result.success_rate:.1%}")
        
        if result.regions:
            print("\nDetected regions:")
            for name, region in list(result.regions.items())[:5]:  # Show first 5
                print(f"  {name}: {region.element_type} at ({region.x}, {region.y}) conf={region.confidence:.2f}")
        
        # Expected results
        expected_accuracy = 0.6  # 60% target with improved validation
        if result.accuracy_score >= expected_accuracy:
            print(f"🎉 SUCCESS: Accuracy {result.accuracy_score:.1%} meets {expected_accuracy:.1%} target!")
        else:
            print(f"⚠️  PARTIAL: Accuracy {result.accuracy_score:.1%} below {expected_accuracy:.1%} target")
            
    except Exception as e:
        print(f"❌ Auto-calibration failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Different confidence thresholds
    print("\n📋 Test 3: Confidence Threshold Testing")
    confidence_levels = [0.3, 0.5, 0.7, 0.9]
    
    for conf in confidence_levels:
        test_regions = {
            f"test_region_{i}": TableRegion(
                x=100+i*50, y=100, width=40, height=60, 
                confidence=conf, element_type="card"
            ) for i in range(4)
        }
        
        validation = calibrator.validate_regions(mock_screenshot, test_regions)
        accuracy = calibrator.calculate_accuracy_score(validation)
        print(f"Confidence {conf:.1f}: {len(test_regions)} regions → {accuracy:.1%} accuracy")
    
    print("\n🎯 Test Summary:")
    print("The improved system should now achieve:")
    print("• 60%+ accuracy with realistic ACR table detection")
    print("• Proper fallback region generation when no features detected")
    print("• More lenient validation criteria matching real ACR layouts")
    print("• Better confidence threshold handling")

if __name__ == "__main__":
    test_improved_accuracy()