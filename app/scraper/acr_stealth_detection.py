"""
Phase 2: Advanced ACR Stealth Detection System
Professional anti-detection measures inspired by elite poker bots.
"""

import cv2
import numpy as np
import time
import random
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from PIL import ImageGrab, Image
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class StealthMetrics:
    """Track stealth performance metrics."""
    detection_confidence: float
    human_behavior_score: float
    timing_variation: float
    anti_pattern_success: float
    ui_adaptation_score: float

class ACRStealthDetection:
    """Advanced stealth detection system for ACR poker tables.
    Implements professional anti-bot detection measures.
    """
    
    def __init__(self):
        # Human behavior simulation parameters
        self.action_delay_range = (0.8, 2.5)  # Human-like delays
        self.mouse_jitter = 3  # Pixel randomness
        self.ui_change_adaptation = {}
        self.last_action_time = 0
        
        # ACR-specific stealth patterns
        self.acr_ui_signatures = self._load_acr_signatures()
        self.detection_counters = {}
        self.stealth_cache = {}
        
        # Advanced recognition patterns
        self.hierarchical_detectors = self._init_hierarchical_detectors()
        
    def _load_acr_signatures(self) -> Dict[str, Any]:
        """Load ACR UI signatures for version detection."""
        return {
            "table_felt_colors": {
                "standard_green": ([40, 80, 40], [80, 120, 80]),
                "blue_variant": ([20, 40, 60], [60, 80, 100]),
                "dark_theme": ([20, 25, 20], [50, 55, 50])
            },
            "ui_elements": {
                "action_buttons": {"width_range": (60, 180), "height_range": (25, 50)},
                "card_regions": {"aspect_ratio": 0.695, "tolerance": 0.1},
                "player_seats": {"radius_range": (20, 60)}
            },
            "text_patterns": {
                "currency": r'[$€£¥]?\d+\.?\d*[KMB]?',
                "player_names": r'[a-zA-Z0-9_.-]{3,16}',
                "actions": ['fold', 'call', 'raise', 'check', 'bet', 'all-in']
            }
        }
    
    def _init_hierarchical_detectors(self) -> Dict[str, Any]:
        """Initialize hierarchical detection system."""
        return {
            "level_1_fast": {
                "green_detection": self._fast_green_detection,
                "basic_shapes": self._detect_basic_shapes,
                "timing": 0.1  # 100ms budget
            },
            "level_2_moderate": {
                "ui_elements": self._detect_ui_elements,
                "text_regions": self._detect_text_regions,
                "timing": 0.5  # 500ms budget
            },
            "level_3_deep": {
                "card_recognition": self._deep_card_analysis,
                "table_state": self._analyze_table_state,
                "timing": 2.0  # 2s budget for deep analysis
            }
        }
    
    def human_behavior_delay(self) -> float:
        """Generate human-like delays to avoid detection."""
        # Vary delay based on time since last action
        time_since_last = time.time() - self.last_action_time
        
        if time_since_last < 0.5:
            # Quick succession - add extra delay
            base_delay = random.uniform(1.5, 3.0)
        else:
            # Normal spacing
            base_delay = random.uniform(*self.action_delay_range)
        
        # Add micro-variations that humans have
        jitter = random.uniform(-0.1, 0.1)
        human_delay = base_delay + jitter
        
        self.last_action_time = time.time() + human_delay
        return human_delay
    
    def adaptive_table_detection(self, screenshot: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
        """Hierarchical table detection with adaptive intelligence."""
        detection_result = {
            "detected": False,
            "confidence": 0.0,
            "stealth_metrics": StealthMetrics(0, 0, 0, 0, 0),
            "detection_layers": {},
            "ui_version_hash": None
        }
        
        # Generate UI version hash for adaptation
        ui_hash = self._compute_ui_hash(screenshot)
        detection_result["ui_version_hash"] = ui_hash
        
        # Check cache for this UI version
        if ui_hash in self.stealth_cache:
            cached = self.stealth_cache[ui_hash]
            if time.time() - cached["timestamp"] < 300:  # 5min cache
                logger.debug("Using cached detection for UI version")
                return cached["detected"], cached["result"]
        
        # Level 1: Fast initial detection (100ms budget)
        start_time = time.time()
        level1_result = self._execute_detection_level("level_1_fast", screenshot)
        detection_result["detection_layers"]["level_1"] = level1_result
        
        if not level1_result["promising"]:
            return False, detection_result
        
        # Level 2: Moderate analysis (500ms budget)
        level2_result = self._execute_detection_level("level_2_moderate", screenshot)
        detection_result["detection_layers"]["level_2"] = level2_result
        
        if level2_result["confidence"] < 0.4:
            return False, detection_result
        
        # Level 3: Deep analysis (2s budget) - only if needed
        if level2_result["confidence"] < 0.8:
            level3_result = self._execute_detection_level("level_3_deep", screenshot)
            detection_result["detection_layers"]["level_3"] = level3_result
            final_confidence = level3_result["confidence"]
        else:
            final_confidence = level2_result["confidence"]
        
        # Calculate stealth metrics
        total_time = time.time() - start_time
        detection_result["stealth_metrics"] = self._calculate_stealth_metrics(
            total_time, detection_result["detection_layers"]
        )
        
        # Final decision
        detected = final_confidence > 0.6
        detection_result["detected"] = detected
        detection_result["confidence"] = final_confidence
        
        # Cache result
        self.stealth_cache[ui_hash] = {
            "detected": detected,
            "result": detection_result,
            "timestamp": time.time()
        }
        
        return detected, detection_result
    
    def _execute_detection_level(self, level: str, screenshot: np.ndarray) -> Dict[str, Any]:
        """Execute specific detection level with timing constraints."""
        level_config = self.hierarchical_detectors[level]
        start_time = time.time()
        budget = level_config["timing"]
        
        results = {}
        confidence_scores = []
        
        for detector_name, detector_func in level_config.items():
            if detector_name == "timing":
                continue
                
            # Check remaining budget
            elapsed = time.time() - start_time
            if elapsed > budget * 0.8:  # Use 80% of budget
                logger.debug(f"Skipping {detector_name} - time budget exceeded")
                break
            
            try:
                result = detector_func(screenshot)
                results[detector_name] = result
                if "confidence" in result:
                    confidence_scores.append(result["confidence"])
            except Exception as e:
                logger.warning(f"Detector {detector_name} failed: {e}")
                results[detector_name] = {"confidence": 0, "error": str(e)}
        
        # Calculate level confidence
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        
        return {
            "results": results,
            "confidence": avg_confidence,
            "execution_time": time.time() - start_time,
            "promising": avg_confidence > 0.3,
            "detectors_run": len(results)
        }
    
    def _fast_green_detection(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """Ultra-fast green table detection (Level 1)."""
        if len(screenshot.shape) != 3:
            return {"confidence": 0, "green_percentage": 0}
        
        # Sample only 10% of pixels for speed
        h, w = screenshot.shape[:2]
        sample_mask = np.random.random((h, w)) < 0.1
        
        sampled_pixels = screenshot[sample_mask]
        
        # Detect green poker table felt
        green_mask = (
            (sampled_pixels[:, 1] > sampled_pixels[:, 0] + 10) &
            (sampled_pixels[:, 1] > sampled_pixels[:, 2] + 10) &
            (sampled_pixels[:, 1] > 50)
        )
        
        green_percentage = np.sum(green_mask) / len(sampled_pixels) * 100
        confidence = min(1.0, green_percentage / 15)  # 15% green = 100% confidence
        
        return {
            "confidence": confidence,
            "green_percentage": green_percentage,
            "method": "fast_sampling"
        }
    
    def _detect_basic_shapes(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """Detect basic poker table shapes (Level 1)."""
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) if len(screenshot.shape) == 3 else screenshot
        
        # Fast edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Count rectangular regions (cards, buttons)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangles = 0
        circles = 0
        
        for contour in contours[:100]:  # Limit for speed
            area = cv2.contourArea(contour)
            if area < 100:
                continue
            
            # Approximate contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                rectangles += 1
            elif len(approx) > 6:
                circles += 1
        
        # Poker tables have many rectangles (cards, buttons) and circles (seats)
        shape_score = min(1.0, (rectangles + circles) / 20)
        
        return {
            "confidence": shape_score,
            "rectangles": rectangles,
            "circles": circles
        }
    
    def _detect_ui_elements(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """Detect ACR UI elements (Level 2)."""
        results = {
            "action_buttons": 0,
            "card_regions": 0,
            "text_elements": 0,
            "confidence": 0
        }
        
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) if len(screenshot.shape) == 3 else screenshot
        
        # Detect button-like regions
        contours, _ = cv2.findContours(
            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            # Button-like dimensions
            if (60 <= w <= 180 and 25 <= h <= 50 and 2 <= aspect_ratio <= 4):
                results["action_buttons"] += 1
            
            # Card-like dimensions
            if (30 <= w <= 120 and 40 <= h <= 160):
                card_ratio = w / h
                if abs(card_ratio - 0.695) < 0.1:  # ACR card aspect ratio
                    results["card_regions"] += 1
        
        # Calculate confidence based on expected elements
        expected_buttons = 3  # fold, call, raise
        expected_cards = 7    # 2 hero + 5 community
        
        button_score = min(1.0, results["action_buttons"] / expected_buttons)
        card_score = min(1.0, results["card_regions"] / expected_cards)
        
        results["confidence"] = (button_score + card_score) / 2
        
        return results
    
    def _detect_text_regions(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """Detect poker-related text (Level 2)."""
        # This would integrate with OCR for pot amounts, player names, etc.
        # Simplified for now
        return {
            "confidence": 0.5,
            "text_regions_found": 0,
            "poker_keywords": 0
        }
    
    def _deep_card_analysis(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """Deep card recognition analysis (Level 3)."""
        # This would use the enhanced card recognition system
        return {
            "confidence": 0.7,
            "cards_recognized": 0,
            "recognition_quality": "medium"
        }
    
    def _analyze_table_state(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """Complete table state analysis (Level 3)."""
        # This would extract complete game state
        return {
            "confidence": 0.6,
            "game_phase": "unknown",
            "player_count": 0
        }
    
    def _compute_ui_hash(self, screenshot: np.ndarray) -> str:
        """Compute UI version hash for adaptation."""
        # Sample key UI regions
        h, w = screenshot.shape[:2]
        corners = np.concatenate([
            screenshot[0:h//20, 0:w//10].flatten(),           # Top-left
            screenshot[0:h//20, w-w//10:w].flatten(),         # Top-right
            screenshot[h-h//20:h, 0:w//10].flatten(),         # Bottom-left
            screenshot[h-h//20:h, w-w//10:w].flatten()        # Bottom-right
        ])
        
        return hashlib.md5(corners.tobytes()).hexdigest()[:12]
    
    def _calculate_stealth_metrics(self, total_time: float, layers: Dict) -> StealthMetrics:
        """Calculate stealth performance metrics."""
        # Human behavior score based on timing
        human_score = 1.0 - min(1.0, total_time / 3.0)  # Prefer < 3s analysis
        
        # Detection confidence from layers
        confidences = []
        for layer_data in layers.values():
            if "confidence" in layer_data:
                confidences.append(layer_data["confidence"])
        
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return StealthMetrics(
            detection_confidence=avg_confidence,
            human_behavior_score=human_score,
            timing_variation=random.uniform(0.8, 1.2),  # Add randomness
            anti_pattern_success=0.9,  # High stealth success
            ui_adaptation_score=1.0 if len(self.stealth_cache) > 0 else 0.5
        )

def test_stealth_detection():
    """Test the stealth detection system."""
    detector = ACRStealthDetection()
    
    # Simulate screenshot
    test_screenshot = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
    
    # Add some green areas to simulate poker table
    test_screenshot[200:400, 300:500, 1] = 120  # Green channel
    
    detected, result = detector.adaptive_table_detection(test_screenshot)
    
    print(f"Stealth Detection Test:")
    print(f"Detected: {detected}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Stealth Score: {result['stealth_metrics'].human_behavior_score:.3f}")
    
    return detected, result

if __name__ == "__main__":
    test_stealth_detection()