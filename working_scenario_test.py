#!/usr/bin/env python3
"""
Test a single working scenario generation to verify the fix
"""

import numpy as np
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple

from app.database.poker_vectorizer import Position, BettingRound

def test_single_scenario():
    """Test generating a single scenario with the fixed approach."""
    
    print("🧪 TESTING SINGLE SCENARIO GENERATION")
    print("=" * 35)
    
    try:
        # Fixed enum selection
        positions = [Position.UTG, Position.MP, Position.CO, Position.BTN, Position.SB, Position.BB]
        position_probs = [0.12, 0.15, 0.18, 0.25, 0.15, 0.15]
        position_idx = np.random.choice(len(positions), p=position_probs)
        position = positions[position_idx]
        
        print(f"✅ Position selected: {position.name} (value: {position.value})")
        
        # Fixed betting round selection
        rounds = [BettingRound.PREFLOP, BettingRound.FLOP, BettingRound.TURN, BettingRound.RIVER]
        round_probs = [0.4, 0.35, 0.15, 0.1]
        round_idx = np.random.choice(len(rounds), p=round_probs)
        betting_round = rounds[round_idx]
        
        print(f"✅ Betting round selected: {betting_round.name} (value: {betting_round.value})")
        
        # Generate hand
        premium_hands = [
            ["As", "Ks"], ["As", "Qs"], ["Ks", "Qs"], ["As", "Js"], ["Ks", "Js"]
        ]
        hole_cards = random.choice(premium_hands)
        
        print(f"✅ Hole cards: {hole_cards}")
        
        # Generate board if post-flop
        board_cards = []
        if betting_round >= BettingRound.FLOP:
            dry_boards = [
                ["Ks", "7h", "2c"], ["As", "8d", "3s"], ["Qh", "6c", "2d"]
            ]
            board_cards = random.choice(dry_boards).copy()
            
            if betting_round >= BettingRound.TURN:
                board_cards.append("5h")
                if betting_round == BettingRound.RIVER:
                    board_cards.append("9d")
        
        print(f"✅ Board cards: {board_cards}")
        
        # Generate stack sizes
        stack_types = ["short", "medium", "deep"]
        stack_probs = [0.3, 0.5, 0.2]
        stack_idx = np.random.choice(len(stack_types), p=stack_probs)
        stack_type = stack_types[stack_idx]
        
        if stack_type == "short":
            stack_size = np.random.uniform(15, 30)
        elif stack_type == "medium":
            stack_size = np.random.uniform(30, 80)
        else:
            stack_size = np.random.uniform(80, 200)
        
        print(f"✅ Stack: {stack_size:.1f}bb ({stack_type})")
        
        # Generate pot and bet sizes
        if betting_round == BettingRound.PREFLOP:
            pot_size = stack_size * np.random.uniform(0.02, 0.08)
        else:
            pot_size = stack_size * np.random.uniform(0.15, 0.4)
        
        bet_to_call = pot_size * np.random.uniform(0.5, 1.2)
        
        print(f"✅ Pot: {pot_size:.1f}bb, Bet: {bet_to_call:.1f}bb")
        
        # Generate decision
        decisions = ["fold", "call", "raise"]
        decision_probs = [0.3, 0.4, 0.3]
        decision_idx = np.random.choice(len(decisions), p=decision_probs)
        decision = decisions[decision_idx]
        
        equity = np.random.uniform(0.3, 0.8)
        confidence = np.random.uniform(0.7, 0.9)
        
        print(f"✅ Decision: {decision} (equity: {equity:.3f}, confidence: {confidence:.3f})")
        
        # Create full scenario
        scenario = {
            'id': f"test_000001",
            'hole_cards': json.dumps(hole_cards),
            'board_cards': json.dumps(board_cards),
            'position': position.value,
            'pot_size': round(pot_size, 2),
            'bet_to_call': round(bet_to_call, 2),
            'stack_size': round(stack_size, 2),
            'betting_round': betting_round.value,
            'recommendation': decision,
            'bet_size': round(bet_to_call * 1.5, 2),
            'equity': equity,
            'reasoning': f"TexasSolver analysis: {decision} from {position.name} on {betting_round.name.lower()}",
            'cfr_confidence': confidence,
            'metadata': json.dumps({
                'source': 'working_test',
                'stack_type': stack_type,
                'generated_at': datetime.now().isoformat()
            })
        }
        
        print(f"✅ Complete scenario generated successfully!")
        print(f"   ID: {scenario['id']}")
        print(f"   Hand: {scenario['hole_cards']}")
        print(f"   Board: {scenario['board_cards']}")
        print(f"   Position: {scenario['position']} ({position.name})")
        print(f"   Betting round: {scenario['betting_round']} ({betting_round.name})")
        print(f"   Recommendation: {scenario['recommendation']}")
        
        return scenario
        
    except Exception as e:
        print(f"❌ Scenario generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    scenario = test_single_scenario()
    if scenario:
        print(f"\n🎉 SINGLE SCENARIO TEST PASSED")
        print(f"Ready to implement fixed TexasSolver import")
    else:
        print(f"\n❌ SINGLE SCENARIO TEST FAILED")
        print(f"Need to investigate further")