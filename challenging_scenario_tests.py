#!/usr/bin/env python3
"""
Debug the specific list index error in scenario generation
"""

import numpy as np
import json
import random
import traceback
from datetime import datetime
from typing import List, Dict, Any, Tuple

from app.database.poker_vectorizer import Position, BettingRound

def debug_list_index_error():
    """Debug the exact list index error."""
    
    print("🔍 DEBUGGING LIST INDEX ERROR")
    print("=" * 29)
    
    # Test the exact problematic code
    try:
        # Position data that's causing issues
        position_data = [
            (Position.UTG, 0.10),     
            (Position.MP, 0.15),      
            (Position.CO, 0.20),      
            (Position.BTN, 0.30),     
            (Position.SB, 0.12),      
            (Position.BB, 0.13)       
        ]
        
        print(f"Position data length: {len(position_data)}")
        for i, (pos, prob) in enumerate(position_data):
            print(f"  {i}: {pos.name} = {prob}")
        
        # Test numpy choice
        position_idx = np.random.choice(len(position_data),
                                      p=[prob for _, prob in position_data])
        position = position_data[position_idx][0]
        
        print(f"✅ Position selection works: {position.name}")
        
        # Test hand categories
        hand_categories = {
            'premium_pairs': [
                ['As', 'Ah'], ['Ks', 'Kh'], ['Qs', 'Qh']
            ],
            'premium_suited': [
                ['As', 'Ks'], ['As', 'Qs'], ['Ks', 'Qs']
            ]
        }
        
        # Test position-based hand selection
        if position in [Position.UTG, Position.MP]:
            categories = ['premium_pairs', 'premium_suited']
            weights = [0.7, 0.3]
        else:
            categories = ['premium_pairs', 'premium_suited']
            weights = [0.5, 0.5]
        
        print(f"Categories: {categories}")
        print(f"Weights: {weights}")
        print(f"Categories length: {len(categories)}")
        print(f"Weights length: {len(weights)}")
        
        category_idx = np.random.choice(len(categories), p=weights)
        print(f"Category index: {category_idx}")
        
        hand_category = categories[category_idx]
        print(f"Selected category: {hand_category}")
        
        hole_cards = random.choice(hand_categories[hand_category])
        print(f"✅ Hand selection works: {hole_cards}")
        
    except Exception as e:
        print(f"❌ Error found: {e}")
        traceback.print_exc()

def test_minimal_scenario():
    """Test minimal scenario generation."""
    
    print(f"\n🧪 TESTING MINIMAL SCENARIO")
    print("=" * 25)
    
    try:
        # Minimal approach
        positions = [Position.BTN, Position.CO]
        position = random.choice(positions)
        
        betting_rounds = [BettingRound.PREFLOP, BettingRound.FLOP]
        betting_round = random.choice(betting_rounds)
        
        hole_cards = ['As', 'Ks']  # Fixed hand
        board_cards = []
        
        if betting_round == BettingRound.FLOP:
            board_cards = ['Qh', '7c', '2d']
        
        stack_size = 100.0
        pot_size = 5.0
        bet_to_call = 3.0
        
        scenario = {
            'id': 'test_minimal',
            'hole_cards': json.dumps(hole_cards),
            'board_cards': json.dumps(board_cards),
            'position': position.value,
            'pot_size': pot_size,
            'bet_to_call': bet_to_call,
            'stack_size': stack_size,
            'betting_round': betting_round.value,
            'recommendation': 'raise',
            'bet_size': 6.0,
            'equity': 0.75,
            'reasoning': f"Minimal test: raise with {hole_cards}",
            'cfr_confidence': 0.85,
            'metadata': json.dumps({'source': 'minimal_test'})
        }
        
        print(f"✅ Minimal scenario created successfully")
        print(f"   Position: {position.name}")
        print(f"   Round: {betting_round.name}")
        print(f"   Hand: {hole_cards}")
        print(f"   Board: {board_cards}")
        
        return scenario
        
    except Exception as e:
        print(f"❌ Minimal scenario failed: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_list_index_error()
    test_minimal_scenario()