"""
High-performance screenshot capture system optimized for Windows poker automation.
Uses MSS library for 60+ FPS real-time capture with OpenCV processing.
"""

import cv2
import numpy as np
import mss
import time
import threading
from typing import Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)

@dataclass
class CaptureRegion:
    """Defines a screen capture region with metadata."""
    name: str
    x: int
    y: int
    width: int
    height: int
    monitor_dict: Optional[Dict] = None
    
    def __post_init__(self):
        """Initialize MSS monitor dictionary."""
        self.monitor_dict = {
            "top": self.y,
            "left": self.x, 
            "width": self.width,
            "height": self.height
        }

class OptimizedScreenCapture:
    """Ultra-fast screenshot capture system using MSS library."""
    
    def __init__(self):
        self.sct = mss.mss()
        self.capture_active = False
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        self.capture_thread = None
        self.frame_queue = Queue(maxsize=5)  # Limit queue size to prevent memory buildup
        
    def capture_region_sync(self, region: CaptureRegion) -> np.ndarray:
        """Synchronous capture of a specific region (ultra-fast)."""
        try:
            # MSS capture (native Win32 API on Windows)
            sct_img = self.sct.grab(region.monitor_dict)
            
            # Convert to numpy array for OpenCV
            img_array = np.array(sct_img)
            
            # Convert BGRA to BGR (remove alpha channel)
            if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            else:
                img_bgr = img_array
                
            return img_bgr
            
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return np.array([])
    
    def start_continuous_capture(self, region: CaptureRegion, 
                               process_callback: Optional[Callable] = None):
        """Start continuous capture in background thread."""
        if self.capture_active:
            logger.warning("Capture already active")
            return
            
        self.capture_active = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop, 
            args=(region, process_callback),
            daemon=True
        )
        self.capture_thread.start()
        logger.info(f"Started continuous capture for {region.name}")
    
    def _capture_loop(self, region: CaptureRegion, process_callback: Optional[Callable]):
        """Background capture loop for maximum performance."""
        while self.capture_active:
            try:
                # Ultra-fast capture
                frame = self.capture_region_sync(region)
                
                if frame is not None:
                    # Update FPS counter
                    self._update_fps()
                    
                    # Add to queue (non-blocking)
                    try:
                        self.frame_queue.put_nowait({
                            'frame': frame,
                            'timestamp': time.time(),
                            'region': region.name
                        })
                    except:
                        # Queue full, skip this frame
                        pass
                    
                    # Call processing callback if provided
                    if process_callback:
                        process_callback(frame, region.name)
                        
                # Small sleep to prevent 100% CPU usage
                time.sleep(0.001)  # ~1000 FPS limit
                
            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                time.sleep(0.1)
    
    def get_latest_frame(self) -> Optional[Dict]:
        """Get the most recent captured frame (non-blocking)."""
        latest_frame = None
        
        # Drain queue to get most recent frame
        try:
            while True:
                latest_frame = self.frame_queue.get_nowait()
        except Empty:
            pass
            
        return latest_frame
    
    def stop_capture(self):
        """Stop continuous capture."""
        self.capture_active = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
        logger.info("Stopped continuous capture")
    
    def _update_fps(self):
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time
            
            if self.current_fps > 0:
                logger.debug(f"Capture FPS: {self.current_fps}")
    
    def get_fps(self) -> int:
        """Get current FPS."""
        return self.current_fps
    
    def __del__(self):
        """Cleanup on destruction."""
        self.stop_capture()

