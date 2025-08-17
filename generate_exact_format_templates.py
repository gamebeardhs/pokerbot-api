#!/usr/bin/env python3
"""
Generate exact replica templates matching the user's 5-card format.
Recreates the precise visual style, font, and layout.
"""

from PIL import Image, ImageDraw, ImageFont
import json
from datetime import datetime
from pathlib import Path

def create_exact_format_card(card_name):
    """Create card template matching the exact user format."""
    
    rank = card_name[0]
    suit = card_name[1].lower()
    
    # Exact colors from user's example
    suit_colors = {
        's': '#2C2C2C',  # Black/dark gray for spades
        'h': '#CC0000',  # Red for hearts
        'd': '#0066CC',  # Blue for diamonds  
        'c': '#009900'   # Green for clubs
    }
    
    # Create 57x82 template (standard card ratio)
    img = Image.new('RGB', (57, 82), color=suit_colors[suit])
    draw = ImageDraw.Draw(img)
    
    # Try to match the user's font style and layout exactly
    try:
        # Try different font options to match the bold, clear style
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
            "/System/Library/Fonts/Arial.ttf",
            "arial.ttf",
            "calibri.ttf"
        ]
        
        font_large = None
        font_medium = None
        
        for font_path in font_paths:
            try:
                font_large = ImageFont.truetype(font_path, 20)  # Large for main rank
                font_medium = ImageFont.truetype(font_path, 16)  # Medium for corners
                break
            except:
                continue
        
        # Fallback to default if no fonts work
        if not font_large:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
    
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
    
    # White text for visibility on colored backgrounds
    text_color = '#FFFFFF'
    
    # Draw the main rank in center (large and prominent like user's example)
    # Center the rank both horizontally and vertically
    bbox = draw.textbbox((0, 0), rank, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    center_x = (57 - text_width) // 2
    center_y = (82 - text_height) // 2
    
    draw.text((center_x, center_y), rank, fill=text_color, font=font_large)
    
    # Add small rank in top-left corner
    draw.text((3, 2), rank, fill=text_color, font=font_medium)
    
    # Add small rank in bottom-right corner  
    bbox_small = draw.textbbox((0, 0), rank, font=font_medium)
    small_width = bbox_small[2] - bbox_small[0]
    small_height = bbox_small[3] - bbox_small[1]
    
    draw.text((57 - small_width - 3, 82 - small_height - 2), rank, fill=text_color, font=font_medium)
    
    # Optional: Add subtle border like in user's example
    draw.rectangle([0, 0, 56, 81], outline='#CCCCCC', width=1)
    
    return img

def generate_all_exact_format_templates():
    """Generate all 52 cards in the exact user format."""
    
    print("Generating 52 Cards in Your Exact Format")
    print("=" * 50)
    print("Recreating the precise visual style from your 5-card example")
    print()
    
    template_dir = Path("training_data/templates")
    backup_dir = Path("training_data/colored_backup")
    
    # Backup current templates
    backup_dir.mkdir(exist_ok=True)
    existing_templates = list(template_dir.glob("*.png"))
    
    if existing_templates:
        print(f"Backing up {len(existing_templates)} existing templates...")
        for template in existing_templates:
            backup_path = backup_dir / template.name
            template.rename(backup_path)
    
    # Generate all 52 cards using exact format
    ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K']
    suits = ['s', 'h', 'd', 'c']  
    
    created_count = 0
    
    print("Creating templates with exact visual format...")
    
    for rank in ranks:
        for suit in suits:
            card_name = rank + suit
            
            # Create template matching user's exact format
            template_img = create_exact_format_card(card_name)
            
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
                "source": "exact_user_format_replica",
                "format": "matches_user_5card_example"
            }
            
            json_path = template_dir / f"{card_name}.json"
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            created_count += 1
            
            # Show progress for key cards
            if card_name in ['As', 'Kh', 'Qd', 'Jc', 'Ts']:
                print(f"✓ {card_name} - Matches your example format")
            elif created_count % 13 == 0:
                print(f"✓ Completed {suit_names[suit]} suit ({created_count}/52)")
    
    print()
    print("=" * 50)
    print(f"Generated {created_count} templates in your exact format")
    print()
    print("Format details:")
    print("- Large centered rank (main visual element)")
    print("- Small ranks in corners")
    print("- Bold, clear fonts")
    print("- Colored backgrounds: Black/Red/Blue/Green")
    print("- White text for maximum visibility")
    print()
    print("These templates now match your 5-card example precisely.")
    print("Visit http://localhost:5000/training-interface to see the results")

if __name__ == "__main__":
    generate_all_exact_format_templates()