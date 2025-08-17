#!/usr/bin/env python3
"""
Direct test of ACR detection using the main system's capture method.
"""

import sys
sys.path.append('.')
from app.scraper.intelligent_calibrator import IntelligentACRCalibrator

def test_acr_detection():
    """Test ACR detection directly through the system."""
    try:
        print("Testing ACR detection with main system...")
        
        # Initialize the calibrator
        calibrator = IntelligentACRCalibrator()
        
        # Capture screenshot using the same method as the system
        screenshot = calibrator.capture_screen()
        height, width = screenshot.shape[:2]
        
        print(f"Main system screenshot: {width}x{height}")
        
        # Test detection
        table_detected, table_info = calibrator.detect_acr_table(screenshot)
        
        print(f"Table detected: {table_detected}")
        print(f"Detection confidence: {table_info.get('confidence', 0):.3f}")
        print(f"Screenshot shape: {table_info.get('screenshot_shape', 'unknown')}")
        
        # Check features
        features = table_info.get('features', {})
        print(f"Card regions found: {len(features.get('card_regions', []))}")
        print(f"Buttons found: {len(features.get('buttons', []))}")
        
        # Check indicators
        indicators = table_info.get('indicators', {})
        print(f"Table felt detected: {indicators.get('table_felt', False)}")
        
        return {
            "table_detected": table_detected,
            "confidence": table_info.get('confidence', 0),
            "resolution": f"{width}x{height}",
            "features": {k: len(v) if isinstance(v, list) else v for k, v in features.items()},
            "indicators": indicators
        }
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    result = test_acr_detection()
    print(f"\nTest Result: {result}")