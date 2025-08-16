"""Debug and calibration tools for poker scrapers."""

import cv2
import numpy as np
import pytesseract
import json
import asyncio
from PIL import Image, ImageGrab, ImageDraw, ImageFont
from typing import Dict, Tuple, List, Optional, Any
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)


class ACRCalibrationTool:
    """Tool to help calibrate ACR scraper screen regions."""
    
    def __init__(self):
        self.screenshot = None
        self.regions = {}
        
    def capture_full_screen(self) -> Image.Image:
        """Capture full screen for region identification."""
        screenshot = ImageGrab.grab()
        self.screenshot = screenshot
        logger.info(f"Captured screenshot: {screenshot.size}")
        return screenshot
    
    def save_screenshot_with_regions(self, regions: Dict[str, Tuple[int, int, int, int]], 
                                   output_path: str = "acr_calibration.png"):
        """Save screenshot with regions overlaid for visual verification."""
        if not self.screenshot:
            self.capture_full_screen()
        
        # Create a copy to draw on
        img_with_regions = self.screenshot.copy()
        draw = ImageDraw.Draw(img_with_regions)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Colors for different regions
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta']
        
        for i, (region_name, (x1, y1, x2, y2)) in enumerate(regions.items()):
            color = colors[i % len(colors)]
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # Add label
            draw.text((x1, y1 - 20), region_name, fill=color, font=font)
        
        img_with_regions.save(output_path)
        logger.info(f"Saved calibration image: {output_path}")
        return output_path
    
    def test_ocr_region(self, region: Tuple[int, int, int, int], 
                       name: str = "test_region") -> Dict[str, Any]:
        """Test OCR on a specific region."""
        if not self.screenshot:
            self.capture_full_screen()
        
        x1, y1, x2, y2 = region
        region_img = self.screenshot.crop((x1, y1, x2, y2))
        
        # Convert to OpenCV format for preprocessing
        cv_img = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # Try different preprocessing techniques
        results = {}
        
        # Raw OCR
        raw_text = pytesseract.image_to_string(region_img)
        results['raw'] = raw_text.strip()
        
        # Threshold OCR
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        binary_pil = Image.fromarray(binary)
        threshold_text = pytesseract.image_to_string(binary_pil)
        results['threshold'] = threshold_text.strip()
        
        # Adaptive threshold OCR
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        adaptive_pil = Image.fromarray(adaptive)
        adaptive_text = pytesseract.image_to_string(adaptive_pil)
        results['adaptive'] = adaptive_text.strip()
        
        # Poker-optimized OCR
        poker_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
        poker_text = pytesseract.image_to_string(binary_pil, config=poker_config)
        results['poker_optimized'] = poker_text.strip()
        
        # Save region image for manual inspection
        region_path = f"region_{name}_{x1}_{y1}.png"
        region_img.save(region_path)
        
        return {
            'region': region,
            'region_name': name,
            'image_saved': region_path,
            'ocr_results': results
        }
    
    def interactive_region_selector(self):
        """Interactive tool to help select screen regions."""
        print("ACR Region Calibration Tool")
        print("1. First, capture a screenshot of ACR table")
        print("2. Manually identify coordinates for each UI element")
        print("3. Test OCR on each region")
        
        if not self.screenshot:
            self.capture_full_screen()
        
        # Standard ACR regions to calibrate
        regions_to_calibrate = [
            'pot_area',
            'hero_cards', 
            'board_cards',
            'action_buttons',
            'stakes_info',
            'seat_1', 'seat_2', 'seat_3', 'seat_4',
            'seat_5', 'seat_6', 'seat_7', 'seat_8'
        ]
        
        calibrated_regions = {}
        
        print(f"\nScreenshot size: {self.screenshot.size}")
        print("For each region, enter coordinates as: x1,y1,x2,y2")
        print("Or press Enter to skip")
        
        for region_name in regions_to_calibrate:
            coords_input = input(f"\nEnter coordinates for {region_name}: ").strip()
            
            if coords_input:
                try:
                    x1, y1, x2, y2 = map(int, coords_input.split(','))
                    calibrated_regions[region_name] = (x1, y1, x2, y2)
                    
                    # Test OCR immediately
                    ocr_result = self.test_ocr_region((x1, y1, x2, y2), region_name)
                    print(f"OCR Results for {region_name}:")
                    for method, text in ocr_result['ocr_results'].items():
                        print(f"  {method}: '{text}'")
                    
                except ValueError:
                    print(f"Invalid format for {region_name}, skipping...")
        
        # Save calibrated regions
        with open('acr_calibrated_regions.json', 'w') as f:
            json.dump(calibrated_regions, f, indent=2)
        
        # Create visual verification image
        if calibrated_regions:
            self.save_screenshot_with_regions(calibrated_regions, "acr_regions_overlay.png")
            print(f"\nCalibrated {len(calibrated_regions)} regions")
            print("Files created:")
            print("- acr_calibrated_regions.json (region coordinates)")
            print("- acr_regions_overlay.png (visual verification)")
        
        return calibrated_regions


