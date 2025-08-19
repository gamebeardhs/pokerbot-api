"""
Windows-specific optimized screen capture using MSS library.
Provides stable, fast window-bound capture for ACR poker client.
"""

import mss
import numpy as np
import cv2
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

try:
    import win32gui
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logger.warning("Windows API not available - using fallback capture")
    
    # Create mock functions for non-Windows environments
    class MockWin32:
        @staticmethod
        def IsWindowVisible(hwnd):
            return False
        @staticmethod 
        def GetWindowText(hwnd):
            return ""
        @staticmethod
        def EnumWindows(callback, param):
            pass
        @staticmethod
        def GetClientRect(hwnd):
            return (0, 0, 0, 0)
        @staticmethod
        def ClientToScreen(hwnd, point):
            return (0, 0)
    
    win32gui = MockWin32()

def find_acr_window() -> Optional[Dict[str, Any]]:
    """Find ACR poker window and return its client area bounds."""
    if not WINDOWS_AVAILABLE:
        return None
        
    hwnd_found = []
    
    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd) or ""
            # Look for various ACR window titles
            acr_indicators = ["americas cardroom", "acr", "poker", "table"]
            if any(indicator in window_title.lower() for indicator in acr_indicators):
                hwnd_found.append((hwnd, window_title))
    
    try:
        win32gui.EnumWindows(enum_callback, None)
        
        if not hwnd_found:
            logger.debug("No ACR window found")
            return None
        
        # Use the first found window (or prioritize by title)
        hwnd, title = hwnd_found[0]
        logger.info(f"Found ACR window: {title}")
        
        # Get client rectangle (excludes window borders/title bar)
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        
        # Convert client coordinates to screen coordinates
        screen_x, screen_y = win32gui.ClientToScreen(hwnd, (0, 0))
        width = right - left
        height = bottom - top
        
        return {
            "hwnd": hwnd,
            "title": title,
            "x": screen_x,
            "y": screen_y,
            "width": width,
            "height": height
        }
        
    except Exception as e:
        logger.error(f"Error finding ACR window: {e}")
        return None

class WindowCapturer:
    """Optimized window capture using MSS for fast, stable screenshot capture."""
    
    def __init__(self, window_title_contains: str = "americas cardroom"):
        """Initialize capturer for specific window."""
        self.window_info = None
        self.sct = mss.mss()
        self.window_title_contains = window_title_contains.lower()
        self.refresh_window_info()
        
    def refresh_window_info(self) -> bool:
        """Refresh window information - call when window might have moved."""
        self.window_info = find_acr_window()
        return self.window_info is not None
    
    def capture_full_window(self) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int]]]:
        """Capture the full ACR window.
        
        Returns:
            (frame_bgr, (width, height)) or (None, None) if capture fails
        """
        if not self.window_info:
            if not self.refresh_window_info():
                return None, None
        
        try:
            monitor = {
                "left": self.window_info["x"],
                "top": self.window_info["y"], 
                "width": self.window_info["width"],
                "height": self.window_info["height"]
            }
            
            # Capture using MSS
            screenshot = self.sct.grab(monitor)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Handle different color formats
            if frame.shape[2] == 4:  # BGRA
                frame = frame[:, :, :3]  # Drop alpha channel
            
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            window_size = (self.window_info["width"], self.window_info["height"])
            return frame_bgr, window_size
            
        except Exception as e:
            logger.error(f"Window capture failed: {e}")
            # Try refreshing window info
            if self.refresh_window_info():
                logger.info("Window info refreshed, retrying capture")
                return self.capture_full_window()
            return None, None
    
    def capture_region(self, relative_box: Tuple[float, float, float, float]) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int]]]:
        """Capture a specific region using relative coordinates.
        
        Args:
            relative_box: (rx, ry, rw, rh) as fractions of window size (0.0 to 1.0)
            
        Returns:
            (region_bgr, (region_width, region_height)) or (None, None)
        """
        if not self.window_info:
            if not self.refresh_window_info():
                return None, None
        
        try:
            rx, ry, rw, rh = relative_box
            
            # Convert relative coordinates to absolute pixels
            base_x = self.window_info["x"]
            base_y = self.window_info["y"]
            win_width = self.window_info["width"]
            win_height = self.window_info["height"]
            
            region_x = int(base_x + rx * win_width)
            region_y = int(base_y + ry * win_height)
            region_width = int(rw * win_width)
            region_height = int(rh * win_height)
            
            monitor = {
                "left": region_x,
                "top": region_y,
                "width": region_width,
                "height": region_height
            }
            
            # Capture region using MSS
            screenshot = self.sct.grab(monitor)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Handle color format
            if frame.shape[2] == 4:  # BGRA
                frame = frame[:, :, :3]  # Drop alpha
                
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            return frame_bgr, (region_width, region_height)
            
        except Exception as e:
            logger.error(f"Region capture failed: {e}")
            return None, None

    def is_window_available(self) -> bool:
        """Check if the target window is available for capture."""
        return self.window_info is not None or self.refresh_window_info()