#!/usr/bin/env python3
"""
Extract ACR-specific card templates from screenshots.
This creates templates that perfectly match ACR's card designs.
"""

import sys
import os
from pathlib import Path
from PIL import Image, ImageGrab
import json
from datetime import datetime
import cv2
import numpy as np

def take_acr_screenshot():
    """Take a screenshot for ACR template extraction."""
    print("📸 ACR Template Screenshot Guide")
    print("=" * 50)
    print()
    print("Steps to create perfect ACR templates:")
    print()
    print("1. 🃏 Open ACR poker client")
    print("2. 🎮 Join any poker table (play money is fine)")
    print("3. 🔍 Make sure cards are clearly visible:")
    print("   - No overlapping cards")
    print("   - Good lighting/contrast")
    print("   - Cards not too small")
    print()
    print("4. ⏱️  Get ready to take screenshot...")
    print("   - Position cards you want to capture")
    print("   - Different ranks and suits if possible")
    print()
    
    input("Press Enter when ACR table is ready...")
    
    print("📸 Taking screenshot in 3 seconds...")
    print("3...")
    import time
    time.sleep(1)
    print("2...")
    time.sleep(1) 
    print("1...")
    time.sleep(1)
    print("📸 Screenshot taken!")
    
    # Take screenshot
    screenshot = ImageGrab.grab()
    screenshot_path = "acr_template_screenshot.png"
    screenshot.save(screenshot_path)
    
    print(f"✅ Screenshot saved as: {screenshot_path}")
    print()
    return screenshot_path

def manual_card_extraction(screenshot_path):
    """Manual extraction of cards from screenshot."""
    print("🎯 Manual Card Extraction")
    print("=" * 50)
    print()
    print("Now I'll help you extract individual cards from the screenshot.")
    print("You'll click on cards to extract them as templates.")
    print()
    
    import cv2
    
    # Load screenshot
    image = cv2.imread(screenshot_path)
    if image is None:
        print(f"❌ Could not load screenshot: {screenshot_path}")
        return False
    
    print("Instructions:")
    print("- Click on a card to extract it")
    print("- Type the card name (e.g., 'As', 'Kh', '2s')")
    print("- Press 'q' to quit")
    print("- Press 's' to skip current selection")
    print()
    
    # Create window
    cv2.namedWindow('ACR Screenshot - Click on cards', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('ACR Screenshot - Click on cards', 1200, 800)
    
    extracted_count = 0
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal extracted_count
        
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f"Clicked at ({x}, {y})")
            
            # Ask for card name
            card_name = input("Enter card name (e.g., 'As', 'Kh', '2s') or 's' to skip: ").strip()
            
            if card_name.lower() == 's':
                return
            
            if len(card_name) != 2:
                print("❌ Invalid card name. Use format like 'As', 'Kh', '2s'")
                return
            
            # Extract card region (adjust size as needed)
            card_width, card_height = 60, 85  # Typical card size
            x1 = max(0, x - card_width // 2)
            y1 = max(0, y - card_height // 2)  
            x2 = min(image.shape[1], x1 + card_width)
            y2 = min(image.shape[0], y1 + card_height)
            
            # Extract card region
            card_region = image[y1:y2, x1:x2]
            
            # Convert to PIL Image
            card_pil = Image.fromarray(cv2.cvtColor(card_region, cv2.COLOR_BGR2RGB))
            
            # Resize to standard template size
            card_pil = card_pil.resize((57, 82), Image.Resampling.LANCZOS)
            
            # Save template
            template_dir = Path("training_data/templates")
            template_dir.mkdir(parents=True, exist_ok=True)
            
            template_path = template_dir / f"{card_name}.png"
            card_pil.save(template_path)
            
            # Save metadata
            metadata = {
                "card": card_name,
                "created": datetime.now().isoformat(),
                "source": "acr_screenshot_extraction",
                "screenshot": screenshot_path,
                "coordinates": [x1, y1, x2, y2],
                "click_point": [x, y]
            }
            
            json_path = template_dir / f"{card_name}.json"
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            extracted_count += 1
            print(f"✅ Extracted template: {card_name} (Total: {extracted_count})")
            
            # Draw rectangle on image to show extraction
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, card_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('ACR Screenshot - Click on cards', image)
    
    cv2.setMouseCallback('ACR Screenshot - Click on cards', mouse_callback)
    cv2.imshow('ACR Screenshot - Click on cards', image)
    
    print("Click on cards in the image window...")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()
    
    print(f"\n🎉 Extracted {extracted_count} ACR card templates")
    print("These templates will work perfectly with ACR's card designs!")
    
    return extracted_count > 0

def main():
    """Main ACR template creation process."""
    print("🃏 ACR Card Template Creator")
    print("=" * 50)
    print()
    print("This tool helps you create perfect templates for ACR card recognition.")
    print("We'll take a screenshot of ACR and extract individual cards.")
    print()
    
    choice = input("Do you want to:\n1. Take new screenshot\n2. Use existing screenshot\nChoose (1/2): ").strip()
    
    if choice == '1':
        screenshot_path = take_acr_screenshot()
    elif choice == '2':
        screenshot_path = input("Enter screenshot path: ").strip()
        if not os.path.exists(screenshot_path):
            print(f"❌ Screenshot not found: {screenshot_path}")
            return False
    else:
        print("❌ Invalid choice")
        return False
    
    # Extract cards from screenshot
    success = manual_card_extraction(screenshot_path)
    
    if success:
        print()
        print("🌐 Next steps:")
        print("1. Visit http://localhost:5000/training-interface")
        print("2. View your new ACR-specific templates")
        print("3. Test recognition accuracy")
        print("4. Extract more cards if needed")
    
    return success

if __name__ == "__main__":
    main()