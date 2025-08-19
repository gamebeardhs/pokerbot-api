"""Scraper manager to coordinate multiple scrapers and integrate with GTO service."""

import asyncio
import logging
from typing import Optional, Dict, Any
try:
    from app.scraper.clubwpt_scraper import ClubWPTGoldScraper
    CLUBWPT_AVAILABLE = True
except ImportError:
    CLUBWPT_AVAILABLE = False
    ClubWPTGoldScraper = None
from app.scraper.acr_scraper import ACRScraper
from app.advisor.enhanced_gto_service import EnhancedGTODecisionService

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages multiple scrapers and coordinates with GTO decision service."""
    
    def __init__(self, gto_service: EnhancedGTODecisionService):
        """Initialize scraper manager with GTO service."""
        self.gto_service = gto_service
        self.scrapers = {
            'acr': ACRScraper()
        }
        
        # Only add ClubWPT scraper if Playwright is available
        if CLUBWPT_AVAILABLE and ClubWPTGoldScraper is not None:
            self.scrapers['clubwpt'] = ClubWPTGoldScraper()
            logger.info("ClubWPT scraper enabled")
        else:
            logger.warning("ClubWPT scraper disabled (Playwright not available)")
            
        self.active_scraper = None
        self.is_running = False
        
    async def start_scraping(self, platform: str = 'auto') -> bool:
        """
        Start scraping for specified platform.
        
        Args:
            platform: 'clubwpt', 'acr', or 'auto' (detect active table)
        """
        try:
            if platform == 'auto':
                platform = await self._detect_active_platform()
                
            if platform not in self.scrapers:
                logger.error(f"Unknown platform: {platform}")
                return False
                
            scraper = self.scrapers[platform]
            
            # Setup scraper
            if not await scraper.setup() if hasattr(scraper.setup, '__call__') else scraper.setup():
                logger.error(f"Failed to setup {platform} scraper")
                return False
                
            self.active_scraper = scraper
            self.is_running = True
            
            logger.info(f"Started scraping for {platform}")
            
            # Start the scraping loop
            asyncio.create_task(self._scraping_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start scraping: {e}")
            return False
    
    async def stop_scraping(self):
        """Stop active scraping."""
        self.is_running = False
        
        if self.active_scraper:
            await self.active_scraper.cleanup()
            self.active_scraper = None
            
        logger.info("Scraping stopped")
    
    async def get_current_gto_advice(self) -> Optional[Dict[str, Any]]:
        """Get GTO advice for current table state."""
        if not self.active_scraper:
            return None
            
        try:
            # Scrape current table state
            table_state = await self.active_scraper.scrape_table_state()
            if not table_state:
                return None
                
            # Convert to enhanced TableState model
            from app.api.models import TableState, Stakes, Seat, StreetAction, BettingAction
            
            # Convert seats with enhanced data
            seats = []
            for seat_data in table_state.get('seats', []):
                # Ensure all enhanced fields are present
                enhanced_seat_data = {
                    'seat': seat_data.get('seat'),
                    'name': seat_data.get('name'),
                    'stack': seat_data.get('stack'),
                    'in_hand': seat_data.get('in_hand', True),
                    'acted': seat_data.get('acted'),
                    'put_in': seat_data.get('put_in', 0.0),
                    'total_invested': seat_data.get('total_invested', 0.0),
                    'is_hero': seat_data.get('is_hero', False),
                    'position': seat_data.get('position'),
                    'is_all_in': seat_data.get('is_all_in', False),
                    'stack_bb': seat_data.get('stack_bb')
                }
                seat = Seat(**enhanced_seat_data)
                seats.append(seat)
            
            # Convert stakes
            stakes_data = table_state.get('stakes', {})
            stakes = Stakes(**stakes_data)
            
            # Convert betting history
            betting_history = []
            for action_data in table_state.get('betting_history', []):
                # Convert to StreetAction format if needed
                if isinstance(action_data, dict):
                    street_action = StreetAction(
                        street=action_data.get('street', 'PREFLOP'),
                        actions=[],
                        pot_size_start=action_data.get('pot_size_start', 0),
                        pot_size_end=action_data.get('pot_size_end', 0),
                        aggressor_seat=action_data.get('aggressor_seat'),
                        action_type=action_data.get('action_type'),
                        aggressor_position=action_data.get('aggressor_position')
                    )
                    betting_history.append(street_action)
            
            # Create enhanced TableState object
            state = TableState(
                table_id=table_state.get('table_id', 'scraped_table'),
                street=table_state.get('street', 'PREFLOP'),
                board=table_state.get('board', []),
                hero_hole=table_state.get('hero_hole', []),
                pot=table_state.get('pot', 0),
                to_call=table_state.get('to_call', 0),
                bet_min=table_state.get('bet_min'),
                stakes=stakes,
                hero_seat=table_state.get('hero_seat'),
                max_seats=table_state.get('max_seats', 6),
                seats=seats,
                # Enhanced fields
                betting_history=betting_history,
                effective_stacks=table_state.get('effective_stacks', {}),
                spr=table_state.get('spr'),
                button_seat=table_state.get('button_seat'),
                sb_seat=table_state.get('sb_seat'),
                bb_seat=table_state.get('bb_seat'),
                rake_cap=table_state.get('rake_cap'),
                rake_percentage=table_state.get('rake_percentage'),
                current_aggressor_seat=table_state.get('current_aggressor_seat'),
                current_action_type=table_state.get('current_action_type'),
                hero_position_vs_aggressor=table_state.get('hero_position_vs_aggressor'),
                num_raises_this_street=table_state.get('num_raises_this_street', 0)
            )
            
            # Get GTO decision
            gto_response = await self.gto_service.compute_gto_decision(state)
            
            return {
                'table_state': table_state,
                'gto_advice': {
                    'action': gto_response.decision.action,
                    'size': gto_response.decision.size,
                    'equity': gto_response.metrics.equity_breakdown.raw_equity,
                    'ev': gto_response.metrics.ev,
                    'confidence': 1.0 - (gto_response.metrics.exploitability or 0.05),
                    'computation_time_ms': gto_response.computation_time_ms
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get GTO advice: {e}")
            return None
    
    async def _detect_active_platform(self) -> str:
        """Auto-detect which platform has an active table."""
        # Check each scraper to see which has an active table
        for platform, scraper in self.scrapers.items():
            try:
                if hasattr(scraper.setup, '__call__'):
                    await scraper.setup()
                else:
                    scraper.setup()
                    
                if scraper.is_table_active():
                    logger.info(f"Detected active table on {platform}")
                    return platform
                    
            except Exception as e:
                logger.debug(f"Failed to detect {platform}: {e}")
                continue
                
        logger.warning("No active poker tables detected")
        return 'clubwpt'  # Default fallback
    
    async def _scraping_loop(self):
        """Main scraping loop that continuously monitors table state."""
        logger.info("Starting scraping loop")
        
        while self.is_running:
            try:
                if not self.active_scraper:
                    await asyncio.sleep(1)
                    continue
                    
                # Check if table is still active
                if not self.active_scraper.is_table_active():
                    logger.info("Table no longer active")
                    await asyncio.sleep(2)
                    continue
                    
                # Get current advice (this will also log the decision)
                advice = await self.get_current_gto_advice()
                
                if advice:
                    gto_advice = advice['gto_advice']
                    logger.info(
                        f"GTO Advice: {gto_advice['action']} "
                        f"(size: {gto_advice['size']:.3f}, "
                        f"equity: {gto_advice['equity']:.3f}, "
                        f"confidence: {gto_advice['confidence']:.3f})"
                    )
                
                # Wait before next scrape (adjust based on needs)
                await asyncio.sleep(2)  # Scrape every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in scraping loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scraper status."""
        return {
            'is_running': self.is_running,
            'active_platform': type(self.active_scraper).__name__ if self.active_scraper else None,
            'available_platforms': list(self.scrapers.keys()),
            'table_active': self.active_scraper.is_table_active() if self.active_scraper else False
        }