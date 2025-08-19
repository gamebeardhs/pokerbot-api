"""ACR (Americas Cardroom) screen capture + OCR scraper."""

import cv2
import numpy as np
import pytesseract
import re
import json
import os
from PIL import Image, ImageGrab
from typing import Optional, Dict, Any, List, Tuple
from app.scraper.base_scraper import BaseScraper
from app.scraper.card_recognition import CardRecognition

class ACRScraper(BaseScraper):
    """Screen capture + OCR scraper for ACR desktop client."""
    
    def __init__(self, calibration_file: Optional[str] = None):
        """Initialize ACR scraper."""
        super().__init__()
        self.window_bounds = None
        self.card_regions = {}
        self.ui_regions = {}
        self.calibration_file = calibration_file or 'acr_calibration_results.json'
        self.calibrated = False
        self.card_recognizer = CardRecognition()
        self.setup_regions()
        
    def setup_regions(self):
        """Setup screen regions using dynamic detection instead of static calibration."""
        # FIXED: Use dynamic window detection instead of static coordinates
        from app.scraper.intelligent_calibrator import IntelligentACRCalibrator
        
        self.dynamic_calibrator = IntelligentACRCalibrator()
        self.use_dynamic_detection = True
        self.calibrated = True  # Dynamic detection is always "calibrated"
        self.logger.info("Using dynamic window detection - adapts to any ACR window position/size")
    
    def load_calibration(self) -> bool:
        """Load calibration coordinates from JSON file."""
        try:
            if os.path.exists(self.calibration_file):
                with open(self.calibration_file, 'r') as f:
                    calibration_data = json.load(f)
                
                # Convert calibration data to UI regions
                self.ui_regions = {}
                for region_name, coords in calibration_data.items():
                    if isinstance(coords, (list, tuple)) and len(coords) == 4:
                        self.ui_regions[region_name] = tuple(coords)
                    elif isinstance(coords, dict) and 'coordinates' in coords:
                        # Handle format from calibration tool
                        self.ui_regions[region_name] = tuple(coords['coordinates'])
                
                self.logger.info(f"Loaded {len(self.ui_regions)} calibrated regions")
                return True
        except Exception as e:
            self.logger.error(f"Failed to load calibration: {e}")
        return False
    
    def _setup_default_regions(self):
        """Setup default uncalibrated regions (fallback only)."""
        self.ui_regions = {
            'pot_area': (850, 300, 1070, 350),
            'hero_cards': (860, 600, 1060, 660),
            'board_cards': (760, 380, 1160, 440),
            'action_buttons': (800, 650, 1120, 720),
            'stakes_info': (50, 50, 250, 100),
            'seat_1_name': (400, 200, 550, 220),
            'seat_1_stack': (400, 240, 550, 280),
            'seat_2_name': (600, 150, 750, 170),
            'seat_2_stack': (600, 190, 750, 230),
            'seat_3_name': (800, 150, 950, 170),
            'seat_3_stack': (800, 190, 950, 230),
            'seat_4_name': (1000, 200, 1150, 220),
            'seat_4_stack': (1000, 240, 1150, 280),
            'seat_5_name': (1000, 500, 1150, 520),
            'seat_5_stack': (1000, 540, 1150, 580),
            'seat_6_name': (800, 550, 950, 570),
            'seat_6_stack': (800, 590, 950, 630),
        }
    
    def setup(self) -> bool:
        """Setup ACR scraper (check calibration and OCR)."""
        try:
            # Check if calibrated
            if not self.calibrated:
                self.logger.warning("ACR scraper not calibrated - run calibration tool first")
                # Still return True to allow testing with defaults
            
            # Test OCR availability
            try:
                pytesseract.get_tesseract_version()
                self.logger.info("OCR engine ready")
            except Exception as e:
                self.logger.error(f"OCR not available: {e}")
                return False
            
            self.logger.info(f"ACR scraper initialized - calibrated: {self.calibrated}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup ACR scraper: {e}")
            return False
    
    def is_table_active(self) -> bool:
        """Check if ACR table is active by looking for poker elements."""
        try:
            # Capture pot area and look for poker indicators
            pot_image = self._capture_region(self.ui_regions['pot_area'])
            if pot_image is None:
                return False
                
            # Convert to grayscale and look for text
            gray = cv2.cvtColor(np.array(pot_image), cv2.COLOR_RGB2GRAY)
            text = pytesseract.image_to_string(gray).strip()
            
            # Look for poker-related text
            poker_indicators = ['pot', 'bet', 'call', 'fold', 'raise', '$', 'chips']
            return any(indicator in text.lower() for indicator in poker_indicators)
            
        except:
            return False
    
    async def scrape_table_state(self) -> Optional[Dict[str, Any]]:
        """Scrape enhanced table state using optimized screen capture and OCR."""
        if not self.is_table_active():
            return None
            
        try:
            # Basic table data
            table_data = {
                'table_id': 'acr_table_1',
                'street': self._extract_street(),
                'pot': self._extract_pot_size(),
                'stakes': self._extract_stakes(),
                'hero_hole': self._extract_hero_cards(),
                'board': self._extract_board_cards(),
                'to_call': self._extract_to_call(),
                'bet_min': self._extract_min_bet(),
                'max_seats': 8  # ACR typically uses 8-max tables
            }
            
            # Enhanced seat data with positions
            seats = self._extract_enhanced_seat_info()
            table_data['seats'] = seats
            
            # Find hero seat and button position
            table_data['hero_seat'] = self._find_hero_seat(seats)
            table_data['button_seat'] = self._detect_button_position()
            
            # Determine positions for all players
            active_seats = []
            if table_data['button_seat'] and seats:
                active_seats = [s['seat'] for s in seats if s.get('in_hand')]
                num_players = len(active_seats)
                positions = self.determine_positions(num_players, table_data['button_seat'])
                
                # Add positions to seats
                for seat in seats:
                    if seat['seat'] in positions:
                        seat['position'] = positions[seat['seat']]
                
                # Set SB/BB seats
                for seat_num, pos in positions.items():
                    if pos == 'SB':
                        table_data['sb_seat'] = seat_num
                    elif pos == 'BB':
                        table_data['bb_seat'] = seat_num
            
            # Extract betting history and context
            action_history = self._extract_action_history()
            table_data['betting_history'] = action_history
            
            # Determine current action context
            current_street = table_data['street']
            action_type, num_raises = self.detect_action_type(action_history, current_street)
            table_data['current_action_type'] = action_type
            table_data['num_raises_this_street'] = num_raises
            table_data['current_aggressor_seat'] = self.find_current_aggressor(action_history, current_street)
            
            # Calculate enhanced metrics
            if table_data['hero_seat']:
                table_data['effective_stacks'] = self.calculate_effective_stacks(seats, table_data['hero_seat'])
                
                # Calculate SPR
                hero_stack = next((s['stack'] for s in seats if s['seat'] == table_data['hero_seat']), 0)
                table_data['spr'] = hero_stack / max(table_data['pot'], 1) if hero_stack > 0 else 0
                
                # Determine position vs aggressor
                if table_data['current_aggressor_seat'] and table_data['button_seat']:
                    table_data['hero_position_vs_aggressor'] = self._calculate_position_vs_aggressor(
                        table_data['hero_seat'], 
                        table_data['current_aggressor_seat'],
                        table_data['button_seat'],
                        len(active_seats) if 'active_seats' in locals() else 6,
                        current_street
                    )
            
            # Add rake information (ACR standard rates)
            table_data['rake_cap'] = 5.0
            table_data['rake_percentage'] = 5.0
            
            # Validate minimum data
            if not table_data.get('stakes'):
                return None
                
            self.logger.debug(f"Scraped enhanced ACR table state: {table_data}")
            return table_data
            
        except Exception as e:
            self.logger.error(f"Failed to scrape ACR table: {e}")
            return None
    
    def _capture_region(self, region: Tuple[int, int, int, int]) -> Optional[Image.Image]:
        """Capture a specific screen region with dynamic window detection."""
        try:
            # FIXED: Use dynamic detection if available
            if hasattr(self, 'use_dynamic_detection') and self.use_dynamic_detection:
                # Get current window bounds dynamically
                screenshot = self.dynamic_calibrator.capture_screen()
                if screenshot is not None:
                    detected, table_info = self.dynamic_calibrator.detect_acr_table(screenshot)
                    if detected and 'features' in table_info:
                        # Convert dynamic regions to coordinates
                        return self._extract_dynamic_region(screenshot, region, table_info['features'])
            
            # Fallback to static coordinates
            x1, y1, x2, y2 = region
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            return screenshot
        except:
            return None
    
    def _extract_dynamic_region(self, screenshot, region_tuple, features):
        """Extract region using dynamic detection features."""
        try:
            # Map static region names to dynamic features
            h, w = screenshot.shape[:2] if len(screenshot.shape) == 3 else screenshot.shape[:2]
            
            # Create dynamic pot area (center-top area)
            pot_region = screenshot[h//3:h//2, w//3:2*w//3]
            
            # Convert numpy array to PIL Image
            from PIL import Image
            if len(pot_region.shape) == 3:
                return Image.fromarray(cv2.cvtColor(pot_region, cv2.COLOR_BGR2RGB))
            else:
                return Image.fromarray(pot_region)
        except:
            return None
    
    def _extract_text_from_region(self, region: Tuple[int, int, int, int], region_name: str = '') -> str:
        """Extract text from screen region using OCR with region-specific optimization."""
        try:
            image = self._capture_region(region)
            if image is None:
                return ""
                
            # Save region image for debugging
            if region_name:
                image.save(f"debug_region_{region_name}.png")
                
            # Preprocess image for better OCR
            gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            
            # Multiple OCR attempts with different preprocessing
            results = self._try_multiple_ocr_methods(gray, region_name)
            
            # Return best result
            best_result = ""
            for method, text in results.items():
                if text and len(text.strip()) > len(best_result):
                    best_result = text.strip()
                    
            return best_result
            
        except Exception as e:
            self.logger.debug(f"OCR failed for region {region_name}: {e}")
            return ""
    
    def _try_multiple_ocr_methods(self, gray_image, region_name: str) -> Dict[str, str]:
        """Try multiple OCR preprocessing methods for better results."""
        results = {}
        
        try:
            # Convert back to PIL for OCR
            pil_gray = Image.fromarray(gray_image)
            
            # Method 1: Binary threshold
            _, binary = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
            binary_pil = Image.fromarray(binary)
            
            # Method 2: Inverted binary (for dark text on light background)
            _, inv_binary = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY_INV)
            inv_binary_pil = Image.fromarray(inv_binary)
            
            # Different configs for different region types
            if 'cards' in region_name or 'card' in region_name:
                # Card-specific OCR
                card_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=23456789TJQKAHSCDhscd '
                results['Card-Optimized'] = pytesseract.image_to_string(binary_pil, config=card_config)
            elif 'pot' in region_name or 'stack' in region_name or 'bet' in region_name:
                # Money amount OCR
                money_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789$.,'
                results['Money'] = pytesseract.image_to_string(binary_pil, config=money_config)
            elif 'name' in region_name:
                # Player name OCR
                name_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-'
                results['Name'] = pytesseract.image_to_string(binary_pil, config=name_config)
            else:
                # General poker OCR
                poker_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
                results['General'] = pytesseract.image_to_string(binary_pil, config=poker_config)
            
            # Also try basic OCR
            results['Basic'] = pytesseract.image_to_string(binary_pil)
            
        except Exception as e:
            results['Error'] = f"OCR failed: {e}"
            
        return results
    
    def _extract_street(self) -> str:
        """Determine current street from board cards."""
        board_cards = self._extract_board_cards()
        if len(board_cards) == 0:
            return "PREFLOP"
        elif len(board_cards) == 3:
            return "FLOP"
        elif len(board_cards) == 4:
            return "TURN"
        elif len(board_cards) == 5:
            return "RIVER"
        return "PREFLOP"
    
    def _extract_pot_size(self) -> float:
        """Extract pot size from pot area."""
        if 'pot_area' not in self.ui_regions:
            return 0.0
            
        text = self._extract_text_from_region(self.ui_regions['pot_area'], 'pot_area')
        amount = self._extract_money_amount(text)
        return amount if amount is not None else 0.0
    
    def _extract_stakes(self) -> Dict[str, Any]:
        """Extract stakes from table info area."""
        text = self._extract_text_from_region(self.ui_regions['stakes_info'])
        
        # Look for stakes format like "$0.01/$0.02" or "NL25"
        stakes_patterns = [
            r'\$?([\d.]+)[/\-]\$?([\d.]+)',  # $0.01/$0.02
            r'NL(\d+)',  # NL25 (where 25 = 25c = $0.25 max buy-in)
        ]
        
        for pattern in stakes_patterns:
            match = re.search(pattern, text)
            if match:
                if 'NL' in pattern:
                    # Convert NL format (NL25 = $0.10/$0.25)
                    nl_value = int(match.group(1))
                    bb = nl_value / 100  # NL25 = $0.25 BB
                    sb = bb / 2
                else:
                    sb = float(match.group(1))
                    bb = float(match.group(2))
                
                return {"sb": sb, "bb": bb, "currency": "USD"}
        
        # Default stakes if not detected
        return {"sb": 0.01, "bb": 0.02, "currency": "USD"}
    
    def _extract_hero_cards(self) -> List[str]:
        """Extract hero's hole cards using card recognition."""
        return self._extract_cards_from_region(self.ui_regions['hero_cards'])
    
    def _extract_board_cards(self) -> List[str]:
        """Extract board cards using card recognition."""
        return self._extract_cards_from_region(self.ui_regions['board_cards'])
    
    def _extract_cards_from_region(self, region: Tuple[int, int, int, int]) -> List[str]:
        """Extract cards from a specific region using advanced card recognition."""
        try:
            image = self._capture_region(region)
            if image is None:
                return []
            
            # Determine max cards based on region type
            if 'hero' in str(region) or 'hole' in str(region):
                max_cards = 2  # Hero cards
            elif 'board' in str(region) or 'community' in str(region):
                max_cards = 5  # Board cards
            else:
                max_cards = 5  # Default
            
            # Use advanced card recognition
            detected_cards = self.card_recognizer.detect_cards_in_region(image, max_cards)
            
            # Convert to string format and normalize
            card_strings = []
            for card in detected_cards:
                if card.confidence > 0.6:  # Higher confidence threshold to reduce false positives
                    card_str = self.normalize_card_format(str(card))
                    if card_str:
                        card_strings.append(card_str)
            
            self.logger.debug(f"Extracted {len(card_strings)} cards from region: {card_strings}")
            return card_strings
            
        except Exception as e:
            self.logger.error(f"Card extraction failed: {e}")
            return []
    
    def _detect_cards_in_image(self, image) -> List[str]:
        """Detect and recognize cards in image using advanced recognition."""
        try:
            # Convert OpenCV image to PIL format
            if isinstance(image, np.ndarray):
                if len(image.shape) == 3:
                    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                else:
                    pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # Use card recognition system
            detected_cards = self.card_recognizer.detect_cards_in_region(pil_image, max_cards=5)
            
            # Return card strings with higher confidence threshold
            return [str(card) for card in detected_cards if card.confidence > 0.6]
            
        except Exception as e:
            self.logger.error(f"Card detection failed: {e}")
            return []
    
    def _extract_to_call(self) -> float:
        """Extract amount needed to call from action area."""
        if 'action_buttons' not in self.ui_regions:
            return 0.0
            
        text = self._extract_text_from_region(self.ui_regions['action_buttons'], 'action_buttons')
        
        # Look for call amount in button text
        call_patterns = [
            r'call\s*\$?([\d,]+\.?\d*)',
            r'(\d+\.?\d*)\s*to\s*call',
        ]
        
        for pattern in call_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except:
                    continue
        return 0.0
    
    def _extract_min_bet(self) -> float:
        """Extract minimum bet from stakes."""
        stakes = self._extract_stakes()
        return stakes.get('bb', 0.02)
    
    def _extract_enhanced_seat_info(self) -> List[Dict[str, Any]]:
        """Extract enhanced player information from all seat regions using calibrated coordinates."""
        seats = []
        
        # Look for seat regions in calibration data
        seat_regions = {}
        for region_name, coords in self.ui_regions.items():
            if 'seat_' in region_name:
                # Extract seat number and type (name/stack/bet)
                parts = region_name.split('_')
                if len(parts) >= 2:
                    try:
                        seat_num = int(parts[1])
                        region_type = '_'.join(parts[2:]) if len(parts) > 2 else 'combined'
                        
                        if seat_num not in seat_regions:
                            seat_regions[seat_num] = {}
                        seat_regions[seat_num][region_type] = coords
                    except ValueError:
                        continue
        
        # Extract data for each seat
        for seat_num in sorted(seat_regions.keys()):
            seat_info = seat_regions[seat_num]
            
            # Extract player name
            player_name = None
            if 'name' in seat_info:
                name_text = self._extract_text_from_region(seat_info['name'], f'seat_{seat_num}_name')
                player_name = self._clean_player_name(name_text)
            
            # Extract stack amount  
            stack_amount = None
            if 'stack' in seat_info:
                stack_text = self._extract_text_from_region(seat_info['stack'], f'seat_{seat_num}_stack')
                stack_amount = self._extract_money_amount(stack_text)
            elif 'combined' in seat_info:
                # If we have combined region, extract both name and stack
                combined_text = self._extract_text_from_region(seat_info['combined'], f'seat_{seat_num}_combined')
                player_name = self._extract_player_name_from_text(combined_text)
                stack_amount = self._extract_stack_from_text(combined_text)
            
            # Extract current bet
            current_bet = 0.0
            if 'bet' in seat_info:
                bet_text = self._extract_text_from_region(seat_info['bet'], f'seat_{seat_num}_bet')
                current_bet = self._extract_money_amount(bet_text)
            
            # Only include if we have meaningful data
            if player_name or stack_amount:
                seat_data = {
                    "seat": seat_num,
                    "name": player_name,
                    "stack": stack_amount,
                    "in_hand": self._is_player_in_hand(seat_num),
                    "is_hero": self._is_hero_seat(seat_num, player_name or ''),
                    "acted": self._has_player_acted(seat_num),
                    "put_in": current_bet,
                    "total_invested": self._extract_total_invested(seat_num),
                    "is_all_in": self._is_player_all_in(seat_num),
                    "position": None,  # Will be filled later
                    "stack_bb": None  # Will be calculated later
                }
                
                # Calculate stack in big blinds
                stakes = self._extract_stakes()
                if seat_data["stack"] and stakes.get('bb'):
                    seat_data["stack_bb"] = seat_data["stack"] / stakes['bb']
                
                seats.append(seat_data)
        
        return seats
    
    def _extract_player_name_from_text(self, text: str) -> Optional[str]:
        """Extract player name from seat text."""
        # Look for text that appears to be a username
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^[\d$.,\s]+$', line):  # Not just numbers/money
                return self._clean_player_name(line)
        return None
    
    def _clean_player_name(self, name_text: str) -> Optional[str]:
        """Clean and validate player name."""
        if not name_text:
            return None
            
        # Clean the text
        cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', name_text.strip())
        
        # Must be reasonable length for a username
        if 2 <= len(cleaned) <= 20:
            return cleaned
        return None
    
    def _extract_stack_from_text(self, text: str) -> Optional[float]:
        """Extract stack size from seat text."""
        return self._extract_money_amount(text)
    
    def _extract_money_amount(self, text: str) -> Optional[float]:
        """Extract money amount from text with multiple patterns."""
        if not text:
            return None
            
        # Multiple patterns for money amounts
        patterns = [
            r'\$([\d,]+\.?\d*)',  # $123.45
            r'([\d,]+\.?\d*)\s*\$',  # 123.45$
            r'([\d,]+\.?\d*)',  # 123.45 (plain number)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    # Reasonable bounds for poker amounts
                    if 0 <= amount <= 1000000:
                        return amount
                except (ValueError, IndexError):
                    continue
        return None
    
    def _is_hero_seat(self, seat_num: int, text: str) -> bool:
        """Determine if this is the hero's seat."""
        # This would need more sophisticated detection
        # Could look for specific UI indicators, highlighted seats, etc.
        # For now, assume seat 6 is hero (common position)
        return seat_num == 6  # Placeholder logic
    
    def _find_hero_seat(self, seats: List[Dict[str, Any]]) -> Optional[int]:
        """Find hero's seat number."""
        for seat in seats:
            if seat.get("is_hero"):
                return seat["seat"]
        return None
    
    def _extract_action_history(self) -> List[Dict[str, Any]]:
        """Extract betting action history (simplified for ACR)."""
        # This would need to track actions throughout the hand
        # For now, return empty list - full implementation would require
        # continuous monitoring and action tracking
        return []
    
    def _detect_button_position(self) -> Optional[int]:
        """Detect button position from UI indicators."""
        # Look for button indicator in each seat region
        for seat_num in range(1, 9):
            seat_key = f'seat_{seat_num}'
            if seat_key in self.ui_regions:
                # Look for button indicator (dealer chip, etc.)
                # This would need visual recognition of button marker
                # For now, use heuristic based on typical ACR layout
                pass
        
        # Default fallback - assume button is at seat with most chips or seat 6
        return 6
    
    def _is_player_in_hand(self, seat_num: int) -> bool:
        """Check if player is still in the hand."""
        # Look for folded indicators in seat region
        seat_key = f'seat_{seat_num}'
        if seat_key in self.ui_regions:
            text = self._extract_text_from_region(self.ui_regions[seat_key])
            # Look for "folded" or grayed out indicators
            if 'fold' in text.lower() or 'out' in text.lower():
                return False
        return True
    
    def _has_player_acted(self, seat_num: int) -> bool:
        """Check if player has acted this street."""
        # This would require tracking actions throughout the street
        # For simplified implementation, assume all visible players have acted
        return True
    
    def _extract_amount_put_in(self, seat_num: int) -> float:
        """Extract amount player put in this street."""
        # Look for bet chips in front of player
        # This would require additional UI regions for bet areas
        return 0.0
    
    def _extract_total_invested(self, seat_num: int) -> float:
        """Extract total amount invested this hand."""
        # Would require tracking throughout the hand
        return 0.0
    
    def _is_player_all_in(self, seat_num: int) -> bool:
        """Check if player is all-in."""
        seat_key = f'seat_{seat_num}'
        if seat_key in self.ui_regions:
            text = self._extract_text_from_region(self.ui_regions[seat_key])
            return 'all' in text.lower() and 'in' in text.lower()
        return False
    
    def _calculate_position_vs_aggressor(self, hero_seat: int, aggressor_seat: int, 
                                       button_seat: int, num_players: int, street: str) -> str:
        """Calculate if hero is in position vs aggressor."""
        if hero_seat == aggressor_seat:
            return "heads_up"
        
        # Calculate action order
        if num_players == 2:
            # Heads up logic
            if street == 'PREFLOP':
                hero_acts_after = (hero_seat == button_seat and aggressor_seat != button_seat)
            else:
                hero_acts_after = hero_seat == button_seat
        else:
            # Multi-way logic
            if street == 'PREFLOP':
                first_to_act = (button_seat % num_players) + 1
                if first_to_act > num_players:
                    first_to_act = 1
            else:
                first_to_act = (button_seat % num_players) + 1
                if first_to_act > num_players:
                    first_to_act = 1
            
            hero_order = (hero_seat - first_to_act + num_players) % num_players
            aggressor_order = (aggressor_seat - first_to_act + num_players) % num_players
            hero_acts_after = hero_order > aggressor_order
        
        return "in_position" if hero_acts_after else "out_of_position"
    
    def cleanup(self):
        """Cleanup scraper resources."""
        self.logger.info("ACR scraper cleaned up")