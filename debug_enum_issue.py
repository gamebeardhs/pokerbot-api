#!/usr/bin/env python3
"""
Debug the exact numpy enum issue to fix TexasSolver importing
"""

import numpy as np
from app.database.poker_vectorizer import Position, BettingRound

def debug_numpy_enum_issue():
    """Debug the exact cause of the numpy enum error."""
    
    print("🔍 DEBUGGING NUMPY ENUM ISSUE")
    print("=" * 29)
    
    # Test enum creation
    print("Testing enum creation:")
    try:
        pos = Position.BTN
        print(f"✅ Position.BTN created: {pos} (type: {type(pos)})")
        print(f"✅ Position.BTN.name: {pos.name}")
        print(f"✅ Position.BTN.value: {pos.value}")
    except Exception as e:
        print(f"❌ Position enum creation failed: {e}")
    
    # Test numpy choice with enums
    print(f"\nTesting numpy choice with Position enums:")
    try:
        positions = [Position.UTG, Position.MP, Position.CO, Position.BTN, Position.SB, Position.BB]
        probabilities = [0.12, 0.15, 0.18, 0.25, 0.15, 0.15]
        
        # This is the problematic line - numpy.choice with enum objects
        chosen_position = np.random.choice(positions, p=probabilities)
        print(f"✅ Chosen position: {chosen_position} (type: {type(chosen_position)})")
        
        # Test accessing .name attribute
        print(f"✅ Position name: {chosen_position.name}")
        
    except Exception as e:
        print(f"❌ Numpy choice with enums failed: {e}")
    
    # Test the fix - using indices instead
    print(f"\nTesting fix - using indices:")
    try:
        positions = [Position.UTG, Position.MP, Position.CO, Position.BTN, Position.SB, Position.BB]
        probabilities = [0.12, 0.15, 0.18, 0.25, 0.15, 0.15]
        
        # Fixed approach - choose index, then get enum
        position_idx = np.random.choice(len(positions), p=probabilities)
        chosen_position = positions[position_idx]
        
        print(f"✅ Fixed position choice: {chosen_position} (type: {type(chosen_position)})")
        print(f"✅ Position name: {chosen_position.name}")
        print(f"✅ Position value: {chosen_position.value}")
        
    except Exception as e:
        print(f"❌ Fixed approach failed: {e}")
    
    # Test with BettingRound too
    print(f"\nTesting BettingRound enum:")
    try:
        rounds = [BettingRound.PREFLOP, BettingRound.FLOP, BettingRound.TURN, BettingRound.RIVER]
        probabilities = [0.4, 0.35, 0.15, 0.1]
        
        round_idx = np.random.choice(len(rounds), p=probabilities)
        chosen_round = rounds[round_idx]
        
        print(f"✅ Fixed round choice: {chosen_round} (type: {type(chosen_round)})")
        print(f"✅ Round name: {chosen_round.name}")
        print(f"✅ Round value: {chosen_round.value}")
        
    except Exception as e:
        print(f"❌ BettingRound test failed: {e}")

if __name__ == "__main__":
    debug_numpy_enum_issue()