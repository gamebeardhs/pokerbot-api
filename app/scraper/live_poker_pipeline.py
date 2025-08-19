"""
Complete live poker automation pipeline integrating optimized capture, 
red button detection, and poker decision engine.
"""

import cv2
import numpy as np
import asyncio
import time
import json
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass, asdict
import logging

from .optimized_capture import OptimizedScreenCapture, WindowDetector, CaptureRegion
from .red_button_detector import RedButtonDetector, ButtonDetection, ButtonType
from ..advisor.enhanced_gto_service import EnhancedGTODecisionService
# from ..api.models import TableState, Seat  # Import when needed

logger = logging.getLogger(__name__)

@dataclass
class LivePokerState:
    """Current state of live poker table."""
    timestamp: float
    is_my_turn: bool
    active_buttons: List[ButtonDetection]
    hero_cards: Optional[List[str]]
    board_cards: Optional[List[str]]
    pot_size: Optional[float]
    stack_size: Optional[float]
    position: Optional[str]
    decision_recommendation: Optional[str]
    confidence: float
    fps: int

class LivePokerPipeline:
    """Complete live poker automation pipeline."""
    
    def __init__(self, update_callback: Optional[Callable] = None):
        # Core components
        self.capture_system = OptimizedScreenCapture()
        self.button_detector = RedButtonDetector()
        self.decision_service = EnhancedGTODecisionService()
        
        # State tracking
        self.current_state = None
        self.last_decision_time = 0
        self.decision_cooldown = 1.0  # Minimum time between decisions
        
        # Callback for UI updates
        self.update_callback = update_callback
        
        # Performance monitoring
        self.frame_count = 0
        self.start_time = time.time()
        
        # Configuration
        self.auto_capture = False
        self.auto_decisions = False
        
    async def initialize(self) -> bool:
        """Initialize all pipeline components."""
        try:
            # Detect poker table regions
            self.regions = WindowDetector.get_optimal_regions()
            
            if not self.regions:
                logger.error("Could not detect poker table regions")
                return False
            
            # Test decision service
            if not self.decision_service.is_available():
                logger.error("Poker decision service not available")
                return False
            
            logger.info("Live poker pipeline initialized successfully")
            logger.info(f"Detected regions: {list(self.regions.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            return False
    
    def start_live_monitoring(self):
        """Start live poker table monitoring."""
        if not self.regions:
            logger.error("Pipeline not initialized")
            return
        
        # Start continuous capture of action button area
        button_region = self.regions.get('action_buttons')
        if button_region:
            self.capture_system.start_continuous_capture(
                button_region, 
                self._process_button_frame
            )
            self.auto_capture = True
            logger.info("Started live poker monitoring")
        else:
            logger.error("No action button region detected")
    
    def stop_live_monitoring(self):
        """Stop live poker table monitoring."""
        self.auto_capture = False
        self.capture_system.stop_capture()
        logger.info("Stopped live poker monitoring")
    
    def _process_button_frame(self, frame: np.ndarray, region_name: str):
        """Process captured button frame for turn detection."""
        try:
            # Detect buttons and determine if it's my turn
            is_turn, detections = self.button_detector.is_my_turn(frame)
            
            # Update state
            current_time = time.time()
            fps = self.capture_system.get_fps()
            
            state = LivePokerState(
                timestamp=current_time,
                is_my_turn=is_turn,
                active_buttons=[d for d in detections if d.is_active],
                hero_cards=None,  # Would need separate capture/OCR
                board_cards=None,  # Would need separate capture/OCR
                pot_size=None,    # Would need separate capture/OCR
                stack_size=None,  # Would need separate capture/OCR
                position=None,    # Would need to determine from seat
                decision_recommendation=None,
                confidence=max([d.confidence for d in detections], default=0.0),
                fps=fps
            )
            
            # Generate decision if it's my turn and auto-decisions enabled
            if is_turn and self.auto_decisions:
                if current_time - self.last_decision_time > self.decision_cooldown:
                    decision = self._generate_decision(state)
                    state.decision_recommendation = decision
                    self.last_decision_time = current_time
            
            self.current_state = state
            
            # Notify UI if callback provided
            if self.update_callback:
                self.update_callback(state)
            
            self.frame_count += 1
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
    
    def _generate_decision(self, state: LivePokerState) -> Optional[str]:
        """Generate poker decision based on current state."""
        try:
            # For now, return simple rule-based decision
            # In full implementation, would capture cards/pot/stack info
            
            active_button_types = [b.button_type for b in state.active_buttons]
            
            if ButtonType.FOLD in active_button_types:
                if ButtonType.CALL in active_button_types:
                    # Facing a bet - use conservative logic
                    return "call" if state.confidence > 0.8 else "fold"
                else:
                    # No bet to call - check or bet
                    return "check"
            
            return "check"  # Safe default
            
        except Exception as e:
            logger.error(f"Decision generation failed: {e}")
            return None
    
    async def capture_full_table_state(self) -> Optional[Dict[str, Any]]:
        """Capture complete table state including cards, pot, stacks."""
        try:
            if not self.regions:
                return None
            
            # Capture different regions
            full_table = self.capture_system.capture_region_sync(self.regions['full_table'])
            hero_cards = self.capture_system.capture_region_sync(self.regions['hero_cards'])
            board_cards = self.capture_system.capture_region_sync(self.regions['board_cards'])
            pot_area = self.capture_system.capture_region_sync(self.regions['pot_area'])
            
            # TODO: Add OCR processing for text extraction
            # TODO: Add card recognition
            # TODO: Add stack/pot size parsing
            
            return {
                'timestamp': time.time(),
                'full_table_captured': full_table is not None,
                'hero_cards_captured': hero_cards is not None,
                'board_cards_captured': board_cards is not None,
                'pot_area_captured': pot_area is not None,
                'regions_available': list(self.regions.keys())
            }
            
        except Exception as e:
            logger.error(f"Full table capture failed: {e}")
            return None
    
    def get_current_state(self) -> Optional[LivePokerState]:
        """Get current poker state."""
        return self.current_state
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        return {
            'frames_processed': self.frame_count,
            'elapsed_time': elapsed,
            'average_fps': avg_fps,
            'current_fps': self.capture_system.get_fps(),
            'auto_capture': self.auto_capture,
            'auto_decisions': self.auto_decisions,
            'regions_detected': len(self.regions) if self.regions else 0
        }
    
    def enable_auto_decisions(self, enable: bool = True):
        """Enable/disable automatic decision generation."""
        self.auto_decisions = enable
        logger.info(f"Auto decisions {'enabled' if enable else 'disabled'}")
    
    def save_debug_frame(self, filename: str = None) -> str:
        """Save current frame with detection overlay for debugging."""
        try:
            if not self.current_state:
                return "No current frame to save"
            
            # Get latest frame
            frame_data = self.capture_system.get_latest_frame()
            if not frame_data:
                return "No frame available"
            
            frame = frame_data['frame']
            
            # Add detection overlay
            annotated = self.button_detector.visualize_detections(
                frame, self.current_state.active_buttons
            )
            
            # Add state information
            cv2.putText(annotated, f"FPS: {self.current_state.fps}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated, f"My Turn: {self.current_state.is_my_turn}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Save with timestamp if no filename provided
            if filename is None:
                filename = f"poker_debug_{int(time.time())}.png"
            
            cv2.imwrite(filename, annotated)
            return f"Debug frame saved to {filename}"
            
        except Exception as e:
            logger.error(f"Failed to save debug frame: {e}")
            return f"Error: {e}"

# Test function
async def test_live_pipeline():
    """Test the complete live poker pipeline."""
    print("Testing Live Poker Pipeline...")
    
    pipeline = LivePokerPipeline()
    
    # Initialize
    if not await pipeline.initialize():
        print("❌ Pipeline initialization failed")
        return
    
    print("✅ Pipeline initialized successfully")
    
    # Test performance
    print("\nTesting capture performance...")
    stats = pipeline.get_performance_stats()
    print(f"Regions detected: {stats['regions_detected']}")
    
    # Test single table capture
    table_state = await pipeline.capture_full_table_state()
    if table_state:
        print("✅ Table state capture working")
        print(f"Captured regions: {table_state['regions_available']}")
    else:
        print("❌ Table state capture failed")
    
    # Test button detection
    print("\nTesting button detection...")
    pipeline.start_live_monitoring()
    
    # Monitor for 10 seconds
    for i in range(10):
        await asyncio.sleep(1)
        state = pipeline.get_current_state()
        
        if state:
            print(f"Turn {i+1}: FPS={state.fps}, My turn={state.is_my_turn}, "
                  f"Active buttons={len(state.active_buttons)}")
        else:
            print(f"Turn {i+1}: No state detected")
    
    pipeline.stop_live_monitoring()
    
    # Final stats
    final_stats = pipeline.get_performance_stats()
    print(f"\nFinal Performance:")
    print(f"Frames processed: {final_stats['frames_processed']}")
    print(f"Average FPS: {final_stats['average_fps']:.1f}")
    print(f"Current FPS: {final_stats['current_fps']}")

if __name__ == "__main__":
    asyncio.run(test_live_pipeline())