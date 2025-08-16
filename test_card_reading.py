#!/usr/bin/env python3
"""
Test script for ACR card reading functionality.
Tests the new card recognition system on calibrated regions.
"""

import json
import sys
import time
import cv2
import numpy as np
from PIL import Image, ImageGrab
from app.scraper.card_recognition import CardRecognition
from app.scraper.acr_scraper import ACRScraper

def test_card_reading():
    """Test card reading functionality."""
    print("🃏 Testing ACR Card Reading System")
    print("=" * 50)
    
    # Initialize components
    card_recognizer = CardRecognition()
    acr_scraper = ACRScraper()
    
    # Check if calibration exists
    if not acr_scraper.calibrated:
        print("❌ No calibration found!")
        print("Run the calibration tool first: python acr_visual_calibrator.py")
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
        
        for region_name in ['hero_cards', 'board_cards']:
            if region_name in acr_scraper.ui_regions:
                print(f"\n🔍 Testing {region_name}...")
                
                # Extract region
                coords = acr_scraper.ui_regions[region_name]
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
                    
                # Test using ACR scraper method
                scraper_cards = acr_scraper._extract_cards_from_region(coords)
                print(f"🔧 ACR Scraper result: {scraper_cards}")
                
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

def main():
    """Main test function."""
    print("🎮 ACR Card Reading Test Suite")
    print("=" * 50)
    
    try:
        # Test imports
        import cv2
        import numpy as np
        import pytesseract
        print("✅ All dependencies available")
        
        # Test card reading system
        success = test_card_reading()
        
        # Test individual methods
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