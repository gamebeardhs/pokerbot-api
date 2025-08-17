#!/usr/bin/env python3
"""
Debug script to help diagnose ACR table detection issues.
"""

import cv2
import numpy as np
from PIL import ImageGrab
import json
from pathlib import Path

def debug_screen_capture():
    """Debug screen capture and ACR detection."""
    print("Debugging ACR Table Detection (Multi-Monitor)")
    print("=" * 60)
    
    try:
        # Capture full screen
        print("Capturing screenshot...")
        screenshot = ImageGrab.grab()
        screenshot_np = np.array(screenshot)
        bgr_image = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        width, height = bgr_image.shape[1], bgr_image.shape[0]
        print(f"Screenshot captured: {width}x{height} pixels")
        
        # Detect multi-monitor setup
        if width > 2000:  # Likely multi-monitor
            estimated_monitors = width // 1920 if width % 1920 < 500 else (width // 1920) + 1
            print(f"Multi-monitor detected: ~{estimated_monitors} monitors ({width/estimated_monitors:.0f}x{height} each)")
        else:
            print(f"Single monitor setup: {width}x{height}")
        
        # Save debug screenshot
        debug_path = "debug_screenshot.png"
        cv2.imwrite(debug_path, bgr_image)
        print(f"Debug screenshot saved: {debug_path}")
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        
        # Look for green colors (poker table felt)
        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        green_area = np.sum(green_mask > 0)
        total_area = gray.shape[0] * gray.shape[1]
        green_percentage = (green_area / total_area) * 100
        
        print(f"Green area analysis: {green_percentage:.1f}% of screen")
        
        if green_percentage > 5:
            print("Significant green area detected - likely poker table")
        else:
            print("No significant green area - ACR table may not be visible")
        
        # Look for rectangular shapes (cards, buttons)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangles = []
        card_candidates = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check for card-like rectangles (ACR cards ~57x82)
            if 30 < w < 120 and 40 < h < 160:
                ratio = w / h
                expected_ratio = 57/82
                if abs(ratio - expected_ratio) < 0.15:
                    card_candidates.append((x, y, w, h, ratio))
            
            # Check for button-like rectangles
            if 80 < w < 200 and 25 < h < 60:
                rectangles.append((x, y, w, h))
        
        print(f"Card-like regions found: {len(card_candidates)}")
        print(f"Button-like regions found: {len(rectangles)}")
        
        # Create annotated image
        debug_annotated = bgr_image.copy()
        
        # Draw green mask overlay
        green_overlay = cv2.bitwise_and(debug_annotated, debug_annotated, mask=green_mask)
        debug_annotated = cv2.addWeighted(debug_annotated, 0.8, green_overlay, 0.2, 0)
        
        # Draw card candidates in blue
        for x, y, w, h, ratio in card_candidates:
            cv2.rectangle(debug_annotated, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(debug_annotated, f"Card {ratio:.2f}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Draw button candidates in red
        for x, y, w, h in rectangles:
            cv2.rectangle(debug_annotated, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(debug_annotated, "Button", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Save annotated image
        annotated_path = "debug_annotated.png"
        cv2.imwrite(annotated_path, debug_annotated)
        print(f"🎨 Annotated debug image saved: {annotated_path}")
        
        print("\n📋 DIAGNOSIS:")
        
        if green_percentage > 10:
            print("✅ Strong poker table signal detected")
            if len(card_candidates) > 2:
                print("✅ Multiple card-like regions found")
                print("🎯 LIKELY CAUSE: Detection threshold too strict")
                print("💡 SOLUTION: Lower confidence threshold in calibrator")
            else:
                print("⚠️  Few card regions detected")
                print("💡 Check if cards are actually visible on screen")
        else:
            print("❌ Weak or no poker table signal")
            print("💡 SOLUTIONS:")
            print("   • Make sure ACR poker client is open and visible")
            print("   • Ensure table is not minimized or covered")
            print("   • Check if poker table has green felt background")
        
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print("1. Check the debug_screenshot.png to see what was captured")
        print("2. Ensure ACR table is fully visible and not minimized")
        print("3. Try clicking 'Detect Table' again after adjusting window")
        
        return {
            "screenshot_size": f"{bgr_image.shape[1]}x{bgr_image.shape[0]}",
            "green_percentage": float(green_percentage),
            "card_candidates": len(card_candidates),
            "button_candidates": len(rectangles),
            "likely_table": bool(green_percentage > 10 and len(card_candidates) > 0)
        }
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = debug_screen_capture()
    print(f"\n📊 Debug Results: {json.dumps(result, indent=2)}")