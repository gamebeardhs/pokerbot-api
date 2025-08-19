"""
Runtime configuration loader for ACR poker system.
Loads settings from JSON config files to avoid code rebuilds.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Loads and manages runtime configuration for ACR system."""
    
    def __init__(self, config_path: str = "config/acr_runtime.json"):
        """Initialize config loader."""
        self.config_path = config_path
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded config from {self.config_path}")
            else:
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self.config = self._get_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            self.config = self._get_default_config()
        
        return self.config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "fps_timing": {
                "min_delay": 0.18,
                "max_delay": 0.42,
                "base_fps": 3.0
            },
            "state_stabilization": {
                "debounce_readings": 2,
                "confidence_threshold": 0.6
            },
            "ocr_settings": {
                "money_psm": 7,
                "stack_psm": 7,
                "name_psm": 7,
                "button_psm": 6,
                "general_psm": 6
            },
            "timer_detection": {
                "hsv_ranges": [
                    {"name": "cyan_blue", "lower": [90, 120, 140], "upper": [110, 255, 255]},
                    {"name": "green", "lower": [70, 120, 140], "upper": [89, 255, 255]},
                    {"name": "yellow_green", "lower": [40, 120, 140], "upper": [69, 255, 255]}
                ],
                "pixel_threshold": 5.0
            }
        }
    
    def get(self, key_path: str, default=None) -> Any:
        """Get config value using dot notation (e.g., 'fps_timing.min_delay')."""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            logger.debug(f"Config key '{key_path}' not found, using default: {default}")
            return default
    
    def get_fps_settings(self) -> Dict[str, float]:
        """Get FPS timing configuration."""
        return {
            "min_delay": self.get("fps_timing.min_delay", 0.18),
            "max_delay": self.get("fps_timing.max_delay", 0.42),
            "base_fps": self.get("fps_timing.base_fps", 3.0)
        }
    
    def get_stabilizer_settings(self) -> Dict[str, Any]:
        """Get state stabilization configuration."""
        return {
            "debounce_readings": self.get("state_stabilization.debounce_readings", 2),
            "confidence_threshold": self.get("state_stabilization.confidence_threshold", 0.6)
        }
    
    def get_ocr_settings(self) -> Dict[str, int]:
        """Get OCR PSM settings for different field types."""
        return {
            "money": self.get("ocr_settings.money_psm", 7),
            "stack": self.get("ocr_settings.stack_psm", 7),
            "name": self.get("ocr_settings.name_psm", 7),
            "buttons": self.get("ocr_settings.button_psm", 6),
            "general": self.get("ocr_settings.general_psm", 6)
        }
    
    def get_timer_detection_settings(self) -> Dict[str, Any]:
        """Get timer detection configuration."""
        hsv_ranges = self.get("timer_detection.hsv_ranges", [])
        pixel_threshold = self.get("timer_detection.pixel_threshold", 5.0)
        
        return {
            "hsv_ranges": hsv_ranges,
            "pixel_threshold": pixel_threshold
        }
    
    def get_default_regions(self) -> Dict[str, tuple]:
        """Get default ACR table regions."""
        regions_config = self.get("regions_acr", {})
        
        # Convert lists to tuples for compatibility
        regions = {}
        for name, coords in regions_config.items():
            if isinstance(coords, list) and len(coords) == 4:
                regions[name] = tuple(coords)
        
        return regions
    
    def reload_config(self) -> bool:
        """Reload configuration from file."""
        try:
            self.load_config()
            logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def save_config(self, new_config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2)
                
            self.config = new_config
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

# Global config loader instance
config_loader = ConfigLoader()