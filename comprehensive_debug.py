#!/usr/bin/env python3
"""
Comprehensive debug logger for ACR poker advisory system.
Captures all system information, screenshot attempts, and detection processes.
"""

import cv2
import numpy as np
import json
import sys
import os
import platform
import traceback
from datetime import datetime
from pathlib import Path

# Add app to path for imports
sys.path.append('.')
try:
    from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
    SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"System import failed: {e}")
    SYSTEM_AVAILABLE = False

class DebugLogger:
    def __init__(self):
        self.log_file = f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.debug_data = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.debug_data.append(log_entry)
        
        # Also write to file immediately
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def log_system_info(self):
        """Log comprehensive system information."""
        self.log("=" * 80)
        self.log("COMPREHENSIVE SYSTEM DEBUG LOG")
        self.log("=" * 80)
        
        # System info
        self.log(f"Platform: {platform.platform()}")
        self.log(f"Python version: {sys.version}")
        self.log(f"Working directory: {os.getcwd()}")
        self.log(f"Script path: {os.path.abspath(__file__)}")
        
        # Environment variables
        relevant_env = ['DISPLAY', 'DISPLAY_CAPTURE_METHOD', 'PATH']
        for var in relevant_env:
            value = os.environ.get(var, 'Not set')
            self.log(f"Environment {var}: {value}")
        
        # Display info
        try:
            import tkinter as tk
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            self.log(f"Tkinter screen size: {screen_width}x{screen_height}")
            root.destroy()
        except Exception as e:
            self.log(f"Tkinter screen info failed: {e}", "WARNING")
    
    def test_screenshot_methods(self):
        """Test all available screenshot methods."""
        self.log("Testing screenshot capture methods...")
        
        methods_tested = []
        
        # Method 1: PIL ImageGrab
        try:
            from PIL import ImageGrab
            self.log("Testing PIL ImageGrab.grab()...")
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            
            method_result = {
                "method": "PIL ImageGrab.grab()",
                "success": True,
                "resolution": f"{screenshot_np.shape[1]}x{screenshot_np.shape[0]}",
                "channels": screenshot_np.shape[2] if len(screenshot_np.shape) > 2 else 1,
                "total_pixels": screenshot_np.sum(),
                "is_black": screenshot_np.sum() == 0,
                "min_value": screenshot_np.min(),
                "max_value": screenshot_np.max(),
                "mean_value": screenshot_np.mean()
            }
            methods_tested.append(method_result)
            self.log(f"PIL grab result: {method_result}")
            
            # Save sample
            cv2.imwrite("debug_pil_grab.png", cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR))
            self.log("Saved debug_pil_grab.png")
            
        except Exception as e:
            methods_tested.append({
                "method": "PIL ImageGrab.grab()",
                "success": False,
                "error": str(e)
            })
            self.log(f"PIL grab failed: {e}", "ERROR")
        
        # Method 2: PIL with all_screens
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            screenshot_np = np.array(screenshot)
            
            method_result = {
                "method": "PIL ImageGrab.grab(all_screens=True)",
                "success": True,
                "resolution": f"{screenshot_np.shape[1]}x{screenshot_np.shape[0]}",
                "channels": screenshot_np.shape[2] if len(screenshot_np.shape) > 2 else 1,
                "total_pixels": screenshot_np.sum(),
                "is_black": screenshot_np.sum() == 0
            }
            methods_tested.append(method_result)
            self.log(f"PIL all_screens result: {method_result}")
            
            # Save sample
            cv2.imwrite("debug_pil_all_screens.png", cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR))
            self.log("Saved debug_pil_all_screens.png")
            
        except Exception as e:
            methods_tested.append({
                "method": "PIL ImageGrab.grab(all_screens=True)",
                "success": False,
                "error": str(e)
            })
            self.log(f"PIL all_screens failed: {e}", "ERROR")
        
        # Method 3: PyAutoGUI
        try:
            import pyautogui
            self.log("Testing PyAutoGUI screenshot...")
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            
            method_result = {
                "method": "PyAutoGUI screenshot()",
                "success": True,
                "resolution": f"{screenshot_np.shape[1]}x{screenshot_np.shape[0]}",
                "channels": screenshot_np.shape[2] if len(screenshot_np.shape) > 2 else 1,
                "total_pixels": screenshot_np.sum(),
                "is_black": screenshot_np.sum() == 0
            }
            methods_tested.append(method_result)
            self.log(f"PyAutoGUI result: {method_result}")
            
            # Save sample
            cv2.imwrite("debug_pyautogui.png", cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR))
            self.log("Saved debug_pyautogui.png")
            
        except ImportError:
            self.log("PyAutoGUI not installed", "WARNING")
        except Exception as e:
            methods_tested.append({
                "method": "PyAutoGUI screenshot()",
                "success": False,
                "error": str(e)
            })
            self.log(f"PyAutoGUI failed: {e}", "ERROR")
        
        return methods_tested
    
    def test_system_detection(self):
        """Test the main system's detection capabilities."""
        if not SYSTEM_AVAILABLE:
            self.log("System not available for testing", "ERROR")
            return None
        
        self.log("Testing main system detection...")
        
        try:
            calibrator = IntelligentACRCalibrator()
            self.log("IntelligentACRCalibrator initialized")
            
            # Test screenshot capture
            screenshot = calibrator.capture_screen()
            self.log(f"System screenshot shape: {screenshot.shape}")
            
            # Test detection
            table_detected, table_info = calibrator.detect_acr_table(screenshot)
            
            detection_result = {
                "table_detected": table_detected,
                "confidence": table_info.get('confidence', 0),
                "screenshot_shape": table_info.get('screenshot_shape', []),
                "features": {k: len(v) if isinstance(v, list) else v for k, v in table_info.get('features', {}).items()},
                "indicators": table_info.get('indicators', {})
            }
            
            self.log(f"System detection result: {json.dumps(detection_result, indent=2, default=str)}")
            
            # Save system screenshot
            cv2.imwrite("debug_system_screenshot.png", screenshot)
            self.log("Saved debug_system_screenshot.png")
            
            return detection_result
            
        except Exception as e:
            self.log(f"System detection failed: {e}", "ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            return None
    
    def test_color_detection(self, screenshot_path="debug_pil_grab.png"):
        """Test color detection on a screenshot."""
        if not os.path.exists(screenshot_path):
            self.log(f"Screenshot {screenshot_path} not found for color testing", "WARNING")
            return
        
        self.log(f"Testing color detection on {screenshot_path}...")
        
        try:
            image = cv2.imread(screenshot_path)
            if image is None:
                self.log(f"Could not load {screenshot_path}", "ERROR")
                return
            
            # Test different green ranges
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            green_ranges = [
                ("Standard", [30, 30, 30], [90, 255, 255]),
                ("Dark", [25, 20, 20], [95, 200, 200]),
                ("Light", [35, 50, 50], [85, 255, 255]),
                ("Wide", [20, 15, 15], [100, 255, 255])
            ]
            
            total_area = image.shape[0] * image.shape[1]
            
            for name, lower, upper in green_ranges:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                green_area = np.sum(mask > 0)
                percentage = (green_area / total_area) * 100
                
                self.log(f"Green detection {name}: {percentage:.2f}% ({green_area}/{total_area} pixels)")
                
                # Save mask for inspection
                cv2.imwrite(f"debug_green_mask_{name.lower()}.png", mask)
            
        except Exception as e:
            self.log(f"Color detection failed: {e}", "ERROR")
    
    def generate_summary(self, methods_tested, detection_result):
        """Generate summary and recommendations."""
        self.log("=" * 80)
        self.log("DEBUG SUMMARY AND RECOMMENDATIONS")
        self.log("=" * 80)
        
        # Working methods
        working_methods = [m for m in methods_tested if m.get('success', False)]
        if working_methods:
            self.log("WORKING SCREENSHOT METHODS:")
            for method in working_methods:
                self.log(f"  - {method['method']}: {method['resolution']}")
                if method.get('is_black', False):
                    self.log(f"    WARNING: Captures black screen - permissions issue")
        
        # Failed methods
        failed_methods = [m for m in methods_tested if not m.get('success', False)]
        if failed_methods:
            self.log("FAILED SCREENSHOT METHODS:")
            for method in failed_methods:
                self.log(f"  - {method['method']}: {method.get('error', 'Unknown error')}")
        
        # Detection results
        if detection_result:
            self.log(f"MAIN SYSTEM DETECTION:")
            self.log(f"  - Table detected: {detection_result['table_detected']}")
            self.log(f"  - Confidence: {detection_result['confidence']}")
            self.log(f"  - Features found: {detection_result['features']}")
        
        # Recommendations
        self.log("RECOMMENDATIONS:")
        
        black_screen_methods = [m for m in working_methods if m.get('is_black', False)]
        if black_screen_methods:
            self.log("  1. BLACK SCREEN DETECTED - Try these fixes:")
            self.log("     - Run Command Prompt as Administrator")
            self.log("     - Change Windows display scale to 100%")
            self.log("     - Enable screen recording permissions for Python")
            self.log("     - Install PyAutoGUI: pip install pyautogui")
        
        if not working_methods:
            self.log("  1. NO WORKING SCREENSHOT METHODS:")
            self.log("     - Install PIL: pip install pillow")
            self.log("     - Install PyAutoGUI: pip install pyautogui")
            self.log("     - Check Python installation")
        
        self.log(f"Complete debug log saved to: {self.log_file}")
        self.log("Files created for inspection:")
        for file in Path('.').glob('debug_*.png'):
            self.log(f"  - {file}")

def main():
    """Run comprehensive debug analysis."""
    logger = DebugLogger()
    
    # System info
    logger.log_system_info()
    
    # Screenshot methods
    methods_tested = logger.test_screenshot_methods()
    
    # System detection
    detection_result = logger.test_system_detection()
    
    # Color detection
    logger.test_color_detection()
    
    # Summary
    logger.generate_summary(methods_tested, detection_result)
    
    print(f"\nComplete debug log saved to: {logger.log_file}")
    print("Share this file to show exactly what's happening on your system.")

if __name__ == "__main__":
    main()