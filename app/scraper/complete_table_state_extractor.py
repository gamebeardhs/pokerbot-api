"""
Complete table state extraction system combining optimized capture,
OCR, card recognition, and validation for real-time poker analysis.
"""

import cv2
import numpy as np
import asyncio
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging

from .optimized_capture import OptimizedScreenCapture, WindowDetector, CaptureRegion
from .enhanced_ocr_engine import EnhancedOCREngine, OCRResult
from .red_button_detector import RedButtonDetector, ButtonDetection
from ..api.models import TableState

logger = logging.getLogger(__name__)

@dataclass
class TableRegionDefinition:
    """Definition of poker table regions for systematic extraction."""
    name: str
    region: CaptureRegion
    extraction_type: str  # 'ocr', 'cards', 'buttons'
    data_type: str       # 'money', 'text', 'cards', 'boolean'
    confidence_threshold: float = 0.7

@dataclass
class ExtractedTableState:
    """Complete extracted poker table state with confidence metrics."""
    timestamp: float
    pot_size: Optional[float] = None
    hero_stack: Optional[float] = None
    hero_cards: List[str] = None
    board_cards: List[str] = None
    active_players: List[Dict] = None
    button_position: Optional[int] = None
    blinds: Dict[str, float] = None
    current_street: str = "PREFLOP"
    action_buttons: List[ButtonDetection] = None
    is_hero_turn: bool = False
    extraction_confidence: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.hero_cards is None:
            self.hero_cards = []
        if self.board_cards is None:
            self.board_cards = []
        if self.active_players is None:
            self.active_players = []
        if self.blinds is None:
            self.blinds = {}
        if self.action_buttons is None:
            self.action_buttons = []
        if self.errors is None:
            self.errors = []

