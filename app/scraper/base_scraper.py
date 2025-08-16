"""Base scraper interface for poker table data extraction."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for poker table scrapers."""
    
    def __init__(self):
        """Initialize scraper."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_active = False
        
    @abstractmethod
    async def scrape_table_state(self) -> Optional[Dict[str, Any]]:
        """
        Scrape current table state from poker client.
        
        Returns:
            Dict containing table state in GTO API format, or None if no data
        """
        pass
    
    @abstractmethod
    def is_table_active(self) -> bool:
        """Check if a poker table is currently active/visible."""
        pass
    
    @abstractmethod
    def setup(self) -> bool:
        """Setup scraper (browser, screen capture, etc). Returns success."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources when scraper is stopped."""
        pass
    
    def normalize_card_format(self, card_str: str) -> str:
        """Normalize card format to lowercase for API consistency."""
        if not card_str or len(card_str) != 2:
            return ""
        return card_str.lower()
    
    def map_street_to_api_format(self, street: str) -> str:
        """Map various street formats to API format."""
        street_mapping = {
            "preflop": "PREFLOP",
            "pre-flop": "PREFLOP", 
            "pre flop": "PREFLOP",
            "flop": "FLOP",
            "turn": "TURN",
            "river": "RIVER",
            "showdown": "SHOWDOWN"
        }
        return street_mapping.get(street.lower().strip(), "PREFLOP")
    
    def determine_positions(self, num_players: int, button_seat: int) -> Dict[int, str]:
        """Determine position for each seat based on button position."""
        position_maps = {
            2: ['BB', 'BTN'],  # Heads up
            3: ['BB', 'SB', 'BTN'],
            4: ['BB', 'SB', 'CO', 'BTN'],
            5: ['BB', 'SB', 'HJ', 'CO', 'BTN'],
            6: ['BB', 'SB', 'UTG', 'HJ', 'CO', 'BTN'],
            7: ['BB', 'SB', 'UTG', 'UTG1', 'HJ', 'CO', 'BTN'],
            8: ['BB', 'SB', 'UTG', 'UTG1', 'MP', 'HJ', 'CO', 'BTN'],
            9: ['BB', 'SB', 'UTG', 'UTG1', 'UTG2', 'MP', 'HJ', 'CO', 'BTN']
        }
        
        positions = {}
        if num_players in position_maps:
            position_list = position_maps[num_players]
            for i in range(num_players):
                seat_num = ((button_seat - 1 + i) % num_players) + 1
                positions[seat_num] = position_list[i]
        
        return positions
    
    def calculate_effective_stacks(self, seats: List[Dict], hero_seat: int) -> Dict[int, float]:
        """Calculate effective stacks vs each opponent."""
        hero_stack = 0
        for seat in seats:
            if seat.get('seat') == hero_seat and seat.get('stack'):
                hero_stack = seat['stack']
                break
        
        effective_stacks = {}
        for seat in seats:
            if seat.get('seat') != hero_seat and seat.get('stack'):
                effective_stacks[seat['seat']] = min(hero_stack, seat['stack'])
        
        return effective_stacks
    
    def detect_action_type(self, action_history: List[Dict], current_street: str) -> Tuple[str, int]:
        """Detect current action type and number of raises."""
        street_actions = [a for a in action_history if a.get('street') == current_street]
        
        # Count raises on this street
        raises = 0
        for action in street_actions:
            if action.get('action') in ['bet', 'raise']:
                raises += 1
        
        # Determine action type
        if raises == 0:
            return 'check_fold', 0
        elif raises == 1:
            return 'call', 0  # Facing a bet
        elif raises == 2:
            return '3bet', 2
        elif raises == 3:
            return '4bet', 3
        elif raises == 4:
            return '5bet', 4
        else:
            return 'shove', raises
    
    def find_current_aggressor(self, action_history: List[Dict], current_street: str) -> Optional[int]:
        """Find the seat of the current aggressor (last bettor/raiser)."""
        street_actions = [a for a in action_history if a.get('street') == current_street]
        
        # Find last aggressive action
        for action in reversed(street_actions):
            if action.get('action') in ['bet', 'raise']:
                return action.get('seat')
        
        return None