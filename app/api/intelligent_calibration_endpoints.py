"""
API endpoints for intelligent ACR table calibration.
Professional poker bot calibration with 95%+ accuracy guarantee.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from app.scraper.intelligent_calibrator import IntelligentACRCalibrator, CalibrationResult

logger = logging.getLogger(__name__)
router = APIRouter()

# Global calibrator instance
intelligent_calibrator = IntelligentACRCalibrator()

@router.post("/auto-calibrate")
async def auto_calibrate_acr_table() -> Dict[str, Any]:
    """Automatically detect and calibrate ACR poker table with 95%+ accuracy."""
    try:
        logger.info("Starting intelligent auto-calibration...")
        
        # Perform auto-calibration
        result = intelligent_calibrator.auto_calibrate_table()
        
        # Determine success based on accuracy threshold
        success = result.success_rate >= 0.95
        
        response = {
            "success": success,
            "table_detected": result.table_detected,
            "accuracy_score": result.accuracy_score,
            "success_rate": result.success_rate,
            "regions_found": len(result.regions),
            "validation_tests": result.validation_tests,
            "timestamp": result.timestamp
        }
        
        if success:
            response["message"] = f"🎯 Auto-calibration successful! {result.success_rate:.1%} accuracy achieved"
            response["regions"] = {name: {
                "x": region.x,
                "y": region.y, 
                "width": region.width,
                "height": region.height,
                "confidence": region.confidence,
                "type": region.element_type
            } for name, region in result.regions.items()}
        else:
            response["message"] = f"⚠️ Auto-calibration below target: {result.success_rate:.1%} < 95%"
            response["recommendations"] = [
                "Ensure ACR poker client is open and visible",
                "Make sure a poker table is active (not lobby)",
                "Check that table is not minimized or obscured",
                "Try with a different table or game type"
            ]
        
        return response
        
    except Exception as e:
        logger.error(f"Auto-calibration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-calibration failed: {str(e)}")

@router.get("/local-debug")
async def debug_local_detection() -> Dict[str, Any]:
    """Debug detection issues for local setup."""
    try:
        # Run the debug script and get results
        import subprocess
        import json
        
        # Execute debug script
        result = subprocess.run(
            ['python', 'test_screenshot.py'], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            return {
                "debug_success": False,
                "error": result.stderr,
                "explanation": "Debug script failed to run",
                "local_setup_issue": True
            }
        
        # Parse the output to extract the JSON result
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            if line.startswith('📊 Debug Results:'):
                try:
                    json_str = line.replace('📊 Debug Results: ', '')
                    debug_data = json.loads(json_str)
                    break
                except:
                    continue
        else:
            debug_data = {"parsed": False}
        
        return {
            "debug_success": True,
            "local_detection": True,
            "debug_output": result.stdout,
            "debug_data": debug_data,
            "files_created": ["debug_screenshot.png", "debug_annotated.png"],
            "next_steps": [
                "Check debug_screenshot.png to see what was captured",
                "Ensure ACR poker client is visible and not minimized",
                "If using Replit remotely, you need local client setup"
            ]
        }
        
    except Exception as e:
        return {
            "debug_success": False,
            "error": str(e),
            "explanation": "Local debugging requires direct desktop access"
        }

@router.get("/detect-table")
async def detect_acr_table() -> Dict[str, Any]:
    """Detect if ACR poker table is currently open and active."""
    try:
        table_detected, table_info = intelligent_calibrator.detect_acr_table()
        
        return {
            "table_detected": table_detected,
            "confidence": table_info.get("confidence", 0.0),
            "features_found": {
                "card_regions": len(table_info.get("features", {}).get("card_regions", [])),
                "buttons": len(table_info.get("features", {}).get("buttons", [])),
                "text_regions": len(table_info.get("features", {}).get("text_regions", [])),
                "circular_elements": len(table_info.get("features", {}).get("circular_elements", []))
            },
            "acr_indicators": table_info.get("indicators", {}),
            "screenshot_resolution": table_info.get("screenshot_shape", [0, 0])[:2],
            "message": "✅ ACR table detected and ready for calibration" if table_detected else
                      "❌ No ACR table detected - please open poker client"
        }
        
    except Exception as e:
        logger.error(f"Table detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Table detection failed: {str(e)}")

@router.get("/calibration-status")
async def get_calibration_status() -> Dict[str, Any]:
    """Get current calibration status and accuracy metrics."""
    try:
        import json
        from pathlib import Path
        
        calibration_file = Path("acr_auto_calibration_results.json")
        
        if calibration_file.exists():
            with open(calibration_file, 'r') as f:
                data = json.load(f)
            
            return {
                "calibrated": True,
                "accuracy_score": data.get("accuracy_score", 0.0),
                "success_rate": data.get("success_rate", 0.0),
                "regions_count": len(data.get("regions", {})),
                "last_calibration": data.get("timestamp", "Unknown"),
                "validation_passed": sum(data.get("validation_tests", {}).values()),
                "validation_total": len(data.get("validation_tests", {})),
                "meets_requirements": data.get("success_rate", 0.0) >= 0.95,
                "message": "✅ System calibrated and ready" if data.get("success_rate", 0.0) >= 0.95 else
                          "⚠️ Calibration below target accuracy"
            }
        else:
            return {
                "calibrated": False,
                "accuracy_score": 0.0,
                "success_rate": 0.0,
                "message": "❌ No calibration data found - run auto-calibration first"
            }
            
    except Exception as e:
        logger.error(f"Failed to get calibration status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/manual-calibrate-region")
async def manual_calibrate_region(region_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manually calibrate a specific region for fine-tuning."""
    try:
        required_fields = ["name", "x", "y", "width", "height", "element_type"]
        missing_fields = [field for field in required_fields if field not in region_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {missing_fields}"
            )
        
        # Validate region using screenshot
        screenshot = intelligent_calibrator.capture_screen()
        x, y, w, h = region_data["x"], region_data["y"], region_data["width"], region_data["height"]
        
        # Extract region
        region = screenshot[y:y+h, x:x+w]
        
        # Validate based on element type
        confidence = 0.5  # Default confidence
        if region_data["element_type"] == "card":
            confidence = intelligent_calibrator.validate_card_region(region)
        elif region_data["element_type"] in ["text", "button", "pot"]:
            text = intelligent_calibrator.extract_text(region)
            confidence = min(0.9, len(text.strip()) / 10) if text.strip() else 0.3
        
        return {
            "success": True,
            "region_name": region_data["name"],
            "confidence": confidence,
            "validated": confidence > 0.4,
            "extracted_content": intelligent_calibrator.extract_text(region) if region_data["element_type"] != "card" else "Card region",
            "message": f"✅ Region '{region_data['name']}' validated with {confidence:.1%} confidence"
        }
        
    except Exception as e:
        logger.error(f"Manual calibration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Manual calibration failed: {str(e)}")

