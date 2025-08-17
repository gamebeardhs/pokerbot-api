#!/usr/bin/env python3
"""Test script for the dual recognition system."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
import numpy as np
from app.scraper.card_recognition import CardRecognition, DualCardRecognition
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_test_card_image():
    """Create a simple test card image for testing."""
    # Create a 80x120 white image (card-like dimensions)
    img_array = np.ones((120, 80, 3), dtype=np.uint8) * 255
    
    # Add some simple text-like features (simulate an Ace of Spades)
    # Add black areas for rank and suit
    img_array[10:30, 10:30] = [0, 0, 0]  # Top-left corner for rank
    img_array[90:110, 50:70] = [0, 0, 0]  # Bottom-right for suit
    
    # Add some edges to make it look more card-like
    img_array[0:5, :] = [200, 200, 200]  # Top border
    img_array[-5:, :] = [200, 200, 200]  # Bottom border
    img_array[:, 0:3] = [200, 200, 200]  # Left border
    img_array[:, -3:] = [200, 200, 200]  # Right border
    
    return Image.fromarray(img_array)

def test_legacy_recognition():
    """Test the legacy OCR-based recognition."""
    print("\n=== Testing Legacy Card Recognition ===")
    
    recognizer = CardRecognition()
    test_image = create_test_card_image()
    
    try:
        cards = recognizer.detect_cards_in_region(test_image, max_cards=2)
        print(f"Legacy recognition found {len(cards)} cards:")
        for card in cards:
            print(f"  - {card} (confidence: {card.confidence:.2f})")
    except Exception as e:
        print(f"Legacy recognition failed: {e}")

def test_dual_recognition():
    """Test the enhanced dual recognition system."""
    print("\n=== Testing Dual Recognition System ===")
    
    try:
        dual_recognizer = DualCardRecognition()
        test_image = create_test_card_image()
        
        # Test the dual mode detection
        cards = dual_recognizer.detect_cards_in_region(test_image, max_cards=2)
        print(f"Dual recognition found {len(cards)} cards:")
        for card in cards:
            print(f"  - {card} (confidence: {card.confidence:.2f})")
            
    except Exception as e:
        print(f"Dual recognition failed: {e}")

def test_template_system():
    """Test the template-based recognition."""
    print("\n=== Testing Template System ===")
    
    try:
        from app.training.neural_trainer import TemplateManager, ColorNormalizer
        
        template_manager = TemplateManager()
        color_normalizer = ColorNormalizer()
        
        print(f"Template manager initialized successfully")
        
        # Check for existing templates
        templates = template_manager.get_all_templates()
        print(f"Found {len(templates)} templates in the system")
        
        if templates:
            for name, template in templates.items():
                print(f"  - {name}: confidence threshold {template.confidence_threshold}")
        else:
            print("  No templates found - template training needed")
            
        # Test color normalizer
        test_image = create_test_card_image()
        normalized = color_normalizer.normalize_card_region(test_image)
        print(f"Color normalization successful: {normalized.size}")
        
    except ImportError:
        print("Template system not available (import error)")
    except Exception as e:
        print(f"Template system test failed: {e}")

def main():
    """Run all recognition tests."""
    print("Starting Card Recognition System Tests...")
    print("=" * 50)
    
    # Test legacy system
    test_legacy_recognition()
    
    # Test dual recognition
    test_dual_recognition()
    
    # Test template system components
    test_template_system()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main()