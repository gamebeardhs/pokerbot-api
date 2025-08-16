#!/usr/bin/env python3
"""Simple tool to test ACR scraper with real data."""

import cv2
import numpy as np
import pytesseract
import json
from PIL import Image, ImageGrab, ImageDraw, ImageFont
from typing import Dict, Tuple, Any
import sys

def capture_acr_screenshot():
    """Capture screenshot and save for reference."""
    print("Capturing screenshot in 3 seconds...")
    print("Make sure ACR poker table is visible...")
    import time
    time.sleep(3)
    
    screenshot = ImageGrab.grab()
    screenshot.save("acr_screenshot.png")
    print(f"✅ Screenshot captured: {screenshot.size[0]}x{screenshot.size[1]} -> acr_screenshot.png")
    return screenshot

def test_region_ocr(screenshot: Image.Image, region: Tuple[int, int, int, int], name: str):
    """Test OCR on a specific region."""
    print(f"\n🔍 Testing region: {name}")
    print(f"Coordinates: {region}")
    
    x1, y1, x2, y2 = region
    
    # Validate coordinates
    if x1 >= x2 or y1 >= y2:
        print("❌ Invalid coordinates (x1 should be < x2, y1 should be < y2)")
        return
    
    if x2 > screenshot.size[0] or y2 > screenshot.size[1]:
        print(f"❌ Coordinates exceed image size ({screenshot.size[0]}x{screenshot.size[1]})")
        return
    
    # Extract region
    region_img = screenshot.crop(region)
    region_filename = f"acr_region_{name}.png"
    region_img.save(region_filename)
    print(f"📁 Region saved: {region_filename}")
    
    # Test different OCR methods
    print("\n📖 OCR Results:")
    
    # Convert to different formats for OCR
    cv_img = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    
    # 1. Raw OCR
    try:
        raw_text = pytesseract.image_to_string(region_img).strip()
        print(f"  Raw:       '{raw_text}'")
    except Exception as e:
        print(f"  Raw:       ERROR - {e}")
        raw_text = ""
    
    # 2. Threshold OCR  
    try:
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        binary_pil = Image.fromarray(binary)
        threshold_text = pytesseract.image_to_string(binary_pil).strip()
        print(f"  Threshold: '{threshold_text}'")
        
        # Save preprocessed image
        binary_pil.save(f"acr_region_{name}_processed.png")
        
    except Exception as e:
        print(f"  Threshold: ERROR - {e}")
        threshold_text = ""
    
    # 3. Poker-optimized OCR
    try:
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
        poker_text = pytesseract.image_to_string(binary_pil, config=config).strip()
        print(f"  Poker:     '{poker_text}'")
    except Exception as e:
        print(f"  Poker:     ERROR - {e}")
        poker_text = ""
    
    # Determine best result
    results = [raw_text, threshold_text, poker_text]
    best_result = max(results, key=len) if any(results) else "NO TEXT DETECTED"
    
    if best_result and best_result != "NO TEXT DETECTED":
        print(f"✅ Best result: '{best_result}'")
        return True
    else:
        print("❌ No readable text found - may need coordinate adjustment")
        return False

def main():
    print("🎮 ACR Real Data Test Tool")
    print("=" * 50)
    print("This tool will help test if the scraper can read actual ACR poker table data.")
    print()
    
    # Check if pytesseract works
    try:
        pytesseract.get_tesseract_version()
        print("✅ OCR engine ready")
    except Exception as e:
        print(f"❌ OCR engine error: {e}")
        print("Make sure tesseract is installed properly")
        return
    
    # Capture screenshot
    screenshot = capture_acr_screenshot()
    
    # Define key regions to test
    test_regions = {
        'pot_area': "Main pot amount (example: 400,200,600,250)",
        'hero_cards': "Your hole cards (example: 300,500,500,550)", 
        'stakes_info': "Table stakes/blinds (example: 50,50,200,100)",
        'action_buttons': "Fold/Call/Raise buttons (example: 400,600,700,650)"
    }
    
    print(f"\n📐 Screenshot size: {screenshot.size[0]}x{screenshot.size[1]}")
    print("Now we'll test specific regions. For each region:")
    print("1. Look at acr_screenshot.png to find the area")
    print("2. Enter coordinates as: x1,y1,x2,y2 (top-left to bottom-right)")
    print("3. We'll test OCR on that region")
    print()
    
    successful_reads = 0
    total_tests = 0
    
    for region_name, description in test_regions.items():
        print(f"\n{'='*60}")
        print(f"Region: {region_name}")
        print(f"Description: {description}")
        print(f"{'='*60}")
        
        while True:
            coords_input = input(f"Enter coordinates for {region_name} (or 'skip'): ").strip()
            
            if coords_input.lower() == 'skip':
                print("Skipped")
                break
                
            try:
                # Parse coordinates
                parts = coords_input.split(',')
                if len(parts) != 4:
                    print("❌ Please enter exactly 4 numbers: x1,y1,x2,y2")
                    continue
                    
                x1, y1, x2, y2 = map(int, parts)
                region = (x1, y1, x2, y2)
                
                # Test the region
                total_tests += 1
                success = test_region_ocr(screenshot, region, region_name)
                if success:
                    successful_reads += 1
                
                # Ask if they want to try different coordinates
                if not success:
                    retry = input("Try different coordinates? (y/n): ").strip().lower()
                    if retry != 'y':
                        break
                else:
                    break
                    
            except ValueError:
                print("❌ Invalid format. Please enter numbers like: 100,200,300,400")
                continue
    
    # Final report
    print(f"\n{'='*60}")
    print("🎯 REAL ACR TEST RESULTS")
    print(f"{'='*60}")
    
    if total_tests > 0:
        success_rate = (successful_reads / total_tests) * 100
        print(f"Success Rate: {successful_reads}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print("✅ EXCELLENT - Scraper should work well with ACR")
        elif success_rate >= 50:
            print("⚠️  MODERATE - Some OCR tuning may be needed")
        else:
            print("❌ POOR - Significant calibration work required")
    else:
        print("No regions tested")
    
    print(f"\n📁 Files created:")
    print("- acr_screenshot.png (full screenshot)")
    print("- acr_region_*.png (individual regions)")
    print("- acr_region_*_processed.png (OCR preprocessing)")
    print("\nUse these images to fine-tune coordinates if needed.")

if __name__ == "__main__":
    main()