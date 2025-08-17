#!/usr/bin/env python3
"""
Test the trained neural network with ACR templates.
"""

from pathlib import Path
from app.recognition.neural_recognizer import TrainedACRRecognizer
from PIL import Image
import cv2
import numpy as np

def test_neural_network():
    """Test trained neural network on sample templates."""
    print("Testing Trained Neural Network")
    print("=" * 50)
    
    # Initialize recognizer
    recognizer = TrainedACRRecognizer()
    
    if not recognizer.is_available():
        print("❌ Neural network model not available")
        return
    
    print("✅ Neural network model loaded successfully")
    
    # Test on some template images
    templates_dir = Path("training_data/templates")
    test_cards = ['As', 'Kh', 'Qd', 'Jc', 'Ts']
    
    print("\nTesting recognition on template cards:")
    for card_name in test_cards:
        template_path = templates_dir / f"{card_name}.png"
        
        if template_path.exists():
            # Load image
            image = Image.open(template_path)
            
            # Predict card
            predicted_card, confidence = recognizer.predict_card(image)
            
            # Check if correct
            correct = predicted_card == card_name
            status = "✅" if correct else "❌"
            
            print(f"{status} {card_name}: Predicted {predicted_card} (confidence: {confidence:.3f})")
        else:
            print(f"❌ Template not found: {card_name}")
    
    # Test on generated training data
    print("\nTesting on generated training variants:")
    advanced_dir = Path("training_data/advanced_dataset")
    
    if advanced_dir.exists():
        # Test a few variants
        sample_cards = ['As', 'Kh']
        for card_name in sample_cards:
            card_dir = advanced_dir / card_name
            if card_dir.exists():
                variants = list(card_dir.glob("*.png"))[:5]  # Test first 5 variants
                
                correct_predictions = 0
                total_predictions = 0
                
                for variant_path in variants:
                    try:
                        image = Image.open(variant_path)
                        predicted_card, confidence = recognizer.predict_card(image)
                        
                        if predicted_card == card_name:
                            correct_predictions += 1
                        total_predictions += 1
                        
                    except Exception as e:
                        print(f"Error testing {variant_path}: {e}")
                
                accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
                print(f"  {card_name}: {correct_predictions}/{total_predictions} correct ({accuracy:.1%})")
    
    print("\nNeural network testing complete!")

if __name__ == "__main__":
    test_neural_network()