@router.post("/start-adaptive")
async def start_adaptive_calibration() -> Dict[str, Any]:
    """Start continuous adaptive calibration for all poker phases."""
    try:
        from app.scraper.adaptive_calibrator import start_adaptive_calibration
        
        success = start_adaptive_calibration()
        
        if success:
            return {
                "success": True,
                "message": "🔄 Adaptive calibration started - automatically adjusts to poker phases",
                "features": [
                    "Continuous monitoring every 500ms",
                    "Automatic phase detection (preflop, flop, turn, river)",
                    "Dynamic element tracking (cards, buttons, bets)",
                    "Auto-recalibration when accuracy drops",
                    "Handles all poker table states"
                ],
                "monitoring": "System now adapts to: hole cards visibility, action buttons, community cards, betting phases"
            }
        else:
            return {
                "success": False,
                "message": "❌ Failed to start adaptive calibration - ensure ACR table is detected first",
                "recommendation": "Run /detect-table first to ensure table is visible"
            }
            
    except Exception as e:
        logger.error(f"Failed to start adaptive calibration: {e}")
        raise HTTPException(status_code=500, detail=f"Adaptive calibration failed: {str(e)}")

@router.post("/stop-adaptive")
async def stop_adaptive_calibration() -> Dict[str, Any]:
    """Stop continuous adaptive calibration."""
    try:
        from app.scraper.adaptive_calibrator import stop_adaptive_calibration
        
        stop_adaptive_calibration()
        
        return {
            "success": True,
            "message": "⏹️ Adaptive calibration stopped",
            "status": "System returned to manual calibration mode"
        }
        
    except Exception as e:
        logger.error(f"Failed to stop adaptive calibration: {e}")
        raise HTTPException(status_code=500, detail=f"Stop adaptive failed: {str(e)}")

