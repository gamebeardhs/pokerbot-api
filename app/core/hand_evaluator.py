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
            
        # For preflop, use preflop hand rankings
        if len(board_cards) == 0:
            return self._preflop_hand_strength(hero_cards)
        
        # Post-flop evaluation
        all_cards = hero_cards + board_cards
        
        if len(all_cards) < 5:
            # For incomplete boards, evaluate made hand + draw potential
            return self._evaluate_incomplete_hand(hero_cards, board_cards)
        
        # Complete 5+ card evaluation
        hand_rank, kickers = self.evaluate_hand(all_cards)
        
        # Convert to realistic hand strength
        return self._convert_rank_to_strength(hand_rank, kickers, all_cards)
    
    def _evaluate_incomplete_hand(self, hero_cards: List[str], board_cards: List[str]) -> float:
        """Evaluate hand strength on flop/turn."""
        all_cards = hero_cards + board_cards
        
        # Pad to 5 cards for evaluation
        padded_cards = all_cards + ['2h'] * (5 - len(all_cards))
        hand_rank, kickers = self.evaluate_hand(padded_cards)
        
        return self._convert_rank_to_strength(hand_rank, kickers, all_cards)
    
    def _convert_rank_to_strength(self, hand_rank: int, kickers: List[int], all_cards: List[str]) -> float:
        """Convert hand rank to realistic strength."""
        # Much more realistic strength mappings
        if hand_rank >= self.HAND_RANKINGS['straight_flush']:
            return 0.98  # Near nuts
        elif hand_rank >= self.HAND_RANKINGS['four_of_a_kind']:
            return 0.95  # Quads
        elif hand_rank >= self.HAND_RANKINGS['full_house']:
            return 0.90  # Full house
        elif hand_rank >= self.HAND_RANKINGS['flush']:
            return 0.75  # Flush
        elif hand_rank >= self.HAND_RANKINGS['straight']:
            return 0.70  # Straight
        elif hand_rank >= self.HAND_RANKINGS['three_of_a_kind']:
            # Sets are very strong
            return 0.85 if self._is_set(all_cards) else 0.65
        elif hand_rank >= self.HAND_RANKINGS['two_pair']:
            return 0.55  # Two pair
        elif hand_rank >= self.HAND_RANKINGS['pair']:
            # Evaluate pair strength
            return self._evaluate_pair_strength(kickers[0] if kickers else 0, all_cards)
        else:
            return 0.15  # High card
    
    def _is_set(self, all_cards: List[str]) -> bool:
        """Check if we have a set (pocket pair + board card)."""
        if len(all_cards) < 3:
            return False
        
        hero_cards = all_cards[:2]
        board_cards = all_cards[2:]
        
        if len(hero_cards) != 2:
            return False
            
        # Check if hole cards are a pair
        hero_rank1 = self.card_to_int(hero_cards[0]) // 4
        hero_rank2 = self.card_to_int(hero_cards[1]) // 4
        
        if hero_rank1 != hero_rank2:
            return False
            
        # Check if board has matching rank
        for board_card in board_cards:
            board_rank = self.card_to_int(board_card) // 4
            if board_rank == hero_rank1:
                return True
        return False
    
    def _evaluate_pair_strength(self, pair_rank: int, all_cards: List[str]) -> float:
        """Evaluate strength of pair based on rank and position."""
        if pair_rank >= 10:  # JJ+
            return 0.65
        elif pair_rank >= 7:  # 88+
            return 0.50
        elif pair_rank >= 4:  # 55+
            return 0.35
        else:  # Low pairs
            return 0.25
    
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
        Estimate equity against random opponent hands using realistic poker equity.
        """
        if not hero_cards:
            return 0.0
            
        # Get made hand strength and draw potential
        made_hand_strength = self._evaluate_made_hand_equity(hero_cards, board_cards)
        draw_equity = self._evaluate_draw_equity(hero_cards, board_cards) if len(board_cards) < 5 else 0
        
        total_equity = made_hand_strength + draw_equity
        
        # Adjust for number of opponents (less aggressive reduction)
        if num_opponents <= 1:
            return min(0.95, total_equity)
        elif num_opponents == 2:
            return min(0.90, total_equity * 0.95)
        elif num_opponents == 3:
            return min(0.85, total_equity * 0.90)
        elif num_opponents == 4:
            return min(0.80, total_equity * 0.85)
        else:
            return min(0.75, total_equity * 0.80)
    
    def _evaluate_made_hand_equity(self, hero_cards: List[str], board_cards: List[str]) -> float:
        """Evaluate current made hand equity."""
        return self.calculate_hand_strength(hero_cards, board_cards)
    
    def _evaluate_draw_equity(self, hero_cards: List[str], board_cards: List[str]) -> float:
        """Calculate equity from drawing hands."""
        if len(board_cards) == 0:  # Preflop
            return 0.0
            
        draw_equity = 0.0
        
        # Check for flush draws
        flush_outs = self._count_flush_outs(hero_cards, board_cards)
        if flush_outs >= 9:  # Nut flush draw
            draw_equity += 0.35
        elif flush_outs >= 8:  # Good flush draw
            draw_equity += 0.30
        elif flush_outs >= 6:  # Weak flush draw
            draw_equity += 0.25
        
        # Check for straight draws
        straight_outs = self._count_straight_outs(hero_cards, board_cards)
        if straight_outs >= 8:  # Open-ended
            draw_equity += 0.30
        elif straight_outs >= 4:  # Gutshot
            draw_equity += 0.15
        
        # Overcard equity
        overcard_outs = self._count_overcard_outs(hero_cards, board_cards)
        if overcard_outs >= 6:  # Two overcards
            draw_equity += 0.20
        elif overcard_outs >= 3:  # One overcard
            draw_equity += 0.10
        
        return min(0.40, draw_equity)  # Cap draw equity
    
    def _count_flush_outs(self, hero_cards: List[str], board_cards: List[str]) -> int:
        """Count flush outs."""
        all_cards = hero_cards + board_cards
        suits = [self.card_to_int(card) % 4 for card in all_cards if card]
        
        suit_counts = Counter(suits)
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        
        if max_suit_count >= 4:
            return 13 - max_suit_count  # Remaining cards of that suit
        return 0
    
    def _count_straight_outs(self, hero_cards: List[str], board_cards: List[str]) -> int:
        """Count straight outs (simplified)."""
        # This is a simplified implementation
        # Real implementation would check all possible straights
        all_cards = hero_cards + board_cards
        ranks = [self.card_to_int(card) // 4 for card in all_cards if card]
        unique_ranks = sorted(set(ranks))
        
        # Look for 4-card straight draws
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] == 3:
                return 8  # Open-ended
            elif unique_ranks[i+2] - unique_ranks[i] == 2:
                return 4  # Gutshot
        
        return 0
    
    def _count_overcard_outs(self, hero_cards: List[str], board_cards: List[str]) -> int:
        """Count overcard outs."""
        if not board_cards:
            return 0
            
        hero_ranks = [self.card_to_int(card) // 4 for card in hero_cards if card]
        board_ranks = [self.card_to_int(card) // 4 for card in board_cards if card]
        
        if not board_ranks:
            return 0
            
        board_high = max(board_ranks)
        overcard_count = sum(1 for rank in hero_ranks if rank > board_high)
        
        return overcard_count * 3  # 3 outs per overcard