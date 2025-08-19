"""
Robust turn detection for ACR poker using button OCR + timer color fallback.
"""

import cv2
import numpy as np
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Button text keywords that indicate it's our turn
BUTTON_KEYWORDS = ("CALL", "CHECK", "RAISE", "BET", "FOLD", "ALLIN", "ALL IN")

# HSV color ranges for timer arc detection (configurable per ACR theme)
TIMER_COLOR_RANGES = {
    "cyan_blue": ((90, 120, 140), (110, 255, 255)),
    "green": ((70, 120, 140), (89, 255, 255)),
    "yellow_green": ((40, 120, 140), (69, 255, 255)),
    "orange": ((10, 120, 140), (25, 255, 255)),
}

class TurnDetector:
    """Robust turn detection with multiple fallback methods."""
    
    def __init__(self):
        """Initialize turn detector."""
        self.last_button_detection = None
        self.last_timer_detection = None
        self.confidence_threshold = 0.6
        
    def is_our_turn(self, capturer, ocr_engine, regions: Dict[str, Tuple[float, float, float, float]]) -> bool:
        """Detect if it's our turn using button OCR + timer color fallback.
        
        Args:
            capturer: WindowCapturer instance
            ocr_engine: EnhancedOCREngine instance  
            regions: Dict of relative region coordinates
            
        Returns:
            True if it's our turn, False otherwise
        """
        # Method 1: Button OCR (primary detection)
        if self._detect_buttons(capturer, ocr_engine, regions):
            logger.debug("Turn detected via button OCR")
            return True
            
        # Method 2: Timer arc color fallback
        if self._detect_timer_arc(capturer, regions):
            logger.debug("Turn detected via timer arc color")
            return True
            
        return False
    
    def _detect_buttons(self, capturer, ocr_engine, regions: Dict[str, Tuple[float, float, float, float]]) -> bool:
        """Detect turn via action button text."""
        try:
            if "buttons" not in regions:
                logger.debug("No buttons region defined")
                return False
                
            # Capture buttons area
            btn_img, _ = capturer.capture_region(regions["buttons"])
            if btn_img is None:
                logger.debug("Failed to capture buttons region")
                return False
            
            # Extract text using button-optimized OCR
            btn_text = ocr_engine.extract_text(btn_img, "buttons")
            btn_text_upper = btn_text.upper()
            
            logger.debug(f"Button text detected: '{btn_text}'")
            
            # Check for action button keywords
            for keyword in BUTTON_KEYWORDS:
                if keyword in btn_text_upper:
                    self.last_button_detection = keyword
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Button detection failed: {e}")
            return False
    
    def _detect_timer_arc(self, capturer, regions: Dict[str, Tuple[float, float, float, float]]) -> bool:
        """Detect turn via timer arc color (fallback method)."""
        try:
            if "hero_timer_arc" not in regions:
                logger.debug("No timer arc region defined")
                return False
                
            # Capture timer arc area
            arc_img, _ = capturer.capture_region(regions["hero_timer_arc"])
            if arc_img is None:
                logger.debug("Failed to capture timer arc region")
                return False
            
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(arc_img, cv2.COLOR_BGR2HSV)
            
            # Check each configured color range
            total_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            
            for color_name, (lower, upper) in TIMER_COLOR_RANGES.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                total_mask = cv2.bitwise_or(total_mask, mask)
            
            # Calculate percentage of pixels matching timer colors
            active_percentage = (total_mask.mean() / 255.0) * 100
            
            logger.debug(f"Timer arc active pixels: {active_percentage:.1f}%")
            
            # Threshold for timer detection (5% of pixels active)
            if active_percentage > 5.0:
                self.last_timer_detection = active_percentage
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Timer arc detection failed: {e}")
            return False
    
    def get_last_detection_info(self) -> Dict[str, Any]:
        """Get information about the last detection."""
        return {
            "last_button_keyword": self.last_button_detection,
            "last_timer_percentage": self.last_timer_detection,
            "detection_method": "buttons" if self.last_button_detection else "timer" if self.last_timer_detection else "none"
        }
    
    def configure_timer_colors(self, color_ranges: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int]]]):
        """Configure HSV color ranges for timer detection."""
        global TIMER_COLOR_RANGES
        TIMER_COLOR_RANGES.update(color_ranges)
        logger.info(f"Updated timer color ranges: {list(color_ranges.keys())}")

# Global turn detector instance
turn_detector = TurnDetector()