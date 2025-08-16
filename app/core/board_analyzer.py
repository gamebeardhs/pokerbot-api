"""Board texture analysis for GTO decision making."""

import logging
from typing import List, Dict, Tuple, Set
from collections import Counter
from app.api.models import BoardTexture

logger = logging.getLogger(__name__)


class BoardAnalyzer:
    """Analyzes board textures for strategic implications."""
    
    # Card ranks (2=0, 3=1, ..., A=12)
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a']
    SUITS = ['h', 'd', 'c', 's']
    
    def __init__(self):
        """Initialize board analyzer."""
        pass
    
    def analyze_board(self, board: List[str]) -> BoardTexture:
        """
        Comprehensive board texture analysis.
        
        Args:
            board: List of board cards like ['7h', '2s', '2d']
            
        Returns:
            BoardTexture object with complete analysis
        """
        if not board:
            return BoardTexture()
            
        try:
            # Parse board cards
            ranks, suits = self._parse_board(board)
            
            # Analyze texture components
            paired = self._is_paired(ranks)
            trips = self._is_trips(ranks)
            quads = self._is_quads(ranks)
            flush_possible = self._is_flush_possible(suits)
            straight_possible = self._is_straight_possible(ranks)
            
            # Calculate composite scores
            wetness_score = self._calculate_wetness(ranks, suits, straight_possible, flush_possible)
            connectivity_score = self._calculate_connectivity(ranks)
            high_card_score = self._calculate_high_card_score(ranks)
            draw_heavy = self._is_draw_heavy(ranks, suits)
            
            return BoardTexture(
                paired=paired,
                trips=trips,
                quads=quads,
                flush_possible=flush_possible,
                straight_possible=straight_possible,
                wetness_score=wetness_score,
                connectivity_score=connectivity_score,
                high_card_score=high_card_score,
                draw_heavy=draw_heavy
            )
            
        except Exception as e:
            logger.error(f"Board analysis failed: {e}")
            return BoardTexture()
    
    def _parse_board(self, board: List[str]) -> Tuple[List[int], List[int]]:
        """Parse board cards into ranks and suits."""
        ranks = []
        suits = []
        
        for card in board:
            if len(card) != 2:
                continue
                
            rank_char = card[0].lower()
            suit_char = card[1].lower()
            
            if rank_char in self.RANKS and suit_char in self.SUITS:
                ranks.append(self.RANKS.index(rank_char))
                suits.append(self.SUITS.index(suit_char))
        
        return ranks, suits
    
    def _is_paired(self, ranks: List[int]) -> bool:
        """Check if board is paired."""
        rank_counts = Counter(ranks)
        return max(rank_counts.values()) >= 2
    
    def _is_trips(self, ranks: List[int]) -> bool:
        """Check if board has trips."""
        rank_counts = Counter(ranks)
        return max(rank_counts.values()) >= 3
    
    def _is_quads(self, ranks: List[int]) -> bool:
        """Check if board has quads."""
        rank_counts = Counter(ranks)
        return max(rank_counts.values()) >= 4
    
    def _is_flush_possible(self, suits: List[int]) -> bool:
        """Check if flush is possible on board."""
        if len(suits) < 3:
            return False
        suit_counts = Counter(suits)
        return max(suit_counts.values()) >= 3
    
    def _is_straight_possible(self, ranks: List[int]) -> bool:
        """Check if straight is possible."""
        if len(ranks) < 3:
            return False
            
        unique_ranks = sorted(set(ranks))
        
        # Check for normal straights
        for i in range(len(unique_ranks) - 2):
            if len(unique_ranks) >= i + 3:
                span = unique_ranks[i + 2] - unique_ranks[i]
                if span <= 4:  # 3 cards within 5 rank span
                    return True
        
        # Check for wheel possibilities (A,2,3,4,5)
        if 12 in unique_ranks:  # Ace present
            low_ranks = [r for r in unique_ranks if r <= 3]
            if len(low_ranks) >= 2:
                return True
        
        return False
    
    def _calculate_wetness(self, ranks: List[int], suits: List[int], 
                          straight_possible: bool, flush_possible: bool) -> float:
        """
        Calculate board wetness score (0-1).
        Higher score = more draws/action possible.
        """
        wetness = 0.0
        
        # Flush draws add wetness
        if flush_possible:
            suit_counts = Counter(suits)
            max_suit = max(suit_counts.values())
            if max_suit == 3:
                wetness += 0.4  # Flush draw
            elif max_suit == 4:
                wetness += 0.6  # Strong flush draw
        
        # Straight draws add wetness
        if straight_possible:
            wetness += 0.3
        
        # Connected boards are wetter
        if len(ranks) >= 3:
            unique_ranks = sorted(set(ranks))
            gaps = []
            for i in range(len(unique_ranks) - 1):
                gaps.append(unique_ranks[i + 1] - unique_ranks[i])
            
            avg_gap = sum(gaps) / len(gaps) if gaps else 5
            if avg_gap <= 2:
                wetness += 0.2  # Very connected
            elif avg_gap <= 3:
                wetness += 0.1  # Somewhat connected
        
        # Multiple suits add wetness
        unique_suits = len(set(suits))
        if unique_suits >= 3:
            wetness += 0.1
        
        return min(1.0, wetness)
    
    def _calculate_connectivity(self, ranks: List[int]) -> float:
        """Calculate board connectivity (0-1)."""
        if len(ranks) < 2:
            return 0.0
        
        unique_ranks = sorted(set(ranks))
        if len(unique_ranks) == 1:
            return 0.0
        
        # Calculate average gap between cards
        gaps = []
        for i in range(len(unique_ranks) - 1):
            gaps.append(unique_ranks[i + 1] - unique_ranks[i])
        
        avg_gap = sum(gaps) / len(gaps)
        
        # Convert to connectivity score
        if avg_gap <= 1:
            return 1.0  # Very connected (like 678)
        elif avg_gap <= 2:
            return 0.8  # Connected (like 579)
        elif avg_gap <= 3:
            return 0.6  # Somewhat connected
        elif avg_gap <= 4:
            return 0.4  # Gapped
        else:
            return 0.2  # Very gapped (like A72)
    
    def _calculate_high_card_score(self, ranks: List[int]) -> float:
        """Calculate high card presence (0-1)."""
        if not ranks:
            return 0.0
        
        # Weight cards by rank
        total_weight = 0.0
        for rank in ranks:
            if rank >= 9:  # J, Q, K, A
                total_weight += 1.0
            elif rank >= 7:  # 9, T
                total_weight += 0.6
            elif rank >= 5:  # 7, 8
                total_weight += 0.3
            else:  # 2-6
                total_weight += 0.1
        
        return min(1.0, total_weight / len(ranks))
    
    def _is_draw_heavy(self, ranks: List[int], suits: List[int]) -> bool:
        """Determine if board is draw-heavy."""
        draw_count = 0
        
        # Count flush draws
        if self._is_flush_possible(suits):
            draw_count += 1
        
        # Count straight draws
        if self._is_straight_possible(ranks):
            draw_count += 1
        
        # Connected + flush draw = very draw heavy
        connectivity = self._calculate_connectivity(ranks)
        if connectivity >= 0.8 and self._is_flush_possible(suits):
            draw_count += 1
        
        return draw_count >= 2
    
    def get_board_category(self, board: List[str]) -> str:
        """
        Categorize board for strategy selection.
        
        Returns:
            Board category like 'dry', 'wet', 'paired', 'monotone', etc.
        """
        if not board:
            return 'empty'
            
        texture = self.analyze_board(board)
        
        # Prioritize most important characteristics
        if texture.quads:
            return 'quads'
        elif texture.trips:
            return 'trips'
        elif texture.paired:
            if texture.wetness_score >= 0.6:
                return 'paired_wet'
            else:
                return 'paired_dry'
        elif len(set(card[1] for card in board)) == 1:
            return 'monotone'
        elif texture.flush_possible and texture.straight_possible:
            return 'wet_coordinated'
        elif texture.wetness_score >= 0.7:
            return 'very_wet'
        elif texture.wetness_score >= 0.4:
            return 'wet'
        elif texture.connectivity_score >= 0.8:
            return 'connected'
        elif texture.high_card_score >= 0.8:
            return 'high_card'
        else:
            return 'dry'
    
    def get_range_interaction(self, board: List[str], position: str) -> Dict[str, float]:
        """
        Analyze how different positional ranges interact with board.
        
        Returns:
            Dictionary with interaction scores for different range types
        """
        texture = self.analyze_board(board)
        
        # Base interaction scores
        interaction = {
            'value_hands': 0.5,      # Strong made hands
            'draws': 0.5,            # Drawing hands  
            'air': 0.5,              # Bluffs/air
            'bluff_catchers': 0.5    # Medium strength hands
        }
        
        # Adjust based on board texture
        if texture.paired:
            interaction['value_hands'] += 0.2  # Sets become more valuable
            interaction['bluff_catchers'] -= 0.1  # Harder to call with weak pairs
        
        if texture.draw_heavy:
            interaction['draws'] += 0.3  # More draw value
            interaction['air'] += 0.2   # More bluffing opportunities
            interaction['value_hands'] += 0.1  # Need to bet for protection
        
        if texture.high_card_score >= 0.8:
            if position in ['BTN', 'CO', 'HJ']:  # Late position
                interaction['air'] += 0.2  # Better for bluffing
            else:  # Early position
                interaction['value_hands'] += 0.1  # Tighter value range
        
        # Normalize scores
        for key in interaction:
            interaction[key] = max(0.0, min(1.0, interaction[key]))
        
        return interaction