class CompleteTableStateExtractor:
    """Complete poker table state extraction system."""
    
    def __init__(self):
        # Core components
        self.capture_system = OptimizedScreenCapture()
        self.ocr_engine = EnhancedOCREngine()
        self.button_detector = RedButtonDetector()
        
        # State tracking
        self.last_extraction_time = 0
        self.extraction_cooldown = 0.5  # Minimum time between full extractions
        self.regions: Optional[Dict[str, CaptureRegion]] = None
        
        # Performance monitoring
        self.extraction_count = 0
        self.success_count = 0
        self.average_extraction_time = 0.0
        
    async def initialize(self) -> bool:
        """Initialize the extraction system."""
        try:
            # Detect poker table regions
            self.regions = WindowDetector.get_optimal_regions()
            
            if not self.regions:
                logger.error("Could not detect poker table regions for extraction")
                return False
            
            # Define extraction regions systematically
            self._define_extraction_regions()
            
            logger.info("Complete table state extractor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Table state extractor initialization failed: {e}")
            return False
    
    def _define_extraction_regions(self):
        """Define systematic extraction regions for all table elements."""
        if not self.regions:
            return
        
        main_region = self.regions['full_table']
        
        # Define comprehensive extraction regions
        self.extraction_regions = {
            # Money information
            'pot_area': TableRegionDefinition(
                name="pot_area",
                region=self.regions.get('pot_area', self._create_relative_region(main_region, 0.4, 0.2, 0.2, 0.1)),
                extraction_type='ocr',
                data_type='money',
                confidence_threshold=0.8
            ),
            
            # Cards
            'hero_cards': TableRegionDefinition(
                name="hero_cards", 
                region=self.regions.get('hero_cards', self._create_relative_region(main_region, 0.35, 0.65, 0.3, 0.1)),
                extraction_type='cards',
                data_type='cards',
                confidence_threshold=0.7
            ),
            
            'board_cards': TableRegionDefinition(
                name="board_cards",
                region=self.regions.get('board_cards', self._create_relative_region(main_region, 0.25, 0.35, 0.5, 0.15)),
                extraction_type='cards', 
                data_type='cards',
                confidence_threshold=0.7
            ),
            
            # Action buttons
            'action_buttons': TableRegionDefinition(
                name="action_buttons",
                region=self.regions.get('action_buttons', self._create_relative_region(main_region, 0.3, 0.8, 0.4, 0.15)),
                extraction_type='buttons',
                data_type='boolean',
                confidence_threshold=0.8
            ),
            
            # Player positions (6-max table)
            'hero_stack': TableRegionDefinition(
                name="hero_stack",
                region=self._create_relative_region(main_region, 0.4, 0.75, 0.2, 0.05),
                extraction_type='ocr',
                data_type='money',
                confidence_threshold=0.8
            )
        }
        
        # Add player seat regions for 6-max table
        seat_positions = [
            (0.15, 0.6, "seat_1"),   # UTG
            (0.1, 0.35, "seat_2"),   # MP
            (0.15, 0.1, "seat_3"),   # CO
            (0.7, 0.1, "seat_4"),    # BTN
            (0.85, 0.35, "seat_5"),  # SB
            (0.7, 0.6, "seat_6")     # BB
        ]
        
        for i, (x_ratio, y_ratio, seat_name) in enumerate(seat_positions):
            # Stack region
            self.extraction_regions[f'{seat_name}_stack'] = TableRegionDefinition(
                name=f"{seat_name}_stack",
                region=self._create_relative_region(main_region, x_ratio, y_ratio + 0.05, 0.15, 0.04),
                extraction_type='ocr',
                data_type='money'
            )
            
            # Name region
            self.extraction_regions[f'{seat_name}_name'] = TableRegionDefinition(
                name=f"{seat_name}_name", 
                region=self._create_relative_region(main_region, x_ratio, y_ratio - 0.05, 0.15, 0.04),
                extraction_type='ocr',
                data_type='text'
            )
    
    def _create_relative_region(self, base_region: CaptureRegion, x_ratio: float, y_ratio: float, 
                               width_ratio: float, height_ratio: float) -> CaptureRegion:
        """Create a region relative to a base region."""
        return CaptureRegion(
            name=f"relative_region",
            x=base_region.x + int(base_region.width * x_ratio),
            y=base_region.y + int(base_region.height * y_ratio),
            width=int(base_region.width * width_ratio),
            height=int(base_region.height * height_ratio)
        )
    
    async def extract_complete_table_state(self) -> ExtractedTableState:
        """Extract complete poker table state with all information."""
        start_time = time.time()
        
        # Check extraction cooldown
        if time.time() - self.last_extraction_time < self.extraction_cooldown:
            logger.debug("Extraction cooldown active")
            return None
        
        try:
            # Capture full table
            if not self.regions:
                await self.initialize()
            
            full_table_image = self.capture_system.capture_region_sync(self.regions['full_table'])
            if full_table_image is None or full_table_image.size == 0:
                logger.warning("Failed to capture full table image")
                return ExtractedTableState(timestamp=time.time(), errors=["Failed to capture table"])
            
            # Initialize extraction result
            extracted_state = ExtractedTableState(timestamp=time.time())
            confidence_scores = []
            
            # Extract pot size
            pot_result = await self._extract_pot_information(full_table_image)
            if pot_result:
                extracted_state.pot_size = pot_result.value
                confidence_scores.append(pot_result.confidence)
            
            # Extract hero cards
            hero_cards = await self._extract_hero_cards(full_table_image)
            if hero_cards:
                extracted_state.hero_cards = hero_cards
                confidence_scores.append(0.8)  # Assume reasonable confidence for cards
            
            # Extract board cards
            board_cards = await self._extract_board_cards(full_table_image)
            if board_cards:
                extracted_state.board_cards = board_cards
                extracted_state.current_street = self._determine_street(board_cards)
                confidence_scores.append(0.8)
            
            # Extract button information and turn detection
            button_info = await self._extract_action_buttons(full_table_image)
            if button_info:
                extracted_state.action_buttons = button_info['buttons']
                extracted_state.is_hero_turn = button_info['is_my_turn']
                confidence_scores.append(button_info['confidence'])
            
            # Extract player information
            player_info = await self._extract_player_information(full_table_image)
            if player_info:
                extracted_state.active_players = player_info['players']
                extracted_state.hero_stack = player_info.get('hero_stack')
                extracted_state.blinds = player_info.get('blinds', {})
                confidence_scores.append(player_info.get('confidence', 0.5))
            
            # Calculate overall confidence
            extracted_state.extraction_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Update performance metrics
            self.extraction_count += 1
            if extracted_state.extraction_confidence > 0.6:
                self.success_count += 1
            
            extraction_time = time.time() - start_time
            self.average_extraction_time = (
                (self.average_extraction_time * (self.extraction_count - 1) + extraction_time) / self.extraction_count
            )
            
            self.last_extraction_time = time.time()
            
            logger.debug(f"Extracted table state: confidence={extracted_state.extraction_confidence:.2f}, "
                        f"time={extraction_time:.3f}s, pot=${extracted_state.pot_size}, "
                        f"cards={len(extracted_state.hero_cards + extracted_state.board_cards)}")
            
            return extracted_state
            
        except Exception as e:
            logger.error(f"Table state extraction failed: {e}")
            return ExtractedTableState(timestamp=time.time(), errors=[str(e)])
    
    async def _extract_pot_information(self, table_image: np.ndarray) -> Optional[OCRResult]:
        """Extract pot size from table image."""
        try:
            pot_region = self.extraction_regions['pot_area']
            region_image = self._extract_region_from_image(table_image, pot_region.region)
            
            if region_image is not None and region_image.size > 0:
                result = self.ocr_engine.extract_text_multimethod(region_image, 'money')
                if result.confidence > pot_region.confidence_threshold:
                    return result
            
            return None
            
        except Exception as e:
            logger.debug(f"Pot extraction failed: {e}")
            return None
    
    async def _extract_hero_cards(self, table_image: np.ndarray) -> List[str]:
        """Extract hero's hole cards."""
        try:
            hero_region = self.extraction_regions['hero_cards']
            region_image = self._extract_region_from_image(table_image, hero_region.region)
            
            if region_image is not None and region_image.size > 0:
                cards = self.ocr_engine.extract_cards(region_image, max_cards=2)
                return cards[:2]  # Hero has exactly 2 cards
                
            return []
            
        except Exception as e:
            logger.debug(f"Hero cards extraction failed: {e}")
            return []
    
    async def _extract_board_cards(self, table_image: np.ndarray) -> List[str]:
        """Extract community board cards."""
        try:
            board_region = self.extraction_regions['board_cards']
            region_image = self._extract_region_from_image(table_image, board_region.region)
            
            if region_image is not None and region_image.size > 0:
                cards = self.ocr_engine.extract_cards(region_image, max_cards=5)
                return cards[:5]  # Max 5 community cards
                
            return []
            
        except Exception as e:
            logger.debug(f"Board cards extraction failed: {e}")
            return []
    
    async def _extract_action_buttons(self, table_image: np.ndarray) -> Optional[Dict]:
        """Extract action button information and turn detection."""
        try:
            button_region = self.extraction_regions['action_buttons']
            region_image = self._extract_region_from_image(table_image, button_region.region)
            
            if region_image is not None and region_image.size > 0:
                is_turn, button_detections = self.button_detector.is_my_turn(region_image)
                
                return {
                    'buttons': button_detections,
                    'is_my_turn': is_turn,
                    'confidence': max([b.confidence for b in button_detections], default=0.0)
                }
                
            return None
            
        except Exception as e:
            logger.debug(f"Button extraction failed: {e}")
            return None
    
    async def _extract_player_information(self, table_image: np.ndarray) -> Optional[Dict]:
        """Extract information about all players at the table."""
        try:
            players = []
            hero_stack = None
            confidences = []
            
            # Extract information for each seat
            for i in range(1, 7):  # 6-max table
                seat_name = f"seat_{i}"
                
                # Extract stack size
                stack_region_name = f"{seat_name}_stack"
                if stack_region_name in self.extraction_regions:
                    stack_region = self.extraction_regions[stack_region_name]
                    stack_image = self._extract_region_from_image(table_image, stack_region.region)
                    
                    if stack_image is not None and stack_image.size > 0:
                        stack_amount = self.ocr_engine.extract_money_amount(stack_image)
                        
                        if stack_amount is not None:
                            player_info = {
                                'seat': i,
                                'stack': stack_amount,
                                'active': True
                            }
                            
                            # Extract player name if possible
                            name_region_name = f"{seat_name}_name"
                            if name_region_name in self.extraction_regions:
                                name_region = self.extraction_regions[name_region_name]
                                name_image = self._extract_region_from_image(table_image, name_region.region)
                                
                                if name_image is not None:
                                    name_result = self.ocr_engine.extract_text_multimethod(name_image, 'names')
                                    if name_result.confidence > 0.5:
                                        player_info['name'] = name_result.processed_text
                                        
                                        # Check if this is hero (simple heuristic: seat 6 is often hero in 6-max)
                                        if i == 6 or 'hero' in name_result.processed_text.lower():
                                            hero_stack = stack_amount
                            
                            players.append(player_info)
                            confidences.append(0.7)
            
            # Estimate blinds based on active players (simple heuristic)
            blinds = self._estimate_blinds(players)
            
            return {
                'players': players,
                'hero_stack': hero_stack,
                'blinds': blinds,
                'confidence': sum(confidences) / len(confidences) if confidences else 0.0
            }
            
        except Exception as e:
            logger.debug(f"Player information extraction failed: {e}")
            return None
    
    def _extract_region_from_image(self, full_image: np.ndarray, region: CaptureRegion) -> Optional[np.ndarray]:
        """Extract a specific region from full table image."""
        try:
            if full_image is None or full_image.size == 0:
                return None
            
            # Calculate relative coordinates within the full image
            h, w = full_image.shape[:2]
            
            # For now, assume region coordinates are relative to full image
            # In real implementation, this would handle coordinate transformation
            x1 = max(0, min(region.x, w))
            y1 = max(0, min(region.y, h))
            x2 = max(x1, min(region.x + region.width, w))
            y2 = max(y1, min(region.y + region.height, h))
            
            extracted = full_image[y1:y2, x1:x2]
            return extracted if extracted.size > 0 else None
            
        except Exception as e:
            logger.debug(f"Region extraction failed: {e}")
            return None
    
    def _determine_street(self, board_cards: List[str]) -> str:
        """Determine current betting round based on board cards."""
        num_cards = len(board_cards)
        
        if num_cards == 0:
            return "PREFLOP"
        elif num_cards == 3:
            return "FLOP" 
        elif num_cards == 4:
            return "TURN"
        elif num_cards == 5:
            return "RIVER"
        else:
            return "UNKNOWN"
    
    def _estimate_blinds(self, players: List[Dict]) -> Dict[str, float]:
        """Estimate blind levels based on stack sizes (simple heuristic)."""
        if not players:
            return {"sb": 0.01, "bb": 0.02}
        
        # Simple heuristic: assume blinds are 1/50th of average stack
        avg_stack = sum(p['stack'] for p in players) / len(players)
        bb = round(avg_stack / 50, 2)
        sb = round(bb / 2, 2)
        
        return {"sb": sb, "bb": bb}
    
    def get_extraction_performance(self) -> Dict[str, Any]:
        """Get performance metrics for extraction system."""
        success_rate = self.success_count / self.extraction_count if self.extraction_count > 0 else 0.0
        
        return {
            'total_extractions': self.extraction_count,
            'successful_extractions': self.success_count,
            'success_rate': success_rate,
            'average_extraction_time': self.average_extraction_time,
            'last_extraction': self.last_extraction_time,
            'regions_configured': len(self.extraction_regions) if hasattr(self, 'extraction_regions') else 0
        }
    
    def save_debug_extraction(self, table_state: ExtractedTableState, filename: str = None) -> str:
        """Save debug information for extraction analysis."""
        try:
            if filename is None:
                filename = f"extraction_debug_{int(time.time())}.json"
            
            debug_data = {
                'timestamp': table_state.timestamp,
                'extracted_state': asdict(table_state),
                'performance_metrics': self.get_extraction_performance(),
                'regions_configured': list(self.extraction_regions.keys()) if hasattr(self, 'extraction_regions') else []
            }
            
            with open(filename, 'w') as f:
                json.dump(debug_data, f, indent=2, default=str)
            
            return f"Debug extraction saved to {filename}"
            
        except Exception as e:
            return f"Failed to save debug extraction: {e}"

