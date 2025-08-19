"""ClubWPT Gold browser-based table scraper."""

import asyncio
import re
from typing import Optional, Dict, Any, List
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    Page = None
from app.scraper.base_scraper import BaseScraper

class ClubWPTGoldScraper(BaseScraper):
    """Scraper for ClubWPT Gold browser-based poker tables."""
    
    def __init__(self):
        """Initialize ClubWPT Gold scraper."""
        super().__init__()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.site_url = "https://clubwptgold.com"
        
    async def setup(self) -> bool:
        """Setup browser and navigate to ClubWPT Gold."""
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning("Playwright not available - ClubWPT scraper disabled")
            return False
            
        try:
            playwright = await async_playwright().start()
            
            # Launch browser (headless for production, visible for debug)
            self.browser = await playwright.chromium.launch(
                headless=True,  # Set to False for debugging
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create page with poker site context
            self.page = await self.browser.new_page()
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate to ClubWPT Gold
            await self.page.goto(self.site_url)
            
            self.logger.info("ClubWPT Gold scraper initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup ClubWPT Gold scraper: {e}")
            return False
    
    async def wait_for_login(self, timeout: int = 300) -> bool:
        """Wait for user to manually log in. Returns True when logged in."""
        try:
            self.logger.info("Waiting for manual login to ClubWPT Gold...")
            
            # Wait for typical post-login elements (adjust selectors as needed)
            await self.page.wait_for_selector(
                '[data-testid="lobby"], .lobby, #lobby, .poker-lobby',
                timeout=timeout * 1000
            )
            
            self.logger.info("Login detected - ready to scrape tables")
            return True
            
        except Exception as e:
            self.logger.error(f"Login timeout or failed: {e}")
            return False
    
    def is_table_active(self) -> bool:
        """Check if a poker table is currently active."""
        if not self.page:
            return False
            
        try:
            # Look for table indicators (adjust selectors based on actual site)
            table_elements = [
                '.poker-table',
                '.table-container', 
                '[data-testid="poker-table"]',
                '.game-table'
            ]
            
            for selector in table_elements:
                if self.page.query_selector(selector):
                    return True
            return False
            
        except:
            return False
    
    async def scrape_table_state(self) -> Optional[Dict[str, Any]]:
        """Scrape enhanced table state from ClubWPT Gold."""
        if not self.page or not self.is_table_active():
            return None
            
        try:
            # Basic table info
            table_data = {
                'table_id': await self._extract_table_id(),
                'street': await self._extract_street(),
                'pot': await self._extract_pot_size(),
                'stakes': await self._extract_stakes(),
                'hero_hole': await self._extract_hero_cards(),
                'board': await self._extract_board_cards(),
                'to_call': await self._extract_to_call(),
                'bet_min': await self._extract_min_bet()
            }
            
            # Enhanced seat data with positions
            seats = await self._extract_enhanced_seat_info()
            table_data['seats'] = seats
            table_data['hero_seat'] = await self._find_hero_seat(seats)
            table_data['max_seats'] = len(seats) if seats else 6
            
            # Detect button and assign positions
            table_data['button_seat'] = await self._detect_button_position()
            
            if table_data['button_seat'] and seats:
                active_seats = [s['seat'] for s in seats if s.get('in_hand')]
                num_players = len(active_seats)
                positions = self.determine_positions(num_players, table_data['button_seat'])
                
                # Add positions to seats and identify SB/BB
                for seat in seats:
                    if seat['seat'] in positions:
                        seat['position'] = positions[seat['seat']]
                        if positions[seat['seat']] == 'SB':
                            table_data['sb_seat'] = seat['seat']
                        elif positions[seat['seat']] == 'BB':
                            table_data['bb_seat'] = seat['seat']
            
            # Extract betting history and context
            action_history = await self._extract_action_history()
            table_data['betting_history'] = action_history
            
            # Determine current action context
            current_street = table_data['street']
            action_type, num_raises = self.detect_action_type(action_history, current_street)
            table_data['current_action_type'] = action_type
            table_data['num_raises_this_street'] = num_raises
            table_data['current_aggressor_seat'] = self.find_current_aggressor(action_history, current_street)
            
            # Calculate enhanced metrics
            if table_data['hero_seat'] and seats:
                table_data['effective_stacks'] = self.calculate_effective_stacks(seats, table_data['hero_seat'])
                
                # Calculate SPR
                hero_stack = next((s['stack'] for s in seats if s['seat'] == table_data['hero_seat']), 0)
                table_data['spr'] = hero_stack / max(table_data['pot'], 1) if hero_stack > 0 else 0
                
                # Determine position vs aggressor
                if table_data['current_aggressor_seat'] and table_data['button_seat']:
                    table_data['hero_position_vs_aggressor'] = await self._calculate_position_vs_aggressor(
                        table_data['hero_seat'], 
                        table_data['current_aggressor_seat'],
                        table_data['button_seat'],
                        num_players if 'num_players' in locals() else 6,
                        current_street
                    )
            
            # Add rake information (ClubWPT standard - typically no rake for social play)
            table_data['rake_cap'] = 0.0
            table_data['rake_percentage'] = 0.0
            
            # Validate we have minimum required data
            if not table_data.get('stakes') or not table_data.get('seats'):
                self.logger.warning("Insufficient table data scraped")
                return None
                
            self.logger.debug(f"Scraped enhanced table state: {table_data}")
            return table_data
            
        except Exception as e:
            self.logger.error(f"Failed to scrape table state: {e}")
            return None
    
    async def _extract_table_id(self) -> str:
        """Extract table ID from page."""
        try:
            # Look for table ID in URL or page elements
            url = self.page.url
            table_match = re.search(r'table[_-]?(\d+)', url, re.IGNORECASE)
            if table_match:
                return f"clubwpt_table_{table_match.group(1)}"
            return f"clubwpt_table_{hash(url) % 10000}"
        except:
            return "clubwpt_table_unknown"
    
    async def _extract_street(self) -> str:
        """Extract current betting street."""
        try:
            # Look for street indicators in the DOM
            street_selectors = [
                '.street-indicator',
                '.betting-round',
                '[data-testid="street"]'
            ]
            
            for selector in street_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    return self.map_street_to_api_format(text or "")
            
            # Fallback: determine from board cards
            board_cards = await self._extract_board_cards()
            if len(board_cards) == 0:
                return "PREFLOP"
            elif len(board_cards) == 3:
                return "FLOP"
            elif len(board_cards) == 4:
                return "TURN"
            elif len(board_cards) == 5:
                return "RIVER"
            
        except:
            pass
        return "PREFLOP"
    
    async def _extract_pot_size(self) -> float:
        """Extract current pot size."""
        try:
            pot_selectors = [
                '.pot-size',
                '.pot-amount',
                '[data-testid="pot"]',
                '.total-pot'
            ]
            
            for selector in pot_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        # Extract numeric value from text like "$1.50" or "150 chips"
                        amount_match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
                        if amount_match:
                            return float(amount_match.group())
        except:
            pass
        return 0.0
    
    async def _extract_stakes(self) -> Dict[str, Any]:
        """Extract table stakes (blinds)."""
        try:
            # Look for stakes in table info area
            stakes_selectors = [
                '.table-stakes',
                '.blinds-info',
                '[data-testid="stakes"]'
            ]
            
            for selector in stakes_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        # Parse formats like "$0.01/$0.02" or "1/2 SC"
                        stakes_match = re.search(r'(\d+\.?\d*)[/\-](\d+\.?\d*)', text)
                        if stakes_match:
                            sb = float(stakes_match.group(1))
                            bb = float(stakes_match.group(2))
                            return {"sb": sb, "bb": bb, "currency": "SC"}
            
            # Fallback defaults for ClubWPT Gold
            return {"sb": 0.01, "bb": 0.02, "currency": "SC"}
            
        except:
            return {"sb": 0.01, "bb": 0.02, "currency": "SC"}
    
    async def _extract_hero_cards(self) -> List[str]:
        """Extract hero's hole cards."""
        try:
            card_selectors = [
                '.hero-cards .card',
                '.my-cards .card',
                '[data-testid="hero-card"]'
            ]
            
            cards = []
            for selector in card_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    # Try to get card value from various attributes/text
                    card_value = await element.get_attribute('data-card')
                    if not card_value:
                        card_value = await element.get_attribute('title')
                    if not card_value:
                        card_value = await element.text_content()
                    
                    if card_value and len(card_value) >= 2:
                        normalized = self.normalize_card_format(card_value[:2])
                        if normalized:
                            cards.append(normalized)
            
            return cards[:2]  # Limit to 2 hole cards
            
        except:
            return []
    
    async def _extract_board_cards(self) -> List[str]:
        """Extract community board cards."""
        try:
            board_selectors = [
                '.board-cards .card',
                '.community-cards .card',
                '[data-testid="board-card"]'
            ]
            
            cards = []
            for selector in board_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    card_value = await element.get_attribute('data-card')
                    if not card_value:
                        card_value = await element.get_attribute('title')
                    if not card_value:
                        card_value = await element.text_content()
                    
                    if card_value and len(card_value) >= 2:
                        normalized = self.normalize_card_format(card_value[:2])
                        if normalized:
                            cards.append(normalized)
            
            return cards[:5]  # Limit to 5 board cards
            
        except:
            return []
    
    async def _extract_to_call(self) -> float:
        """Extract amount needed to call."""
        try:
            call_selectors = [
                '.call-amount',
                '.to-call',
                '[data-testid="call-amount"]'
            ]
            
            for selector in call_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        amount_match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
                        if amount_match:
                            return float(amount_match.group())
        except:
            pass
        return 0.0
    
    async def _extract_min_bet(self) -> float:
        """Extract minimum bet amount."""
        # For ClubWPT Gold, min bet is typically the big blind
        stakes = await self._extract_stakes()
        return stakes.get('bb', 0.02)
    
    async def _extract_enhanced_seat_info(self) -> List[Dict[str, Any]]:
        """Extract enhanced information about all seats/players."""
        try:
            seats = []
            seat_selectors = [
                '.seat',
                '.player-seat',
                '[data-testid="seat"]'
            ]
            
            for selector in seat_selectors:
                elements = await self.page.query_selector_all(selector)
                for i, element in enumerate(elements):
                    seat_data = {
                        "seat": i + 1,
                        "name": None,
                        "stack": None,
                        "in_hand": False,
                        "is_hero": False,
                        "acted": None,
                        "put_in": 0.0,
                        "total_invested": 0.0,
                        "is_all_in": False,
                        "position": None,
                        "stack_bb": None
                    }
                    
                    # Extract player name
                    name_elem = await element.query_selector('.player-name, .name, .username')
                    if name_elem:
                        seat_data["name"] = await name_elem.text_content()
                    
                    # Extract stack size
                    stack_elem = await element.query_selector('.stack, .chips, .bankroll')
                    if stack_elem:
                        stack_text = await stack_elem.text_content()
                        if stack_text:
                            stack_match = re.search(r'[\d,]+\.?\d*', stack_text.replace(',', ''))
                            if stack_match:
                                seat_data["stack"] = float(stack_match.group())
                    
                    # Check if player is in hand (not folded/sitting out)
                    seat_data["in_hand"] = not await element.query_selector('.folded, .sitting-out, .out')
                    
                    # Check if this is hero seat
                    seat_data["is_hero"] = bool(await element.query_selector('.hero, .my-seat, .active-player'))
                    
                    # Check if player has acted
                    seat_data["acted"] = bool(await element.query_selector('.acted, .action-taken'))
                    
                    # Extract amount put in this street
                    bet_elem = await element.query_selector('.bet-amount, .current-bet')
                    if bet_elem:
                        bet_text = await bet_elem.text_content()
                        if bet_text:
                            bet_match = re.search(r'[\d,]+\.?\d*', bet_text.replace(',', ''))
                            if bet_match:
                                seat_data["put_in"] = float(bet_match.group())
                    
                    # Check if all-in
                    seat_data["is_all_in"] = bool(await element.query_selector('.all-in, .allin'))
                    
                    if seat_data["name"] or seat_data["stack"]:
                        seats.append(seat_data)
            
            # Calculate stack in big blinds for each seat
            stakes = await self._extract_stakes()
            bb = stakes.get('bb', 0.02)
            for seat in seats:
                if seat["stack"] and bb > 0:
                    seat["stack_bb"] = seat["stack"] / bb
            
            return seats
            
        except Exception as e:
            self.logger.error(f"Failed to extract enhanced seat info: {e}")
            return []
    
    async def _find_hero_seat(self, seats: List[Dict[str, Any]]) -> Optional[int]:
        """Find hero's seat number from seat info."""
        for seat in seats:
            if seat.get("is_hero"):
                return seat["seat"]
        return None
    
    async def _extract_action_history(self) -> List[Dict[str, Any]]:
        """Extract betting action history from the table."""
        try:
            action_history = []
            
            # Look for action log or betting history elements
            history_selectors = [
                '.action-history .action',
                '.betting-log .bet-action',
                '[data-testid="action-history"] .action'
            ]
            
            for selector in history_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    action_text = await element.text_content()
                    if action_text:
                        # Parse action text (format varies by site)
                        # Example: "Player1 bets $5.00" or "Hero raises to $10.00"
                        action_info = self._parse_action_text(action_text)
                        if action_info:
                            action_history.append(action_info)
            
            return action_history
            
        except Exception as e:
            self.logger.error(f"Failed to extract action history: {e}")
            return []
    
    def _parse_action_text(self, action_text: str) -> Optional[Dict[str, Any]]:
        """Parse action text into structured data."""
        try:
            # Common patterns for poker actions
            patterns = [
                r'(\w+)\s+(folds?|calls?|bets?|raises?)\s*(?:to\s*)?\$?([\d,]+\.?\d*)?',
                r'(\w+)\s+(checks?|all-?ins?)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, action_text, re.IGNORECASE)
                if match:
                    player_name = match.group(1)
                    action = match.group(2).lower().rstrip('s')  # Remove plural
                    amount = 0.0
                    
                    if len(match.groups()) > 2 and match.group(3):
                        amount = float(match.group(3).replace(',', ''))
                    
                    return {
                        'player': player_name,
                        'action': action,
                        'amount': amount,
                        'street': 'PREFLOP',  # Would need to determine actual street
                        'seat': None  # Would need to map player name to seat
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to parse action text '{action_text}': {e}")
            return None
    
    async def _detect_button_position(self) -> Optional[int]:
        """Detect button position from dealer indicator."""
        try:
            # Look for dealer button indicators
            button_selectors = [
                '.dealer-button',
                '.button',
                '[data-testid="dealer-button"]',
                '.dealer-chip'
            ]
            
            for selector in button_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    # Find which seat contains the button
                    parent_seat = await element.query_selector('xpath=ancestor::*[contains(@class, "seat")]')
                    if parent_seat:
                        # Extract seat number from class or data attribute
                        seat_classes = await parent_seat.get_attribute('class')
                        if seat_classes:
                            seat_match = re.search(r'seat[_-]?(\d+)', seat_classes)
                            if seat_match:
                                return int(seat_match.group(1))
            
            # Fallback: assume button is at seat 6 (common position)
            return 6
            
        except Exception as e:
            self.logger.error(f"Failed to detect button position: {e}")
            return 6
    
    async def _calculate_position_vs_aggressor(self, hero_seat: int, aggressor_seat: int, 
                                             button_seat: int, num_players: int, street: str) -> str:
        """Calculate if hero is in position vs aggressor."""
        if hero_seat == aggressor_seat:
            return "heads_up"
        
        try:
            # Use same logic as ACR scraper
            if num_players == 2:
                if street == 'PREFLOP':
                    hero_acts_after = (hero_seat == button_seat and aggressor_seat != button_seat)
                else:
                    hero_acts_after = hero_seat == button_seat
            else:
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
            
        except Exception as e:
            self.logger.error(f"Failed to calculate position vs aggressor: {e}")
            return "out_of_position"
    
    async def cleanup(self):
        """Cleanup browser resources."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            self.logger.info("ClubWPT Gold scraper cleaned up")
        except:
            pass