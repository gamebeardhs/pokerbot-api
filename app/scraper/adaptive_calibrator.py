"""
Adaptive ACR Calibration System
Continuously adapts to poker table phases: pre-flop, flop, turn, river, showdown
Handles dynamic element visibility (hole cards, buttons, bets, etc.)
"""

import cv2
import numpy as np
import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import logging
from PIL import ImageGrab
from collections import defaultdict
from app.scraper.intelligent_calibrator import IntelligentACRCalibrator, TableRegion, CalibrationResult

logger = logging.getLogger(__name__)

@dataclass
class GamePhase:
    """Represents current game phase and visible elements."""
    phase: str  # preflop, flop, turn, river, showdown, between_hands
    visible_elements: Set[str]
    hero_in_hand: bool
    hero_turn: bool
    betting_round_active: bool
    community_cards_count: int
    timestamp: float

@dataclass
class AdaptiveRegion:
    """Region that adapts based on game phase."""
    base_region: TableRegion
    required_phases: Set[str]  # Phases when this region should be visible
    confidence_threshold: float
    last_seen: float
    detection_history: List[float]  # Recent confidence scores

class AdaptiveCalibratorManager:
    """Manages continuous adaptive calibration for poker table phases."""
    
    def __init__(self):
        self.base_calibrator = IntelligentACRCalibrator()
        self.is_running = False
        self.monitoring_thread = None
        
        # Adaptive regions with phase requirements
        self.adaptive_regions = {}
        self.current_phase = GamePhase(
            phase="unknown",
            visible_elements=set(),
            hero_in_hand=False,
            hero_turn=False,
            betting_round_active=False,
            community_cards_count=0,
            timestamp=time.time()
        )
        
        # Detection settings
        self.monitoring_interval = 0.5  # Check every 500ms
        self.confidence_history_size = 10
        self.phase_stability_threshold = 3  # Require 3 consistent detections
        
        # Phase-specific element mapping
        self.setup_phase_requirements()
        
    def setup_phase_requirements(self):
        """Define which elements are visible in which phases."""
        self.phase_requirements = {
            "hero_cards": {"preflop", "flop", "turn", "river", "showdown"},
            "community_1": {"flop", "turn", "river", "showdown"},
            "community_2": {"flop", "turn", "river", "showdown"}, 
            "community_3": {"flop", "turn", "river", "showdown"},
            "community_4": {"turn", "river", "showdown"},
            "community_5": {"river", "showdown"},
            "fold_button": {"hero_turn"},
            "call_button": {"hero_turn"},
            "raise_button": {"hero_turn"},
            "pot": {"preflop", "flop", "turn", "river", "betting_active"},
            "player_bets": {"betting_active", "postflop"},
            "player_names": {"always"},  # Always visible
            "dealer_button": {"always"}
        }
    
    def start_adaptive_monitoring(self) -> bool:
        """Start continuous adaptive calibration monitoring."""
        if self.is_running:
            logger.info("Adaptive monitoring already running")
            return True
        
        # Initial calibration
        initial_result = self.base_calibrator.auto_calibrate_table()
        if not initial_result.table_detected:
            logger.error("Cannot start adaptive monitoring - no table detected")
            return False
        
        if initial_result.success_rate < 0.8:  # Lower threshold for initial setup
            logger.warning(f"Starting with lower accuracy: {initial_result.success_rate:.1%}")
        
        # Initialize adaptive regions
        self.initialize_adaptive_regions(initial_result)
        
        # Start monitoring thread
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"Adaptive calibration monitoring started - tracking {len(self.adaptive_regions)} regions")
        return True
    
    def stop_adaptive_monitoring(self):
        """Stop continuous monitoring."""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        logger.info("Adaptive calibration monitoring stopped")
    
    def initialize_adaptive_regions(self, calibration_result: CalibrationResult):
        """Initialize adaptive regions from base calibration."""
        for name, region in calibration_result.regions.items():
            required_phases = self.phase_requirements.get(name, {"always"})
            
            adaptive_region = AdaptiveRegion(
                base_region=region,
                required_phases=required_phases,
                confidence_threshold=0.6,
                last_seen=time.time(),
                detection_history=[region.confidence]
            )
            
            self.adaptive_regions[name] = adaptive_region
        
        logger.info(f"Initialized {len(self.adaptive_regions)} adaptive regions")
    
    def _monitoring_loop(self):
        """Main monitoring loop for adaptive calibration."""
        logger.info("Adaptive monitoring loop started")
        
        while self.is_running:
            try:
                # Capture current state
                screenshot = self.base_calibrator.capture_screen()
                
                # Detect current game phase
                new_phase = self.detect_current_phase(screenshot)
                phase_changed = new_phase.phase != self.current_phase.phase
                
                if phase_changed:
                    logger.info(f"Phase change detected: {self.current_phase.phase} → {new_phase.phase}")
                    self.handle_phase_change(new_phase)
                
                self.current_phase = new_phase
                
                # Update region tracking
                self.update_region_tracking(screenshot)
                
                # Adaptive recalibration if needed
                if self.should_recalibrate():
                    self.perform_adaptive_recalibration(screenshot)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(1.0)  # Longer sleep on error
        
        logger.info("Adaptive monitoring loop stopped")
    
    def detect_current_phase(self, screenshot: np.ndarray) -> GamePhase:
        """Detect current game phase from screenshot."""
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # Count community cards
        community_count = self.count_community_cards(gray)
        
        # Detect if hero is in hand (cards visible)
        hero_in_hand = self.detect_hero_cards(gray)
        
        # Detect if it's hero's turn (buttons visible)
        hero_turn = self.detect_action_buttons(gray)
        
        # Detect betting activity
        betting_active = self.detect_betting_activity(gray)
        
        # Determine phase
        if community_count == 0:
            phase = "preflop" if hero_in_hand else "between_hands"
        elif community_count == 3:
            phase = "flop"
        elif community_count == 4:
            phase = "turn" 
        elif community_count == 5:
            phase = "river"
        else:
            phase = "showdown" if hero_in_hand else "between_hands"
        
        # Build visible elements set
        visible_elements = set()
        if hero_in_hand:
            visible_elements.add("hero_cards")
        if hero_turn:
            visible_elements.update(["fold_button", "call_button", "raise_button"])
        if betting_active:
            visible_elements.add("pot")
        if community_count >= 3:
            for i in range(1, min(community_count + 1, 6)):
                visible_elements.add(f"community_{i}")
        
        return GamePhase(
            phase=phase,
            visible_elements=visible_elements,
            hero_in_hand=hero_in_hand,
            hero_turn=hero_turn,
            betting_round_active=betting_active,
            community_cards_count=community_count,
            timestamp=time.time()
        )
    
    def count_community_cards(self, gray_image: np.ndarray) -> int:
        """Count visible community cards."""
        community_regions = []
        for i in range(1, 6):
            region_name = f"community_{i}"
            if region_name in self.adaptive_regions:
                region = self.adaptive_regions[region_name].base_region
                card_area = gray_image[region.y:region.y+region.height, 
                                    region.x:region.x+region.width]
                
                # Simple card detection - look for card-like patterns
                if self.is_card_visible(card_area):
                    community_regions.append(region_name)
        
        return len(community_regions)
    
    def detect_hero_cards(self, gray_image: np.ndarray) -> bool:
        """Detect if hero's cards are visible."""
        for card_region in ["hero_card_1", "hero_card_2"]:
            if card_region in self.adaptive_regions:
                region = self.adaptive_regions[card_region].base_region
                card_area = gray_image[region.y:region.y+region.height,
                                    region.x:region.x+region.width]
                
                if self.is_card_visible(card_area):
                    return True
        return False
    
    def detect_action_buttons(self, gray_image: np.ndarray) -> bool:
        """Detect if action buttons are visible."""
        for button in ["fold_button", "call_button", "raise_button"]:
            if button in self.adaptive_regions:
                region = self.adaptive_regions[button].base_region
                button_area = gray_image[region.y:region.y+region.height,
                                       region.x:region.x+region.width]
                
                # Look for button-like text
                text = self.base_calibrator.extract_text(button_area)
                if any(word in text.lower() for word in ["fold", "call", "raise", "check", "bet"]):
                    return True
        return False
    
    def detect_betting_activity(self, gray_image: np.ndarray) -> bool:
        """Detect if betting is currently active."""
        # Look for pot region and bet amounts
        if "pot" in self.adaptive_regions:
            region = self.adaptive_regions["pot"].base_region
            pot_area = gray_image[region.y:region.y+region.height,
                                 region.x:region.x+region.width]
            
            text = self.base_calibrator.extract_text(pot_area)
            # Look for currency symbols or numbers indicating active pot
            if any(char in text for char in ['$', '€', '£']) or any(char.isdigit() for char in text):
                return True
        
        return False
    
    def is_card_visible(self, card_area: np.ndarray) -> bool:
        """Check if a card is visible in the given area."""
        if card_area.size == 0:
            return False
        
        # Simple card detection - look for white/light colored rectangular regions
        mean_intensity = np.mean(card_area)
        
        # Cards typically have higher intensity than felt background
        return mean_intensity > 80  # Threshold for card visibility
    
    def handle_phase_change(self, new_phase: GamePhase):
        """Handle game phase changes."""
        logger.info(f"Handling phase change to: {new_phase.phase}")
        logger.info(f"Visible elements: {new_phase.visible_elements}")
        
        # Update region expectations
        for region_name, adaptive_region in self.adaptive_regions.items():
            should_be_visible = (
                "always" in adaptive_region.required_phases or
                new_phase.phase in adaptive_region.required_phases or
                any(elem in adaptive_region.required_phases for elem in new_phase.visible_elements)
            )
            
            if should_be_visible and region_name not in new_phase.visible_elements:
                logger.debug(f"Region {region_name} should be visible but not detected")
            elif not should_be_visible and region_name in new_phase.visible_elements:
                logger.debug(f"Region {region_name} detected but not expected in {new_phase.phase}")
    
    def update_region_tracking(self, screenshot: np.ndarray):
        """Update tracking information for all regions."""
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        for region_name, adaptive_region in self.adaptive_regions.items():
            region = adaptive_region.base_region
            
            # Extract region from screenshot
            area = gray[region.y:region.y+region.height, region.x:region.x+region.width]
            
            # Calculate current confidence
            confidence = self.calculate_region_confidence(area, region.element_type)
            
            # Update history
            adaptive_region.detection_history.append(confidence)
            if len(adaptive_region.detection_history) > self.confidence_history_size:
                adaptive_region.detection_history.pop(0)
            
            # Update last seen if confidence is good
            if confidence > adaptive_region.confidence_threshold:
                adaptive_region.last_seen = time.time()
    
    def calculate_region_confidence(self, area: np.ndarray, element_type: str) -> float:
        """Calculate confidence score for a region area."""
        if area.size == 0:
            return 0.0
        
        if element_type == "card":
            return self.base_calibrator.validate_card_region(area)
        elif element_type in ["text", "button", "pot"]:
            text = self.base_calibrator.extract_text(area)
            return min(0.9, len(text.strip()) / 10) if text.strip() else 0.1
        else:
            # Generic confidence based on image properties
            return min(0.8, np.std(area) / 50)  # Higher std = more detail = higher confidence
    
    def should_recalibrate(self) -> bool:
        """Determine if adaptive recalibration is needed."""
        current_time = time.time()
        
        # Check for regions that haven't been seen recently
        stale_regions = 0
        for region_name, adaptive_region in self.adaptive_regions.items():
            time_since_seen = current_time - adaptive_region.last_seen
            if time_since_seen > 30.0:  # 30 seconds without detection
                stale_regions += 1
        
        # Recalibrate if too many regions are stale
        if stale_regions > len(self.adaptive_regions) * 0.3:  # 30% stale
            logger.info(f"Recalibration needed: {stale_regions} stale regions")
            return True
        
        # Check average confidence
        avg_confidence = np.mean([
            np.mean(region.detection_history) 
            for region in self.adaptive_regions.values()
            if region.detection_history
        ])
        
        if avg_confidence < 0.5:
            logger.info(f"Recalibration needed: low confidence {avg_confidence:.1%}")
            return True
        
        return False
    
    def perform_adaptive_recalibration(self, screenshot: np.ndarray):
        """Perform targeted recalibration of problematic regions."""
        logger.info("Performing adaptive recalibration...")
        
        # Full recalibration
        result = self.base_calibrator.auto_calibrate_table()
        
        if result.success_rate > 0.7:  # Accept lower threshold for adaptive updates
            # Update regions that improved
            updated_count = 0
            for name, new_region in result.regions.items():
                if name in self.adaptive_regions:
                    old_confidence = np.mean(self.adaptive_regions[name].detection_history)
                    if new_region.confidence > old_confidence:
                        self.adaptive_regions[name].base_region = new_region
                        self.adaptive_regions[name].last_seen = time.time()
                        self.adaptive_regions[name].detection_history = [new_region.confidence]
                        updated_count += 1
            
            logger.info(f"Adaptive recalibration updated {updated_count} regions")
        else:
            logger.warning(f"Adaptive recalibration failed: {result.success_rate:.1%}")
    
    def get_current_status(self) -> Dict:
        """Get current adaptive calibration status."""
        current_time = time.time()
        
        region_status = {}
        for name, region in self.adaptive_regions.items():
            avg_confidence = np.mean(region.detection_history) if region.detection_history else 0.0
            time_since_seen = current_time - region.last_seen
            
            region_status[name] = {
                "confidence": avg_confidence,
                "last_seen_seconds_ago": time_since_seen,
                "required_phases": list(region.required_phases),
                "currently_expected": any(
                    phase in region.required_phases 
                    for phase in [self.current_phase.phase, "always"]
                ) or any(
                    elem in region.required_phases 
                    for elem in self.current_phase.visible_elements
                )
            }
        
        return {
            "is_running": self.is_running,
            "current_phase": asdict(self.current_phase),
            "regions": region_status,
            "overall_health": self._calculate_overall_health()
        }
    
    def _calculate_overall_health(self) -> float:
        """Calculate overall system health score."""
        if not self.adaptive_regions:
            return 0.0
        
        # Average confidence of all regions
        confidences = [
            np.mean(region.detection_history) 
            for region in self.adaptive_regions.values()
            if region.detection_history
        ]
        
        if not confidences:
            return 0.0
        
        avg_confidence = np.mean(confidences)
        
        # Penalty for stale regions
        current_time = time.time()
        stale_count = sum(
            1 for region in self.adaptive_regions.values()
            if current_time - region.last_seen > 30.0
        )
        
        staleness_penalty = stale_count / len(self.adaptive_regions)
        
        return max(0.0, avg_confidence - staleness_penalty)

# Global adaptive manager instance
adaptive_manager = AdaptiveCalibratorManager()

def start_adaptive_calibration() -> bool:
    """Start adaptive calibration monitoring."""
    return adaptive_manager.start_adaptive_monitoring()

def stop_adaptive_calibration():
    """Stop adaptive calibration monitoring."""
    adaptive_manager.stop_adaptive_monitoring()

def get_adaptive_status() -> Dict:
    """Get current adaptive calibration status."""
    return adaptive_manager.get_current_status()