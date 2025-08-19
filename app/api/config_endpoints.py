"""
Configuration management endpoints for runtime tuning without code rebuilds.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.utils.config_loader import config_loader

router = APIRouter(prefix="/config", tags=["configuration"])
logger = logging.getLogger(__name__)

@router.get("/current")
async def get_current_config():
    """Get current runtime configuration."""
    return {
        "config_path": config_loader.config_path,
        "config": config_loader.config,
        "status": "loaded"
    }

@router.get("/fps-settings")
async def get_fps_settings():
    """Get FPS timing configuration."""
    return config_loader.get_fps_settings()

@router.get("/ocr-settings") 
async def get_ocr_settings():
    """Get OCR PSM settings for different field types."""
    return config_loader.get_ocr_settings()

@router.get("/timer-detection")
async def get_timer_detection():
    """Get timer detection HSV ranges and thresholds."""
    return config_loader.get_timer_detection_settings()

@router.get("/default-regions")
async def get_default_regions():
    """Get default ACR table regions."""
    regions = config_loader.get_default_regions()
    return {
        "regions": regions,
        "count": len(regions),
        "description": "Relative coordinates (rx, ry, rw, rh) as percentages"
    }

@router.post("/update-fps")
async def update_fps_settings(fps_config: Dict[str, float]):
    """Update FPS timing settings."""
    try:
        current_config = config_loader.config.copy()
        
        if "fps_timing" not in current_config:
            current_config["fps_timing"] = {}
            
        # Update only provided values
        for key, value in fps_config.items():
            if key in ["min_delay", "max_delay", "base_fps"]:
                current_config["fps_timing"][key] = value
        
        # Save updated config
        success = config_loader.save_config(current_config)
        
        if success:
            return {
                "status": "updated",
                "new_fps_settings": config_loader.get_fps_settings()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
    except Exception as e:
        logger.error(f"Failed to update FPS settings: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-timer-colors")
async def update_timer_colors(timer_config: Dict[str, Any]):
    """Update timer detection HSV color ranges."""
    try:
        current_config = config_loader.config.copy()
        
        if "timer_detection" not in current_config:
            current_config["timer_detection"] = {}
        
        # Update HSV ranges if provided
        if "hsv_ranges" in timer_config:
            current_config["timer_detection"]["hsv_ranges"] = timer_config["hsv_ranges"]
            
        # Update pixel threshold if provided
        if "pixel_threshold" in timer_config:
            current_config["timer_detection"]["pixel_threshold"] = timer_config["pixel_threshold"]
        
        # Save updated config
        success = config_loader.save_config(current_config)
        
        if success:
            return {
                "status": "updated", 
                "new_timer_settings": config_loader.get_timer_detection_settings()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
    except Exception as e:
        logger.error(f"Failed to update timer settings: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reload")
async def reload_configuration():
    """Reload configuration from file."""
    success = config_loader.reload_config()
    
    if success:
        return {
            "status": "reloaded",
            "config_path": config_loader.config_path,
            "loaded_sections": list(config_loader.config.keys())
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to reload configuration")

@router.get("/validate")
async def validate_configuration():
    """Validate current configuration for completeness and correctness."""
    validation_results = {
        "valid": True,
        "warnings": [],
        "errors": []
    }
    
    # Check required sections
    required_sections = ["fps_timing", "state_stabilization", "ocr_settings", "timer_detection"]
    for section in required_sections:
        if section not in config_loader.config:
            validation_results["errors"].append(f"Missing required section: {section}")
            validation_results["valid"] = False
    
    # Check FPS timing values
    fps_settings = config_loader.get_fps_settings()
    if fps_settings["min_delay"] >= fps_settings["max_delay"]:
        validation_results["errors"].append("min_delay must be less than max_delay")
        validation_results["valid"] = False
    
    if fps_settings["base_fps"] <= 0:
        validation_results["errors"].append("base_fps must be positive")
        validation_results["valid"] = False
    
    # Check stabilizer settings
    stabilizer_settings = config_loader.get_stabilizer_settings()
    if stabilizer_settings["debounce_readings"] < 1:
        validation_results["errors"].append("debounce_readings must be >= 1")
        validation_results["valid"] = False
    
    # Check regions if present
    regions = config_loader.get_default_regions()
    for region_name, coords in regions.items():
        if len(coords) != 4:
            validation_results["errors"].append(f"Region {region_name} must have 4 coordinates")
            validation_results["valid"] = False
            continue
            
        rx, ry, rw, rh = coords
        if not (0.0 <= rx <= 1.0 and 0.0 <= ry <= 1.0 and 
                0.0 <= rw <= 1.0 and 0.0 <= rh <= 1.0):
            validation_results["errors"].append(f"Region {region_name} coordinates must be 0.0-1.0")
            validation_results["valid"] = False
            
        if rx + rw > 1.0 or ry + rh > 1.0:
            validation_results["warnings"].append(f"Region {region_name} extends beyond window bounds")
    
    return validation_results