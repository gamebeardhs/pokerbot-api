"""Demo version of calibration tool to test functionality in Replit environment."""

import json
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalibrationDemo:
    """Demo calibration functionality using sample images."""
    
    def __init__(self):
        self.regions_info = {
            'pot_area': {'desc': 'Pot Amount Display', 'priority': 'HIGH'},
            'hero_cards': {'desc': 'Your Hole Cards', 'priority': 'HIGH'},
            'board_cards': {'desc': 'Community Cards', 'priority': 'HIGH'},
            'action_buttons': {'desc': 'Fold/Call/Raise Buttons', 'priority': 'HIGH'},
            'stakes_info': {'desc': 'Table Stakes/Blinds', 'priority': 'MEDIUM'},
            'seat_1': {'desc': 'Player Seat 1', 'priority': 'MEDIUM'},
            'seat_2': {'desc': 'Player Seat 2', 'priority': 'MEDIUM'}
        }
        
        # Sample calibration data for testing
        self.sample_regions = {
            'pot_area': (400, 200, 600, 250),
            'hero_cards': (300, 500, 500, 550),
            'board_cards': (350, 300, 650, 350),
            'action_buttons': (400, 600, 700, 650),
            'stakes_info': (50, 50, 200, 100),
            'seat_1': (100, 150, 300, 250),
            'seat_2': (700, 150, 900, 250)
        }
        
    def create_sample_poker_table(self, width=1000, height=700) -> Image.Image:
        """Create a sample poker table image for demo purposes."""
        # Create base image
        img = Image.new('RGB', (width, height), color='#0d5016')  # Poker green
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 20)
            font_medium = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw poker table elements based on our sample regions
        
        # Pot area
        x1, y1, x2, y2 = self.sample_regions['pot_area']
        draw.rectangle([x1-5, y1-5, x2+5, y2+5], fill='black', outline='white')
        draw.text((x1+10, y1+10), "Pot: $47.50", fill='white', font=font_large)
        
        # Hero cards
        x1, y1, x2, y2 = self.sample_regions['hero_cards']
        draw.rectangle([x1, y1, x1+80, y2], fill='white', outline='black')
        draw.text((x1+10, y1+10), "Ah", fill='black', font=font_medium)
        draw.rectangle([x1+90, y1, x2, y2], fill='white', outline='black')
        draw.text((x1+100, y1+10), "Ks", fill='black', font=font_medium)
        
        # Board cards
        x1, y1, x2, y2 = self.sample_regions['board_cards']
        for i, card in enumerate(['7h', '2s', '2d']):
            card_x = x1 + i * 70
            draw.rectangle([card_x, y1, card_x+60, y2], fill='white', outline='black')
            draw.text((card_x+10, y1+10), card, fill='black', font=font_medium)
        
        # Action buttons
        x1, y1, x2, y2 = self.sample_regions['action_buttons']
        buttons = ['Fold', 'Call $5.00', 'Raise']
        button_width = (x2 - x1) // 3
        for i, btn_text in enumerate(buttons):
            btn_x = x1 + i * button_width
            color = '#ff4444' if btn_text == 'Fold' else '#44ff44' if 'Call' in btn_text else '#4444ff'
            draw.rectangle([btn_x, y1, btn_x + button_width - 10, y2], fill=color, outline='white')
            draw.text((btn_x + 10, y1 + 15), btn_text, fill='white', font=font_medium)
        
        # Stakes info
        x1, y1, x2, y2 = self.sample_regions['stakes_info']
        draw.rectangle([x1, y1, x2, y2], fill='black', outline='white')
        draw.text((x1+5, y1+5), "NL Hold'em", fill='white', font=font_small)
        draw.text((x1+5, y1+25), "$0.05/$0.10", fill='white', font=font_small)
        
        # Player seats
        seats_data = [
            ('Player1', '$125.50'),
            ('Hero123', '$98.75')
        ]
        
        for i, (region_key, (player_name, stack)) in enumerate(zip(['seat_1', 'seat_2'], seats_data)):
            x1, y1, x2, y2 = self.sample_regions[region_key]
            # Player avatar/seat
            draw.ellipse([x1, y1, x1+80, y1+80], fill='#444444', outline='white')
            draw.text((x1+85, y1+10), player_name, fill='white', font=font_medium)
            draw.text((x1+85, y1+35), stack, fill='yellow', font=font_medium)
            if i == 1:  # Hero seat
                draw.text((x1+85, y1+55), "(You)", fill='lime', font=font_small)
        
        return img
    
    def test_ocr_methods(self, region_img: Image.Image) -> Dict[str, str]:
        """Test different OCR preprocessing methods."""
        results = {}
        
        try:
            # Convert to OpenCV format
            cv_img = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            # Raw OCR
            results['Raw'] = pytesseract.image_to_string(region_img).strip()
            
            # Threshold OCR
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            binary_pil = Image.fromarray(binary)
            results['Threshold'] = pytesseract.image_to_string(binary_pil).strip()
            
            # Inverted threshold (for dark text on light background)
            _, inv_binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            inv_binary_pil = Image.fromarray(inv_binary)
            results['Inverted'] = pytesseract.image_to_string(inv_binary_pil).strip()
            
            # Poker-optimized OCR
            poker_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,() '
            results['Poker Optimized'] = pytesseract.image_to_string(binary_pil, config=poker_config).strip()
            
        except Exception as e:
            results['Error'] = str(e)
        
        return results
    
    def test_region_extraction(self, img: Image.Image, region_name: str, coords: Tuple[int, int, int, int]):
        """Test extracting and processing a specific region."""
        print(f"\\n{'='*50}")
        print(f"Testing Region: {region_name}")
        print(f"Description: {self.regions_info[region_name]['desc']}")
        print(f"Priority: {self.regions_info[region_name]['priority']}")
        print(f"Coordinates: {coords}")
        print(f"{'='*50}")
        
        try:
            # Extract region
            x1, y1, x2, y2 = coords
            region_img = img.crop((x1, y1, x2, y2))
            
            # Save region for inspection
            region_filename = f"demo_region_{region_name}.png"
            region_img.save(region_filename)
            print(f"✅ Region image saved: {region_filename}")
            
            # Test OCR
            ocr_results = self.test_ocr_methods(region_img)
            
            print("\\n📖 OCR Results:")
            for method, text in ocr_results.items():
                status = "✅" if text and len(text) > 0 else "❌"
                print(f"  {status} {method:15}: '{text}'")
            
            # Determine best result
            best_result = self.get_best_ocr_result(ocr_results, region_name)
            print(f"\\n🎯 Best Result: '{best_result}'")
            
            return {
                'region': region_name,
                'coordinates': coords,
                'ocr_results': ocr_results,
                'best_result': best_result,
                'image_saved': region_filename
            }
            
        except Exception as e:
            print(f"❌ Error processing region: {e}")
            return None
    
    def get_best_ocr_result(self, ocr_results: Dict[str, str], region_name: str) -> str:
        """Determine the best OCR result for a region."""
        # Priority order for different methods
        method_priority = ['Poker Optimized', 'Threshold', 'Inverted', 'Raw']
        
        for method in method_priority:
            if method in ocr_results and ocr_results[method].strip():
                return ocr_results[method].strip()
        
        return "No readable text found"
    
    def create_calibration_overlay(self, img: Image.Image, regions: Dict[str, Tuple[int, int, int, int]]) -> Image.Image:
        """Create an overlay image showing all calibrated regions."""
        overlay_img = img.copy()
        draw = ImageDraw.Draw(overlay_img)
        
        colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan', 'orange']
        
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        for i, (region_name, coords) in enumerate(regions.items()):
            color = colors[i % len(colors)]
            x1, y1, x2, y2 = coords
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Draw label with background
            label = f"{region_name} ({self.regions_info[region_name]['priority']})"
            draw.rectangle([x1, y1 - 20, x1 + len(label) * 8, y1], fill=color)
            draw.text((x1 + 2, y1 - 18), label, fill='white', font=font)
        
        return overlay_img
    
    def run_demo(self):
        """Run the complete calibration demo."""
        print("🎮 Poker Scraper Calibration Demo")
        print("=" * 60)
        print("This demo tests the calibration functionality using a sample poker table.")
        print()
        
        # Create sample poker table
        print("🎨 Creating sample poker table image...")
        sample_img = self.create_sample_poker_table()
        sample_img.save("demo_poker_table.png")
        print("✅ Sample table saved: demo_poker_table.png")
        
        # Test each region
        print("\\n🔍 Testing region extraction and OCR...")
        results = []
        
        for region_name, coords in self.sample_regions.items():
            result = self.test_region_extraction(sample_img, region_name, coords)
            if result:
                results.append(result)
        
        # Create overlay image
        print("\\n🖼️  Creating calibration overlay...")
        overlay_img = self.create_calibration_overlay(sample_img, self.sample_regions)
        overlay_img.save("demo_calibration_overlay.png")
        print("✅ Overlay saved: demo_calibration_overlay.png")
        
        # Save calibration data
        print("\\n💾 Saving demo calibration data...")
        with open("demo_calibration.json", "w") as f:
            json.dump(self.sample_regions, f, indent=2)
        print("✅ Calibration data saved: demo_calibration.json")
        
        # Summary report
        print("\\n📊 CALIBRATION DEMO SUMMARY")
        print("=" * 60)
        
        successful_regions = 0
        for result in results:
            region_name = result['region']
            best_result = result['best_result']
            priority = self.regions_info[region_name]['priority']
            
            if best_result != "No readable text found":
                status = "✅ SUCCESS"
                successful_regions += 1
            else:
                status = "❌ NEEDS WORK"
            
            print(f"{status} {region_name:15} ({priority:6}): '{best_result}'")
        
        print(f"\\n🎯 Overall Success Rate: {successful_regions}/{len(results)} regions ({(successful_regions/len(results)*100):.1f}%)")
        
        print("\\n📁 Files Created:")
        print("- demo_poker_table.png (sample table)")
        print("- demo_calibration_overlay.png (visual verification)")
        print("- demo_calibration.json (coordinates)")
        print("- demo_region_*.png (individual regions)")
        
        print("\\n🚀 Next Steps:")
        if successful_regions >= len(results) * 0.8:  # 80% success rate
            print("✅ Demo successful! The calibration system works correctly.")
            print("   You can now run the full interactive calibration tool.")
        else:
            print("⚠️  Some regions need adjustment. This is normal - the demo uses")
            print("   synthetic data. Real calibration will work better with actual ACR tables.")
        
        return results


def main():
    """Run the calibration demo."""
    try:
        demo = CalibrationDemo()
        results = demo.run_demo()
        
        print("\\n" + "=" * 60)
        print("Demo complete! Check the generated images and files.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()