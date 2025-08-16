"""Advanced card recognition system for poker table screenshots."""

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from typing import List, Tuple, Optional, Dict, Any
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Card:
    """Represents a detected card."""
    rank: str
    suit: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    
    def __str__(self):
        return f"{self.rank}{self.suit}"

class CardRecognition:
    """Advanced card recognition using multiple detection methods."""
    
    def __init__(self):
        self.rank_patterns = {
            'A': ['A', 'a', '@'],
            'K': ['K', 'k'],
            'Q': ['Q', 'q'],
            'J': ['J', 'j'],
            'T': ['T', 't', '10'],
            '9': ['9'],
            '8': ['8'],
            '7': ['7'],
            '6': ['6'],
            '5': ['5'],
            '4': ['4'],
            '3': ['3'],
            '2': ['2']
        }
        
        self.suit_patterns = {
            's': ['s', 'spades', '♠'],
            'h': ['h', 'hearts', '♥'],
            'd': ['d', 'diamonds', '♦'],
            'c': ['c', 'clubs', '♣']
        }
        
        # Color ranges for suit detection (HSV)
        self.suit_colors = {
            'spades': [(0, 0, 0), (180, 255, 50)],    # Black
            'clubs': [(0, 0, 0), (180, 255, 50)],     # Black
            'hearts': [(0, 120, 70), (10, 255, 255)], # Red
            'diamonds': [(0, 120, 70), (10, 255, 255)]  # Red
        }
    
    def detect_cards_in_region(self, image: Image.Image, max_cards: int = 5) -> List[Card]:
        """
        Detect and recognize cards in an image region.
        Uses multiple detection methods for best accuracy.
        """
        try:
            if image is None:
                return []
            
            # Convert to OpenCV format
            cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Method 1: Contour-based card detection
            cards_contour = self._detect_cards_by_contours(cv_img, max_cards)
            
            # Method 2: Template/grid-based detection
            cards_grid = self._detect_cards_by_grid(cv_img, max_cards)
            
            # Method 3: OCR-based detection
            cards_ocr = self._detect_cards_by_ocr(image, max_cards)
            
            # Combine and rank results
            all_cards = cards_contour + cards_grid + cards_ocr
            
            # Filter and rank by confidence
            best_cards = self._rank_and_filter_cards(all_cards, max_cards)
            
            logger.debug(f"Detected {len(best_cards)} cards: {[str(c) for c in best_cards]}")
            return best_cards
            
        except Exception as e:
            logger.error(f"Card detection failed: {e}")
            return []
    
    def _detect_cards_by_contours(self, cv_img: np.ndarray, max_cards: int) -> List[Card]:
        """Detect cards using contour detection and shape analysis."""
        cards = []
        
        try:
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Adaptive thresholding for better edge detection
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours that could be cards
            card_contours = self._filter_card_contours(contours, cv_img.shape)
            
            for i, contour in enumerate(card_contours[:max_cards]):
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Extract card region
                card_region = cv_img[y:y+h, x:x+w]
                
                # Try to recognize rank and suit
                rank, suit, confidence = self._recognize_card_content(card_region)
                
                if rank and suit:
                    cards.append(Card(rank, suit, confidence * 0.7, (x, y, x+w, y+h)))
                    
        except Exception as e:
            logger.debug(f"Contour detection failed: {e}")
            
        return cards
    
    def _detect_cards_by_grid(self, cv_img: np.ndarray, max_cards: int) -> List[Card]:
        """Detect cards by dividing region into expected card positions."""
        cards = []
        
        try:
            h, w = cv_img.shape[:2]
            
            # Estimate card positions based on typical layouts
            if max_cards == 2:  # Hero cards (side by side)
                card_width = w // 2
                positions = [(0, 0, card_width, h), (card_width, 0, w, h)]
            elif max_cards == 5:  # Board cards (5 in a row)
                card_width = w // 5
                positions = [(i * card_width, 0, (i + 1) * card_width, h) for i in range(5)]
            else:
                # General grid approach
                card_width = w // max_cards
                positions = [(i * card_width, 0, (i + 1) * card_width, h) for i in range(max_cards)]
            
            for i, (x1, y1, x2, y2) in enumerate(positions):
                # Extract potential card region
                card_region = cv_img[y1:y2, x1:x2]
                
                # Check if region contains a card (has enough variation)
                if self._region_has_card_content(card_region):
                    rank, suit, confidence = self._recognize_card_content(card_region)
                    
                    if rank and suit:
                        cards.append(Card(rank, suit, confidence * 0.8, (x1, y1, x2, y2)))
                        
        except Exception as e:
            logger.debug(f"Grid detection failed: {e}")
            
        return cards
    
    def _detect_cards_by_ocr(self, image: Image.Image, max_cards: int) -> List[Card]:
        """Detect cards using enhanced OCR approaches."""
        cards = []
        
        try:
            # Multiple OCR preprocessing approaches
            preprocessed_images = self._preprocess_for_card_ocr(image)
            
            for method_name, proc_img in preprocessed_images.items():
                text = self._extract_card_text(proc_img)
                detected_cards = self._parse_cards_from_text(text, method_name)
                cards.extend(detected_cards)
                
        except Exception as e:
            logger.debug(f"OCR detection failed: {e}")
            
        return cards
    
    def _filter_card_contours(self, contours, img_shape: Tuple) -> List:
        """Filter contours that could represent cards."""
        card_contours = []
        
        h, w = img_shape[:2]
        min_area = (w * h) * 0.01  # At least 1% of image
        max_area = (w * h) * 0.5   # At most 50% of image
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if min_area < area < max_area:
                # Check aspect ratio (cards are roughly rectangular)
                x, y, rect_w, rect_h = cv2.boundingRect(contour)
                aspect_ratio = rect_w / rect_h if rect_h > 0 else 0
                
                # Card aspect ratios typically between 0.6 and 1.7
                if 0.4 < aspect_ratio < 2.0:
                    card_contours.append(contour)
        
        # Sort by area (largest first)
        card_contours.sort(key=cv2.contourArea, reverse=True)
        return card_contours
    
    def _region_has_card_content(self, region: np.ndarray) -> bool:
        """Check if a region likely contains card content."""
        if region.size == 0:
            return False
            
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY) if len(region.shape) == 3 else region
        
        # Check for sufficient contrast variation
        std_dev = np.std(gray)
        mean_val = np.mean(gray)
        
        # Cards should have reasonable contrast
        return bool(std_dev > 15 and 30 < mean_val < 220)
    
    def _recognize_card_content(self, card_region: np.ndarray) -> Tuple[Optional[str], Optional[str], float]:
        """Recognize rank and suit from a card region."""
        if card_region.size == 0:
            return None, None, 0.0
            
        try:
            # Convert to PIL for OCR
            pil_region = Image.fromarray(cv2.cvtColor(card_region, cv2.COLOR_BGR2RGB))
            
            # Try multiple recognition methods
            rank, suit, conf1 = self._recognize_by_ocr(pil_region)
            if rank and suit:
                return rank, suit, conf1
                
            rank, suit, conf2 = self._recognize_by_color_analysis(card_region)
            if rank and suit:
                return rank, suit, conf2
                
            return None, None, 0.0
            
        except Exception as e:
            logger.debug(f"Card recognition failed: {e}")
            return None, None, 0.0
    
    def _recognize_by_ocr(self, image: Image.Image) -> Tuple[Optional[str], Optional[str], float]:
        """Recognize card using OCR."""
        try:
            # Enhance image for better OCR
            enhanced = self._enhance_for_ocr(image)
            
            # Card-specific OCR config
            config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKAHSCDhscd♠♥♦♣ '
            
            text = pytesseract.image_to_string(enhanced, config=config).strip()
            
            # Parse rank and suit from text
            rank, suit = self._parse_card_from_text(text)
            
            if rank and suit:
                return rank, suit, 0.8
                
        except Exception as e:
            logger.debug(f"OCR recognition failed: {e}")
            
        return None, None, 0.0
    
    def _recognize_by_color_analysis(self, card_region: np.ndarray) -> Tuple[Optional[str], Optional[str], float]:
        """Recognize card suit using color analysis."""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(card_region, cv2.COLOR_BGR2HSV)
            
            # Detect red (hearts/diamonds) vs black (spades/clubs)
            red_mask = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
            red_pixels = cv2.countNonZero(red_mask)
            
            total_pixels = card_region.shape[0] * card_region.shape[1]
            red_ratio = red_pixels / total_pixels
            
            # If significant red content, likely hearts or diamonds
            if red_ratio > 0.05:  # 5% red pixels
                suit = 'h'  # Default to hearts, could be refined
                confidence = min(red_ratio * 10, 1.0)
            else:
                suit = 's'  # Default to spades for black
                confidence = 0.6
                
            # For rank, try basic shape analysis or return None
            rank = self._analyze_rank_by_shape(card_region)
            
            if rank:
                return rank, suit, confidence * 0.6
                
        except Exception as e:
            logger.debug(f"Color analysis failed: {e}")
            
        return None, None, 0.0
    
    def _analyze_rank_by_shape(self, card_region: np.ndarray) -> Optional[str]:
        """Basic rank detection using shape analysis."""
        # This would require more sophisticated computer vision
        # For now, return None - OCR method is more reliable
        return None
    
    def _preprocess_for_card_ocr(self, image: Image.Image) -> Dict[str, Image.Image]:
        """Create multiple preprocessed versions for OCR."""
        preprocessed = {}
        
        try:
            # Original
            preprocessed['original'] = image
            
            # Enhanced contrast
            enhancer = ImageEnhance.Contrast(image)
            preprocessed['contrast'] = enhancer.enhance(2.0)
            
            # Sharpened
            preprocessed['sharp'] = image.filter(ImageFilter.SHARPEN)
            
            # Grayscale with high contrast
            gray = image.convert('L')
            enhancer = ImageEnhance.Contrast(gray)
            preprocessed['gray_contrast'] = enhancer.enhance(3.0)
            
            # Binary threshold
            gray_array = np.array(gray)
            _, binary = cv2.threshold(gray_array, 127, 255, cv2.THRESH_BINARY)
            preprocessed['binary'] = Image.fromarray(binary)
            
        except Exception as e:
            logger.debug(f"Preprocessing failed: {e}")
            preprocessed['original'] = image
            
        return preprocessed
    
    def _enhance_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image specifically for card OCR."""
        try:
            # Resize for better OCR if too small
            w, h = image.size
            if w < 50 or h < 50:
                scale = max(2, 100 // min(w, h))
                image = image.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            gray = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(2.5)
            
            # Apply sharpening
            sharpened = enhanced.filter(ImageFilter.SHARPEN)
            
            return sharpened
            
        except Exception:
            return image
    
    def _extract_card_text(self, image: Image.Image) -> str:
        """Extract text from preprocessed card image."""
        try:
            # Card-optimized OCR settings
            configs = [
                r'--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKAHSCDhscd ',
                r'--oem 3 --psm 7 -c tessedit_char_whitelist=23456789TJQKAHSCDhscd ',
                r'--oem 3 --psm 6 -c tessedit_char_whitelist=23456789TJQKAHSCDhscd♠♥♦♣ ',
            ]
            
            for config in configs:
                text = pytesseract.image_to_string(image, config=config).strip()
                if text:
                    return text
                    
        except Exception as e:
            logger.debug(f"Text extraction failed: {e}")
            
        return ""
    
    def _parse_cards_from_text(self, text: str, method: str) -> List[Card]:
        """Parse individual cards from OCR text."""
        cards = []
        
        try:
            # Clean text
            cleaned = re.sub(r'[^23456789TJQKAHSCDhscd♠♥♦♣\s]', '', text)
            
            # Look for card patterns
            patterns = [
                r'([23456789TJQKA])([hscd♠♥♦♣])',  # Rank + suit
                r'([23456789TJQKA])\s*([hscd♠♥♦♣])',  # Rank space suit
                r'([23456789TJQKA])([HSCD])',  # Rank + uppercase suit
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, cleaned, re.IGNORECASE)
                for rank, suit in matches:
                    normalized_rank = self._normalize_rank(rank)
                    normalized_suit = self._normalize_suit(suit)
                    
                    if normalized_rank and normalized_suit:
                        confidence = 0.9 if method == 'original' else 0.7
                        cards.append(Card(normalized_rank, normalized_suit, confidence, (0, 0, 0, 0)))
            
            # Also try splitting by spaces and parsing pairs
            tokens = cleaned.split()
            for token in tokens:
                if len(token) >= 2:
                    rank_char = token[0]
                    suit_char = token[1] if len(token) > 1 else token[-1]
                    
                    normalized_rank = self._normalize_rank(rank_char)
                    normalized_suit = self._normalize_suit(suit_char)
                    
                    if normalized_rank and normalized_suit:
                        cards.append(Card(normalized_rank, normalized_suit, 0.6, (0, 0, 0, 0)))
                        
        except Exception as e:
            logger.debug(f"Card parsing failed: {e}")
            
        return cards
    
    def _parse_card_from_text(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse a single card from text."""
        if not text:
            return None, None
            
        # Clean and normalize
        cleaned = re.sub(r'[^23456789TJQKAHSCDhscd♠♥♦♣]', '', text)
        
        if len(cleaned) >= 2:
            rank = self._normalize_rank(cleaned[0])
            suit = self._normalize_suit(cleaned[1])
            return rank, suit
            
        return None, None
    
    def _normalize_rank(self, rank: str) -> Optional[str]:
        """Normalize rank to standard format."""
        rank = rank.upper()
        
        rank_map = {
            'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J',
            'T': 'T', '10': 'T',
            '9': '9', '8': '8', '7': '7', '6': '6',
            '5': '5', '4': '4', '3': '3', '2': '2'
        }
        
        return rank_map.get(rank)
    
    def _normalize_suit(self, suit: str) -> Optional[str]:
        """Normalize suit to standard format."""
        suit_map = {
            'S': 's', 's': 's', '♠': 's',
            'H': 'h', 'h': 'h', '♥': 'h',
            'D': 'd', 'd': 'd', '♦': 'd',
            'C': 'c', 'c': 'c', '♣': 'c'
        }
        
        return suit_map.get(suit)
    
    def _rank_and_filter_cards(self, cards: List[Card], max_cards: int) -> List[Card]:
        """Rank cards by confidence and filter duplicates."""
        if not cards:
            return []
        
        # Group by card string
        card_groups = {}
        for card in cards:
            card_str = str(card)
            if card_str not in card_groups:
                card_groups[card_str] = []
            card_groups[card_str].append(card)
        
        # Take best confidence for each unique card
        best_cards = []
        for card_str, group in card_groups.items():
            best_card = max(group, key=lambda c: c.confidence)
            best_cards.append(best_card)
        
        # Sort by confidence and limit
        best_cards.sort(key=lambda c: c.confidence, reverse=True)
        return best_cards[:max_cards]