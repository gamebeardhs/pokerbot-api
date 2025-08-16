"""Manual trigger system for ACR GTO analysis."""

import json
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.scraper.acr_scraper import ACRScraper
from app.advisor.enhanced_gto_service import EnhancedGTODecisionService
from app.api.models import TableState, GTOResponse, Stakes, Seat

logger = logging.getLogger(__name__)


class ManualTriggerService:
    """Service for manual GTO analysis triggers."""
    
    def __init__(self, gto_service: EnhancedGTODecisionService, calibration_file: Optional[str] = None):
        """Initialize manual trigger service."""
        self.gto_service = gto_service
        self.acr_scraper = ACRScraper(calibration_file)
        self.logger = logger
        
        # Setup scraper
        if not self.acr_scraper.setup():
            self.logger.warning("ACR scraper setup failed - analysis may be limited")
    
    async def analyze_current_hand(self) -> Dict[str, Any]:
        """Take screenshot and analyze current hand for GTO decision."""
        start_time = time.time()
        
        try:
            self.logger.info("Starting manual hand analysis")
            
            # Step 1: Check if table is active
            if not self.acr_scraper.is_table_active():
                return {
                    "ok": False,
                    "error": "No active ACR table detected",
                    "details": "Please ensure ACR poker client is open with an active table"
                }
            
            # Step 2: Scrape table state
            raw_table_data = await self.acr_scraper.scrape_table_state()
            if not raw_table_data:
                return {
                    "ok": False,
                    "error": "Failed to extract table data",
                    "details": "Could not read table information from screen"
                }
            
            # Step 3: Convert to proper TableState model
            table_state = self._convert_to_table_state(raw_table_data)
            if not table_state:
                return {
                    "ok": False,
                    "error": "Failed to parse table state",
                    "details": "Extracted data could not be converted to valid table state"
                }
            
            # Step 4: Get GTO decision
            gto_response = await self.gto_service.compute_gto_decision(table_state)
            if not gto_response or not gto_response.ok:
                return {
                    "ok": False,
                    "error": "GTO analysis failed",
                    "details": "Could not compute optimal decision"
                }
            
            # Step 5: Return complete analysis
            analysis_time = int((time.time() - start_time) * 1000)
            
            return {
                "ok": True,
                "gto_decision": gto_response.dict(),
                "table_state": table_state.dict(),
                "raw_data": raw_table_data,
                "analysis_time_ms": analysis_time,
                "calibrated": self.acr_scraper.calibrated,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Manual analysis failed: {e}")
            return {
                "ok": False,
                "error": f"Analysis error: {str(e)}",
                "details": "Unexpected error during hand analysis"
            }
    
    def _convert_to_table_state(self, raw_data: Dict[str, Any]) -> Optional[TableState]:
        """Convert raw scraper data to TableState model."""
        try:
            # Extract stakes
            stakes_data = raw_data.get('stakes', {})
            stakes = Stakes(
                sb=stakes_data.get('sb', 0.01),
                bb=stakes_data.get('bb', 0.02),
                currency=stakes_data.get('currency', 'USD')
            )
            
            # Convert seats
            seats = []
            raw_seats = raw_data.get('seats', [])
            for seat_data in raw_seats:
                seat = Seat(
                    seat=seat_data.get('seat'),
                    name=seat_data.get('name'),
                    stack=seat_data.get('stack'),
                    in_hand=seat_data.get('in_hand', True),
                    acted=seat_data.get('acted', False),
                    put_in=seat_data.get('put_in', 0.0),
                    total_invested=seat_data.get('total_invested', 0.0),
                    is_hero=seat_data.get('is_hero', False),
                    is_all_in=seat_data.get('is_all_in', False),
                    stack_bb=seat_data.get('stack_bb')
                )
                seats.append(seat)
            
            # Create table state
            table_state = TableState(
                table_id=raw_data.get('table_id', 'acr_manual'),
                stakes=stakes,
                street=raw_data.get('street', 'PREFLOP'),
                board=raw_data.get('board', []),
                hero_hole=raw_data.get('hero_hole', []),
                pot=raw_data.get('pot', 0.0),
                to_call=raw_data.get('to_call', 0.0),
                bet_min=raw_data.get('bet_min', stakes.bb),
                seats=seats,
                max_seats=raw_data.get('max_seats', 8),
                hero_seat=raw_data.get('hero_seat'),
                button_seat=raw_data.get('button_seat'),
                sb_seat=raw_data.get('sb_seat'),
                bb_seat=raw_data.get('bb_seat'),
                spr=raw_data.get('spr'),
                current_aggressor_seat=raw_data.get('current_aggressor_seat'),
                current_action_type=raw_data.get('current_action_type'),
                hero_position_vs_aggressor=raw_data.get('hero_position_vs_aggressor'),
                num_raises_this_street=raw_data.get('num_raises_this_street', 0),
                rake_cap=raw_data.get('rake_cap', 5.0),
                rake_percentage=raw_data.get('rake_percentage', 5.0),
                betting_history=raw_data.get('betting_history', []),
                effective_stacks=raw_data.get('effective_stacks', {}),
                timestamp=datetime.now().isoformat()
            )
            
            return table_state
            
        except Exception as e:
            self.logger.error(f"Failed to convert table state: {e}")
            return None
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """Get calibration status and loaded regions."""
        return {
            "calibrated": self.acr_scraper.calibrated,
            "calibration_file": self.acr_scraper.calibration_file,
            "regions_loaded": len(self.acr_scraper.ui_regions),
            "available_regions": list(self.acr_scraper.ui_regions.keys())
        }
    
    def test_ocr_regions(self) -> Dict[str, Any]:
        """Test OCR on all calibrated regions (for debugging)."""
        if not self.acr_scraper.calibrated:
            return {
                "ok": False,
                "error": "No calibration loaded",
                "details": "Run calibration tool first"
            }
        
        try:
            results = {}
            for region_name, coords in self.acr_scraper.ui_regions.items():
                text = self.acr_scraper._extract_text_from_region(coords, region_name)
                results[region_name] = {
                    "coordinates": coords,
                    "extracted_text": text,
                    "has_text": bool(text and text.strip())
                }
            
            return {
                "ok": True,
                "results": results,
                "total_regions": len(results),
                "regions_with_text": sum(1 for r in results.values() if r["has_text"])
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error": f"OCR test failed: {str(e)}"
            }