# Test function
async def test_complete_extraction():
    """Test the complete table state extraction system."""
    print("Testing Complete Table State Extractor...")
    
    extractor = CompleteTableStateExtractor()
    
    # Initialize
    if not await extractor.initialize():
        print("❌ Failed to initialize extractor")
        return
    
    print("✅ Extractor initialized successfully")
    
    # Test extraction
    extracted_state = await extractor.extract_complete_table_state()
    
    if extracted_state:
        print(f"✅ Extraction successful:")
        print(f"  Confidence: {extracted_state.extraction_confidence:.2f}")
        print(f"  Pot: ${extracted_state.pot_size}")
        print(f"  Hero cards: {extracted_state.hero_cards}")
        print(f"  Board cards: {extracted_state.board_cards}")
        print(f"  Street: {extracted_state.current_street}")
        print(f"  My turn: {extracted_state.is_hero_turn}")
        print(f"  Active players: {len(extracted_state.active_players)}")
        
        if extracted_state.errors:
            print(f"  Errors: {extracted_state.errors}")
    else:
        print("❌ Extraction failed")
    
    # Performance metrics
    performance = extractor.get_extraction_performance()
    print(f"\nPerformance:")
    print(f"  Success rate: {performance['success_rate']:.1%}")
    print(f"  Average time: {performance['average_extraction_time']:.3f}s")

if __name__ == "__main__":
    asyncio.run(test_complete_extraction())