@router.get("/adaptive-status")
async def get_adaptive_calibration_status() -> Dict[str, Any]:
    """Get current adaptive calibration status and phase detection."""
    try:
        from app.scraper.adaptive_calibrator import get_adaptive_status
        
        status = get_adaptive_status()
        
        current_phase = status.get("current_phase", {})
        overall_health = status.get("overall_health", 0.0)
        
        # Count regions by status
        regions = status.get("regions", {})
        healthy_regions = sum(1 for r in regions.values() if r.get("confidence", 0) > 0.7)
        total_regions = len(regions)
        
        return {
            "success": True,
            "adaptive_running": status.get("is_running", False),
            "current_phase": {
                "game_phase": current_phase.get("phase", "unknown"),
                "hero_in_hand": current_phase.get("hero_in_hand", False),
                "hero_turn": current_phase.get("hero_turn", False),
                "community_cards": current_phase.get("community_cards_count", 0),
                "betting_active": current_phase.get("betting_round_active", False)
            },
            "system_health": {
                "overall_score": f"{overall_health:.1%}",
                "healthy_regions": f"{healthy_regions}/{total_regions}",
                "status": "Excellent" if overall_health > 0.9 else "Good" if overall_health > 0.7 else "Fair" if overall_health > 0.5 else "Poor"
            },
            "visible_elements": list(current_phase.get("visible_elements", [])),
            "region_details": regions,
            "message": f"🔄 Adaptive calibration {'running' if status.get('is_running') else 'stopped'} - {overall_health:.1%} health"
        }
        
    except Exception as e:
        logger.error(f"Failed to get adaptive status: {e}")
        raise HTTPException(status_code=500, detail=f"Adaptive status failed: {str(e)}")

@router.get("/calibration-templates")
async def get_calibration_templates() -> Dict[str, Any]:
    """Get available calibration templates and reference data."""
    try:
        templates_info = {
            "card_templates": len(intelligent_calibrator.templates),
            "ui_templates": len([k for k in intelligent_calibrator.templates.keys() if k.startswith("ui_")]),
            "total_templates": len(intelligent_calibrator.templates),
            "template_list": list(intelligent_calibrator.templates.keys())
        }
        
        return {
            "success": True,
            "templates": templates_info,
            "calibration_requirements": {
                "minimum_accuracy": "95%",
                "required_regions": ["hero_cards", "action_buttons", "pot", "community_cards"],
                "validation_tests": 5,
                "confidence_threshold": 0.7
            },
            "adaptive_features": {
                "continuous_monitoring": "Every 500ms",
                "phase_detection": ["preflop", "flop", "turn", "river", "showdown", "between_hands"],
                "dynamic_elements": ["hole_cards", "community_cards", "action_buttons", "bets", "pot"],
                "auto_recalibration": "When accuracy drops below threshold"
            },
            "message": f"✅ {templates_info['total_templates']} templates loaded and ready"
        }
        
    except Exception as e:
        logger.error(f"Failed to get template info: {e}")
        raise HTTPException(status_code=500, detail=f"Template info failed: {str(e)}")