class ClubWPTCalibrationTool:
    """Tool to help calibrate ClubWPT scraper CSS selectors."""
    
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def setup(self):
        """Setup browser for DOM inspection."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)  # Visible for debugging
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
    async def navigate_to_table(self, url: str = "https://clubwptgold.com"):
        """Navigate to ClubWPT and wait for manual login."""
        if not self.page:
            await self.setup()
            
        await self.page.goto(url)
        print("Please manually log in and navigate to a poker table...")
        print("Press Enter when you're at a poker table and ready to calibrate...")
        input()
        
    async def find_elements_by_text(self, search_text: str) -> List[Dict[str, Any]]:
        """Find elements containing specific text."""
        if not self.page:
            return []
            
        # Search for elements containing the text
        elements = await self.page.query_selector_all(f"*:has-text('{search_text}')")
        
        results = []
        for i, element in enumerate(elements[:10]):  # Limit to first 10 matches
            try:
                tag_name = await element.evaluate("el => el.tagName")
                classes = await element.get_attribute("class") or ""
                text_content = await element.text_content()
                
                # Get CSS selector path
                selector = await element.evaluate("""
                    el => {
                        let path = [];
                        while (el.parentElement) {
                            let selector = el.tagName.toLowerCase();
                            if (el.id) {
                                selector += '#' + el.id;
                                path.unshift(selector);
                                break;
                            } else if (el.className) {
                                selector += '.' + el.className.split(' ').join('.');
                            }
                            path.unshift(selector);
                            el = el.parentElement;
                        }
                        return path.join(' > ');
                    }
                """)
                
                results.append({
                    'index': i,
                    'tag': tag_name,
                    'classes': classes,
                    'text': text_content[:100] + '...' if len(text_content) > 100 else text_content,
                    'selector': selector
                })
            except:
                continue
                
        return results
    
    async def test_selector(self, selector: str) -> Dict[str, Any]:
        """Test if a CSS selector works and what it returns."""
        if not self.page:
            return {'error': 'Page not initialized'}
            
        try:
            elements = await self.page.query_selector_all(selector)
            
            results = []
            for i, element in enumerate(elements[:5]):  # Test first 5 matches
                text = await element.text_content()
                tag = await element.evaluate("el => el.tagName")
                classes = await element.get_attribute("class")
                
                results.append({
                    'index': i,
                    'tag': tag,
                    'classes': classes,
                    'text': text[:100] + '...' if text and len(text) > 100 else text
                })
            
            return {
                'selector': selector,
                'found_count': len(elements),
                'elements': results
            }
            
        except Exception as e:
            return {'selector': selector, 'error': str(e)}
    
    async def interactive_selector_finder(self):
        """Interactive tool to find and test CSS selectors."""
        print("ClubWPT Selector Calibration Tool")
        print("Make sure you're logged in and at a poker table")
        
        if not self.page:
            await self.navigate_to_table()
        
        # Elements we need to find
        elements_to_find = [
            ('pot_size', 'pot amount'),
            ('hero_cards', 'your hole cards'),
            ('board_cards', 'community cards'),
            ('player_seats', 'player seats'),
            ('player_names', 'player names'),
            ('stack_amounts', 'chip stacks'),
            ('action_buttons', 'fold/call/raise buttons'),
            ('dealer_button', 'dealer button'),
            ('betting_amounts', 'current bets')
        ]
        
        calibrated_selectors = {}
        
        for element_type, description in elements_to_find:
            print(f"\n=== Finding {element_type} ({description}) ===")
            
            # Option 1: Search by text
            search_text = input(f"Enter text to search for {description} (or press Enter to skip): ").strip()
            if search_text:
                elements = await self.find_elements_by_text(search_text)
                if elements:
                    print("Found elements:")
                    for elem in elements:
                        print(f"  {elem['index']}: {elem['tag']}.{elem['classes']} - '{elem['text']}'")
                        print(f"    Selector: {elem['selector']}")
                    
                    choice = input("Enter index to use, or 'c' for custom selector: ").strip()
                    if choice.isdigit() and int(choice) < len(elements):
                        calibrated_selectors[element_type] = elements[int(choice)]['selector']
                        continue
            
            # Option 2: Custom selector
            custom_selector = input(f"Enter custom CSS selector for {description}: ").strip()
            if custom_selector:
                test_result = await self.test_selector(custom_selector)
                print(f"Selector test result:")
                print(f"  Found {test_result.get('found_count', 0)} elements")
                if 'elements' in test_result:
                    for elem in test_result['elements']:
                        print(f"    {elem['tag']}: '{elem['text']}'")
                
                if input("Use this selector? (y/n): ").lower() == 'y':
                    calibrated_selectors[element_type] = custom_selector
        
        # Save calibrated selectors
        with open('clubwpt_calibrated_selectors.json', 'w') as f:
            json.dump(calibrated_selectors, f, indent=2)
        
        print(f"\nCalibrated {len(calibrated_selectors)} selectors")
        print("Saved to: clubwpt_calibrated_selectors.json")
        
        return calibrated_selectors
    
    async def test_all_selectors(self, selectors: Dict[str, str]):
        """Test all calibrated selectors to verify they work."""
        print("\\nTesting all selectors...")
        
        for element_type, selector in selectors.items():
            print(f"\\nTesting {element_type}: {selector}")
            result = await self.test_selector(selector)
            
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                print(f"  ✅ Found {result['found_count']} elements")
                if result.get('elements'):
                    for elem in result['elements'][:2]:  # Show first 2
                        print(f"    - {elem['text']}")
    
    async def cleanup(self):
        """Cleanup browser resources."""
        if self.browser:
            await self.browser.close()


async def main():
    """Main calibration interface."""
    print("Poker Scraper Calibration Tool")
    print("1. ACR (screen capture) calibration")
    print("2. ClubWPT (browser) calibration") 
    print("3. Test existing calibrations")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == '1':
        acr_tool = ACRCalibrationTool()
        regions = acr_tool.interactive_region_selector()
        print(f"ACR calibration complete! Calibrated {len(regions)} regions.")
        
    elif choice == '2':
        clubwpt_tool = ClubWPTCalibrationTool()
        try:
            await clubwpt_tool.setup()
            await clubwpt_tool.navigate_to_table()
            selectors = await clubwpt_tool.interactive_selector_finder()
            await clubwpt_tool.test_all_selectors(selectors)
            print(f"ClubWPT calibration complete! Calibrated {len(selectors)} selectors.")
        finally:
            await clubwpt_tool.cleanup()
            
    elif choice == '3':
        # Test existing calibrations
        try:
            with open('acr_calibrated_regions.json', 'r') as f:
                acr_regions = json.load(f)
            print(f"Found ACR calibration with {len(acr_regions)} regions")
            
            acr_tool = ACRCalibrationTool()
            acr_tool.capture_full_screen()
            
            for region_name, coords in acr_regions.items():
                result = acr_tool.test_ocr_region(coords, region_name)
                print(f"{region_name}: {result['ocr_results']['poker_optimized']}")
                
        except FileNotFoundError:
            print("No ACR calibration found")
        
        try:
            with open('clubwpt_calibrated_selectors.json', 'r') as f:
                clubwpt_selectors = json.load(f)
            print(f"Found ClubWPT calibration with {len(clubwpt_selectors)} selectors")
            
            clubwpt_tool = ClubWPTCalibrationTool()
            await clubwpt_tool.setup()
            await clubwpt_tool.navigate_to_table()
            await clubwpt_tool.test_all_selectors(clubwpt_selectors)
            await clubwpt_tool.cleanup()
            
        except FileNotFoundError:
            print("No ClubWPT calibration found")


if __name__ == "__main__":
    asyncio.run(main())