class WindowDetector:
    """Detect and track poker client windows."""
    
    @staticmethod
    def detect_acr_window() -> Optional[CaptureRegion]:
        """Detect ACR poker client window bounds."""
        try:
            # Try to use pyautogui for window detection
            import pyautogui
            
            # Get all windows (platform-specific)
            try:
                # Try Windows-specific approach first
                try:
                    import win32gui
                except ImportError:
                    win32gui = None
                
                if win32gui:
                    def enum_windows_callback(hwnd, windows):
                            window_text = win32gui.GetWindowText(hwnd)
                            if 'americas cardroom' in window_text.lower() or 'acr' in window_text.lower():
                                rect = win32gui.GetWindowRect(hwnd)
                                windows.append({
                                    'title': window_text,
                                    'rect': rect,
                                    'hwnd': hwnd
                                })
                    
                    windows = []
                    win32gui.EnumWindows(enum_windows_callback, windows)
                    
                    if windows:
                        # Use first ACR window found
                        rect = windows[0]['rect']
                        return CaptureRegion(
                            name="ACR_Table",
                            x=rect[0],
                            y=rect[1], 
                            width=rect[2] - rect[0],
                            height=rect[3] - rect[1]
                        )
                else:
                    logger.info("win32gui not available, using manual detection")
                    
            except ImportError:
                logger.info("win32gui not available, using manual detection")
            
            # Fallback: Use default poker table region
            screen_width, screen_height = pyautogui.size()
            
            # Default region (center of screen, typical poker table size)
            width = min(1200, int(screen_width * 0.8))
            height = min(800, int(screen_height * 0.7))
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            return CaptureRegion(
                name="Default_Poker_Region",
                x=x, y=y, width=width, height=height
            )
            
        except Exception as e:
            logger.error(f"Window detection failed: {e}")
            return None
    
    @staticmethod
    def get_optimal_regions() -> Dict[str, CaptureRegion]:
        """Get optimized capture regions for poker elements."""
        
        # Detect main table window
        main_region = WindowDetector.detect_acr_window()
        
        if not main_region:
            logger.warning("Could not detect poker window, using screen defaults")
            return {}
        
        # Define sub-regions within the main poker table
        regions = {
            'full_table': main_region,
            
            # Action buttons (bottom center)
            'action_buttons': CaptureRegion(
                name="Action_Buttons",
                x=main_region.x + int(main_region.width * 0.3),
                y=main_region.y + int(main_region.height * 0.8),
                width=int(main_region.width * 0.4),
                height=int(main_region.height * 0.15)
            ),
            
            # Hero cards (bottom center)
            'hero_cards': CaptureRegion(
                name="Hero_Cards", 
                x=main_region.x + int(main_region.width * 0.35),
                y=main_region.y + int(main_region.height * 0.65),
                width=int(main_region.width * 0.3),
                height=int(main_region.height * 0.1)
            ),
            
            # Board cards (center)
            'board_cards': CaptureRegion(
                name="Board_Cards",
                x=main_region.x + int(main_region.width * 0.25),
                y=main_region.y + int(main_region.height * 0.35),
                width=int(main_region.width * 0.5),
                height=int(main_region.height * 0.15)
            ),
            
            # Pot area (top center)
            'pot_area': CaptureRegion(
                name="Pot_Area",
                x=main_region.x + int(main_region.width * 0.4),
                y=main_region.y + int(main_region.height * 0.2),
                width=int(main_region.width * 0.2),
                height=int(main_region.height * 0.1)
            )
        }
        
        return regions

# Performance test function
def test_capture_performance():
    """Test screenshot capture performance."""
    capture = OptimizedScreenCapture()
    
    # Detect poker regions
    regions = WindowDetector.get_optimal_regions()
    
    if not regions:
        logger.error("No poker regions detected")
        return
    
    # Test single capture performance
    test_region = regions['full_table']
    
    print(f"Testing capture performance for {test_region.name}")
    print(f"Region: {test_region.width}x{test_region.height} at ({test_region.x}, {test_region.y})")
    
    # Performance test
    start_time = time.time()
    frames_captured = 0
    test_duration = 5.0  # 5 seconds
    
    while time.time() - start_time < test_duration:
        frame = capture.capture_region_sync(test_region)
        if frame is not None:
            frames_captured += 1
    
    elapsed = time.time() - start_time
    fps = frames_captured / elapsed
    
    print(f"Captured {frames_captured} frames in {elapsed:.2f} seconds")
    print(f"Average FPS: {fps:.1f}")
    print(f"Frame time: {1000/fps:.2f}ms per frame")
    
    if fps > 30:
        print("✅ EXCELLENT performance - ready for real-time poker automation")
    elif fps > 15:
        print("✅ GOOD performance - suitable for poker automation")
    else:
        print("⚠️  LOW performance - may need optimization")

if __name__ == "__main__":
    test_capture_performance()