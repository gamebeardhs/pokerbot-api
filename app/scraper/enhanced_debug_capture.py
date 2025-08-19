"""
Enhanced debug capture with comprehensive environment info and triage data.
"""

import os
import json
import cv2
import time
import sys
import platform
import pytesseract
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def get_environment_info() -> Dict[str, Any]:
    """Collect comprehensive environment information for debugging."""
    env_info = {
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "system": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "python_version": sys.version,
        },
        "display": {
            "dpi_aware": False,
            "scaling_factor": 1.0,
        }
    }
    
    # Windows-specific info
    if os.name == "nt":
        try:
            from app.utils.bootstrap_dpi import get_dpi_scaling
            env_info["display"]["scaling_factor"] = get_dpi_scaling()
            env_info["display"]["dpi_aware"] = True
        except Exception as e:
            logger.debug(f"Could not get DPI info: {e}")
    
    # Tesseract info
    try:
        env_info["tesseract"] = {
            "path": pytesseract.pytesseract.tesseract_cmd,
            "version": pytesseract.get_tesseract_version(),
        }
    except Exception as e:
        env_info["tesseract"] = {"error": str(e)}
    
    return env_info

class EnhancedDebugCapture:
    """Enhanced debug capture with full triage capabilities."""
    
    def __init__(self, base_dir: str = "captures"):
        """Initialize enhanced debug capture."""
        self.base_dir = base_dir
        self.session_dir = None
        self.hand_count = 0
        
    def create_session_dir(self) -> str:
        """Create timestamped session directory."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_dir = os.path.join(self.base_dir, timestamp)
        
        # Create directory structure
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Save environment info immediately
        env_info = get_environment_info()
        env_path = os.path.join(self.session_dir, "env.json")
        with open(env_path, 'w', encoding='utf-8') as f:
            json.dump(env_info, f, indent=2)
            
        logger.info(f"Debug session created: {self.session_dir}")
        return self.session_dir
    
    def save_full_debug_bundle(self, capturer, ocr_engine, regions: Dict[str, tuple], 
                               table_state: Optional[Dict] = None, 
                               error_context: str = ""):
        """Save complete debug bundle for triage."""
        if not self.session_dir:
            self.create_session_dir()
        
        self.hand_count += 1
        bundle_data = {
            "hand_number": self.hand_count,
            "timestamp": datetime.now().isoformat(),
            "error_context": error_context,
            "regions_used": regions,
            "ocr_results": {},
            "image_files": [],
            "table_state": table_state
        }
        
        try:
            # Capture full table
            full_img, window_size = capturer.capture_full_window()
            if full_img is not None:
                full_path = os.path.join(self.session_dir, "table_full.png")
                cv2.imwrite(full_path, full_img)
                bundle_data["image_files"].append("table_full.png")
                bundle_data["window_size"] = window_size
            
            # Capture and OCR each region
            for region_name, rel_coords in regions.items():
                try:
                    # Capture region
                    region_img, _ = capturer.capture_region(rel_coords)
                    if region_img is not None:
                        # Save image
                        img_filename = f"{region_name}.png"
                        img_path = os.path.join(self.session_dir, img_filename)
                        cv2.imwrite(img_path, region_img)
                        bundle_data["image_files"].append(img_filename)
                        
                        # Run OCR
                        field_type = self._get_field_type(region_name)
                        raw_text = ocr_engine.extract_text(region_img, field_type)
                        normalized = ocr_engine.text(region_img, field_type) 
                        
                        bundle_data["ocr_results"][region_name] = {
                            "raw": raw_text,
                            "normalized": normalized,
                            "field_type": field_type,
                            "region_coords": rel_coords
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to process region {region_name}: {e}")
                    bundle_data["ocr_results"][region_name] = {"error": str(e)}
            
            # Save bundle JSON
            bundle_path = os.path.join(self.session_dir, f"debug_bundle_hand_{self.hand_count:03d}.json")
            with open(bundle_path, 'w', encoding='utf-8') as f:
                json.dump(bundle_data, f, indent=2)
                
            logger.info(f"Debug bundle saved: hand_{self.hand_count:03d}")
            
        except Exception as e:
            logger.error(f"Failed to save debug bundle: {e}")
    
    def _get_field_type(self, region_name: str) -> str:
        """Map region names to OCR field types."""
        field_mapping = {
            "pot": "money",
            "hero_stack": "stack", 
            "buttons": "buttons",
            "hero_timer_arc": "timer",
        }
        
        # Handle player names/stacks
        if "name" in region_name:
            return "name"
        elif "stack" in region_name:
            return "stack"
        
        return field_mapping.get(region_name, "general")
    
    def save_calibration_debug(self, window_info: Dict, regions: Dict[str, tuple]):
        """Save calibration debugging info."""
        if not self.session_dir:
            self.create_session_dir()
        
        calibration_debug = {
            "timestamp": datetime.now().isoformat(),
            "window_info": window_info,
            "relative_regions": regions,
            "validation": {}
        }
        
        # Validate regions
        from app.utils.regions import validate_relative_regions
        calibration_debug["validation"]["regions_valid"] = validate_relative_regions(regions)
        
        # Save calibration debug
        cal_path = os.path.join(self.session_dir, "calibration_debug.json")
        with open(cal_path, 'w', encoding='utf-8') as f:
            json.dump(calibration_debug, f, indent=2)
        
        logger.info("Calibration debug info saved")

# Global enhanced debug capture instance  
enhanced_debug_capture = EnhancedDebugCapture()