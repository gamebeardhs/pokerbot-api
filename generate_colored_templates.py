#!/usr/bin/env python3
"""
Generate a complete 52-card template set using the user's color format:
- Spades: Black background
- Hearts: Red background  
- Diamonds: Blue background
- Clubs: Green background
"""

from PIL import Image, ImageDraw, ImageFont
import json
from datetime import datetime
from pathlib import Path

def create_colored_card_template(card_name):
    """Create a card template with colored background matching the user's format."""
    
    rank = card_name[0]
    suit = card_name[1].lower()
    
    # Color scheme based on user's example
    suit_colors = {
        's': '#2C2C2C',  # Black for spades
        'h': '#C41E3A',  # Red for hearts
        'd': '#2E86AB',  # Blue for diamonds
        'c': '#228B22'   # Green for clubs
    }
    
    # Text color (white for visibility on colored backgrounds)
    text_color = '#FFFFFF'
    
    # Create image with colored background
    img = Image.new('RGB', (57, 82), color=suit_colors[suit])
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([0, 0, 56, 81], outline='#FFFFFF', width=1)
    
    try:
        # Try to load a decent font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw rank in top-left corner
        draw.text((4, 2), rank, fill=text_color, font=font_large)
        
        # Draw suit symbol below rank
        suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
        draw.text((4, 18), suit_symbols.get(suit, suit.upper()), fill=text_color, font=font_small)
        
        # Draw rank in bottom-right corner (upside down)
        draw.text((45, 62), rank, fill=text_color, font=font_large)
        draw.text((45, 78), suit_symbols.get(suit, suit.upper()), fill=text_color, font=font_small)
        
        # For face cards, add center symbol
        if rank in ['J', 'Q', 'K', 'A']:
            # Large center symbol
            draw.text((23, 35), suit_symbols.get(suit, suit.upper()), fill=text_color, font=font_large)
            draw.text((20, 50), rank, fill=text_color, font=font_large)
        
    except Exception as e:
        # Fallback to simple text if font loading fails
        draw.text((20, 35), card_name, fill=text_color)
    
    return img

def generate_all_colored_templates():
    """Generate all 52 card templates with colored backgrounds."""
    
    print("Generating 52-Card Colored Template Set")
    print("=" * 50)
    print("Format: Spades=Black, Hearts=Red, Diamonds=Blue, Clubs=Green")
    print()
    
    template_dir = Path("training_data/templates")
    backup_dir = Path("training_data/previous_templates")
    
    # Backup existing templates
    backup_dir.mkdir(exist_ok=True)
    existing_templates = list(template_dir.glob("*.png"))
    
    if existing_templates:
        print(f"Backing up {len(existing_templates)} existing templates...")
        for template in existing_templates:
            backup_path = backup_dir / template.name
            template.rename(backup_path)
    
    # Generate all 52 cards
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    suits = ['s', 'h', 'd', 'c']  # spades, hearts, diamonds, clubs
    
    created_count = 0
    
    for rank in ranks:
        for suit in suits:
            card_name = rank + suit
            
            # Create template image
            template_img = create_colored_card_template(card_name)
            
            # Save template
            template_path = template_dir / f"{card_name}.png"
            template_img.save(template_path)
            
            # Create metadata
            suit_names = {'s': 'spades', 'h': 'hearts', 'd': 'diamonds', 'c': 'clubs'}
            suit_colors = {'s': 'black', 'h': 'red', 'd': 'blue', 'c': 'green'}
            
            metadata = {
                "card": card_name,
                "rank": rank,
                "suit": suit,
                "suit_name": suit_names[suit],
                "background_color": suit_colors[suit],
                "created": datetime.now().isoformat(),
                "source": "colored_template_generator",
                "format": "user_specified_colors"
            }
            
            json_path = template_dir / f"{card_name}.json"
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            created_count += 1
            print(f"Created {card_name} - {suit_names[suit]} ({suit_colors[suit]})")
    
    print()
    print("=" * 50)
    print(f"Generated {created_count} colored card templates")
    print(f"Total templates: {created_count}/52")
    print()
    print("Color scheme:")
    print("- Spades: Black background")
    print("- Hearts: Red background") 
    print("- Diamonds: Blue background")
    print("- Clubs: Green background")
    print()
    print("Next steps:")
    print("1. Visit http://localhost:5000/training-interface")
    print("2. View your new colored templates")
    print("3. Test recognition accuracy")

if __name__ == "__main__":
    generate_all_colored_templates()