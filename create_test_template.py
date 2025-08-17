#!/usr/bin/env python3
"""Create a test template to demonstrate the template system."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from app.training.neural_trainer import TemplateManager
import base64
import io
import json

def create_card_template(rank, suit):
    """Create a realistic-looking card template."""
    # Create a white card background
    width, height = 80, 120
    card = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(card)
    
    # Add card border
    draw.rectangle([2, 2, width-3, height-3], outline='black', width=2)
    
    # Define colors for suits
    suit_colors = {
        's': 'black',  # spades
        'c': 'black',  # clubs
        'h': 'red',    # hearts
        'd': 'red'     # diamonds
    }
    
    # Define suit symbols
    suit_symbols = {
        's': '♠',  # spades
        'h': '♥',  # hearts
        'd': '♦',  # diamonds
        'c': '♣'   # clubs
    }
    
    color = suit_colors.get(suit, 'black')
    symbol = suit_symbols.get(suit, suit)
    
    try:
        # Try to use a larger font
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # Draw rank in top-left corner
    draw.text((8, 8), rank, fill=color, font=font_large)
    
    # Draw suit symbol below rank
    draw.text((8, 35), symbol, fill=color, font=font_medium)
    
    # Draw smaller rank and suit in bottom-right (upside down)
    draw.text((width-25, height-35), rank, fill=color, font=font_medium)
    draw.text((width-25, height-55), symbol, fill=color, font=font_medium)
    
    return card

def create_and_save_template(card_name, rank, suit):
    """Create a template and save it using the TemplateManager."""
    template_manager = TemplateManager()
    
    # Create the card image
    card_image = create_card_template(rank, suit)
    
    # Save the template using add_template method (check signature)
    success = template_manager.add_template(card_name, card_image, 0.7)
    
    if success:
        print(f"✓ Created template for {card_name}")
        
        # Also save as a file for visual inspection
        card_image.save(f"test_template_{card_name}.png")
        print(f"  Saved visual template as test_template_{card_name}.png")
    else:
        print(f"✗ Failed to create template for {card_name}")
    
    return success

def test_template_matching():
    """Test template matching with created templates."""
    template_manager = TemplateManager()
    
    # Get all templates
    templates = template_manager.get_all_templates()
    print(f"\nFound {len(templates)} templates:")
    
    for name, template in templates.items():
        print(f"  - {name}: confidence threshold {template.confidence_threshold}")
        
        # Test matching against itself (should be high confidence)
        test_image = create_card_template(name[0], name[1])
        confidence = template_manager.match_template(test_image, name)
        print(f"    Self-match confidence: {confidence:.3f}")

def main():
    """Create test templates and demonstrate the system."""
    print("Creating Test Templates for Dual Recognition System")
    print("=" * 55)
    
    # Create a few sample card templates
    test_cards = [
        ("As", "A", "s"),  # Ace of Spades
        ("Kh", "K", "h"),  # King of Hearts
        ("Qd", "Q", "d"),  # Queen of Diamonds
        ("Jc", "J", "c"),  # Jack of Clubs
        ("Ts", "T", "s"),  # Ten of Spades
    ]
    
    created_count = 0
    for card_name, rank, suit in test_cards:
        if create_and_save_template(card_name, rank, suit):
            created_count += 1
    
    print(f"\nCreated {created_count} templates successfully!")
    
    if created_count > 0:
        print("\nTesting template matching...")
        test_template_matching()
    
    print("\n" + "=" * 55)
    print(f"Template creation complete! Created {created_count} templates.")
    print("You can now test the dual recognition system with these templates.")

if __name__ == "__main__":
    main()