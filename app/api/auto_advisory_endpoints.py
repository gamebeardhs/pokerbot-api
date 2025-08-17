"""
Automated ACR Advisory System - Continuously monitors for turn detection
and automatically provides GTO recommendations when it's your turn to act.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from threading import Thread, Event
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import numpy as np

from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
from app.scraper.manual_trigger import ManualTriggerService
from app.advisor.enhanced_gto_service import EnhancedGTODecisionService

logger = logging.getLogger(__name__)
router = APIRouter()

class AutoAdvisoryService:
    """Automated turn detection and GTO advisory service."""
    
    def __init__(self):
        self.calibrator = IntelligentACRCalibrator()
        self.gto_service = EnhancedGTODecisionService()
        self.trigger_service = ManualTriggerService(self.gto_service)
        
        self.monitoring = False
        self.stop_event = Event()
        self.monitor_thread = None
        
        # Turn detection state
        self.last_button_state = None
        self.turn_detected = False
        self.last_analysis_time = 0
        
        # Advisory results
        self.latest_advice = None
        self.advice_history = []
        
    def start_monitoring(self):
        """Start continuous ACR table monitoring."""
        if self.monitoring:
            return {"status": "already_running"}
            
        self.monitoring = True
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🤖 Automated ACR advisory started - monitoring for your turn")
        return {"status": "started", "message": "Monitoring ACR table for your turn to act"}
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        if not self.monitoring:
            return {"status": "not_running"}
            
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            
        logger.info("🛑 Automated ACR advisory stopped")
        return {"status": "stopped"}
    
    def _monitor_loop(self):
        """Main monitoring loop that detects turns and provides advice."""
        logger.info("🔄 Starting ACR monitoring loop...")
        
        while self.monitoring and not self.stop_event.is_set():
            try:
                # Check if it's your turn to act
                turn_detected = self._detect_turn_to_act()
                
                if turn_detected and not self.turn_detected:
                    # New turn detected - provide GTO advice
                    logger.info("🎯 Your turn detected - analyzing hand...")
                    advice = self._get_automated_advice()
                    
                    if advice:
                        self.latest_advice = advice
                        self.advice_history.append({
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "advice": advice
                        })
                        # Keep only last 10 hands
                        if len(self.advice_history) > 10:
                            self.advice_history.pop(0)
                            
                        logger.info(f"💡 GTO Advice: {advice.get('action', 'N/A')} - {advice.get('reasoning', 'N/A')}")
                
                self.turn_detected = turn_detected
                
                # Sleep between checks (don't overwhelm the system)
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(2.0)  # Longer sleep on error
    
    def _detect_turn_to_act(self) -> bool:
        """Detect if it's currently your turn to act."""
        try:
            # Take screenshot and look for active action buttons
            screenshot = self.calibrator.capture_screen()
            
            # Check for highlighted/active buttons (your turn indicators)
            active_buttons = self._detect_active_buttons(screenshot)
            
            # Compare with previous state to detect new turn
            current_state = {
                "active_buttons": len(active_buttons),
                "timestamp": time.time()
            }
            
            # Only trigger if buttons became active (new turn)
            if self.last_button_state is None:
                self.last_button_state = current_state
                return False
                
            # Detect transition to active state
            was_inactive = self.last_button_state["active_buttons"] == 0
            now_active = current_state["active_buttons"] >= 2  # At least 2 buttons (fold/call or call/raise)
            
            self.last_button_state = current_state
            
            # Return True if transition from inactive to active
            return was_inactive and now_active
            
        except Exception as e:
            logger.error(f"Turn detection error: {e}")
            return False
    
    def _detect_active_buttons(self, screenshot: np.ndarray) -> list:
        """Detect active/highlighted action buttons indicating your turn."""
        # Simple button detection - look for bright colored rectangular regions
        if len(screenshot.shape) == 3:
            # Convert to HSV for better color detection
            import cv2
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_RGB2HSV)
            
            # Look for bright button colors (green for call, red for fold, blue for raise)
            bright_mask = cv2.inRange(hsv, np.array([0, 50, 100]), np.array([180, 255, 255]))
            
            # Find contours (button regions)
            contours, _ = cv2.findContours(bright_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter for button-sized rectangles
            buttons = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Button size filters (typical poker client buttons)
                if 50 < w < 200 and 20 < h < 60:
                    buttons.append({"x": x, "y": y, "w": w, "h": h})
            
            return buttons
        
        return []
    
    def _get_automated_advice(self) -> Optional[Dict[str, Any]]:
        """Get automated GTO advice for current hand."""
        try:
            # Prevent rapid-fire analysis
            if time.time() - self.last_analysis_time < 5.0:
                return None
            self.last_analysis_time = time.time()
            
            # Use manual trigger service to analyze current table state
            result = self.trigger_service.analyze_current_hand()
            
            if result and "error" not in result:
                return {
                    "action": result.get("recommended_action", "CHECK"),
                    "bet_size": result.get("bet_sizing", ""),
                    "equity": result.get("equity", {}).get("total", 0),
                    "confidence": result.get("confidence", "MEDIUM"),
                    "reasoning": result.get("reasoning", ""),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "automated": True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Automated advice error: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "monitoring": self.monitoring,
            "turn_detected": self.turn_detected,
            "latest_advice": self.latest_advice,
            "advice_count": len(self.advice_history),
            "last_check": time.strftime("%Y-%m-%d %H:%M:%S")
        }

# Global service instance
auto_advisory = AutoAdvisoryService()

@router.post("/start")
async def start_auto_advisory():
    """Start automated ACR table monitoring and advisory."""
    result = auto_advisory.start_monitoring()
    return JSONResponse(content=result)

@router.post("/stop") 
async def stop_auto_advisory():
    """Stop automated monitoring."""
    result = auto_advisory.stop_monitoring()
    return JSONResponse(content=result)

@router.get("/status")
async def get_auto_advisory_status():
    """Get current status of automated advisory system."""
    status = auto_advisory.get_status()
    return JSONResponse(content=status)

@router.get("/latest-advice")
async def get_latest_advice():
    """Get the most recent automated advice."""
    if auto_advisory.latest_advice:
        return JSONResponse(content=auto_advisory.latest_advice)
    else:
        raise HTTPException(status_code=404, detail="No advice available yet")

@router.get("/advice-history") 
async def get_advice_history():
    """Get history of automated advice for recent hands."""
    return JSONResponse(content={
        "history": auto_advisory.advice_history,
        "total_hands": len(auto_advisory.advice_history)
    })