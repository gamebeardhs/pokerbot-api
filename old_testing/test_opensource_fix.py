#!/usr/bin/env python3
"""
Test the fixed ColorNormalizer with RGBA images from open source templates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import zipfile
from pathlib import Path
from PIL import Image
from app.training.neural_trainer import TemplateManager, ColorNormalizer
import tempfile
import shutil

def test_opensource_templates():
    """Test downloading and processing open source templates with the fix."""
    print("🧪 Testing Open Source Template Fix")
    print("=" * 40)
    
    tm = TemplateManager()
    
    try:
        # Download the ZIP file from GitHub
        url = "https://github.com/hayeah/playing-cards-assets/archive/master.zip"
        print("📥 Downloading playing-cards-assets...")
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "cards.zip")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("📦 Extracting templates...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find PNG files in extracted content
            png_dir = Path(temp_dir) / "playing-cards-assets-master" / "png"
            if png_dir.exists():
                png_files = list(png_dir.glob("*.png"))[:5]  # Test first 5
                print(f"🃏 Testing {len(png_files)} sample images...")
                
                success_count = 0
                for png_file in png_files:
                    try:
                        print(f"   Testing: {png_file.name}")
                        
                        # Load image
                        image = Image.open(png_file)
                        print(f"     Original format: {image.mode} {image.size}")
                        
                        # Test color normalization
                        normalized = ColorNormalizer.normalize_card_region(image)
                        print(f"     Normalized: {normalized.mode} {normalized.size}")
                        
                        # Test template creation
                        card_name = f"test_{success_count}"
                        if tm.add_template(card_name, normalized, 0.8):
                            print(f"     ✅ Template created successfully")
                            success_count += 1
                        else:
                            print(f"     ❌ Template creation failed")
                            
                    except Exception as e:
                        print(f"     ❌ Error: {e}")
                        
                print(f"\n📊 Results: {success_count}/{len(png_files)} templates created successfully")
                
                if success_count > 0:
                    print("✅ Fix successful! Open source templates now work.")
                else:
                    print("❌ Fix incomplete. Still having issues.")
                    
                # Cleanup test templates
                for i in range(success_count):
                    tm.remove_template(f"test_{i}")
                    
            else:
                print("❌ Could not find PNG directory")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_opensource_fix()