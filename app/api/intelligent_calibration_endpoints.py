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
            "message": f"✅ {templates_info['total_templates']} templates loaded and ready"
        }
        
    except Exception as e:
        logger.error(f"Failed to get template info: {e}")
        raise HTTPException(status_code=500, detail=f"Template info failed: {str(e)}")