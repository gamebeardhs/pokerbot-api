"""
Offline OCR regression test runner.
Tests OCR accuracy against saved golden reference images without requiring live ACR.
"""

import json
import os
import sys
import cv2
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.scraper.enhanced_ocr_engine import EnhancedOCREngine
from app.core.turn_detection import TurnDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crop_rel(img, rel_coords):
    """Crop image using relative coordinates."""
    h, w = img.shape[:2]
    rx, ry, rw, rh = rel_coords
    x1 = int(rx * w)
    y1 = int(ry * h) 
    x2 = int((rx + rw) * w)
    y2 = int((ry + rh) * h)
    return img[y1:y2, x1:x2]

def test_turn_detection(img, regions, ocr_engine):
    """Test turn detection using button OCR + timer fallback."""
    # Button detection
    btn_img = crop_rel(img, regions["buttons"])
    btn_txt = ocr_engine.extract_text(btn_img, "buttons").upper()
    
    button_keywords = ("CALL", "CHECK", "RAISE", "BET", "FOLD", "ALLIN", "ALL IN")
    buttons_present = any(keyword in btn_txt for keyword in button_keywords)
    
    # Timer arc fallback
    arc_img = crop_rel(img, regions["hero_timer_arc"])
    hsv = cv2.cvtColor(arc_img, cv2.COLOR_BGR2HSV)
    
    # HSV ranges for timer detection
    mask = (
        cv2.inRange(hsv, (90, 120, 140), (110, 255, 255)) |  # cyan/blue
        cv2.inRange(hsv, (70, 120, 140), (89, 255, 255)) |   # green  
        cv2.inRange(hsv, (40, 120, 140), (69, 255, 255))     # yellow-green
    )
    
    timer_active = mask.mean() > 5.0
    is_our_turn = buttons_present or timer_active
    
    return {
        "buttons_text": btn_txt,
        "buttons_present": buttons_present,
        "timer_active": timer_active,
        "is_our_turn": is_our_turn
    }

def run_ocr_test(test_folder):
    """Run OCR regression test against golden reference."""
    logger.info(f"Running OCR regression test: {test_folder}")
    
    # Load test metadata
    meta_path = os.path.join(test_folder, "meta.json")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"meta.json not found in {test_folder}")
        
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    regions = meta["regions"]
    expected = meta.get("expected", {})
    
    # Load main table image
    table_path = os.path.join(test_folder, "table_full.png")
    if not os.path.exists(table_path):
        raise FileNotFoundError(f"table_full.png not found in {test_folder}")
        
    table_img = cv2.imread(table_path)
    if table_img is None:
        raise ValueError("Failed to load table_full.png")
    
    logger.info(f"Loaded table image: {table_img.shape}")
    
    # Initialize OCR engine
    ocr_engine = EnhancedOCREngine()
    
    # Test results
    results = {
        "test_folder": test_folder,
        "table_dimensions": table_img.shape[:2]
    }
    
    # Test pot OCR
    if "pot" in regions:
        pot_img = crop_rel(table_img, regions["pot"])
        pot_raw = ocr_engine.extract_text(pot_img, "money")
        pot_normalized = ocr_engine.normalize_money(pot_raw)
        
        results["pot"] = {
            "raw": pot_raw,
            "normalized": pot_normalized,
            "region": regions["pot"]
        }
    
    # Test hero stack OCR
    if "hero_stack" in regions:
        stack_img = crop_rel(table_img, regions["hero_stack"])
        stack_raw = ocr_engine.extract_text(stack_img, "stack")
        stack_normalized = ocr_engine.normalize_money(stack_raw)
        
        results["hero_stack"] = {
            "raw": stack_raw,
            "normalized": stack_normalized,
            "region": regions["hero_stack"]
        }
    
    # Test turn detection
    turn_results = test_turn_detection(table_img, regions, ocr_engine)
    results["turn_detection"] = turn_results
    
    # Test board cards (if region exists)
    if "board" in regions:
        board_img = crop_rel(table_img, regions["board"])
        board_text = ocr_engine.extract_text(board_img, "general")
        results["board"] = {
            "raw": board_text,
            "region": regions["board"]
        }
    
    # Test hero cards (if region exists)
    if "hero_cards" in regions:
        cards_img = crop_rel(table_img, regions["hero_cards"])
        cards_text = ocr_engine.extract_text(cards_img, "general")
        results["hero_cards"] = {
            "raw": cards_text,
            "region": regions["hero_cards"]
        }
    
    # Print results
    print(json.dumps(results, indent=2))
    
    # Run assertions against expected values
    failures = []
    
    if "pot" in expected and "pot" in results:
        if expected["pot"] != results["pot"]["normalized"]:
            failures.append(("pot", expected["pot"], results["pot"]["normalized"]))
    
    if "hero_stack" in expected and "hero_stack" in results:
        if expected["hero_stack"] != results["hero_stack"]["normalized"]:
            failures.append(("hero_stack", expected["hero_stack"], results["hero_stack"]["normalized"]))
    
    if "buttons_present" in expected:
        actual = results["turn_detection"]["buttons_present"]
        if expected["buttons_present"] != actual:
            failures.append(("buttons_present", expected["buttons_present"], actual))
    
    if "is_our_turn" in expected:
        actual = results["turn_detection"]["is_our_turn"]
        if expected["is_our_turn"] != actual:
            failures.append(("is_our_turn", expected["is_our_turn"], actual))
    
    # Report test results
    if failures:
        logger.error("❌ REGRESSION TEST FAILED")
        print("\nASSERTION FAILURES:")
        for field, expected_val, actual_val in failures:
            print(f"- {field}: expected '{expected_val}' got '{actual_val}'")
        return False
    else:
        logger.info("✅ REGRESSION TEST PASSED")
        print(f"\n✅ All assertions passed for {len(expected)} expected values")
        return True

def main():
    """Main entry point for offline OCR testing."""
    if len(sys.argv) < 2:
        test_folder = "tests/acr_golden"
    else:
        test_folder = sys.argv[1]
    
    try:
        success = run_ocr_test(test_folder)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()