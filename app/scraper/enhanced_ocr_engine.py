"""
Enhanced OCR engine with field-specific optimizations for poker table elements.
Provides specialized text extraction for different poker UI elements.
"""

import cv2
import numpy as np
import pytesseract
import re
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """OCR extraction result with confidence and metadata."""
    text: str
    confidence: float
    field_type: str = "general"
    raw_text: str = ""
    normalized: bool = False

# Field-specific Tesseract settings
PSM_SETTINGS = {
    "money": "7",      # Single text line
    "stack": "7",      # Single text line  
    "timer": "7",      # Single text line
    "name": "7",       # Single text line
    "buttons": "6",    # Block of text
    "general": "6"     # Block of text
}

WHITELIST_CHARS = {
    "money": "0123456789.$,",
    "stack": "0123456789.$,KkMm",  # Include K/M for abbreviated amounts
    "timer": "0123456789:",
    "name": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_ ",
    "buttons": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    "general": None  # No restrictions
}

class EnhancedOCREngine:
    """OCR engine optimized for poker table text extraction."""
    
    def __init__(self):
        """Initialize OCR engine with Windows path detection."""
        self.setup_tesseract_path()
        
    def setup_tesseract_path(self):
        """Configure Tesseract path for Windows compatibility."""
        if os.name == "nt":  # Windows
            # Common Tesseract installation paths
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
                    os.environ.get("USERNAME", "")
                )
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    logger.info(f"Using Tesseract at: {path}")
                    break
            else:
                logger.warning("Tesseract not found at standard Windows locations")
            
            # Set tessdata path if available
            tessdata_path = r"C:\Program Files\Tesseract-OCR\tessdata"
            if os.path.exists(tessdata_path):
                os.environ["TESSDATA_PREFIX"] = tessdata_path
    
    def preprocess_for_ocr(self, img_bgr: np.ndarray, field_type: str = "general") -> np.ndarray:
        """Preprocess image for optimal OCR results based on field type."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Upscale for better OCR accuracy
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Field-specific preprocessing
        if field_type in ["money", "stack"]:
            # For money/stack: high contrast, noise reduction
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif field_type == "buttons":
            # For buttons: edge enhancement
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        else:
            # General preprocessing
            gray = cv2.bilateralFilter(gray, 7, 75, 75)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def extract_text(self, img_bgr: np.ndarray, field_type: str = "general") -> str:
        """Extract text using field-specific OCR settings."""
        try:
            # Preprocess image
            processed = self.preprocess_for_ocr(img_bgr, field_type)
            
            # Build Tesseract config
            psm = PSM_SETTINGS.get(field_type, "6")
            config_parts = [f"--psm {psm}"]
            
            # Add character whitelist if specified
            whitelist = WHITELIST_CHARS.get(field_type)
            if whitelist:
                config_parts.append(f'-c tessedit_char_whitelist="{whitelist}"')
            
            config = " ".join(config_parts)
            
            # Extract text
            text = pytesseract.image_to_string(processed, config=config)
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {field_type}: {e}")
            return ""
    
    def normalize_money(self, raw_text: str) -> str:
        """Normalize money text to clean format."""
        if not raw_text:
            return "0"
        
        # Common OCR mistakes
        text = raw_text.replace('O', '0').replace('o', '0').replace('l', '1').replace('I', '1')
        
        # Keep only money-related characters
        text = re.sub(r'[^0-9\.\,\$KkMm]', '', text)
        
        # Handle K/M abbreviations
        if text.upper().endswith('K'):
            try:
                base_value = float(text[:-1].replace(',', ''))
                return str(int(base_value * 1000))
            except:
                pass
        elif text.upper().endswith('M'):
            try:
                base_value = float(text[:-1].replace(',', ''))
                return str(int(base_value * 1000000))
            except:
                pass
        
        # Remove multiple commas and clean up
        text = re.sub(r',+', ',', text)
        text = text.replace('$', '').replace(',', '')
        
        # Validate it's a valid number
        try:
            float(text)
            return text
        except:
            return "0"
    
    def normalize_player_name(self, raw_text: str) -> str:
        """Normalize player name text."""
        if not raw_text:
            return ""
        
        # Remove common OCR artifacts and clean up
        name = raw_text.strip()
        name = re.sub(r'[^a-zA-Z0-9\-_\s]', '', name)
        name = ' '.join(name.split())  # Remove extra whitespace
        
        return name[:20]  # Limit length
    
    def normalize_timer(self, raw_text: str) -> str:
        """Normalize timer text."""
        if not raw_text:
            return "0"
        
        # Extract time format (e.g., "15" or "1:30")
        time_match = re.search(r'(\d+):?(\d+)?', raw_text)
        if time_match:
            minutes = int(time_match.group(1))
            seconds = int(time_match.group(2)) if time_match.group(2) else 0
            return str(minutes * 60 + seconds)
        
        return "0"
    
    def extract_and_normalize(self, img_bgr: np.ndarray, field_type: str = "general") -> str:
        """Extract text and apply field-specific normalization."""
        raw_text = self.extract_text(img_bgr, field_type)
        
        if field_type in ["money", "stack"]:
            return self.normalize_money(raw_text)
        elif field_type == "name":
            return self.normalize_player_name(raw_text)
        elif field_type == "timer":
            return self.normalize_timer(raw_text)
        else:
            return raw_text.strip()
    
    def extract_with_result(self, img_bgr: np.ndarray, field_type: str = "general") -> OCRResult:
        """Extract text and return OCRResult object for compatibility."""
        raw_text = self.extract_text(img_bgr, field_type)
        normalized_text = self.extract_and_normalize(img_bgr, field_type)
        
        # Simple confidence estimation based on text length and character diversity
        confidence = min(0.95, len(normalized_text) / 20.0 + 0.5) if normalized_text else 0.1
        
        return OCRResult(
            text=normalized_text,
            confidence=confidence,
            field_type=field_type,
            raw_text=raw_text,
            normalized=True
        )

def test_enhanced_ocr():
    """Test function for enhanced OCR engine - for compatibility."""
    engine = EnhancedOCREngine()
    logger.info("Enhanced OCR engine test - ready for Windows poker analysis")
    return {"status": "ready", "engine": "EnhancedOCREngine"}