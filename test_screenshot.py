#!/usr/bin/env python3
"""
Test screenshot capture to verify resolution and detect ACR table.
"""

import cv2
import numpy as np
from PIL import ImageGrab

def test_screenshot_capture():
    """Test actual screenshot capture resolution."""
    try:
        print("Testing screenshot capture...")
        
        # Capture using PIL (same method as the system)
        screenshot = ImageGrab.grab()
        screenshot_np = np.array(screenshot)
        bgr_image = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        height, width = bgr_image.shape[:2]
        print(f"Screenshot resolution: {width}x{height}")
        
        # Save for inspection
        cv2.imwrite("test_screenshot.png", bgr_image)
        print("Screenshot saved as: test_screenshot.png")
        
        # Quick green analysis
        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        green_lower = np.array([30, 30, 30])
        green_upper = np.array([90, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        green_area = np.sum(green_mask > 0)
        total_area = width * height
        green_percentage = (green_area / total_area) * 100
        
        print(f"Green area detected: {green_percentage:.1f}%")
        
        if green_percentage > 2:
            print("Green area found - likely has poker table!")
        else:
            print("No significant green area - check if ACR table is visible")
            
        return {
            "resolution": f"{width}x{height}",
            "green_percentage": green_percentage,
            "file_saved": "test_screenshot.png"
        }
        
    except Exception as e:
        print(f"Screenshot test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = test_screenshot_capture()
    print(f"Result: {result}")