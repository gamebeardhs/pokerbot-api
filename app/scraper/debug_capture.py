"""
Debug capture system for poker table analysis.
Saves screenshots and OCR results for troubleshooting and optimization.
"""

import os
import json
import cv2
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DebugCapture:
    """Handles debug capture and logging for poker table analysis."""
    
    def __init__(self, base_dir: str = "debug_captures"):
        """Initialize debug capture system."""
        self.base_dir = base_dir
        self.session_dir = None
        self.session_id = None
        self.hand_count = 0
        
    def start_session(self) -> str:
        """Start a new debug session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"session_{timestamp}"
        self.session_dir = os.path.join(self.base_dir, self.session_id)
        
        # Create directory structure
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, "full_table"), exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, "regions"), exist_ok=True)
        os.makedirs(os.path.join(self.session_dir, "ocr_data"), exist_ok=True)
        
        logger.info(f"Started debug session: {self.session_id}")
        return self.session_dir
    
    def new_hand(self) -> int:
        """Start capturing for a new hand."""
        self.hand_count += 1
        return self.hand_count
    
    def save_full_table(self, img_bgr, hand_num: Optional[int] = None):
        """Save full table screenshot."""
        if not self.session_dir:
            self.start_session()
        
        hand_num = hand_num or self.hand_count
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"hand_{hand_num:03d}_{timestamp}_table.png"
        filepath = os.path.join(self.session_dir, "full_table", filename)
        
        try:
            cv2.imwrite(filepath, img_bgr)
            logger.debug(f"Saved full table: {filename}")
        except Exception as e:
            logger.error(f"Failed to save full table: {e}")
    
    def save_region(self, region_name: str, img_bgr, hand_num: Optional[int] = None):
        """Save specific region screenshot."""
        if not self.session_dir:
            self.start_session()
        
        hand_num = hand_num or self.hand_count
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"hand_{hand_num:03d}_{timestamp}_{region_name}.png"
        filepath = os.path.join(self.session_dir, "regions", filename)
        
        try:
            cv2.imwrite(filepath, img_bgr)
            logger.debug(f"Saved region {region_name}: {filename}")
        except Exception as e:
            logger.error(f"Failed to save region {region_name}: {e}")
    
    def save_ocr_data(self, ocr_results: Dict[str, Any], hand_num: Optional[int] = None):
        """Save OCR extraction results."""
        if not self.session_dir:
            self.start_session()
        
        hand_num = hand_num or self.hand_count
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"hand_{hand_num:03d}_{timestamp}_ocr.json"
        filepath = os.path.join(self.session_dir, "ocr_data", filename)
        
        # Add metadata
        data = {
            "timestamp": timestamp,
            "hand_number": hand_num,
            "session_id": self.session_id,
            "ocr_results": ocr_results
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved OCR data: {filename}")
        except Exception as e:
            logger.error(f"Failed to save OCR data: {e}")
    
    def save_table_state(self, table_state: Dict[str, Any], hand_num: Optional[int] = None):
        """Save complete table state analysis."""
        if not self.session_dir:
            self.start_session()
        
        hand_num = hand_num or self.hand_count
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"hand_{hand_num:03d}_{timestamp}_state.json"
        filepath = os.path.join(self.session_dir, filename)
        
        # Add metadata
        data = {
            "timestamp": timestamp,
            "hand_number": hand_num,
            "session_id": self.session_id,
            "table_state": table_state
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved table state: {filename}")
        except Exception as e:
            logger.error(f"Failed to save table state: {e}")
    
    def create_summary_report(self):
        """Create a summary report of the debug session."""
        if not self.session_dir:
            return
        
        try:
            # Count files
            full_table_count = len([f for f in os.listdir(os.path.join(self.session_dir, "full_table")) if f.endswith('.png')])
            regions_count = len([f for f in os.listdir(os.path.join(self.session_dir, "regions")) if f.endswith('.png')])
            ocr_count = len([f for f in os.listdir(os.path.join(self.session_dir, "ocr_data")) if f.endswith('.json')])
            
            summary = {
                "session_id": self.session_id,
                "start_time": datetime.now().isoformat(),
                "hands_captured": self.hand_count,
                "full_table_screenshots": full_table_count,
                "region_screenshots": regions_count,
                "ocr_extractions": ocr_count,
                "session_directory": self.session_dir
            }
            
            summary_path = os.path.join(self.session_dir, "session_summary.json")
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
                
            logger.info(f"Debug session summary saved: {summary_path}")
            
        except Exception as e:
            logger.error(f"Failed to create summary report: {e}")
    
    def get_latest_captures(self, count: int = 5) -> Dict[str, list]:
        """Get paths to the latest captured files."""
        if not self.session_dir:
            return {"full_table": [], "regions": [], "ocr_data": []}
        
        result = {"full_table": [], "regions": [], "ocr_data": []}
        
        try:
            # Get latest full table screenshots
            full_table_dir = os.path.join(self.session_dir, "full_table")
            if os.path.exists(full_table_dir):
                files = sorted([f for f in os.listdir(full_table_dir) if f.endswith('.png')])
                result["full_table"] = [os.path.join(full_table_dir, f) for f in files[-count:]]
            
            # Get latest region screenshots  
            regions_dir = os.path.join(self.session_dir, "regions")
            if os.path.exists(regions_dir):
                files = sorted([f for f in os.listdir(regions_dir) if f.endswith('.png')])
                result["regions"] = [os.path.join(regions_dir, f) for f in files[-count:]]
            
            # Get latest OCR data
            ocr_dir = os.path.join(self.session_dir, "ocr_data")
            if os.path.exists(ocr_dir):
                files = sorted([f for f in os.listdir(ocr_dir) if f.endswith('.json')])
                result["ocr_data"] = [os.path.join(ocr_dir, f) for f in files[-count:]]
                
        except Exception as e:
            logger.error(f"Error getting latest captures: {e}")
        
        return result

# Global debug capture instance
debug_capturer = DebugCapture()