"""Range analysis and range vs range equity calculations."""

import logging
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict, Counter
import itertools
from app.api.models import Position, RangeInfo
from app.core.hand_evaluator import HandEvaluator

logger = logging.getLogger(__name__)


class RangeAnalyzer:
    """Analyzes player ranges and calculates range vs range equity."""
    
    # Standard preflop ranges by position
    PREFLOP_RANGES = {
        Position.UTG: [
            # Ultra-tight UTG range (~8%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo",
            "KQs", "KQo", "KJs"
        ],
        Position.UTG1: [
            # Tight UTG+1 range (~10%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs",
            "KQs", "KQo", "KJs", "KJo", "KTs",
            "QJs", "QTs", "JTs"
        ],
        Position.MP: [
            # Middle position range (~12%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo",
            "KQs", "KQo", "KJs", "KJo", "KTs", "KTo",
            "QJs", "QJo", "QTs", "JTs", "J9s", "T9s", "98s"
        ],
        Position.LJ: [
            # Lojack range (~15%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s",
            "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s",
            "QJs", "QJo", "QTs", "QTo", "Q9s",
            "JTs", "JTo", "J9s", "J8s", "T9s", "T8s", "98s", "97s", "87s"
        ],
        Position.HJ: [
            # Hijack range (~18%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s", "A7s",
            "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "K8s",
            "QJs", "QJo", "QTs", "QTo", "Q9s", "Q8s",
            "JTs", "JTo", "J9s", "J8s", "J7s", "T9s", "T8s", "T7s",
            "98s", "97s", "96s", "87s", "86s", "76s", "65s"
        ],
        Position.CO: [
            # Cutoff range (~22%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A9o", "A8s", "A7s", "A6s", "A5s",
            "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "K9o", "K8s", "K7s",
            "QJs", "QJo", "QTs", "QTo", "Q9s", "Q9o", "Q8s", "Q7s",
            "JTs", "JTo", "J9s", "J9o", "J8s", "J7s", "J6s",
            "T9s", "T9o", "T8s", "T7s", "T6s", "98s", "97s", "96s", "95s",
            "87s", "86s", "85s", "76s", "75s", "65s", "64s", "54s"
        ],
        Position.BTN: [
            # Button range (~28%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A9o", "A8s", "A8o", 
            "A7s", "A7o", "A6s", "A6o", "A5s", "A5o", "A4s", "A3s", "A2s",
            "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "K9o", "K8s", "K8o", "K7s", "K6s", "K5s",
            "QJs", "QJo", "QTs", "QTo", "Q9s", "Q9o", "Q8s", "Q8o", "Q7s", "Q6s",
            "JTs", "JTo", "J9s", "J9o", "J8s", "J8o", "J7s", "J6s", "J5s",
            "T9s", "T9o", "T8s", "T8o", "T7s", "T6s", "T5s", "98s", "98o", "97s", "96s", "95s",
            "87s", "87o", "86s", "85s", "84s", "76s", "75s", "74s", "65s", "64s", "63s", "54s", "53s"
        ],
        Position.SB: [
            # Small blind vs BB (~35%)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A9o", "A8s", "A8o", 
            "A7s", "A7o", "A6s", "A6o", "A5s", "A5o", "A4s", "A4o", "A3s", "A3o", "A2s", "A2o",
            "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "K9o", "K8s", "K8o", "K7s", "K7o", "K6s", "K5s", "K4s",
            "QJs", "QJo", "QTs", "QTo", "Q9s", "Q9o", "Q8s", "Q8o", "Q7s", "Q7o", "Q6s", "Q5s",
            "JTs", "JTo", "J9s", "J9o", "J8s", "J8o", "J7s", "J7o", "J6s", "J5s", "J4s",
            "T9s", "T9o", "T8s", "T8o", "T7s", "T7o", "T6s", "T5s", "T4s",
            "98s", "98o", "97s", "97o", "96s", "95s", "94s", "87s", "87o", "86s", "85s", "84s",
            "76s", "76o", "75s", "74s", "73s", "65s", "64s", "63s", "54s", "53s", "52s", "43s", "42s", "32s"
        ],
        Position.BB: [
            # Big blind vs single raiser (~calling range)
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
            "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "K8s", "K7s", "K6s", "K5s",
            "QJs", "QJo", "QTs", "QTo", "Q9s", "Q8s", "Q7s", "Q6s",
            "JTs", "JTo", "J9s", "J9o", "J8s", "J7s", "J6s",
            "T9s", "T9o", "T8s", "T7s", "T6s", "98s", "98o", "97s", "96s",
            "87s", "87o", "86s", "85s", "76s", "75s", "65s", "64s", "54s"
        ]
    }
    
    def __init__(self):
        """Initialize range analyzer."""
        self.hand_evaluator = HandEvaluator()
        
    def get_preflop_range(self, position: Position, action: str = "open") -> List[str]:
        """
        Get preflop opening range for position.
        
        Args:
            position: Player position
            action: Type of action (open, 3bet, call, etc.)
            
        Returns:
            List of hand combinations
        """
        if action == "open":
            return self.PREFLOP_RANGES.get(position, [])
        elif action == "3bet":
            return self._get_3bet_range(position)
        elif action == "call":
            return self._get_calling_range(position)
        else:
            return self.PREFLOP_RANGES.get(position, [])
    
    def _get_3bet_range(self, position: Position) -> List[str]:
        """Get 3-betting range for position."""
        # Tighter 3-bet ranges (~4-6%)
        if position in [Position.UTG, Position.UTG1, Position.MP]:
            return ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
        elif position in [Position.LJ, Position.HJ]:
            return ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "KQs"]
        elif position == Position.CO:
            return ["AA", "KK", "QQ", "JJ", "TT", "99", "AKs", "AKo", "AQs", "AQo", "AJs", "KQs", "A5s", "A4s"]
        elif position == Position.BTN:
            return ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", 
                   "KQs", "KQo", "KJs", "A5s", "A4s", "A3s", "A2s", "K5s", "Q5s", "J8s", "T8s", "97s"]
        else:  # Blinds
            return ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs",
                   "KQs", "KQo", "KJs", "KJo", "A5s", "A4s", "A3s", "A2s", "54s", "65s", "76s"]
    
    def _get_calling_range(self, position: Position) -> List[str]:
        """Get calling range vs raise for position."""
        # Calling ranges are typically wider than opening ranges
        base_range = self.PREFLOP_RANGES.get(position, [])
        
        # Add speculative hands for calling
        calling_additions = []
        if position in [Position.CO, Position.BTN]:
            calling_additions = ["32s", "42s", "43s", "52s", "53s", "62s", "63s", "72s", "73s", "82s", "83s", "92s"]
        elif position in [Position.SB, Position.BB]:
            calling_additions = ["23s", "24s", "25s", "26s", "27s", "28s", "29s", "34s", "35s", "36s", "37s", "38s", "39s"]
        
        return base_range + calling_additions
    
    def estimate_current_range(self, preflop_range: List[str], board: List[str], 
                              actions: List[str], position: Position) -> List[str]:
        """
        Estimate current range after board and actions.
        
        Args:
            preflop_range: Starting preflop range
            board: Board cards
            actions: Sequence of actions taken
            position: Player position
            
        Returns:
            Updated range after filtering
        """
        current_range = preflop_range.copy()
        
        if not board:
            return current_range
        
        # Filter range based on actions
        for action in actions:
            if action == "fold":
                return []
            elif action == "bet" or action == "raise":
                current_range = self._filter_range_for_aggression(current_range, board)
            elif action == "call":
                current_range = self._filter_range_for_call(current_range, board)
            elif action == "check":
                current_range = self._filter_range_for_check(current_range, board)
        
        return current_range
    
    def _filter_range_for_aggression(self, range_hands: List[str], board: List[str]) -> List[str]:
        """Filter range for betting/raising actions."""
        filtered = []
        
        for hand in range_hands:
            # Convert hand notation to actual cards for evaluation
            hand_cards = self._hand_notation_to_cards(hand)
            if not hand_cards:
                continue
                
            # Evaluate hand strength on this board
            strength = self.hand_evaluator.calculate_hand_strength(hand_cards, board)
            
            # Keep strong hands and some bluffs
            if strength >= 0.6:  # Strong hands always bet
                filtered.append(hand)
            elif strength >= 0.4:  # Medium hands bet sometimes
                if self._should_include_for_semi_bluff(hand, board):
                    filtered.append(hand)
            elif strength <= 0.25:  # Weak hands as bluffs
                if self._should_include_as_bluff(hand, board):
                    filtered.append(hand)
        
        return filtered
    
    def _filter_range_for_call(self, range_hands: List[str], board: List[str]) -> List[str]:
        """Filter range for calling actions."""
        filtered = []
        
        for hand in range_hands:
            hand_cards = self._hand_notation_to_cards(hand)
            if not hand_cards:
                continue
                
            strength = self.hand_evaluator.calculate_hand_strength(hand_cards, board)
            
            # Call with medium to strong hands
            if 0.25 <= strength <= 0.8:  # Calling range
                filtered.append(hand)
            elif strength > 0.8:  # Sometimes slowplay very strong hands
                if hash(hand) % 5 == 0:  # 20% of the time
                    filtered.append(hand)
        
        return filtered
    
    def _filter_range_for_check(self, range_hands: List[str], board: List[str]) -> List[str]:
        """Filter range for checking actions."""
        filtered = []
        
        for hand in range_hands:
            hand_cards = self._hand_notation_to_cards(hand)
            if not hand_cards:
                continue
                
            strength = self.hand_evaluator.calculate_hand_strength(hand_cards, board)
            
            # Check with weak hands, medium hands, and some strong hands
            if strength <= 0.3:  # Weak hands check
                filtered.append(hand)
            elif 0.3 < strength <= 0.65:  # Medium hands check sometimes
                if hash(hand) % 3 != 0:  # 66% of the time
                    filtered.append(hand)
            elif strength > 0.8:  # Slowplay some strong hands
                if hash(hand) % 4 == 0:  # 25% of the time
                    filtered.append(hand)
        
        return filtered
    
    def _hand_notation_to_cards(self, hand: str) -> List[str]:
        """Convert hand notation like 'AKs' to actual cards like ['ah', 'kd']."""
        if len(hand) < 2:
            return []
            
        rank1 = hand[0].lower()
        rank2 = hand[1].lower()
        
        # Determine if suited or offsuit
        if len(hand) == 3:
            if hand[2] == 's':  # Suited
                return [rank1 + 'h', rank2 + 'h']
            elif hand[2] == 'o':  # Offsuit
                return [rank1 + 'h', rank2 + 'd']
        elif len(hand) == 2:  # Pocket pair
            if rank1 == rank2:
                return [rank1 + 'h', rank1 + 'd']
            else:  # Assume offsuit for two different ranks
                return [rank1 + 'h', rank2 + 'd']
        
        return []
    
    def _should_include_for_semi_bluff(self, hand: str, board: List[str]) -> bool:
        """Check if hand should be included as semi-bluff."""
        hand_cards = self._hand_notation_to_cards(hand)
        if not hand_cards:
            return False
            
        # Check for draws
        all_cards = hand_cards + board
        
        # Simplified draw detection
        suits = [card[1] for card in all_cards]
        ranks = [card[0] for card in all_cards]
        
        # Flush draw potential
        suit_counts = Counter(suits)
        has_flush_draw = max(suit_counts.values()) >= 4
        
        # Straight draw potential (simplified)
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 't': 10, 'j': 11, 'q': 12, 'k': 13, 'a': 14}
        rank_nums = [rank_values.get(r, 0) for r in ranks if r in rank_values]
        unique_ranks = sorted(set(rank_nums))
        has_straight_draw = False
        
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i + 3] - unique_ranks[i] <= 5:
                has_straight_draw = True
                break
        
        return has_flush_draw or has_straight_draw
    
    def _should_include_as_bluff(self, hand: str, board: List[str]) -> bool:
        """Check if hand should be included as pure bluff."""
        # Include some weak hands as bluffs (simplified logic)
        return hash(hand + ''.join(board)) % 4 == 0  # 25% of weak hands as bluffs
    
    def calculate_range_equity(self, range1: List[str], range2: List[str], 
                              board: List[str]) -> float:
        """
        Calculate equity of range1 vs range2 on given board.
        
        Args:
            range1: First player's range
            range2: Second player's range  
            board: Board cards
            
        Returns:
            Equity of range1 (0.0 to 1.0)
        """
        if not range1 or not range2:
            return 0.5
            
        total_equity = 0.0
        combinations = 0
        
        # Sample equity calculation (simplified for performance)
        sample_size = min(100, len(range1) * len(range2))
        
        for i, hand1 in enumerate(range1[:10]):  # Limit for performance
            for j, hand2 in enumerate(range2[:10]):
                if combinations >= sample_size:
                    break
                    
                cards1 = self._hand_notation_to_cards(hand1)
                cards2 = self._hand_notation_to_cards(hand2)
                
                if cards1 and cards2:
                    # Check for card conflicts
                    all_cards = cards1 + cards2 + board
                    if len(set(all_cards)) == len(all_cards):  # No conflicts
                        equity = self._calculate_hand_vs_hand_equity(cards1, cards2, board)
                        total_equity += equity
                        combinations += 1
            
            if combinations >= sample_size:
                break
        
        return total_equity / combinations if combinations > 0 else 0.5
    
    def _calculate_hand_vs_hand_equity(self, hand1: List[str], hand2: List[str], 
                                      board: List[str]) -> float:
        """Calculate equity of hand1 vs hand2."""
        # Simplified equity calculation
        strength1 = self.hand_evaluator.calculate_hand_strength(hand1, board)
        strength2 = self.hand_evaluator.calculate_hand_strength(hand2, board)
        
        if strength1 > strength2:
            return 0.8  # Strong advantage
        elif strength1 < strength2:
            return 0.2  # Disadvantage
        else:
            return 0.5  # Roughly equal
    
    def get_range_strength_distribution(self, range_hands: List[str], 
                                       board: List[str]) -> Dict[str, float]:
        """
        Analyze range strength distribution.
        
        Returns:
            Dictionary with percentages of strong/medium/weak hands
        """
        if not range_hands:
            return {"strong": 0.0, "medium": 0.0, "weak": 0.0}
            
        strong_count = 0
        medium_count = 0
        weak_count = 0
        
        for hand in range_hands:
            cards = self._hand_notation_to_cards(hand)
            if cards:
                strength = self.hand_evaluator.calculate_hand_strength(cards, board)
                
                if strength >= 0.65:
                    strong_count += 1
                elif strength >= 0.35:
                    medium_count += 1
                else:
                    weak_count += 1
        
        total = len(range_hands)
        return {
            "strong": strong_count / total if total > 0 else 0.0,
            "medium": medium_count / total if total > 0 else 0.0,
            "weak": weak_count / total if total > 0 else 0.0
        }