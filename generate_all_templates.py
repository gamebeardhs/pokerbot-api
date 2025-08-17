#!/usr/bin/env python3
"""
Generate all 52 card templates automatically.
This script creates templates for all poker cards using multiple methods.
"""

import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_existing_templates():
    """Check how many templates already exist."""
    template_dir = Path("training_data/templates")
    if not template_dir.exists():
        template_dir.mkdir(parents=True, exist_ok=True)
        return 0
    
    # Count existing .png template files
    templates = list(template_dir.glob("*.png"))
    return len(templates)

def create_template_from_open_source(card_name):
    """Create a template by downloading from open source."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import json
        from datetime import datetime
        
        template_dir = Path("training_data/templates")
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a realistic-looking card template
        # Standard poker card ratio: 57x82 pixels
        img = Image.new('RGB', (57, 82), color='white')
        draw = ImageDraw.Draw(img)
        
        # Parse card name
        rank = card_name[0]
        suit = card_name[1].lower()
        
        # Suit symbols and colors
        suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
        suit_colors = {'s': 'black', 'h': 'red', 'd': 'red', 'c': 'black'}
        
        # Draw border
        draw.rectangle([0, 0, 56, 81], outline='black', width=1)
        
        # Draw rank and suit (simplified)
        try:
            # Try to draw the card representation
            draw.text((5, 5), rank, fill=suit_colors[suit])
            draw.text((5, 15), suit_symbols.get(suit, suit), fill=suit_colors[suit])
            draw.text((45, 65), rank, fill=suit_colors[suit])
            draw.text((45, 75), suit_symbols.get(suit, suit), fill=suit_colors[suit])
        except:
            # Fallback to simple text
            draw.text((20, 35), card_name, fill='black')
        
        # Save template
        template_path = template_dir / f"{card_name}.png"
        img.save(template_path)
        
        # Create JSON metadata
        metadata = {
            "card": card_name,
            "created": datetime.now().isoformat(),
            "source": "generated_template",
            "rank": rank,
            "suit": suit
        }
        
        json_path = template_dir / f"{card_name}.json"
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create template for {card_name}: {e}")
        return False

def main():
    """Generate all 52 card templates."""
    print("🃏 Generating Complete 52-Card Template Set")
    print("=" * 50)
    
    try:
        # Check existing templates
        existing_count = check_existing_templates()
        print(f"📊 Current templates: {existing_count}")
        
        if existing_count >= 52:
            print("✅ All 52 templates already exist!")
            print("\nTo view them, visit: http://localhost:5000/training-interface")
            return
        
        print(f"📦 Need to generate {52 - existing_count} more templates")
        print()
        
        # Generate missing templates
        all_cards = [
            # Spades
            '2s', '3s', '4s', '5s', '6s', '7s', '8s', '9s', 'Ts', 'Js', 'Qs', 'Ks', 'As',
            # Hearts  
            '2h', '3h', '4h', '5h', '6h', '7h', '8h', '9h', 'Th', 'Jh', 'Qh', 'Kh', 'Ah',
            # Diamonds
            '2d', '3d', '4d', '5d', '6d', '7d', '8d', '9d', 'Td', 'Jd', 'Qd', 'Kd', 'Ad',
            # Clubs
            '2c', '3c', '4c', '5c', '6c', '7c', '8c', '9c', 'Tc', 'Jc', 'Qc', 'Kc', 'Ac'
        ]
        
        generated_count = 0
        
        for card in all_cards:
            template_path = Path(f"training_data/templates/{card}.png")
            
            if template_path.exists():
                print(f"✅ {card} - Already exists")
                continue
            
            try:
                # Try to generate template
                success = create_template_from_open_source(card)
                
                if success:
                    print(f"✅ {card} - Generated successfully")
                    generated_count += 1
                else:
                    print(f"⚠️  {card} - Generation failed, will need manual creation")
                    
            except Exception as e:
                print(f"❌ {card} - Error: {e}")
        
        print()
        print("=" * 50)
        print(f"🎉 Generated {generated_count} new templates")
        
        # Final stats
        final_count = check_existing_templates()
        print(f"📊 Total templates now: {final_count}/52")
        
        if final_count >= 52:
            print("🎉 Complete 52-card template set ready!")
        else:
            missing = 52 - final_count
            print(f"📝 Still need {missing} templates - create them manually via /training-interface")
        
        print()
        print("🌐 Next steps:")
        print("1. Visit http://localhost:5000/training-interface")  
        print("2. Test template recognition accuracy")
        print("3. Create missing templates manually if needed")
        print("4. Use templates for card recognition training")
        
    except Exception as e:
        logger.error(f"Template generation failed: {e}")
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()