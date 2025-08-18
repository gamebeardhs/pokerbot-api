"""
Poker Situation Vectorization System
Converts poker game states into numerical vectors for similarity matching.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from enum import IntEnum

logger = logging.getLogger(__name__)

class Position(IntEnum):
    UTG = 0
    UTG1 = 1
    MP = 2
    MP1 = 3
    MP2 = 4
    CO = 5
    BTN = 6
    SB = 7
    BB = 8

class BettingRound(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3

@dataclass
class PokerSituation:
    """Complete poker situation for vectorization."""
    hole_cards: List[str]  # e.g., ['As', 'Kh']
    board_cards: List[str]  # e.g., ['Qd', 'Jc', '9s']
    position: Position
    pot_size: float
    bet_to_call: float
    stack_size: float
    num_players: int
    betting_round: BettingRound
    num_callers: int = 0
    num_raisers: int = 0
    opponent_actions: List[str] = None

class PokerVectorizer:
    """Converts poker situations into numerical vectors for similarity search."""
    
    def __init__(self):
        self.dimension = 32  # Total vector dimension
        self.suits = {'s': 1, 'h': 2, 'd': 3, 'c': 4}
        self.ranks = {
            'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
            '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2
        }
        
    def vectorize_situation(self, situation: PokerSituation) -> np.ndarray:
        """Convert poker situation to 32-dimensional vector."""
        vector = np.zeros(32, dtype=np.float32)
        
        # Hand features (6 dimensions)
        hand_vector = self._vectorize_hand(situation.hole_cards)
        vector[0:6] = hand_vector
        
        # Board features (10 dimensions for flop+turn+river)
        board_vector = self._vectorize_board(situation.board_cards)
        vector[6:16] = board_vector
        
        # Position features (4 dimensions)
        pos_vector = self._vectorize_position(situation.position, situation.num_players)
        vector[16:20] = pos_vector
        
        # Betting features (8 dimensions)
        betting_vector = self._vectorize_betting(
            situation.pot_size, situation.bet_to_call, situation.stack_size,
            situation.num_callers, situation.num_raisers
        )
        vector[20:28] = betting_vector
        
        # Game state features (4 dimensions)
        state_vector = self._vectorize_game_state(
            situation.betting_round, situation.num_players
        )
        vector[28:32] = state_vector
        
        return vector
    
    def _vectorize_hand(self, hole_cards: List[str]) -> np.ndarray:
        """Convert hole cards to 6-dimensional vector."""
        vector = np.zeros(6, dtype=np.float32)
        
        if len(hole_cards) != 2:
            return vector
            
        card1, card2 = hole_cards[0], hole_cards[1]
        
        # Extract ranks and suits
        rank1, suit1 = self.ranks.get(card1[0], 2), self.suits.get(card1[1], 1)
        rank2, suit2 = self.ranks.get(card2[0], 2), self.suits.get(card2[1], 1)
        
        # Normalize ranks to 0-1
        vector[0] = rank1 / 14.0
        vector[1] = rank2 / 14.0
        
        # Hand strength indicators
        vector[2] = 1.0 if rank1 == rank2 else 0.0  # pocket pair
        vector[3] = 1.0 if suit1 == suit2 else 0.0  # suited
        vector[4] = abs(rank1 - rank2) / 14.0  # gap size
        vector[5] = max(rank1, rank2) / 14.0  # high card strength
        
        return vector
    
    def _vectorize_board(self, board_cards: List[str]) -> np.ndarray:
        """Convert board cards to 10-dimensional vector."""
        vector = np.zeros(10, dtype=np.float32)
        
        if not board_cards:
            return vector  # preflop
            
        # Basic board info
        vector[0] = len(board_cards) / 5.0  # board completion
        
        # Extract ranks and suits
        ranks = []
        suits = []
        for card in board_cards:
            if len(card) >= 2:
                ranks.append(self.ranks.get(card[0], 2))
                suits.append(self.suits.get(card[1], 1))
        
        if ranks:
            # Board texture features
            vector[1] = len(set(ranks)) / len(ranks)  # rank diversity
            vector[2] = len(set(suits)) / len(suits)  # suit diversity
            vector[3] = max(ranks) / 14.0  # highest card
            vector[4] = min(ranks) / 14.0  # lowest card
            
            # Advanced texture analysis
            if len(ranks) >= 3:
                sorted_ranks = sorted(ranks, reverse=True)
                vector[5] = self._check_straight_draw(sorted_ranks)
                vector[6] = self._check_flush_draw(suits)
                vector[7] = 1.0 if len(set(ranks)) != len(ranks) else 0.0  # paired board
                vector[8] = sum(1 for r in ranks if r >= 10) / len(ranks)  # broadway cards
                vector[9] = sum(1 for r in ranks if r <= 6) / len(ranks)  # low cards
        
        return vector
    
    def _vectorize_position(self, position: Position, num_players: int) -> np.ndarray:
        """Convert position to 4-dimensional vector."""
        vector = np.zeros(4, dtype=np.float32)
        
        vector[0] = position.value / 8.0  # normalized position
        vector[1] = 1.0 if position == Position.BTN else 0.0  # button
        vector[2] = 1.0 if position in [Position.SB, Position.BB] else 0.0  # blinds
        vector[3] = (8 - position.value) / 8.0  # players to act after
        
        return vector
    
    def _vectorize_betting(self, pot_size: float, bet_to_call: float, 
                          stack_size: float, num_callers: int, num_raisers: int) -> np.ndarray:
        """Convert betting info to 8-dimensional vector."""
        vector = np.zeros(8, dtype=np.float32)
        
        # Normalize betting amounts (assuming big blind = 1.0)
        vector[0] = min(pot_size / 100.0, 1.0)  # normalized pot size
        vector[1] = min(bet_to_call / 20.0, 1.0)  # normalized bet size
        
        # Pot odds and SPR
        if pot_size > 0:
            vector[2] = min(bet_to_call / (pot_size + bet_to_call), 1.0)  # pot odds
            vector[3] = min(stack_size / pot_size / 10.0, 1.0)  # SPR (normalized)
        
        # Action indicators
        vector[4] = min(num_callers / 5.0, 1.0)  # number of callers
        vector[5] = min(num_raisers / 3.0, 1.0)  # number of raisers
        vector[6] = min(bet_to_call / stack_size, 1.0) if stack_size > 0 else 0  # bet/stack ratio
        vector[7] = 1.0 if bet_to_call > 0 else 0.0  # facing bet
        
        return vector
    
    def _vectorize_game_state(self, betting_round: BettingRound, num_players: int) -> np.ndarray:
        """Convert game state to 4-dimensional vector."""
        vector = np.zeros(4, dtype=np.float32)
        
        vector[0] = betting_round.value / 3.0  # normalized street
        vector[1] = min(num_players / 9.0, 1.0)  # number of players
        vector[2] = 1.0 if betting_round == BettingRound.PREFLOP else 0.0  # preflop flag
        vector[3] = 1.0 if betting_round == BettingRound.RIVER else 0.0  # river flag
        
        return vector
    
    def _check_straight_draw(self, ranks: List[int]) -> float:
        """Check for straight draw potential (0-1 score)."""
        if len(ranks) < 3:
            return 0.0
            
        # Check for gaps in sequence
        sorted_ranks = sorted(set(ranks), reverse=True)
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(sorted_ranks)):
            if sorted_ranks[i-1] - sorted_ranks[i] == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
                
        return min(max_consecutive / 5.0, 1.0)
    
    def _check_flush_draw(self, suits: List[int]) -> float:
        """Check for flush draw potential (0-1 score)."""
        if len(suits) < 3:
            return 0.0
            
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
            
        max_suit_count = max(suit_counts.values())
        return min(max_suit_count / 5.0, 1.0)

    def create_test_situations(self, count: int = 1000) -> List[Tuple[PokerSituation, np.ndarray]]:
        """Generate test situations for database population."""
        situations = []
        
        # Common preflop scenarios
        for i in range(count // 3):
            situation = self._generate_preflop_situation()
            vector = self.vectorize_situation(situation)
            situations.append((situation, vector))
        
        # Common flop scenarios  
        for i in range(count // 3):
            situation = self._generate_flop_situation()
            vector = self.vectorize_situation(situation)
            situations.append((situation, vector))
            
        # Turn/river scenarios
        for i in range(count - 2 * (count // 3)):
            situation = self._generate_postflop_situation()
            vector = self.vectorize_situation(situation)
            situations.append((situation, vector))
            
        return situations
    
    def _generate_preflop_situation(self) -> PokerSituation:
        """Generate random preflop situation."""
        import random
        
        # Random hole cards
        ranks = list(self.ranks.keys())
        suits = list(self.suits.keys())
        hole_cards = [f"{random.choice(ranks)}{random.choice(suits)}" for _ in range(2)]
        
        return PokerSituation(
            hole_cards=hole_cards,
            board_cards=[],
            position=Position(random.randint(0, 8)),
            pot_size=random.uniform(1.5, 15.0),
            bet_to_call=random.uniform(0, 10.0),
            stack_size=random.uniform(20, 200),
            num_players=random.randint(2, 9),
            betting_round=BettingRound.PREFLOP,
            num_callers=random.randint(0, 3),
            num_raisers=random.randint(0, 2)
        )
    
    def _generate_flop_situation(self) -> PokerSituation:
        """Generate random flop situation."""
        import random
        
        ranks = list(self.ranks.keys())
        suits = list(self.suits.keys())
        hole_cards = [f"{random.choice(ranks)}{random.choice(suits)}" for _ in range(2)]
        board_cards = [f"{random.choice(ranks)}{random.choice(suits)}" for _ in range(3)]
        
        return PokerSituation(
            hole_cards=hole_cards,
            board_cards=board_cards,
            position=Position(random.randint(0, 8)),
            pot_size=random.uniform(3.0, 50.0),
            bet_to_call=random.uniform(0, 25.0),
            stack_size=random.uniform(10, 150),
            num_players=random.randint(2, 6),
            betting_round=BettingRound.FLOP,
            num_callers=random.randint(0, 2),
            num_raisers=random.randint(0, 2)
        )
    
    def _generate_postflop_situation(self) -> PokerSituation:
        """Generate random turn/river situation."""
        import random
        
        ranks = list(self.ranks.keys())
        suits = list(self.suits.keys())
        hole_cards = [f"{random.choice(ranks)}{random.choice(suits)}" for _ in range(2)]
        
        street = random.choice([BettingRound.TURN, BettingRound.RIVER])
        board_size = 4 if street == BettingRound.TURN else 5
        board_cards = [f"{random.choice(ranks)}{random.choice(suits)}" for _ in range(board_size)]
        
        return PokerSituation(
            hole_cards=hole_cards,
            board_cards=board_cards,
            position=Position(random.randint(0, 8)),
            pot_size=random.uniform(10.0, 100.0),
            bet_to_call=random.uniform(0, 50.0),
            stack_size=random.uniform(5, 100),
            num_players=random.randint(2, 4),
            betting_round=street,
            num_callers=random.randint(0, 1),
            num_raisers=random.randint(0, 1)
        )