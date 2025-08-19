"""
Red button detection and turn detection system for ACR poker automation.
Uses OpenCV template matching and HSV color analysis for reliable detection.
"""

import cv2
import numpy as np
import os
import time
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ButtonType(Enum):
    """Types of poker buttons to detect."""
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    BET = "bet"
    CHECK = "check"
    ALL_IN = "allin"

@dataclass
class ButtonDetection:
    """Result of button detection."""
    button_type: ButtonType
    confidence: float
    position: Tuple[int, int]  # (x, y) center
    bounding_box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    is_active: bool
    color_match: float  # How well it matches red color

class RedButtonDetector:
    """Advanced red button detection system using OpenCV."""
    
    def __init__(self, template_dir: str = "app/scraper/templates"):
        self.template_dir = template_dir
        self.button_templates = {}
        self.confidence_threshold = 0.7
        self.red_threshold = 0.6
        self.load_templates()
        
    def load_templates(self):
        """Load button templates for template matching."""
        try:
            os.makedirs(self.template_dir, exist_ok=True)
            
            # Create default button templates if they don't exist
            if not os.listdir(self.template_dir):
                self._create_default_templates()
            
            # Load existing templates
            for filename in os.listdir(self.template_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    template_path = os.path.join(self.template_dir, filename)
                    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                    
                    if template is not None:
                        # Extract button type from filename
                        button_name = filename.split('_')[0].lower()
                        if button_name in [bt.value for bt in ButtonType]:
                            self.button_templates[button_name] = template
                            logger.info(f"Loaded template for {button_name} button")
            
            logger.info(f"Loaded {len(self.button_templates)} button templates")
            
        except Exception as e:
            logger.error(f"Failed to load button templates: {e}")
    
    def _create_default_templates(self):
        """Create default button templates programmatically."""
        # Create simple colored rectangle templates as defaults
        template_size = (100, 40)
        
        # Red colors for different button types
        button_colors = {
            'fold': (50, 50, 200),    # Red
            'call': (50, 200, 50),    # Green  
            'raise': (200, 100, 50),  # Orange/Red
            'bet': (200, 50, 50),     # Red
            'check': (100, 100, 100), # Gray
            'allin': (150, 50, 200)   # Purple/Red
        }
        
        for button_name, color in button_colors.items():
            # Create a colored rectangle template
            template = np.zeros((template_size[1], template_size[0], 3), dtype=np.uint8)
            template[:] = color
            
            # Add some text-like features
            cv2.rectangle(template, (10, 10), (90, 30), (255, 255, 255), 1)
            cv2.rectangle(template, (20, 15), (80, 25), (0, 0, 0), -1)
            
            template_path = os.path.join(self.template_dir, f"{button_name}_button.png")
            cv2.imwrite(template_path, template)
            
        logger.info("Created default button templates")
    
    def detect_red_buttons(self, image: np.ndarray) -> List[ButtonDetection]:
        """Detect all red/active poker buttons in image."""
        detections = []
        
        # Method 1: Template matching
        template_detections = self._template_matching_detection(image)
        detections.extend(template_detections)
        
        # Method 2: Color-based detection
        color_detections = self._color_based_detection(image)
        detections.extend(color_detections)
        
        # Remove duplicates and sort by confidence
        detections = self._remove_duplicate_detections(detections)
        detections.sort(key=lambda x: x.confidence, reverse=True)
        
        return detections
    
    def _template_matching_detection(self, image: np.ndarray) -> List[ButtonDetection]:
        """Detect buttons using template matching."""
        detections = []
        
        for button_name, template in self.button_templates.items():
            # Multi-scale template matching
            for scale in [0.8, 1.0, 1.2]:
                scaled_template = cv2.resize(template, None, fx=scale, fy=scale)
                
                # Perform template matching
                result = cv2.matchTemplate(image, scaled_template, cv2.TM_CCOEFF_NORMED)
                
                # Find matches above threshold
                locations = np.where(result >= self.confidence_threshold)
                
                for pt in zip(*locations[::-1]):  # Switch x and y
                    confidence = float(result[pt[1], pt[0]])
                    h, w = scaled_template.shape[:2]
                    
                    # Check if this region is actually red/active
                    button_region = image[pt[1]:pt[1]+h, pt[0]:pt[0]+w]
                    red_score = self._analyze_red_content(button_region)
                    
                    detection = ButtonDetection(
                        button_type=ButtonType(button_name),
                        confidence=confidence,
                        position=(pt[0] + w//2, pt[1] + h//2),
                        bounding_box=(pt[0], pt[1], pt[0]+w, pt[1]+h),
                        is_active=red_score > self.red_threshold,
                        color_match=red_score
                    )
                    detections.append(detection)
        
        return detections
    
    def _color_based_detection(self, image: np.ndarray) -> List[ButtonDetection]:
        """Detect buttons based on red color analysis."""
        detections = []
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define red color ranges (HSV)
        red_ranges = [
            # Lower red range
            (np.array([0, 50, 50]), np.array([10, 255, 255])),
            # Upper red range  
            (np.array([170, 50, 50]), np.array([180, 255, 255]))
        ]
        
        # Create red mask
        red_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in red_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            red_mask = cv2.bitwise_or(red_mask, mask)
        
        # Find contours in red areas
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by size (typical button size)
            if 500 < area < 10000:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio (buttons are typically wider than tall)
                aspect_ratio = w / h
                if 1.5 < aspect_ratio < 4.0:
                    # Extract button region for analysis
                    button_region = image[y:y+h, x:x+w]
                    red_score = self._analyze_red_content(button_region)
                    
                    # Try to classify button type based on position/size
                    button_type = self._classify_button_by_position(x + w//2, y + h//2, image.shape)
                    
                    detection = ButtonDetection(
                        button_type=button_type,
                        confidence=red_score,
                        position=(x + w//2, y + h//2),
                        bounding_box=(x, y, x+w, y+h),
                        is_active=True,  # Found via red detection
                        color_match=red_score
                    )
                    detections.append(detection)
        
        return detections
    
    def _analyze_red_content(self, region: np.ndarray) -> float:
        """Analyze how much red content is in a region."""
        if region.size == 0:
            return 0.0
            
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
            
            # Create red mask
            red_mask1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
            red_mask2 = cv2.inRange(hsv, np.array([170, 50, 50]), np.array([180, 255, 255]))
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            # Calculate percentage of red pixels
            red_pixels = np.sum(red_mask > 0)
            total_pixels = region.shape[0] * region.shape[1]
            
            return red_pixels / total_pixels if total_pixels > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Red analysis failed: {e}")
            return 0.0
    
    def _classify_button_by_position(self, x: int, y: int, image_shape: Tuple) -> ButtonType:
        """Classify button type based on position in image."""
        height, width = image_shape[:2]
        
        # Typical button layout: Fold | Call/Check | Raise/Bet
        if x < width * 0.33:
            return ButtonType.FOLD
        elif x < width * 0.66:
            return ButtonType.CALL  # Could also be CHECK
        else:
            return ButtonType.RAISE  # Could also be BET
    
    def _remove_duplicate_detections(self, detections: List[ButtonDetection]) -> List[ButtonDetection]:
        """Remove overlapping detections."""
        if not detections:
            return []
        
        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)
        
        filtered = []
        for detection in detections:
            # Check if this detection overlaps with any existing one
            overlap = False
            for existing in filtered:
                if self._detections_overlap(detection, existing):
                    overlap = True
                    break
            
            if not overlap:
                filtered.append(detection)
        
        return filtered
    
    def _detections_overlap(self, det1: ButtonDetection, det2: ButtonDetection) -> bool:
        """Check if two detections overlap significantly."""
        x1, y1, x2, y2 = det1.bounding_box
        x3, y3, x4, y4 = det2.bounding_box
        
        # Calculate overlap area
        overlap_x = max(0, min(x2, x4) - max(x1, x3))
        overlap_y = max(0, min(y2, y4) - max(y1, y3))
        overlap_area = overlap_x * overlap_y
        
        # Calculate areas
        area1 = (x2 - x1) * (y2 - y1)
        area2 = (x4 - x3) * (y4 - y3)
        min_area = min(area1, area2)
        
        # Consider overlapping if >50% of smaller detection overlaps
        return overlap_area > (min_area * 0.5)
    
    def is_my_turn(self, image: np.ndarray) -> Tuple[bool, List[ButtonDetection]]:
        """Determine if it's the player's turn based on button detection."""
        detections = self.detect_red_buttons(image)
        
        # Filter for active buttons
        active_buttons = [d for d in detections if d.is_active and d.confidence > self.confidence_threshold]
        
        # It's my turn if there are active action buttons
        is_turn = len(active_buttons) > 0
        
        # Look for specific action buttons
        action_buttons = [d for d in active_buttons if d.button_type in [ButtonType.FOLD, ButtonType.CALL, ButtonType.RAISE, ButtonType.BET]]
        
        return is_turn and len(action_buttons) > 0, detections
    
    def visualize_detections(self, image: np.ndarray, detections: List[ButtonDetection]) -> np.ndarray:
        """Draw detection results on image for debugging."""
        result = image.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection.bounding_box
            
            # Choose color based on button type and activity
            if detection.is_active:
                color = (0, 255, 0) if detection.confidence > 0.8 else (0, 255, 255)
            else:
                color = (128, 128, 128)
            
            # Draw bounding box
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
            
            # Add label
            label = f"{detection.button_type.value}: {detection.confidence:.2f}"
            cv2.putText(result, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return result

# Test function
def test_red_button_detection():
    """Test red button detection system."""
    detector = RedButtonDetector()
    
    # Create test image with colored rectangles
    test_image = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # Draw some button-like rectangles
    cv2.rectangle(test_image, (100, 500), (200, 540), (50, 50, 200), -1)  # Red fold button
    cv2.rectangle(test_image, (300, 500), (400, 540), (50, 200, 50), -1)  # Green call button
    cv2.rectangle(test_image, (500, 500), (600, 540), (200, 100, 50), -1) # Orange raise button
    
    # Test detection
    print("Testing red button detection...")
    detections = detector.detect_red_buttons(test_image)
    
    print(f"Found {len(detections)} button detections:")
    for i, detection in enumerate(detections):
        print(f"  {i+1}. {detection.button_type.value}: confidence={detection.confidence:.2f}, "
              f"active={detection.is_active}, red_score={detection.color_match:.2f}")
    
    # Test turn detection
    is_turn, all_detections = detector.is_my_turn(test_image)
    print(f"Is my turn: {is_turn}")
    
    # Save visualization
    result_image = detector.visualize_detections(test_image, detections)
    cv2.imwrite("button_detection_test.png", result_image)
    print("Saved test result to button_detection_test.png")

if __name__ == "__main__":
    test_red_button_detection()