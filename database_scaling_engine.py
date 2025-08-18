#!/usr/bin/env python3
"""
Advanced database scaling engine for GTO poker situations.
Implements research-based strategies for optimal coverage and performance.
"""

import sqlite3
import numpy as np
import json
import time
import random
from typing import Dict, List, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import itertools

class Position(Enum):
    UTG = 1
    UTG1 = 2
    MP = 3
    MP1 = 4
    CO = 5
    BTN = 6
    SB = 7
    BB = 8

class BettingRound(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"

@dataclass
class PokerSituation:
    hole_cards: List[str]
    board_cards: List[str]
    position: Position
    pot_size: float
    bet_to_call: float
    stack_size: float
    num_players: int
    betting_round: BettingRound
    
    def to_dict(self) -> Dict:
        return {
            'hole_cards': self.hole_cards,
            'board_cards': self.board_cards,
            'position': self.position.name,
            'pot_size': self.pot_size,
            'bet_to_call': self.bet_to_call,
            'stack_size': self.stack_size,
            'num_players': self.num_players,
            'betting_round': self.betting_round.value
        }

class AdvancedSituationGenerator:
    """Generates poker situations using research-based optimal coverage strategies."""
    
    def __init__(self):
        self.cards = self._generate_deck()
        self.precomputed_ranges = self._load_preflop_ranges()
        self.board_textures = self._generate_board_textures()
        
    def _generate_deck(self) -> List[str]:
        """Generate standard 52-card deck."""
        suits = ['h', 'd', 'c', 's']
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        return [rank + suit for rank in ranks for suit in suits]
    
    def _load_preflop_ranges(self) -> Dict[str, List[Tuple[str, str]]]:
        """Load GTO preflop ranges for different positions."""
        # Research-based preflop ranges (simplified for efficiency)
        ranges = {
            'UTG': [('AA', 'AA'), ('KK', 'KK'), ('QQ', 'QQ'), ('JJ', 'JJ'), ('TT', 'TT'), 
                   ('99', '99'), ('AKs', 'AKs'), ('AKo', 'AKo'), ('AQs', 'AQs'), ('AJs', 'AJs')],
            'MP': [('AA', 'AA'), ('KK', 'KK'), ('QQ', 'QQ'), ('JJ', 'JJ'), ('TT', 'TT'), 
                  ('99', '99'), ('88', '88'), ('77', '77'), ('AKs', 'AKs'), ('AKo', 'AKo'), 
                  ('AQs', 'AQs'), ('AQo', 'AQo'), ('AJs', 'AJs'), ('KQs', 'KQs')],
            'CO': [('AA', 'AA'), ('KK', 'KK'), ('QQ', 'QQ'), ('JJ', 'JJ'), ('TT', 'TT'), 
                  ('99', '99'), ('88', '88'), ('77', '77'), ('66', '66'), ('55', '55'),
                  ('AKs', 'AKs'), ('AKo', 'AKo'), ('AQs', 'AQs'), ('AQo', 'AQo'), ('AJs', 'AJs'),
                  ('AJo', 'AJo'), ('KQs', 'KQs'), ('KQo', 'KQo'), ('KJs', 'KJs')],
            'BTN': [('AA', 'AA'), ('KK', 'KK'), ('QQ', 'QQ'), ('JJ', 'JJ'), ('TT', 'TT'), 
                   ('99', '99'), ('88', '88'), ('77', '77'), ('66', '66'), ('55', '55'),
                   ('44', '44'), ('33', '33'), ('22', '22'), ('AKs', 'AKs'), ('AKo', 'AKo'),
                   ('AQs', 'AQs'), ('AQo', 'AQo'), ('AJs', 'AJs'), ('AJo', 'AJo'), ('ATs', 'ATs'),
                   ('A9s', 'A9s'), ('KQs', 'KQs'), ('KQo', 'KQo'), ('KJs', 'KJs'), ('KJo', 'KJo')],
            'SB': [('AA', 'AA'), ('KK', 'KK'), ('QQ', 'QQ'), ('JJ', 'JJ'), ('TT', 'TT'), 
                  ('99', '99'), ('88', '88'), ('77', '77'), ('66', '66'), ('AKs', 'AKs'),
                  ('AKo', 'AKo'), ('AQs', 'AQs'), ('AQo', 'AQo'), ('AJs', 'AJs'), ('KQs', 'KQs')],
            'BB': [('AA', 'AA'), ('KK', 'KK'), ('QQ', 'QQ'), ('JJ', 'JJ'), ('TT', 'TT'), 
                  ('99', '99'), ('88', '88'), ('77', '77'), ('AKs', 'AKs'), ('AKo', 'AKo'),
                  ('AQs', 'AQs'), ('AJs', 'AJs'), ('KQs', 'KQs'), ('QJs', 'QJs')]
        }
        
        # Convert to actual card pairs
        converted_ranges = {}
        for pos, range_list in ranges.items():
            converted_ranges[pos] = []
            for hand_range in range_list:
                converted_ranges[pos].extend(self._expand_hand_range(hand_range[0]))
        
        return converted_ranges
    
    def _expand_hand_range(self, hand_notation: str) -> List[Tuple[str, str]]:
        """Expand hand notation (e.g., 'AKs') to specific card combinations."""
        if len(hand_notation) == 3 and hand_notation[2] == 's':  # Suited
            rank1, rank2 = hand_notation[0], hand_notation[1]
            return [(rank1 + suit, rank2 + suit) for suit in ['h', 'd', 'c', 's']]
        elif len(hand_notation) == 3 and hand_notation[2] == 'o':  # Offsuit
            rank1, rank2 = hand_notation[0], hand_notation[1]
            combinations = []
            for suit1 in ['h', 'd', 'c', 's']:
                for suit2 in ['h', 'd', 'c', 's']:
                    if suit1 != suit2:
                        combinations.append((rank1 + suit1, rank2 + suit2))
            return combinations
        elif len(hand_notation) == 2 and hand_notation[0] == hand_notation[1]:  # Pairs
            rank = hand_notation[0]
            combinations = []
            for i, suit1 in enumerate(['h', 'd', 'c', 's']):
                for suit2 in ['h', 'd', 'c', 's'][i+1:]:
                    combinations.append((rank + suit1, rank + suit2))
            return combinations
        else:
            return [(hand_notation,)]
    
    def _generate_board_textures(self) -> Dict[str, List[List[str]]]:
        """Generate representative board textures for postflop play."""
        textures = {
            'dry': [
                ['As', '7h', '2c'],  # Rainbow dry
                ['Kd', '8s', '3h'],  # Rainbow dry
                ['Qh', '9c', '4d'],  # Rainbow dry
            ],
            'wet': [
                ['Ah', 'Kh', 'Qd'],  # Two flush draw + straight draw
                ['9h', '8h', '7c'],  # Straight + flush draw
                ['Jd', 'Td', '9s'],  # Open-ended straight draw
            ],
            'paired': [
                ['As', 'Ah', '7c'],  # Paired aces
                ['Kd', 'Ks', '9h'],  # Paired kings
                ['8h', '8c', '3d'],  # Paired eights
            ],
            'monotone': [
                ['Ah', 'Kh', 'Qh'],  # All hearts
                ['Jd', '9d', '6d'],  # All diamonds
                ['Ts', '7s', '4s'],  # All spades
            ]
        }
        return textures
    
    def generate_strategic_situations(self, target_count: int) -> List[PokerSituation]:
        """Generate situations using strategic coverage approach."""
        situations = []
        
        # Distribution strategy based on poker research:
        # - 40% preflop (most frequent decisions)
        # - 35% flop (critical decision point)
        # - 15% turn (refined ranges)
        # - 10% river (final decisions)
        
        distributions = {
            BettingRound.PREFLOP: int(target_count * 0.40),
            BettingRound.FLOP: int(target_count * 0.35),
            BettingRound.TURN: int(target_count * 0.15),
            BettingRound.RIVER: int(target_count * 0.10)
        }
        
        for round_type, count in distributions.items():
            print(f"Generating {count} {round_type.value} situations...")
            
            if round_type == BettingRound.PREFLOP:
                situations.extend(self._generate_preflop_situations(count))
            else:
                situations.extend(self._generate_postflop_situations(round_type, count))
            
            if len(situations) >= target_count:
                break
        
        # Ensure we don't exceed target
        return situations[:target_count]
    
    def _generate_preflop_situations(self, count: int) -> List[PokerSituation]:
        """Generate preflop situations based on positional ranges."""
        situations = []
        positions = list(Position)
        
        for _ in range(count):
            position = random.choice(positions)
            num_players = random.choice([6, 9])  # 6-max or full ring
            
            # Select cards from position-appropriate range
            if position.name in self.precomputed_ranges:
                hole_cards = random.choice(self.precomputed_ranges[position.name])
            else:
                # Fallback to random cards
                hole_cards = random.sample(self.cards, 2)
            
            # Generate realistic betting scenarios
            pot_size = random.choice([3.0, 4.5, 6.0, 9.0, 12.0])  # Based on blinds
            bet_to_call = self._generate_realistic_bet(pot_size, "preflop")
            stack_size = random.uniform(75, 200)  # Realistic stack sizes
            
            situation = PokerSituation(
                hole_cards=list(hole_cards) if isinstance(hole_cards, tuple) else hole_cards,
                board_cards=[],
                position=position,
                pot_size=pot_size,
                bet_to_call=bet_to_call,
                stack_size=stack_size,
                num_players=num_players,
                betting_round=BettingRound.PREFLOP
            )
            situations.append(situation)
        
        return situations
    
    def _generate_postflop_situations(self, round_type: BettingRound, count: int) -> List[PokerSituation]:
        """Generate postflop situations with strategic board textures."""
        situations = []
        
        for _ in range(count):
            # Select board texture strategically
            texture_type = random.choice(['dry', 'wet', 'paired', 'monotone'])
            base_board = random.choice(self.board_textures[texture_type])
            
            # Extend board for turn/river
            board = base_board.copy()
            remaining_cards = [c for c in self.cards if c not in board]
            
            if round_type in [BettingRound.TURN, BettingRound.RIVER]:
                board.append(random.choice(remaining_cards))
                remaining_cards.remove(board[-1])
                
            if round_type == BettingRound.RIVER:
                board.append(random.choice(remaining_cards))
                remaining_cards.remove(board[-1])
            
            # Select hole cards that don't conflict with board
            hole_cards = random.sample(remaining_cards, 2)
            
            # Generate position and betting
            position = random.choice(list(Position))
            num_players = random.choice([2, 3, 4, 6])  # Postflop player counts
            
            # Escalating pot sizes for later streets
            base_pot = random.uniform(15, 50)
            if round_type == BettingRound.TURN:
                base_pot *= random.uniform(1.5, 2.5)
            elif round_type == BettingRound.RIVER:
                base_pot *= random.uniform(2.0, 4.0)
            
            pot_size = round(base_pot, 1)
            bet_to_call = self._generate_realistic_bet(pot_size, round_type.value)
            stack_size = random.uniform(pot_size * 2, pot_size * 8)  # Realistic SPR
            
            situation = PokerSituation(
                hole_cards=hole_cards,
                board_cards=board,
                position=position,
                pot_size=pot_size,
                bet_to_call=bet_to_call,
                stack_size=stack_size,
                num_players=num_players,
                betting_round=round_type
            )
            situations.append(situation)
        
        return situations
    
    def _generate_realistic_bet(self, pot_size: float, street: str) -> float:
        """Generate realistic bet sizes based on street and pot size."""
        if street == "preflop":
            # Preflop: 2-4x BB raises, 3-bets, etc.
            options = [0, 2.0, 3.0, 4.0, 6.0, 9.0, 12.0]
            return random.choice(options)
        else:
            # Postflop: percentage-based betting
            bet_percentages = [0, 0.25, 0.33, 0.5, 0.66, 0.75, 1.0, 1.5]
            percentage = random.choice(bet_percentages)
            return round(pot_size * percentage, 1)

def scale_database_to_target(target_size: int = 10000):
    """Scale the GTO database to target size with optimal coverage."""
    print(f"🚀 SCALING DATABASE TO {target_size:,} SITUATIONS")
    print("=" * 60)
    
    # Check current database size
    db_path = Path("gto_database.db")
    current_count = 0
    
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM gto_situations")
            current_count = cursor.fetchone()[0]
    
    print(f"Current database size: {current_count:,} situations")
    
    if current_count >= target_size:
        print(f"✅ Database already at or above target size")
        return
    
    needed = target_size - current_count
    print(f"Generating {needed:,} new situations...")
    
    # Initialize advanced generator
    generator = AdvancedSituationGenerator()
    
    # Generate situations in batches for memory efficiency
    batch_size = 1000
    total_generated = 0
    
    start_time = time.time()
    
    while total_generated < needed:
        current_batch_size = min(batch_size, needed - total_generated)
        
        print(f"Generating batch {total_generated//batch_size + 1} ({current_batch_size} situations)...")
        
        # Generate strategic situations
        situations = generator.generate_strategic_situations(current_batch_size)
        
        # Send to database population endpoint
        success_count = 0
        for situation in situations:
            try:
                import requests
                response = requests.post(
                    "http://localhost:5000/database/add-situation",
                    json=situation.to_dict(),
                    timeout=10
                )
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"   Warning: Failed to add situation: {e}")
                continue
        
        total_generated += success_count
        elapsed = time.time() - start_time
        rate = total_generated / elapsed if elapsed > 0 else 0
        
        print(f"   Added {success_count}/{current_batch_size} situations")
        print(f"   Progress: {total_generated:,}/{needed:,} ({total_generated/needed*100:.1f}%)")
        print(f"   Rate: {rate:.1f} situations/second")
        print(f"   ETA: {(needed-total_generated)/rate/60:.1f} minutes")
        
        if success_count < current_batch_size * 0.5:  # If less than 50% success
            print("   ⚠️ Low success rate, pausing...")
            time.sleep(2)
    
    total_time = time.time() - start_time
    print(f"\n🎯 SCALING COMPLETE")
    print(f"   Added: {total_generated:,} situations")
    print(f"   Total time: {total_time:.1f} seconds")
    print(f"   Final size: {current_count + total_generated:,} situations")
    print(f"   Coverage improvement: {((current_count + total_generated)/229671*100):.2f}%")

if __name__ == "__main__":
    scale_database_to_target(10000)