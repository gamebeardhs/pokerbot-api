"""ACR (Americas Cardroom) screen capture + OCR scraper."""

import cv2
import numpy as np
import pytesseract
import re
from PIL import Image, ImageGrab
from typing import Optional, Dict, Any, List, Tuple
from app.scraper.base_scraper import BaseScraper

class ACRScraper(BaseScraper):
    """Screen capture + OCR scraper for ACR desktop client."""
    
    def __init__(self):
        """Initialize ACR scraper."""
        super().__init__()
        self.window_bounds = None
        self.card_regions = {}
        self.ui_regions = {}
        self.setup_regions()
        
    def setup_regions(self):
        """Setup screen regions for different UI elements."""
        # These coordinates need to be calibrated for ACR client
        # Default regions for 1920x1080 screen with ACR client
        self.ui_regions = {
            'pot_area': (850, 300, 1070, 350),
            'hero_cards': (860, 600, 1060, 660),
            'board_cards': (760, 380, 1160, 440),
            'action_buttons': (800, 650, 1120, 720),
            'stakes_info': (50, 50, 250, 100),
            'seat_1': (400, 200, 550, 280),
            'seat_2': (600, 150, 750, 230),
            'seat_3': (800, 150, 950, 230),
            'seat_4': (1000, 200, 1150, 280),
            'seat_5': (1000, 500, 1150, 580),
            'seat_6': (800, 550, 950, 630),
            'seat_7': (600, 550, 750, 630),
            'seat_8': (400, 500, 550, 580),
        }
    
    def setup(self) -> bool:
        """Setup ACR scraper (find ACR window)."""
        try:
            # Try to detect ACR window (this is simplified - would need actual window detection)
            self.logger.info("ACR scraper initialized - ready for screen capture")
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
        """Scrape enhanced table state using screen capture and OCR."""
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
        """Capture a specific screen region."""
        try:
            x1, y1, x2, y2 = region
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            return screenshot
        except:
            return None
    
    def _extract_text_from_region(self, region: Tuple[int, int, int, int]) -> str:
        """Extract text from screen region using OCR."""
        try:
            image = self._capture_region(region)
            if image is None:
                return ""
                
            # Preprocess image for better OCR
            gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            
            # Apply thresholding to improve text recognition
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # Use OCR with poker-optimized config
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz$.,/ '
            text = pytesseract.image_to_string(binary, config=custom_config)
            
            return text.strip()
            
        except:
            return ""
    
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
        text = self._extract_text_from_region(self.ui_regions['pot_area'])
        
        # Look for dollar amounts or chip counts
        amount_patterns = [
            r'\$?([\d,]+\.?\d*)',  # $123.45 or 123.45
            r'([\d,]+)\s*chips?',  # 123 chips
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except:
                    continue
        return 0.0
    
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
        """Extract cards from a specific region using image recognition."""
        try:
            image = self._capture_region(region)
            if image is None:
                return []
                
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # This is a simplified card detection - would need more sophisticated
            # computer vision for accurate card recognition
            cards = self._detect_cards_in_image(cv_image)
            
            return [self.normalize_card_format(card) for card in cards if card]
            
        except:
            return []
    
    def _detect_cards_in_image(self, image) -> List[str]:
        """Detect and recognize cards in image (simplified implementation)."""
        # This would need a full card recognition system
        # For now, return empty list - would require training card templates
        # or using more advanced CV techniques
        
        # Placeholder: In real implementation, you'd:
        # 1. Detect card rectangles using contour detection
        # 2. Extract rank and suit using template matching or trained models
        # 3. Return list of cards like ["ah", "ks"]
        
        return []
    
    def _extract_to_call(self) -> float:
        """Extract amount needed to call from action area."""
        text = self._extract_text_from_region(self.ui_regions['action_buttons'])
        
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
        """Extract enhanced player information from all seat regions."""
        seats = []
        
        for seat_num in range(1, 9):  # ACR 8-max
            seat_key = f'seat_{seat_num}'
            if seat_key not in self.ui_regions:
                continue
                
            region = self.ui_regions[seat_key]
            text = self._extract_text_from_region(region)
            
            if not text.strip():
                continue  # Empty seat
                
            seat_data = {
                "seat": seat_num,
                "name": self._extract_player_name_from_text(text),
                "stack": self._extract_stack_from_text(text),
                "in_hand": self._is_player_in_hand(seat_num),
                "is_hero": self._is_hero_seat(seat_num, text),
                "acted": self._has_player_acted(seat_num),
                "put_in": self._extract_amount_put_in(seat_num),
                "total_invested": self._extract_total_invested(seat_num),
                "is_all_in": self._is_player_all_in(seat_num),
                "position": None,  # Will be filled later
                "stack_bb": None  # Will be calculated later
            }
            
            # Calculate stack in big blinds
            stakes = self._extract_stakes()
            if seat_data["stack"] and stakes.get('bb'):
                seat_data["stack_bb"] = seat_data["stack"] / stakes['bb']
            
            if seat_data["name"] or seat_data["stack"]:
                seats.append(seat_data)
        
        return seats
    
    def _extract_player_name_from_text(self, text: str) -> Optional[str]:
        """Extract player name from seat text."""
        # Look for text that appears to be a username
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^[\d$.,\s]+$', line):  # Not just numbers/money
                return line
        return None
    
    def _extract_stack_from_text(self, text: str) -> Optional[float]:
        """Extract stack size from seat text."""
        # Look for money amounts
        money_match = re.search(r'\$?([\d,]+\.?\d*)', text)
        if money_match:
            try:
                return float(money_match.group(1).replace(',', ''))
            except:
                pass
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