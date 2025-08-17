"""
High-performance hash-based card recognition system.
Inspired by DickReuter's 500x faster C++ approach.
"""

import cv2
import numpy as np
import hashlib
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

class CardHashRecognizer:
    """Ultra-fast card recognition using perceptual hashing."""
    
    def __init__(self):
        self.card_hashes: Dict[str, str] = {}
        self.hash_to_card: Dict[str, str] = {}
        self.template_cache: Dict[str, np.ndarray] = {}
        self.hash_cache: Dict[str, str] = {}  # Image region -> hash cache
        self.load_card_hashes()
    
    def load_card_hashes(self):
        """Load pre-computed card hashes for instant recognition."""
        templates_dir = Path("training_data/templates")
        if not templates_dir.exists():
            logger.warning("No templates directory found")
            return
        
        for template_path in templates_dir.glob("*.png"):
            card_name = template_path.stem
            
            # Load and process template
            image = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
            if image is not None:
                # Cache template for fallback matching
                self.template_cache[card_name] = image
                
                # Generate perceptual hash
                card_hash = self.compute_perceptual_hash(image)
                self.card_hashes[card_name] = card_hash
                self.hash_to_card[card_hash] = card_name
        
        logger.info(f"Loaded {len(self.card_hashes)} card hashes for instant recognition")
    
    def compute_perceptual_hash(self, image: np.ndarray, hash_size: int = 8) -> str:
        """
        Compute perceptual hash (pHash) for robust card recognition.
        Resistant to minor lighting/scale changes.
        """
        # Resize to standard size
        resized = cv2.resize(image, (hash_size * 4, hash_size * 4))
        
        # Convert to float for DCT
        float_img = np.float32(resized)
        
        # Apply DCT (Discrete Cosine Transform) - fix OpenCV compatibility
        try:
            dct = cv2.dct(float_img)
        except Exception:
            # Fallback for OpenCV compatibility issues
            import numpy.fft
            dct = np.abs(np.fft.fft2(float_img))
        
        # Extract top-left hash_size x hash_size corner
        dct_low = dct[:hash_size, :hash_size]
        
        # Calculate median
        median = np.median(dct_low)
        
        # Create binary hash
        binary_hash = dct_low > median
        
        # Convert to hex string
        hash_str = ""
        for row in binary_hash:
            for bit in row:
                hash_str += "1" if bit else "0"
        
        # Convert binary to hex for compact storage
        hex_hash = hex(int(hash_str, 2))[2:].zfill(16)
        
        return hex_hash
    
    def recognize_card_region(self, region: np.ndarray) -> Optional[Tuple[str, float]]:
        """
        Ultra-fast card recognition using hash lookup.
        Returns (card_name, confidence) or None.
        """
        if region.size == 0:
            return None
        
        # Convert to grayscale if needed
        if len(region.shape) == 3:
            region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Normalize size for consistent hashing
        normalized = cv2.resize(region, (57, 82))  # ACR card size
        
        # Generate region identifier for caching
        region_id = hashlib.md5(normalized.tobytes()).hexdigest()
        
        # Check cache first
        if region_id in self.hash_cache:
            cached_hash = self.hash_cache[region_id]
            if cached_hash in self.hash_to_card:
                return self.hash_to_card[cached_hash], 0.95
        
        # Compute perceptual hash
        region_hash = self.compute_perceptual_hash(normalized)
        
        # Cache the hash
        self.hash_cache[region_id] = region_hash
        
        # Direct hash lookup (fastest)
        if region_hash in self.hash_to_card:
            return self.hash_to_card[region_hash], 0.98
        
        # Fuzzy hash matching (for minor variations)
        best_match, best_confidence = self.fuzzy_hash_match(region_hash)
        if best_confidence > 0.85:
            return best_match, best_confidence
        
        # Fallback to template matching for unknown cards
        return self.template_fallback(normalized)
    
    def fuzzy_hash_match(self, target_hash: str, threshold: int = 5) -> Tuple[str, float]:
        """
        Fuzzy matching for minor hash variations.
        Uses Hamming distance for hash comparison.
        """
        best_card = None
        best_score = 0.0
        
        target_int = int(target_hash, 16)
        
        for card_name, card_hash in self.card_hashes.items():
            card_int = int(card_hash, 16)
            
            # Calculate Hamming distance
            xor_result = target_int ^ card_int
            hamming_distance = bin(xor_result).count('1')
            
            # Convert to confidence score
            max_bits = 64  # 8x8 hash = 64 bits
            confidence = 1.0 - (hamming_distance / max_bits)
            
            if confidence > best_score and hamming_distance <= threshold:
                best_score = confidence
                best_card = card_name
        
        return best_card or "unknown", best_score
    
    def template_fallback(self, region: np.ndarray) -> Optional[Tuple[str, float]]:
        """Fallback template matching for hash failures."""
        best_card = None
        best_confidence = 0.0
        
        for card_name, template in self.template_cache.items():
            # Resize template to match region
            resized_template = cv2.resize(template, region.shape[::-1])
            
            # Template matching
            result = cv2.matchTemplate(region, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_card = card_name
        
        if best_confidence > 0.7 and best_card:
            return best_card, best_confidence
        
        return None
    
    def batch_recognize(self, regions: List[np.ndarray]) -> List[Optional[Tuple[str, float]]]:
        """Batch recognition for multiple card regions."""
        results = []
        for region in regions:
            result = self.recognize_card_region(region)
            results.append(result)
        return results
    
    def update_hash_database(self, new_card_image: np.ndarray, card_name: str):
        """Add new card to hash database for learning."""
        card_hash = self.compute_perceptual_hash(new_card_image)
        
        self.card_hashes[card_name] = card_hash
        self.hash_to_card[card_hash] = card_name
        self.template_cache[card_name] = new_card_image.copy()
        
        # Save to disk
        templates_dir = Path("training_data/templates")
        templates_dir.mkdir(exist_ok=True)
        
        template_path = templates_dir / f"{card_name}.png"
        cv2.imwrite(str(template_path), new_card_image)
        
        logger.info(f"Added new card hash for {card_name}")
    
    def get_performance_stats(self) -> Dict:
        """Get recognition performance statistics."""
        return {
            "total_cards": len(self.card_hashes),
            "cached_hashes": len(self.hash_cache),
            "template_cache_size": len(self.template_cache),
            "hash_database_complete": len(self.card_hashes) >= 52
        }

class FastCardBatch:
    """Ultra-fast batch processing for multiple cards."""
    
    def __init__(self):
        self.recognizer = CardHashRecognizer()
    
    def process_poker_table(self, screenshot: np.ndarray, regions: Dict[str, Tuple[int, int, int, int]]) -> Dict[str, Optional[str]]:
        """
        Process entire poker table in one optimized batch.
        Returns dict of region_name -> card_name.
        """
        results = {}
        
        # Extract all regions in one pass
        region_images = {}
        for region_name, (x, y, w, h) in regions.items():
            region_img = screenshot[y:y+h, x:x+w]
            region_images[region_name] = region_img
        
        # Batch process all regions
        for region_name, region_img in region_images.items():
            recognition_result = self.recognizer.recognize_card_region(region_img)
            
            if recognition_result:
                card_name, confidence = recognition_result
                if confidence > 0.8:  # High confidence threshold
                    results[region_name] = card_name
                else:
                    results[region_name] = None
            else:
                results[region_name] = None
        
        return results

# Global instances for performance
hash_recognizer = CardHashRecognizer()
fast_batch = FastCardBatch()

def recognize_card_fast(region: np.ndarray) -> Optional[str]:
    """Fast single card recognition."""
    result = hash_recognizer.recognize_card_region(region)
    return result[0] if result and result[1] > 0.8 else None

def recognize_table_fast(screenshot: np.ndarray, regions: Dict) -> Dict[str, Optional[str]]:
    """Fast full table recognition."""
    return fast_batch.process_poker_table(screenshot, regions)