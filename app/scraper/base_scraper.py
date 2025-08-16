"""Base scraper interface for poker table data extraction."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
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