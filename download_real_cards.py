#!/usr/bin/env python3
"""
Download real poker card images from online sources.
This creates accurate templates that match actual card designs.
"""

import requests
import os
import json
from PIL import Image
from io import BytesIO
from pathlib import Path
import time

def download_card_image(card_name, save_path):
    """Download a real poker card image."""
    
    # Map card names to URLs from open poker card databases
    base_urls = [
        # Open source poker card sets
        f"https://deckofcardsapi.com/static/img/{card_name}.png",
        f"https://raw.githubusercontent.com/hayeah/playing-cards-assets/master/png/{card_name.upper()}.png",
        f"https://tekeye.uk/playing_cards/images/{card_name.lower()}.png"
    ]
    
    for url in base_urls:
        try:
            print(f"Trying to download {card_name} from {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Load and process image
                img = Image.open(BytesIO(response.content))
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to standard template size
                img = img.resize((57, 82), Image.Resampling.LANCZOS)
                
                # Save template
                img.save(save_path)
                print(f"✅ Downloaded and saved {card_name}")
                return True
                
        except Exception as e:
            print(f"Failed URL {url}: {e}")
            continue
    
    return False

def create_card_from_deckofcards_api(card_name):
    """Use Deck of Cards API to get real card images."""
    
    # Map our format to Deck of Cards API format
    rank_map = {
        '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
        'T': '0', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
    }
    
    suit_map = {'s': 'S', 'h': 'H', 'd': 'D', 'c': 'C'}
    
    rank = card_name[0]
    suit = card_name[1]
    
    # Convert to API format
    api_rank = rank_map.get(rank, rank)
    api_suit = suit_map.get(suit.lower(), suit.upper())
    api_card = api_rank + api_suit
    
    url = f"https://deckofcardsapi.com/static/img/{api_card}.png"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        pass
    
    return None

def download_all_real_cards():
    """Download real card images for all 52 cards."""
    
    print("🃏 Downloading Real Poker Card Images")
    print("=" * 50)
    
    template_dir = Path("training_data/templates")
    backup_dir = Path("training_data/generated_backup")
    
    # Backup generated templates
    backup_dir.mkdir(exist_ok=True)
    for generated_file in template_dir.glob("*.png"):
        if generated_file.stem not in ['As', 'Kh', 'Qd', 'Jc', 'Ts']:  # Keep original good ones
            generated_file.rename(backup_dir / generated_file.name)
    
    all_cards = [
        # Spades
        '2S', '3S', '4S', '5S', '6S', '7S', '8S', '9S', '0S', 'JS', 'QS', 'KS', 'AS',
        # Hearts  
        '2H', '3H', '4H', '5H', '6H', '7H', '8H', '9H', '0H', 'JH', 'QH', 'KH', 'AH',
        # Diamonds
        '2D', '3D', '4D', '5D', '6D', '7D', '8D', '9D', '0D', 'JD', 'QD', 'KD', 'AD',
        # Clubs
        '2C', '3C', '4C', '5C', '6C', '7C', '8C', '9C', '0C', 'JC', 'QC', 'KC', 'AC'
    ]
    
    # Map API format back to our format
    api_to_our = {
        '0': 'T'  # 10 is represented as 0 in API
    }
    
    downloaded = 0
    failed = []
    
    for api_card in all_cards:
        # Convert to our naming convention
        rank = api_card[0]
        suit = api_card[1].lower()
        
        our_rank = api_to_our.get(rank, rank)
        our_card = our_rank + suit
        
        template_path = template_dir / f"{our_card}.png"
        
        # Skip if we already have a good template
        if our_card in ['As', 'Kh', 'Qd', 'Jc', 'Ts'] and template_path.exists():
            print(f"✅ {our_card} - Keeping existing template")
            continue
        
        # Try to download real card image
        url = f"https://deckofcardsapi.com/static/img/{api_card}.png"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Process and save image
                img = Image.open(BytesIO(response.content))
                
                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to our template size
                img = img.resize((57, 82), Image.Resampling.LANCZOS)
                
                # Save template
                img.save(template_path)
                
                # Create JSON metadata
                metadata = {
                    "card": our_card,
                    "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "deckofcardsapi.com",
                    "url": url,
                    "rank": our_rank,
                    "suit": suit
                }
                
                json_path = template_dir / f"{our_card}.json"
                with open(json_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"✅ {our_card} - Downloaded real card image")
                downloaded += 1
                
            else:
                print(f"❌ {our_card} - Download failed (HTTP {response.status_code})")
                failed.append(our_card)
                
        except Exception as e:
            print(f"❌ {our_card} - Error: {e}")
            failed.append(our_card)
        
        # Rate limiting
        time.sleep(0.1)
    
    print("\n" + "=" * 50)
    print(f"🎉 Downloaded {downloaded} real card templates")
    
    if failed:
        print(f"❌ Failed to download {len(failed)} cards: {', '.join(failed)}")
        print("These will keep the generated templates as fallback")
    
    # Final count
    total_templates = len(list(template_dir.glob("*.png")))
    print(f"📊 Total templates: {total_templates}/52")
    
    print("\n🌐 Next steps:")
    print("1. Visit http://localhost:5000/training-interface")  
    print("2. View the new real card templates")
    print("3. Test recognition accuracy with actual card designs")

if __name__ == "__main__":
    download_all_real_cards()