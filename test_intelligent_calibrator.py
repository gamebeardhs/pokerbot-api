#!/usr/bin/env python3
"""
Test the intelligent ACR calibration system.
"""

from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
import cv2
import numpy as np

def test_intelligent_calibration():
    """Test the intelligent calibration system."""
    print("Testing Intelligent ACR Calibration System")
    print("=" * 60)
    
    # Initialize calibrator
    calibrator = IntelligentACRCalibrator()
    
    print(f"Templates loaded: {len(calibrator.templates)}")
    print(f"Minimum accuracy target: {calibrator.min_accuracy:.1%}")
    
    # Test table detection
    print("\n1. Testing table detection...")
    table_detected, table_info = calibrator.detect_acr_table()
    
    print(f"Table detected: {table_detected}")
    print(f"Detection confidence: {table_info.get('confidence', 0):.1%}")
    print(f"Features found:")
    features = table_info.get('features', {})
    for feature_type, items in features.items():
        print(f"  - {feature_type}: {len(items) if isinstance(items, list) else items}")
    
    if table_detected:
        print("\n2. Running auto-calibration...")
        result = calibrator.auto_calibrate_table()
        
        print(f"Auto-calibration results:")
        print(f"  - Success rate: {result.success_rate:.1%}")
        print(f"  - Accuracy score: {result.accuracy_score:.1%}")
        print(f"  - Regions found: {len(result.regions)}")
        print(f"  - Table detected: {result.table_detected}")
        
        print(f"\nValidation tests:")
        for test, passed in result.validation_tests.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {test}")
        
        if result.success_rate >= 0.95:
            print(f"\n🎯 SUCCESS: Auto-calibration achieved {result.success_rate:.1%} accuracy!")
            
            print(f"\nDetected regions:")
            for name, region in result.regions.items():
                print(f"  - {name}: ({region.x}, {region.y}) {region.width}x{region.height} [{region.confidence:.1%}]")
        else:
            print(f"\n⚠️ Auto-calibration below target: {result.success_rate:.1%} < 95%")
            print("Recommendations:")
            print("- Ensure ACR poker client is open and visible")
            print("- Make sure a poker table is active (not lobby)")
            print("- Check that table is not minimized")
    else:
        print("\n❌ No ACR table detected")
        print("Please open ACR poker client with an active table")
    
    return table_detected

if __name__ == "__main__":
    test_intelligent_calibration()