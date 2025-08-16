"""Poker hand evaluation for equity calculation."""

import itertools
from typing import List, Tuple, Dict
from collections import Counter

class HandEvaluator:
    """Evaluates poker hands and calculates equity."""
    
    # Card ranks (2=0, 3=1, ..., A=12)
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'j', 'q', 'k', 'a']
    SUITS = ['h', 'd', 'c', 's']
    
    # Hand rankings (higher number = better hand)
    HAND_RANKINGS = {
        'high_card': 1,
        'pair': 2, 
        'two_pair': 3,
        'three_of_a_kind': 4,
        'straight': 5,
        'flush': 6,
        'full_house': 7,
        'four_of_a_kind': 8,
        'straight_flush': 9,
        'royal_flush': 10
    }
    
    def __init__(self):
        """Initialize hand evaluator."""
        pass
    
    def card_to_int(self, card_str: str) -> int:
        """Convert card string like 'ah' to integer representation."""
        if len(card_str) != 2:
            return 0
        rank_char = card_str[0].lower()
        suit_char = card_str[1].lower()
        
        try:
            rank = self.RANKS.index(rank_char)
            suit = self.SUITS.index(suit_char)
            return rank * 4 + suit
        except ValueError:
            return 0
    
    def int_to_card(self, card_int: int) -> str:
        """Convert integer back to card string."""
        if card_int < 0 or card_int >= 52:
            return ""
        rank = card_int // 4
        suit = card_int % 4
        return self.RANKS[rank] + self.SUITS[suit]
    
    def evaluate_hand(self, cards: List[str]) -> Tuple[int, List[int]]:
        """
        Evaluate poker hand and return (hand_rank, kickers).
        
        Args:
            cards: List of card strings like ['ah', 'kd', 'qh', 'jc', 'th']
            
        Returns:
            Tuple of (hand_rank, kickers) where higher rank = better hand
        """
        if len(cards) < 5:
            return (0, [])
            
        # Convert to integers and get ranks/suits
        card_ints = [self.card_to_int(c) for c in cards if c]
        ranks = [c // 4 for c in card_ints]
        suits = [c % 4 for c in card_ints]
        
        # Count ranks
        rank_counts = Counter(ranks)
        sorted_ranks = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        
        # Check for flush
        suit_counts = Counter(suits)
        is_flush = max(suit_counts.values()) >= 5
        
        # Check for straight
        unique_ranks = sorted(set(ranks), reverse=True)
        is_straight, straight_high = self._check_straight(unique_ranks)
        
        # Determine hand type
        if is_straight and is_flush:
            if straight_high == 12:  # Ace high straight flush
                return (self.HAND_RANKINGS['royal_flush'], [12])
            else:
                return (self.HAND_RANKINGS['straight_flush'], [straight_high])
        
        # Four of a kind
        if sorted_ranks[0][1] == 4:
            return (self.HAND_RANKINGS['four_of_a_kind'], 
                   [sorted_ranks[0][0], sorted_ranks[1][0]])
        
        # Full house
        if sorted_ranks[0][1] == 3 and sorted_ranks[1][1] >= 2:
            return (self.HAND_RANKINGS['full_house'], 
                   [sorted_ranks[0][0], sorted_ranks[1][0]])
        
        # Flush
        if is_flush:
            flush_suit = max(suit_counts.keys(), key=lambda k: suit_counts[k])
            flush_cards = [r for r, s in zip(ranks, suits) if s == flush_suit]
            return (self.HAND_RANKINGS['flush'], sorted(flush_cards, reverse=True)[:5])
        
        # Straight
        if is_straight:
            return (self.HAND_RANKINGS['straight'], [straight_high])
        
        # Three of a kind
        if sorted_ranks[0][1] == 3:
            kickers = [r for r, c in sorted_ranks[1:] if c == 1]
            return (self.HAND_RANKINGS['three_of_a_kind'], 
                   [sorted_ranks[0][0]] + sorted(kickers, reverse=True)[:2])
        
        # Two pair
        if sorted_ranks[0][1] == 2 and sorted_ranks[1][1] == 2:
            high_pair = max(sorted_ranks[0][0], sorted_ranks[1][0])
            low_pair = min(sorted_ranks[0][0], sorted_ranks[1][0])
            kicker = next(r for r, c in sorted_ranks if c == 1)
            return (self.HAND_RANKINGS['two_pair'], [high_pair, low_pair, kicker])
        
        # One pair
        if sorted_ranks[0][1] == 2:
            kickers = [r for r, c in sorted_ranks[1:] if c == 1]
            return (self.HAND_RANKINGS['pair'], 
                   [sorted_ranks[0][0]] + sorted(kickers, reverse=True)[:3])
        
        # High card
        return (self.HAND_RANKINGS['high_card'], sorted(ranks, reverse=True)[:5])
    
    def _check_straight(self, ranks: List[int]) -> Tuple[bool, int]:
        """Check for straight and return (is_straight, high_card)."""
        if len(ranks) < 5:
            return False, 0
            
        # Check for normal straight
        for i in range(len(ranks) - 4):
            if ranks[i] - ranks[i + 4] == 4:
                return True, ranks[i]
        
        # Check for wheel straight (A,2,3,4,5)
        if 12 in ranks and 0 in ranks and 1 in ranks and 2 in ranks and 3 in ranks:
            return True, 3  # 5-high straight
            
        return False, 0
    
    def calculate_hand_strength(self, hero_cards: List[str], board_cards: List[str]) -> float:
        """
        Calculate relative hand strength (0.0 to 1.0).
        
        Args:
            hero_cards: Hero's hole cards
            board_cards: Community board cards
            
        Returns:
            Hand strength from 0.0 (worst) to 1.0 (best possible)
        """
        if not hero_cards:
            return 0.0
            
        all_cards = hero_cards + board_cards
        
        if len(all_cards) < 2:
            return 0.0
        
        # For preflop, use preflop hand rankings
        if len(board_cards) == 0:
            return self._preflop_hand_strength(hero_cards)
        
        # Post-flop hand evaluation
        if len(all_cards) < 5:
            # Pad with dummy cards for evaluation
            all_cards += ['2h'] * (5 - len(all_cards))
        
        hand_rank, kickers = self.evaluate_hand(all_cards)
        
        # Normalize to 0-1 scale
        max_possible_rank = self.HAND_RANKINGS['royal_flush']
        base_strength = hand_rank / max_possible_rank
        
        # Add kicker strength
        if kickers:
            kicker_bonus = sum(k for k in kickers[:3]) / (12 * 3)  # Normalize kickers
            base_strength += kicker_bonus * 0.1  # Small bonus for kickers
        
        return min(1.0, base_strength)
    
    def _preflop_hand_strength(self, hero_cards: List[str]) -> float:
        """Calculate preflop hand strength."""
        if len(hero_cards) != 2:
            return 0.0
            
        card1_rank = self.card_to_int(hero_cards[0]) // 4
        card2_rank = self.card_to_int(hero_cards[1]) // 4
        card1_suit = self.card_to_int(hero_cards[0]) % 4
        card2_suit = self.card_to_int(hero_cards[1]) % 4
        
        high_rank = max(card1_rank, card2_rank)
        low_rank = min(card1_rank, card2_rank)
        
        # Pocket pairs
        if card1_rank == card2_rank:
            if high_rank >= 10:  # JJ+
                return 0.9
            elif high_rank >= 7:  # 88+
                return 0.75
            elif high_rank >= 4:  # 55+
                return 0.6
            else:  # 22-44
                return 0.45
        
        # Suited cards
        if card1_suit == card2_suit:
            if high_rank >= 11:  # AK, AQ, etc
                return 0.8
            elif high_rank >= 9 and low_rank >= 8:  # T9s+
                return 0.7
            elif high_rank >= 9 and low_rank >= 6:  # T7s+
                return 0.6
            else:
                return 0.4
        
        # Offsuit cards
        if high_rank >= 11 and low_rank >= 10:  # AK, AQ, KQ
            return 0.75
        elif high_rank >= 11 and low_rank >= 8:  # AJ, AT, KJ, KT
            return 0.6
        elif high_rank >= 10 and low_rank >= 8:  # QJ, QT, JT
            return 0.5
        else:
            return 0.3
    
    def estimate_equity_vs_opponents(
        self, 
        hero_cards: List[str], 
        board_cards: List[str], 
        num_opponents: int
    ) -> float:
        """
        Estimate equity against random opponent hands.
        
        This is a simplified approximation. A full implementation would
        run Monte Carlo simulations.
        """
        hand_strength = self.calculate_hand_strength(hero_cards, board_cards)
        
        # Adjust for number of opponents
        # More opponents = need stronger hand to win
        if num_opponents <= 1:
            return hand_strength
        elif num_opponents == 2:
            return hand_strength * 0.9
        elif num_opponents == 3:
            return hand_strength * 0.8
        elif num_opponents == 4:
            return hand_strength * 0.7
        else:
            return hand_strength * 0.6