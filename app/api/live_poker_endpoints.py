"""
API endpoints for live poker monitoring and automated advisory.
Integrates optimized capture system with real-time turn detection.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Optional, Any
import asyncio
import os
import time
import logging

from ..scraper.live_poker_pipeline import LivePokerPipeline, LivePokerState
from ..scraper.optimized_capture import OptimizedScreenCapture
from ..scraper.red_button_detector import RedButtonDetector

logger = logging.getLogger(__name__)

router = APIRouter()

# Global pipeline instance
live_pipeline: Optional[LivePokerPipeline] = None

@router.post("/start-monitoring")
async def start_live_monitoring():
    """Start live poker table monitoring with optimized capture."""
    global live_pipeline
    
    try:
        if live_pipeline and live_pipeline.auto_capture:
            return {"status": "already_running", "message": "Live monitoring already active"}
        
        # Initialize pipeline
        live_pipeline = LivePokerPipeline()
        
        # Initialize components
        if not await live_pipeline.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize live pipeline")
        
        # Start monitoring
        live_pipeline.start_live_monitoring()
        
        return {
            "status": "started",
            "message": "Live poker monitoring started successfully",
            "regions_detected": len(live_pipeline.regions) if live_pipeline.regions else 0,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to start live monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/stop-monitoring")
async def stop_live_monitoring():
    """Stop live poker table monitoring."""
    global live_pipeline
    
    try:
        if not live_pipeline or not live_pipeline.auto_capture:
            return {"status": "not_running", "message": "Live monitoring not active"}
        
        live_pipeline.stop_live_monitoring()
        
        return {
            "status": "stopped", 
            "message": "Live poker monitoring stopped",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop live monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.get("/status")
async def get_live_status():
    """Get current live poker monitoring status."""
    global live_pipeline
    
    try:
        if not live_pipeline:
            return {
                "status": "not_initialized",
                "monitoring_active": False,
                "auto_decisions": False,
                "current_state": None,
                "performance": None
            }
        
        # Get current state
        current_state = live_pipeline.get_current_state()
        performance = live_pipeline.get_performance_stats()
        
        return {
            "status": "initialized",
            "monitoring_active": live_pipeline.auto_capture,
            "auto_decisions": live_pipeline.auto_decisions,
            "current_state": {
                "timestamp": current_state.timestamp if current_state else None,
                "is_my_turn": current_state.is_my_turn if current_state else False,
                "active_buttons": len(current_state.active_buttons) if current_state else 0,
                "decision_recommendation": current_state.decision_recommendation if current_state else None,
                "confidence": current_state.confidence if current_state else 0.0,
                "fps": current_state.fps if current_state else 0
            } if current_state else None,
            "performance": performance,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/enable-auto-decisions")
async def enable_auto_decisions(enable: bool = True):
    """Enable or disable automatic decision generation."""
    global live_pipeline
    
    try:
        if not live_pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not initialized")
        
        live_pipeline.enable_auto_decisions(enable)
        
        return {
            "status": "success",
            "auto_decisions": enable,
            "message": f"Auto decisions {'enabled' if enable else 'disabled'}",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to toggle auto decisions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle auto decisions: {str(e)}")

@router.get("/capture-table")
async def capture_full_table():
    """Capture complete table state including all regions."""
    global live_pipeline
    
    try:
        if not live_pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not initialized")
        
        table_state = await live_pipeline.capture_full_table_state()
        
        if not table_state:
            raise HTTPException(status_code=500, detail="Failed to capture table state")
        
        return {
            "status": "success",
            "table_state": table_state,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to capture table: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to capture table: {str(e)}")

@router.get("/performance")
async def get_performance_stats():
    """Get detailed performance statistics."""
    global live_pipeline
    
    try:
        if not live_pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not initialized")
        
        stats = live_pipeline.get_performance_stats()
        
        return {
            "status": "success",
            "performance": stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance: {str(e)}")

@router.post("/save-debug-frame")
async def save_debug_frame(filename: Optional[str] = None):
    """Save current frame with detection overlay for debugging."""
    global live_pipeline
    
    try:
        if not live_pipeline:
            raise HTTPException(status_code=400, detail="Pipeline not initialized")
        
        result = live_pipeline.save_debug_frame(filename)
        
        return {
            "status": "success",
            "message": result,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to save debug frame: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save debug frame: {str(e)}")

@router.get("/test-capture-performance")
async def test_capture_performance():
    """Test screenshot capture performance."""
    try:
        from ..scraper.optimized_capture import test_capture_performance
        
        # Run performance test (this might take a few seconds)
        test_capture_performance()
        
        return {
            "status": "success",
            "message": "Performance test completed - check server logs for results",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance test failed: {str(e)}")

@router.get("/test-button-detection") 
async def test_button_detection():
    """Test red button detection system."""
    try:
        from ..scraper.red_button_detector import test_red_button_detection
        
        # Run button detection test
        test_red_button_detection()
        
        return {
            "status": "success", 
            "message": "Button detection test completed - check server logs and button_detection_test.png",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Button detection test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Button detection test failed: {str(e)}")

# Health check for live monitoring system
@router.get("/health")
async def live_monitoring_health():
    """Health check for live monitoring system."""
    try:
        # Test core components
        capture_test = OptimizedScreenCapture()
        detector_test = RedButtonDetector()
        
        return {
            "status": "healthy",
            "components": {
                "optimized_capture": "available",
                "red_button_detector": "available", 
                "button_templates": len(detector_test.button_templates),
                "live_pipeline": "initialized" if live_pipeline else "not_initialized"
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }