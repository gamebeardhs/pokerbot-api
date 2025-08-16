#!/usr/bin/env python3
"""
Standalone ACR Poker Scraper Calibration Tool
Run this locally on the same machine where ACR poker client is running.

Requirements:
- pip install pillow opencv-python pytesseract
- Install Tesseract OCR: https://github.com/tesseract-ocr/tesseract

Usage:
1. Open ACR poker client and join a table
2. Run: python acr_calibration_standalone.py
3. Follow the prompts to test screen regions
"""

import cv2
import numpy as np
import pytesseract
import json
import time
from PIL import Image, ImageGrab, ImageDraw, ImageFont
from typing import Dict, Tuple, Any

class ACRCalibrationTool:
    def __init__(self):
        self.screenshot = None
        self.calibrated_regions = {}
        
    def capture_acr_screenshot(self):
        """Capture screenshot and save for reference."""
        print("📸 Preparing to capture screenshot...")
        print("⏰ Make sure ACR poker table is visible and active...")
        
        for i in range(3, 0, -1):
            print(f"📷 Capturing in {i}...")
            time.sleep(1)
        
        self.screenshot = ImageGrab.grab()
        self.screenshot.save("acr_screenshot.png")
        print(f"✅ Screenshot captured: {self.screenshot.size[0]}x{self.screenshot.size[1]}")
        print("📁 Saved as: acr_screenshot.png")
        return self.screenshot

    def test_region_ocr(self, region: Tuple[int, int, int, int], name: str):
        """Test OCR on a specific region with multiple methods."""
        print(f"\n🔍 Testing region: {name}")
        print(f"📐 Coordinates: {region}")
        
        x1, y1, x2, y2 = region
        
        # Validate coordinates
        if x1 >= x2 or y1 >= y2:
            print("❌ Invalid coordinates (x1 < x2, y1 < y2)")
            return False
        
        if x2 > self.screenshot.size[0] or y2 > self.screenshot.size[1]:
            print(f"❌ Coordinates exceed screenshot ({self.screenshot.size[0]}x{self.screenshot.size[1]})")
            return False
        
        # Extract and save region
        region_img = self.screenshot.crop(region)
        region_filename = f"acr_region_{name}.png"
        region_img.save(region_filename)
        print(f"💾 Region image saved: {region_filename}")
        
        # Test multiple OCR approaches
        results = self._test_multiple_ocr_methods(region_img, name)
        
        # Display results
        print("\n📖 OCR Results:")
        best_result = ""
        best_confidence = 0
        
        for method, text in results.items():
            status = "✅" if text and len(text.strip()) > 0 else "❌"
            confidence = len(text.strip()) if text else 0
            print(f"  {status} {method:15}: '{text}'")
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_result = text
        
        if best_result and len(best_result.strip()) > 0:
            print(f"\n🎯 Best result: '{best_result.strip()}'")
            self.calibrated_regions[name] = {
                'coordinates': region,
                'best_ocr': best_result.strip(),
                'all_results': results
            }
            return True
        else:
            print("❌ No readable text detected")
            return False

    def _test_multiple_ocr_methods(self, region_img: Image.Image, name: str) -> Dict[str, str]:
        """Test different OCR preprocessing methods."""
        results = {}
        
        try:
            # Convert to OpenCV format
            cv_img = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Method 1: Raw OCR
            try:
                results['Raw'] = pytesseract.image_to_string(region_img).strip()
            except Exception as e:
                results['Raw'] = f"ERROR: {e}"
            
            # Method 2: Binary threshold
            try:
                _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                binary_pil = Image.fromarray(binary)
                binary_pil.save(f"acr_region_{name}_binary.png")
                results['Binary'] = pytesseract.image_to_string(binary_pil).strip()
            except Exception as e:
                results['Binary'] = f"ERROR: {e}"
            
            # Method 3: Inverted binary threshold
            try:
                _, inv_binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
                inv_binary_pil = Image.fromarray(inv_binary)
                inv_binary_pil.save(f"acr_region_{name}_inverted.png")
                results['Inverted'] = pytesseract.image_to_string(inv_binary_pil).strip()
            except Exception as e:
                results['Inverted'] = f"ERROR: {e}"
            
            # Method 4: Poker-optimized config
            try:
                poker_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
                results['Poker-Optimized'] = pytesseract.image_to_string(binary_pil, config=poker_config).strip()
            except Exception as e:
                results['Poker-Optimized'] = f"ERROR: {e}"
            
            # Method 5: Adaptive threshold
            try:
                adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                adaptive_pil = Image.fromarray(adaptive)
                adaptive_pil.save(f"acr_region_{name}_adaptive.png")
                results['Adaptive'] = pytesseract.image_to_string(adaptive_pil).strip()
            except Exception as e:
                results['Adaptive'] = f"ERROR: {e}"
                
        except Exception as e:
            results['CRITICAL_ERROR'] = str(e)
        
        return results

    def run_interactive_calibration(self):
        """Run the interactive calibration process."""
        print("🎮 ACR Poker Scraper - Real Data Calibration")
        print("=" * 60)
        print("This tool will test if we can read actual ACR poker table data.")
        print()
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
        
        # Capture screenshot
        screenshot = self.capture_acr_screenshot()
        if not screenshot:
            print("❌ Failed to capture screenshot")
            return
        
        # Define regions to test
        regions_to_test = {
            'pot_area': {
                'description': 'Main pot amount display',
                'example': 'Pot: $47.50',
                'priority': 'HIGH'
            },
            'hero_cards': {
                'description': 'Your hole cards area',
                'example': 'Ah Ks',
                'priority': 'HIGH'
            },
            'board_cards': {
                'description': 'Community cards (flop/turn/river)',
                'example': '7h 2s 2d',
                'priority': 'HIGH'
            },
            'action_buttons': {
                'description': 'Fold/Call/Raise buttons',
                'example': 'Call $5.00',
                'priority': 'HIGH'
            },
            'stakes_info': {
                'description': 'Table stakes/blinds',
                'example': '$0.01/$0.02',
                'priority': 'MEDIUM'
            }
        }
        
        print(f"📏 Screenshot dimensions: {screenshot.size[0]} x {screenshot.size[1]}")
        print("\n📖 Instructions:")
        print("1. Open acr_screenshot.png to see your captured table")
        print("2. For each region, identify the coordinates (x1,y1,x2,y2)")
        print("3. Enter coordinates when prompted (or type 'skip')")
        print("4. We'll test OCR on each region")
        print()
        
        successful_regions = 0
        total_regions = 0
        
        for region_name, info in regions_to_test.items():
            print(f"\n{'=' * 70}")
            print(f"🎯 Region: {region_name.upper()}")
            print(f"📝 Description: {info['description']}")
            print(f"💡 Example: {info['example']}")
            print(f"⚡ Priority: {info['priority']}")
            print(f"{'=' * 70}")
            
            while True:
                coords_input = input(f"\nEnter coordinates for {region_name} (x1,y1,x2,y2) or 'skip': ").strip()
                
                if coords_input.lower() == 'skip':
                    print("⏭️  Skipped")
                    break
                
                try:
                    # Parse coordinates
                    parts = [x.strip() for x in coords_input.split(',')]
                    if len(parts) != 4:
                        print("❌ Please enter exactly 4 numbers separated by commas")
                        continue
                    
                    x1, y1, x2, y2 = map(int, parts)
                    region = (x1, y1, x2, y2)
                    
                    # Test OCR on this region
                    total_regions += 1
                    success = self.test_region_ocr(region, region_name)
                    
                    if success:
                        successful_regions += 1
                        print("✅ Region successfully calibrated!")
                        break
                    else:
                        retry = input("❓ Try different coordinates? (y/n): ").strip().lower()
                        if retry != 'y':
                            break
                    
                except ValueError:
                    print("❌ Invalid format. Please enter numbers like: 100,200,300,400")
                    continue
        
        # Generate final report
        self._generate_calibration_report(successful_regions, total_regions)

    def _check_prerequisites(self):
        """Check if all required components are available."""
        print("🔍 Checking prerequisites...")
        
        try:
            # Test Tesseract
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract OCR: {version}")
        except Exception as e:
            print(f"❌ Tesseract OCR not found: {e}")
            print("📥 Install from: https://github.com/tesseract-ocr/tesseract")
            return False
        
        try:
            # Test image capture
            test_img = ImageGrab.grab(bbox=(0, 0, 100, 100))
            print("✅ Screen capture working")
        except Exception as e:
            print(f"❌ Screen capture failed: {e}")
            return False
        
        print("✅ All prerequisites met")
        return True

    def _generate_calibration_report(self, successful: int, total: int):
        """Generate final calibration report."""
        print(f"\n{'=' * 70}")
        print("📊 CALIBRATION RESULTS")
        print(f"{'=' * 70}")
        
        if total > 0:
            success_rate = (successful / total) * 100
            print(f"Success Rate: {successful}/{total} regions ({success_rate:.1f}%)")
            
            if success_rate >= 80:
                print("🎉 EXCELLENT! ACR scraper should work very well")
            elif success_rate >= 60:
                print("👍 GOOD! ACR scraper should work with minor tuning")
            elif success_rate >= 40:
                print("⚠️  MODERATE! Some regions need coordinate adjustment")
            else:
                print("❌ POOR! Significant calibration work needed")
        
        # Save calibration data
        if self.calibrated_regions:
            with open('acr_calibration_results.json', 'w') as f:
                json.dump(self.calibrated_regions, f, indent=2)
            print(f"\n💾 Calibration data saved: acr_calibration_results.json")
        
        print(f"\n📁 Files created for analysis:")
        print("• acr_screenshot.png - Full captured table")
        print("• acr_region_*.png - Individual region extracts")
        print("• acr_region_*_binary.png - OCR preprocessing samples")
        print("• acr_calibration_results.json - Coordinate and OCR data")
        
        print(f"\n🚀 Next steps:")
        if successful >= 3:  # At least 3 working regions
            print("✅ Ready to test with full poker advisory API!")
        else:
            print("🔧 Fine-tune coordinates and re-test failed regions")

def main():
    """Main entry point for ACR calibration."""
    calibrator = ACRCalibrationTool()
    calibrator.run_interactive_calibration()

if __name__ == "__main__":
    main()