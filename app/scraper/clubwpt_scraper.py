"""ClubWPT Gold browser-based table scraper."""

import asyncio
import re
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page
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
        """Scrape current table state from ClubWPT Gold."""
        if not self.page or not self.is_table_active():
            return None
            
        try:
            # Extract table data (these selectors need to be adjusted based on actual ClubWPT Gold DOM)
            table_data = {}
            
            # Basic table info
            table_data['table_id'] = await self._extract_table_id()
            table_data['street'] = await self._extract_street()
            table_data['pot'] = await self._extract_pot_size()
            table_data['stakes'] = await self._extract_stakes()
            
            # Cards
            table_data['hero_hole'] = await self._extract_hero_cards()
            table_data['board'] = await self._extract_board_cards()
            
            # Betting info
            table_data['to_call'] = await self._extract_to_call()
            table_data['bet_min'] = await self._extract_min_bet()
            
            # Players and seats
            table_data['seats'] = await self._extract_seat_info()
            table_data['hero_seat'] = await self._find_hero_seat(table_data['seats'])
            table_data['max_seats'] = len(table_data['seats'])
            
            # Validate we have minimum required data
            if not table_data.get('stakes') or not table_data.get('seats'):
                self.logger.warning("Insufficient table data scraped")
                return None
                
            self.logger.debug(f"Scraped table state: {table_data}")
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
    
    async def _extract_seat_info(self) -> List[Dict[str, Any]]:
        """Extract information about all seats/players."""
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
                        "is_hero": False
                    }
                    
                    # Extract player name
                    name_elem = await element.query_selector('.player-name, .name')
                    if name_elem:
                        seat_data["name"] = await name_elem.text_content()
                    
                    # Extract stack size
                    stack_elem = await element.query_selector('.stack, .chips')
                    if stack_elem:
                        stack_text = await stack_elem.text_content()
                        if stack_text:
                            stack_match = re.search(r'[\d,]+\.?\d*', stack_text.replace(',', ''))
                            if stack_match:
                                seat_data["stack"] = float(stack_match.group())
                    
                    # Check if player is in hand
                    seat_data["in_hand"] = not await element.query_selector('.folded, .sitting-out')
                    
                    # Check if this is hero seat
                    seat_data["is_hero"] = bool(await element.query_selector('.hero, .my-seat'))
                    
                    if seat_data["name"] or seat_data["stack"]:
                        seats.append(seat_data)
            
            return seats
            
        except:
            return []
    
    async def _find_hero_seat(self, seats: List[Dict[str, Any]]) -> Optional[int]:
        """Find hero's seat number from seat info."""
        for seat in seats:
            if seat.get("is_hero"):
                return seat["seat"]
        return None
    
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