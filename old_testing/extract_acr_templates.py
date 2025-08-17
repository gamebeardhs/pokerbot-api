#!/usr/bin/env python3
"""
Extract ACR card templates automatically from multiple sources.
This will save you from manually creating all 52 card templates.
"""

import os
import shutil
import requests
import zipfile
from pathlib import Path
from PIL import Image
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.training.neural_trainer import TemplateManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ACRTemplateExtractor:
    def __init__(self):
        self.template_manager = TemplateManager()
        self.acr_path = r"C:\AmericasCardroom\resources\assets\gc\hdpi\kpoker"
        
        # Standard 52-card deck mapping
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.suits = ['s', 'h', 'd', 'c']  # spades, hearts, diamonds, clubs
        self.all_cards = [rank + suit for rank in self.ranks for suit in self.suits]
        
    def extract_from_acr_client(self) -> bool:
        """Extract templates directly from ACR client installation."""
        print("\n🎯 Method 1: Extracting from ACR Client")
        print("=" * 50)
        
        if not os.path.exists(self.acr_path):
            print(f"❌ ACR client not found at: {self.acr_path}")
            print("   Please install ACR client first or check the path")
            return False
        
        print(f"✅ Found ACR client at: {self.acr_path}")
        
        # List all PNG files in the ACR directory
        png_files = [f for f in os.listdir(self.acr_path) if f.endswith('.png')]
        print(f"📁 Found {len(png_files)} PNG files")
        
        card_files = []
        for file in png_files:
            # Look for card-like files (you may need to adjust this based on ACR naming)
            if any(rank in file.upper() for rank in ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']):
                card_files.append(file)
            elif any(suit in file.lower() for suit in ['spade', 'heart', 'diamond', 'club']):
                card_files.append(file)
        
        print(f"🃏 Found {len(card_files)} potential card files:")
        for file in card_files[:10]:  # Show first 10
            print(f"   - {file}")
        if len(card_files) > 10:
            print(f"   ... and {len(card_files) - 10} more")
            
        # Copy card files to our templates directory
        created_count = 0
        for file in card_files:
            try:
                source_path = os.path.join(self.acr_path, file)
                image = Image.open(source_path)
                
                # Try to determine card from filename
                card_name = self._guess_card_from_filename(file)
                if card_name and card_name in self.all_cards:
                    success = self.template_manager.add_template(card_name, image, 0.8)
                    if success:
                        created_count += 1
                        print(f"   ✅ Created template: {card_name} from {file}")
                    
            except Exception as e:
                logger.debug(f"Failed to process {file}: {e}")
                
        print(f"\n✅ Successfully created {created_count} templates from ACR client!")
        return created_count > 0
    
    def download_opensource_templates(self) -> bool:
        """Download templates from the hayeah/playing-cards-assets repository."""
        print("\n🌐 Method 2: Downloading Open Source Templates")
        print("=" * 50)
        
        try:
            # Download the ZIP file from GitHub
            url = "https://github.com/hayeah/playing-cards-assets/archive/master.zip"
            print("📥 Downloading playing-cards-assets...")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save and extract ZIP file
            zip_path = "playing-cards-assets.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("📦 Extracting templates...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("temp_cards")
            
            # Find PNG files in extracted content
            png_dir = Path("temp_cards/playing-cards-assets-master/png")
            if png_dir.exists():
                created_count = 0
                png_files = list(png_dir.glob("*.png"))
                print(f"🃏 Found {len(png_files)} card images")
                
                for png_file in png_files:
                    try:
                        # Parse filename to get card (e.g., "2_of_spades.png" -> "2s")
                        card_name = self._parse_opensource_filename(png_file.name)
                        if card_name and card_name in self.all_cards:
                            image = Image.open(png_file)
                            success = self.template_manager.add_template(card_name, image, 0.8)
                            if success:
                                created_count += 1
                                print(f"   ✅ Created template: {card_name}")
                                
                    except Exception as e:
                        logger.debug(f"Failed to process {png_file}: {e}")
                
                print(f"\n✅ Successfully created {created_count} templates from open source!")
                
                # Cleanup
                os.remove(zip_path)
                shutil.rmtree("temp_cards")
                
                return created_count > 0
            else:
                print("❌ Could not find PNG directory in downloaded files")
                return False
                
        except Exception as e:
            print(f"❌ Failed to download open source templates: {e}")
            return False
    
    def create_all_missing_templates(self) -> bool:
        """Create any missing templates using our existing template generator."""
        print("\n🎨 Method 3: Creating Missing Templates")
        print("=" * 50)
        
        existing_templates = self.template_manager.get_all_templates()
        missing_cards = [card for card in self.all_cards if card not in existing_templates]
        
        if not missing_cards:
            print("✅ All 52 cards already have templates!")
            return True
            
        print(f"📝 Creating templates for {len(missing_cards)} missing cards...")
        
        from create_test_template import create_card_template
        
        created_count = 0
        for card in missing_cards:
            try:
                rank, suit = card[0], card[1]
                card_image = create_card_template(rank, suit)
                success = self.template_manager.add_template(card, card_image, 0.7)
                if success:
                    created_count += 1
                    if created_count <= 5:  # Show first 5
                        print(f"   ✅ Created template: {card}")
                        
            except Exception as e:
                logger.debug(f"Failed to create template for {card}: {e}")
        
        if created_count > 5:
            print(f"   ... and {created_count - 5} more templates")
            
        print(f"\n✅ Successfully created {created_count} missing templates!")
        return created_count > 0
    
    def _guess_card_from_filename(self, filename: str) -> str:
        """Guess card name from ACR filename."""
        # This is a best-guess function - ACR naming may vary
        filename_upper = filename.upper()
        
        # Try to find rank and suit in filename
        rank_map = {
            'ACE': 'A', 'KING': 'K', 'QUEEN': 'Q', 'JACK': 'J',
            'TEN': 'T', '10': 'T',
            'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': 'T',
            '9': '9', '8': '8', '7': '7', '6': '6', '5': '5', '4': '4', '3': '3', '2': '2'
        }
        
        suit_map = {
            'SPADE': 's', 'HEART': 'h', 'DIAMOND': 'd', 'CLUB': 'c',
            'SPADES': 's', 'HEARTS': 'h', 'DIAMONDS': 'd', 'CLUBS': 'c',
            'S': 's', 'H': 'h', 'D': 'd', 'C': 'c'
        }
        
        found_rank = None
        found_suit = None
        
        for key, rank in rank_map.items():
            if key in filename_upper:
                found_rank = rank
                break
                
        for key, suit in suit_map.items():
            if key in filename_upper:
                found_suit = suit
                break
        
        if found_rank and found_suit:
            return found_rank + found_suit
            
        return None
    
    def _parse_opensource_filename(self, filename: str) -> str:
        """Parse open source filename to card name."""
        # Common patterns: "2_of_spades.png", "ace_of_hearts.png"
        filename_lower = filename.lower().replace('.png', '')
        
        rank_map = {
            'ace': 'A', 'king': 'K', 'queen': 'Q', 'jack': 'J',
            '10': 'T', 'ten': 'T',
            '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
        }
        
        suit_map = {
            'spades': 's', 'hearts': 'h', 'diamonds': 'd', 'clubs': 'c'
        }
        
        for rank_key, rank in rank_map.items():
            for suit_key, suit in suit_map.items():
                if rank_key in filename_lower and suit_key in filename_lower:
                    return rank + suit
        
        return None
    
    def run_extraction(self):
        """Run the complete template extraction process."""
        print("🃏 ACR Card Template Extractor")
        print("=" * 60)
        
        initial_count = len(self.template_manager.get_all_templates())
        print(f"📊 Starting with {initial_count} existing templates")
        
        success = False
        
        # Method 1: Try ACR client extraction
        if self.extract_from_acr_client():
            success = True
        
        # Method 2: Try open source download
        elif self.download_opensource_templates():
            success = True
        
        # Method 3: Create missing templates manually
        if self.create_all_missing_templates():
            success = True
        
        final_count = len(self.template_manager.get_all_templates())
        created = final_count - initial_count
        
        print("\n" + "=" * 60)
        print("📈 EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Templates before: {initial_count}")
        print(f"Templates after:  {final_count}")
        print(f"Templates created: {created}")
        print(f"Coverage: {final_count}/52 cards ({final_count/52*100:.1f}%)")
        
        if final_count >= 52:
            print("\n🎉 SUCCESS! All 52 cards now have templates!")
            print("Your enhanced training system is ready for ACR poker recognition!")
        elif created > 0:
            print(f"\n✅ Progress made! Created {created} new templates.")
            print("You can run this script again to try other methods.")
        else:
            print("\n⚠️  No new templates created. Check the error messages above.")
            
        return success

def main():
    """Main extraction function."""
    extractor = ACRTemplateExtractor()
    extractor.run_extraction()

if __name__ == "__main__":
    main()