#!/usr/bin/env python3
"""
Standalone test script for ACR card reading functionality.
Tests the new card recognition system on calibrated regions.

Run this script locally to test card reading without the API server.
"""

import json
import sys
import time
import cv2
import numpy as np
import os
from PIL import Image, ImageGrab

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.scraper.card_recognition import CardRecognition
    from app.scraper.acr_scraper import ACRScraper
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_card_reading():
    """Test card reading functionality."""
    print("🃏 Testing ACR Card Reading System (Standalone)")
    print("=" * 55)
    
    # Initialize components
    card_recognizer = CardRecognition()
    
    # Try to initialize ACR scraper
    try:
        acr_scraper = ACRScraper()
        has_calibration = acr_scraper.calibrated
    except Exception as e:
        print(f"⚠️ ACR Scraper initialization failed: {e}")
        print("Will test card recognition with manual regions...")
        acr_scraper = None
        has_calibration = False
    
    # Check if calibration exists
    if not has_calibration:
        print("❌ No calibration found!")
        print("Options:")
        print("1. Run calibration tool: python acr_visual_calibrator.py")
        print("2. Continue with manual region testing")
        
        response = input("\nContinue with manual testing? (y/n): ")
        if response.lower() != 'y':
            return False
    
    print(f"✅ Loaded calibration with {len(acr_scraper.ui_regions)} regions")
    
    # Test on live screen
    print("\n📸 Capturing current screen in 3 seconds...")
    print("Make sure ACR poker table is visible!")
    
    for i in range(3, 0, -1):
        print(f"Capturing in {i}...")
        time.sleep(1)
    
    try:
        # Capture full screen
        screenshot = ImageGrab.grab()
        print(f"✅ Screenshot captured: {screenshot.size[0]}x{screenshot.size[1]}")
        
        # Test card regions
        results = {}
        
        # Define test regions
        if has_calibration and acr_scraper and hasattr(acr_scraper, 'ui_regions'):
            test_regions = {
                'hero_cards': acr_scraper.ui_regions.get('hero_cards'),
                'board_cards': acr_scraper.ui_regions.get('board_cards')
            }
        else:
            # Manual test regions (you can adjust these coordinates)
            print("\n📐 Using manual test regions (adjust coordinates if needed)")
            w, h = screenshot.size
            test_regions = {
                'hero_cards_manual': (w//3, h//2, 2*w//3, 3*h//4),  # Bottom center area
                'board_cards_manual': (w//4, h//3, 3*w//4, 2*h//3)   # Center area
            }
            print(f"Screen size: {w}x{h}")
            for name, coords in test_regions.items():
                print(f"  {name}: {coords}")
        
        for region_name, coords in test_regions.items():
            if coords:
                print(f"\n🔍 Testing {region_name}...")
                
                # Extract region
                x1, y1, x2, y2 = coords
                region_image = screenshot.crop((x1, y1, x2, y2))
                
                # Save region for debugging
                region_image.save(f"test_{region_name}.png")
                print(f"📁 Saved region image: test_{region_name}.png")
                
                # Test card recognition
                max_cards = 2 if 'hero' in region_name else 5
                detected_cards = card_recognizer.detect_cards_in_region(region_image, max_cards)
                
                if detected_cards:
                    print(f"✅ Detected {len(detected_cards)} cards:")
                    for card in detected_cards:
                        print(f"   • {card.rank}{card.suit} (confidence: {card.confidence:.2f})")
                    results[region_name] = [str(card) for card in detected_cards]
                else:
                    print(f"❌ No cards detected in {region_name}")
                    results[region_name] = []
                    
                # Test using ACR scraper method if available
                if acr_scraper and has_calibration:
                    try:
                        scraper_cards = acr_scraper._extract_cards_from_region(coords)
                        print(f"🔧 ACR Scraper result: {scraper_cards}")
                    except Exception as e:
                        print(f"⚠️ ACR Scraper test failed: {e}")
                
        # Summary
        print("\n📊 CARD READING TEST RESULTS")
        print("=" * 40)
        
        total_detected = sum(len(cards) for cards in results.values())
        if total_detected > 0:
            print(f"✅ Successfully detected {total_detected} cards total")
            for region, cards in results.items():
                if cards:
                    print(f"   {region}: {', '.join(cards)}")
        else:
            print("❌ No cards detected - may need calibration adjustment")
            
        # Test recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if total_detected == 0:
            print("• Check that poker table is active and visible")
            print("• Verify calibration regions are accurate")
            print("• Ensure cards are clearly visible on screen")
        elif total_detected < 3:
            print("• Some cards may not be visible or clear")
            print("• Consider re-calibrating regions for better accuracy")
        else:
            print("• Card reading system is working well!")
            print("• Ready for live poker analysis")
            
        return total_detected > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_individual_card_methods():
    """Test individual card recognition methods."""
    print("\n🧪 Testing Individual Recognition Methods")
    print("=" * 45)
    
    card_recognizer = CardRecognition()
    
    # Create test card image (placeholder)
    test_image = Image.new('RGB', (100, 140), color='white')
    
    try:
        # Test contour detection
        print("Testing contour detection...")
        cards_contour = card_recognizer._detect_cards_by_contours(
            cv2.cvtColor(np.array(test_image), cv2.COLOR_RGB2BGR), 2
        )
        print(f"Contour method: {len(cards_contour)} cards")
        
        # Test grid detection
        print("Testing grid detection...")
        cards_grid = card_recognizer._detect_cards_by_grid(
            cv2.cvtColor(np.array(test_image), cv2.COLOR_RGB2BGR), 2
        )
        print(f"Grid method: {len(cards_grid)} cards")
        
        # Test OCR detection
        print("Testing OCR detection...")
        cards_ocr = card_recognizer._detect_cards_by_ocr(test_image, 2)
        print(f"OCR method: {len(cards_ocr)} cards")
        
    except Exception as e:
        print(f"Method testing failed: {e}")

def test_simple_card_recognition():
    """Simple standalone card recognition test."""
    print("\n🧪 Simple Card Recognition Test")
    print("=" * 40)
    
    card_recognizer = CardRecognition()
    
    print("📸 Capturing screen for simple test...")
    time.sleep(2)
    
    try:
        screenshot = ImageGrab.grab()
        w, h = screenshot.size
        
        # Test on different screen regions
        test_areas = {
            'center': (w//3, h//3, 2*w//3, 2*h//3),
            'bottom': (w//4, 2*h//3, 3*w//4, h),
            'left': (0, h//3, w//3, 2*h//3)
        }
        
        total_found = 0
        for area_name, coords in test_areas.items():
            print(f"\n🔍 Testing {area_name} area: {coords}")
            
            region = screenshot.crop(coords)
            region.save(f"test_area_{area_name}.png")
            
            cards = card_recognizer.detect_cards_in_region(region, max_cards=5)
            
            if cards:
                print(f"✅ Found {len(cards)} cards:")
                for card in cards:
                    print(f"   • {card.rank}{card.suit} (confidence: {card.confidence:.2f})")
                total_found += len(cards)
            else:
                print(f"❌ No cards detected")
        
        print(f"\n📊 Total cards found: {total_found}")
        return total_found > 0
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🎮 ACR Card Reading Test Suite (Standalone)")
    print("=" * 55)
    
    try:
        # Test imports
        import cv2
        import numpy as np
        import pytesseract
        print("✅ All dependencies available")
        
        print("\nChoose test mode:")
        print("1. Full test with calibration (requires calibrated regions)")
        print("2. Simple test (tests card recognition on screen areas)")
        print("3. Both tests")
        
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        success = False
        
        if choice in ['1', '3']:
            # Test with calibration
            success = test_card_reading()
        
        if choice in ['2', '3']:
            # Simple test
            simple_success = test_simple_card_recognition()
            success = success or simple_success
        
        if choice not in ['1', '2', '3']:
            print("Invalid choice, running simple test...")
            success = test_simple_card_recognition()
        
        # Test individual methods if requested
        if success:
            test_methods = input("\nTest individual recognition methods? (y/n): ")
            if test_methods.lower() == 'y':
                test_individual_card_methods()
        
        if success:
            print("\n🎉 Card reading system is ready!")
        else:
            print("\n⚠️ Card reading needs adjustment")
            
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install required packages: pip install opencv-python pytesseract pillow")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()