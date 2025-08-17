#!/usr/bin/env python3
"""Test the template recognition system with actual created templates."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
from app.scraper.card_recognition import CardRecognition
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_template_recognition_with_created_templates():
    """Test template recognition using the created template images."""
    print("\n=== Testing Template Recognition with Created Templates ===")
    
    recognizer = CardRecognition()
    
    # Test with each created template
    template_files = [
        "test_template_As.png",
        "test_template_Kh.png", 
        "test_template_Qd.png",
        "test_template_Jc.png",
        "test_template_Ts.png"
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            print(f"\nTesting with {template_file}:")
            
            # Load the template image
            test_image = Image.open(template_file)
            print(f"  Image size: {test_image.size}")
            
            # Test dual mode recognition
            cards = recognizer.detect_cards_dual_mode(test_image, max_cards=2)
            print(f"  Dual recognition found {len(cards)} cards:")
            for card in cards:
                print(f"    - {card} (confidence: {card.confidence:.3f})")
                
            # Also test legacy recognition for comparison  
            legacy_cards = recognizer.detect_cards_in_region(test_image, max_cards=2)
            print(f"  Legacy recognition found {len(legacy_cards)} cards:")
            for card in legacy_cards:
                print(f"    - {card} (confidence: {card.confidence:.3f})")
        else:
            print(f"Template file {template_file} not found")

def test_data_augmentation():
    """Test the data augmentation system."""
    print("\n=== Testing Data Augmentation System ===")
    
    try:
        from app.training.neural_trainer import NeuralCardTrainer
        
        trainer = NeuralCardTrainer()
        
        # Generate training dataset from templates
        dataset = trainer.generate_training_dataset(variants_per_card=5)  # Small number for testing
        
        print(f"Generated training dataset:")
        print(f"  Total images: {len(dataset['images'])}")
        print(f"  Total labels: {len(dataset['labels'])}")
        print(f"  Unique cards: {len(set(dataset['card_names']))}")
        
        # Show card distribution
        card_counts = {}
        for card in dataset['card_names']:
            card_counts[card] = card_counts.get(card, 0) + 1
        
        print(f"  Card distribution:")
        for card, count in card_counts.items():
            print(f"    {card}: {count} variants")
            
    except Exception as e:
        print(f"Data augmentation test failed: {e}")

def main():
    """Run template recognition tests."""
    print("Testing Enhanced Template Recognition System")
    print("=" * 50)
    
    # Test with created templates
    test_template_recognition_with_created_templates()
    
    # Test data augmentation
    test_data_augmentation()
    
    print("\n" + "=" * 50)
    print("Template recognition tests completed!")

if __name__ == "__main__":
    main()