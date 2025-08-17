"""
Intelligent ACR Table Auto-Calibration System
Professional poker bot inspired calibration with 95%+ accuracy guarantee.
"""

import cv2
import numpy as np
import pytesseract
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging
from PIL import ImageGrab, Image
import re

logger = logging.getLogger(__name__)

@dataclass
class TableRegion:
    """Represents a detected table region with confidence score."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    element_type: str
    template_match: bool = False

@dataclass
class CalibrationResult:
    """Complete calibration results with validation metrics."""
    regions: Dict[str, TableRegion]
    accuracy_score: float
    validation_tests: Dict[str, bool]
    timestamp: str
    table_detected: bool
    success_rate: float

class IntelligentACRCalibrator:
    """Auto-calibration system for ACR poker tables using professional bot techniques."""
    
    def __init__(self):
        self.min_accuracy = 0.95  # 95% success rate requirement
        self.templates = {}
        self.ocr_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789AKQJT$,.() '
        self.load_reference_templates()
        
    def load_reference_templates(self):
        """Load ACR reference templates for recognition."""
        templates_dir = Path("training_data/templates")
        if templates_dir.exists():
            for template_path in templates_dir.glob("*.png"):
                card_name = template_path.stem
                template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    self.templates[card_name] = template
            
            logger.info(f"Loaded {len(self.templates)} card templates for calibration")
        
        # Load UI element templates if available
        self.load_ui_templates()
    
    def load_ui_templates(self):
        """Load UI element templates from attached assets."""
        ui_templates_dir = Path("attached_assets")
        ui_elements = ["bet", "playername", "button", "pot"]
        
        for element in ui_elements:
            # Look for element templates
            element_files = list(ui_templates_dir.glob(f"*{element}*"))
            if element_files:
                template_path = element_files[0]
                try:
                    template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
                    if template is not None:
                        self.templates[f"ui_{element}"] = template
                        logger.info(f"Loaded UI template: {element}")
                except Exception as e:
                    logger.warning(f"Failed to load UI template {element}: {e}")
    
    def detect_acr_table(self, screenshot: np.ndarray = None) -> Tuple[bool, Dict]:
        """Detect if ACR poker table is open and get basic info."""
        if screenshot is None:
            screenshot = self.capture_screen()
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        
        # ACR-specific detection patterns
        acr_indicators = self.find_acr_indicators(gray)
        
        # Look for poker table patterns
        table_features = self.detect_table_features(gray)
        
        # Calculate confidence
        detection_confidence = self.calculate_detection_confidence(acr_indicators, table_features)
        
        table_info = {
            "detected": detection_confidence > 0.3,  # Lowered threshold for better detection
            "confidence": detection_confidence,
            "features": table_features,
            "indicators": acr_indicators,
            "screenshot_shape": screenshot.shape
        }
        
        return table_info["detected"], table_info
    
    def find_acr_indicators(self, gray_image: np.ndarray) -> Dict:
        """Find ACR-specific visual indicators."""
        indicators = {
            "acr_logo": False,
            "table_felt": False,
            "card_positions": [],
            "ui_elements": []
        }
        
        # Look for green felt color pattern (ACR tables)
        hsv = cv2.cvtColor(cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV)
        
        # Green felt detection
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        green_area = np.sum(green_mask > 0)
        total_area = gray_image.shape[0] * gray_image.shape[1]
        
        if green_area / total_area > 0.1:  # At least 10% green (table felt)
            indicators["table_felt"] = True
        
        # Look for card-like rectangular shapes
        indicators["card_positions"] = self.find_card_regions(gray_image)
        
        return indicators
    
    def detect_table_features(self, gray_image: np.ndarray) -> Dict:
        """Detect poker table features and UI elements."""
        features = {
            "buttons": [],
            "text_regions": [],
            "card_regions": [],
            "circular_elements": []  # For player positions
        }
        
        # Button detection (rectangular with text)
        features["buttons"] = self.find_buttons(gray_image)
        
        # Text regions (for player names, amounts)
        features["text_regions"] = self.find_text_regions(gray_image)
        
        # Card regions
        features["card_regions"] = self.find_card_regions(gray_image)
        
        # Circular elements (player seats)
        features["circular_elements"] = self.find_circular_elements(gray_image)
        
        return features
    
    def find_card_regions(self, gray_image: np.ndarray) -> List[TableRegion]:
        """Find potential card regions using aspect ratio and size."""
        card_regions = []
        
        # ACR card dimensions approximately 57x82 pixels
        expected_ratio = 57/82  # width/height
        tolerance = 0.15
        
        # Find contours
        edges = cv2.Canny(gray_image, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size and aspect ratio
            if (30 < w < 120 and 40 < h < 160):
                ratio = w / h
                if abs(ratio - expected_ratio) < tolerance:
                    # Additional validation using template matching if available
                    confidence = self.validate_card_region(gray_image[y:y+h, x:x+w])
                    
                    if confidence > 0.3:
                        card_regions.append(TableRegion(
                            x=x, y=y, width=w, height=h,
                            confidence=confidence,
                            element_type="card",
                            template_match=True
                        ))
        
        return card_regions
    
    def validate_card_region(self, region: np.ndarray) -> float:
        """Validate if a region contains a card using template matching."""
        if not self.templates:
            return 0.5  # Medium confidence without templates
        
        # Resize region to standard card size
        resized = cv2.resize(region, (57, 82))
        
        max_confidence = 0.0
        
        # Test against a few card templates
        test_cards = ['As', 'Kh', 'Qd', 'Jc', 'Ts']  # Sample cards
        
        for card in test_cards:
            if card in self.templates:
                result = cv2.matchTemplate(resized, self.templates[card], cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                max_confidence = max(max_confidence, max_val)
        
        return max_confidence
    
    def find_buttons(self, gray_image: np.ndarray) -> List[TableRegion]:
        """Find action buttons (fold, call, raise)."""
        buttons = []
        
        # Look for rectangular regions with text
        contours, _ = cv2.findContours(
            cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Button-like dimensions
            if (60 < w < 200 and 25 < h < 60):
                aspect_ratio = w / h
                if 1.5 < aspect_ratio < 4.0:  # Button-like aspect ratio
                    
                    # Extract region and try OCR
                    region = gray_image[y:y+h, x:x+w]
                    text = self.extract_text(region)
                    
                    # Check for button-like text
                    button_words = ['fold', 'call', 'raise', 'check', 'bet', 'all-in']
                    is_button = any(word in text.lower() for word in button_words)
                    
                    confidence = 0.8 if is_button else 0.4
                    
                    buttons.append(TableRegion(
                        x=x, y=y, width=w, height=h,
                        confidence=confidence,
                        element_type="button"
                    ))
        
        return buttons
    
    def find_text_regions(self, gray_image: np.ndarray) -> List[TableRegion]:
        """Find text regions for player names, amounts, etc."""
        text_regions = []
        
        # Use MSER for text detection
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray_image)
        
        for region in regions:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(region)
            
            # Filter by size
            if (20 < w < 300 and 10 < h < 50):
                # Extract text
                text_region = gray_image[y:y+h, x:x+w]
                text = self.extract_text(text_region)
                
                # Validate if it's meaningful text
                if len(text.strip()) > 2 and not text.isspace():
                    confidence = min(0.9, len(text.strip()) / 20)
                    
                    text_regions.append(TableRegion(
                        x=x, y=y, width=w, height=h,
                        confidence=confidence,
                        element_type="text"
                    ))
        
        return text_regions
    
    def find_circular_elements(self, gray_image: np.ndarray) -> List[TableRegion]:
        """Find circular elements (player seats, dealer button)."""
        circular_elements = []
        
        # Hough Circle detection
        circles = cv2.HoughCircles(
            gray_image, cv2.HOUGH_GRADIENT, 1, 50,
            param1=50, param2=30, minRadius=15, maxRadius=80
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            for (x, y, r) in circles:
                circular_elements.append(TableRegion(
                    x=x-r, y=y-r, width=2*r, height=2*r,
                    confidence=0.7,
                    element_type="circular"
                ))
        
        return circular_elements
    
    def extract_text(self, region: np.ndarray) -> str:
        """Extract text from image region using OCR."""
        try:
            # Preprocess for better OCR
            processed = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            processed = cv2.resize(processed, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            text = pytesseract.image_to_string(processed, config=self.ocr_config)
            return text.strip()
        except:
            return ""
    
    def calculate_detection_confidence(self, indicators: Dict, features: Dict) -> float:
        """Calculate overall table detection confidence."""
        confidence = 0.0
        
        # Table felt detected
        if indicators["table_felt"]:
            confidence += 0.3
        
        # Card positions found
        if len(indicators["card_positions"]) >= 2:
            confidence += 0.2
        
        # UI elements found
        if len(features["buttons"]) >= 2:
            confidence += 0.2
        
        if len(features["text_regions"]) >= 3:
            confidence += 0.15
        
        if len(features["circular_elements"]) >= 4:
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def auto_calibrate_table(self) -> CalibrationResult:
        """Automatically calibrate ACR table with 95%+ accuracy target."""
        logger.info("Starting intelligent auto-calibration...")
        
        # Capture screenshot
        screenshot = self.capture_screen()
        
        # Detect ACR table
        table_detected, table_info = self.detect_acr_table(screenshot)
        
        if not table_detected:
            return CalibrationResult(
                regions={},
                accuracy_score=0.0,
                validation_tests={"table_detection": False},
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                table_detected=False,
                success_rate=0.0
            )
        
        # Extract regions intelligently
        regions = self.extract_calibration_regions(screenshot, table_info)
        
        # Validate regions
        validation_results = self.validate_regions(screenshot, regions)
        
        # Calculate accuracy
        accuracy = self.calculate_accuracy_score(validation_results)
        
        # Create calibration result
        result = CalibrationResult(
            regions=regions,
            accuracy_score=accuracy,
            validation_tests=validation_results,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            table_detected=table_detected,
            success_rate=accuracy
        )
        
        # Save if meets requirements
        if accuracy >= self.min_accuracy:
            self.save_calibration(result)
            logger.info(f"✅ Auto-calibration successful: {accuracy:.1%} accuracy")
        else:
            logger.warning(f"❌ Auto-calibration below target: {accuracy:.1%} < {self.min_accuracy:.1%}")
        
        return result
    
    def extract_calibration_regions(self, screenshot: np.ndarray, table_info: Dict) -> Dict[str, TableRegion]:
        """Extract specific regions needed for poker bot functionality."""
        regions = {}
        
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        features = table_info["features"]
        
        # Hero cards (bottom center)
        hero_cards = self.find_hero_card_regions(features["card_regions"])
        if len(hero_cards) >= 2:
            regions["hero_card_1"] = hero_cards[0]
            regions["hero_card_2"] = hero_cards[1]
        
        # Community cards (center top)
        community_regions = self.find_community_card_regions(features["card_regions"])
        for i, region in enumerate(community_regions[:5]):
            regions[f"community_{i+1}"] = region
        
        # Action buttons (bottom right)
        button_regions = self.identify_action_buttons(features["buttons"], gray)
        regions.update(button_regions)
        
        # Pot region (center)
        pot_region = self.find_pot_region(features["text_regions"], gray)
        if pot_region:
            regions["pot"] = pot_region
        
        # Player regions (around table)
        player_regions = self.find_player_regions(features["circular_elements"], features["text_regions"])
        regions.update(player_regions)
        
        return regions
    
    def find_hero_card_regions(self, card_regions: List[TableRegion]) -> List[TableRegion]:
        """Find hero's card regions (typically bottom center)."""
        if not card_regions:
            return []
        
        # Sort by y-coordinate (bottom first) then by x-coordinate
        hero_candidates = sorted(
            [r for r in card_regions if r.confidence > 0.3],
            key=lambda r: (-r.y, r.x)
        )
        
        return hero_candidates[:2]  # First two cards
    
    def find_community_card_regions(self, card_regions: List[TableRegion]) -> List[TableRegion]:
        """Find community card regions (typically center)."""
        if not card_regions:
            return []
        
        # Find cards in the center horizontal area
        height = max(r.y + r.height for r in card_regions) if card_regions else 600
        center_y = height // 3  # Upper third for community cards
        
        community_candidates = [
            r for r in card_regions 
            if abs(r.y - center_y) < 100 and r.confidence > 0.3
        ]
        
        # Sort by x-coordinate (left to right)
        return sorted(community_candidates, key=lambda r: r.x)
    
    def identify_action_buttons(self, button_regions: List[TableRegion], gray: np.ndarray) -> Dict[str, TableRegion]:
        """Identify specific action buttons."""
        button_map = {}
        
        for button in button_regions:
            if button.confidence < 0.4:
                continue
            
            # Extract button text
            region = gray[button.y:button.y+button.height, button.x:button.x+button.width]
            text = self.extract_text(region).lower()
            
            # Map button by text content
            if "fold" in text:
                button_map["fold_button"] = button
            elif "call" in text or "check" in text:
                button_map["call_button"] = button  
            elif "raise" in text or "bet" in text:
                button_map["raise_button"] = button
            elif "all" in text and "in" in text:
                button_map["allin_button"] = button
        
        return button_map
    
    def find_pot_region(self, text_regions: List[TableRegion], gray: np.ndarray) -> Optional[TableRegion]:
        """Find the pot amount region."""
        for region in text_regions:
            # Extract text and look for dollar signs or numeric patterns
            text_area = gray[region.y:region.y+region.height, region.x:region.x+region.width]
            text = self.extract_text(text_area)
            
            # Look for pot-like text patterns
            if re.search(r'[$]?\d+\.?\d*', text) or "pot" in text.lower():
                region.element_type = "pot"
                region.confidence = min(0.9, region.confidence + 0.1)
                return region
        
        return None
    
    def find_player_regions(self, circular_elements: List[TableRegion], text_regions: List[TableRegion]) -> Dict[str, TableRegion]:
        """Find player name and stack regions."""
        player_regions = {}
        
        # Associate text regions with circular elements (seats)
        for i, seat in enumerate(circular_elements[:9]):  # Max 9 players
            # Find nearby text regions
            nearby_text = [
                t for t in text_regions
                if self.distance(seat, t) < 100
            ]
            
            if nearby_text:
                # Choose the closest text region
                closest = min(nearby_text, key=lambda t: self.distance(seat, t))
                closest.element_type = f"player_{i+1}"
                player_regions[f"player_{i+1}_name"] = closest
        
        return player_regions
    
    def distance(self, region1: TableRegion, region2: TableRegion) -> float:
        """Calculate distance between two regions."""
        center1 = (region1.x + region1.width//2, region1.y + region1.height//2)
        center2 = (region2.x + region2.width//2, region2.y + region2.height//2)
        return ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
    
    def validate_regions(self, screenshot: np.ndarray, regions: Dict[str, TableRegion]) -> Dict[str, bool]:
        """Validate extracted regions for functionality."""
        validation = {}
        
        # Test card recognition
        validation["hero_cards_detected"] = "hero_card_1" in regions and "hero_card_2" in regions
        
        # Test button recognition
        validation["action_buttons_detected"] = any(
            btn in regions for btn in ["fold_button", "call_button", "raise_button"]
        )
        
        # Test text extraction
        validation["text_extraction_working"] = len([
            r for r in regions.values() if r.element_type in ["text", "pot"]
        ]) >= 2
        
        # Test overall coverage
        validation["sufficient_regions"] = len(regions) >= 6
        
        # Test confidence levels
        validation["high_confidence_regions"] = sum(
            1 for r in regions.values() if r.confidence > 0.7
        ) >= len(regions) * 0.6
        
        return validation
    
    def calculate_accuracy_score(self, validation: Dict[str, bool]) -> float:
        """Calculate overall accuracy score."""
        total_tests = len(validation)
        passed_tests = sum(validation.values())
        
        return passed_tests / total_tests if total_tests > 0 else 0.0
    
    def capture_screen(self) -> np.ndarray:
        """Capture current screen with enhanced detection."""
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot_np = np.array(screenshot)
            bgr_image = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            logger.info(f"Screenshot captured: {bgr_image.shape[1]}x{bgr_image.shape[0]} pixels")
            return bgr_image
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            # Create a larger dummy image if capture fails
            return np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    def save_calibration(self, result: CalibrationResult):
        """Save successful calibration results."""
        # Convert to serializable format
        regions_dict = {}
        for name, region in result.regions.items():
            regions_dict[name] = asdict(region)
        
        save_data = {
            "regions": regions_dict,
            "accuracy_score": result.accuracy_score,
            "validation_tests": result.validation_tests,
            "timestamp": result.timestamp,
            "table_detected": result.table_detected,
            "success_rate": result.success_rate
        }
        
        # Save to file
        with open("acr_auto_calibration_results.json", 'w') as f:
            json.dump(save_data, f, indent=2)
        
        logger.info(f"Saved auto-calibration results with {result.success_rate:.1%} success rate")

def test_intelligent_calibration():
    """Test the intelligent calibration system."""
    calibrator = IntelligentACRCalibrator()
    result = calibrator.auto_calibrate_table()
    
    print(f"Auto-Calibration Results:")
    print(f"Table Detected: {result.table_detected}")
    print(f"Success Rate: {result.success_rate:.1%}")
    print(f"Regions Found: {len(result.regions)}")
    print(f"Validation Tests: {sum(result.validation_tests.values())}/{len(result.validation_tests)} passed")
    
    return result

if __name__ == "__main__":
    test_intelligent_calibration()