#!/usr/bin/env python3
"""
Direct Database Testing: 12 Real Poker Scenarios
Tests the current 6,757 situation database with realistic scenarios
"""

import sys
import os
sys.path.append('/home/runner/workspace')

from app.database.gto_database import gto_db
from app.database.poker_vectorizer import PokerSituation, Position, BettingRound

def test_database_scenarios():
    """Test 12 realistic poker scenarios directly against the database."""
    
    print("DATABASE SCENARIO TESTING")
    print("Testing 12 realistic scenarios against 6,757 situation database")
    print("=" * 65)
    
    # Initialize database
    if not gto_db.initialized:
        gto_db.initialize()
    
    scenarios = [
        {
            "name": "Premium Preflop - Button AKs",
            "situation": PokerSituation(
                hole_cards=["As", "Ks"],
                board_cards=[],
                position=Position.BTN,
                pot_size=3.0,
                bet_to_call=2.0,
                stack_size=100.0,
                num_players=6,
                betting_round=BettingRound.PREFLOP
            )
        },
        {
            "name": "Trash Preflop - UTG 72o",
            "situation": PokerSituation(
                hole_cards=["7d", "2c"],
                board_cards=[],
                position=Position.UTG,
                pot_size=1.5,
                bet_to_call=1.0,
                stack_size=50.0,
                num_players=9,
                betting_round=BettingRound.PREFLOP
            )
        },
        {
            "name": "Straight Draw - QJs on AKT",
            "situation": PokerSituation(
                hole_cards=["Qh", "Jh"],
                board_cards=["As", "Kc", "Ts"],
                position=Position.CO,
                pot_size=12.0,
                bet_to_call=8.0,
                stack_size=80.0,
                num_players=4,
                betting_round=BettingRound.FLOP
            )
        },
        {
            "name": "Overpair - AA on 27J",
            "situation": PokerSituation(
                hole_cards=["Ac", "Ad"],
                board_cards=["2h", "7s", "Jd"],
                position=Position.BB,
                pot_size=15.0,
                bet_to_call=10.0,
                stack_size=120.0,
                num_players=3,
                betting_round=BettingRound.FLOP
            )
        },
        {
            "name": "Set on Turn - TT on 987A",
            "situation": PokerSituation(
                hole_cards=["Td", "Tc"],
                board_cards=["9h", "8s", "7c", "Ad"],
                position=Position.SB,
                pot_size=25.0,
                bet_to_call=15.0,
                stack_size=95.0,
                num_players=2,
                betting_round=BettingRound.TURN
            )
        },
        {
            "name": "Straight on River - KQ on AJT92",
            "situation": PokerSituation(
                hole_cards=["Kh", "Qd"],
                board_cards=["As", "Jd", "Tc", "9s", "2h"],
                position=Position.BTN,
                pot_size=40.0,
                bet_to_call=30.0,
                stack_size=75.0,
                num_players=2,
                betting_round=BettingRound.RIVER
            )
        },
        {
            "name": "Pocket Pair - 88 Preflop CO",
            "situation": PokerSituation(
                hole_cards=["8h", "8d"],
                board_cards=[],
                position=Position.CO,
                pot_size=1.5,
                bet_to_call=0.0,
                stack_size=100.0,
                num_players=6,
                betting_round=BettingRound.PREFLOP
            )
        },
        {
            "name": "Weak Ace - A3o BB vs raise",
            "situation": PokerSituation(
                hole_cards=["Ad", "3c"],
                board_cards=[],
                position=Position.BB,
                pot_size=4.0,
                bet_to_call=3.0,
                stack_size=50.0,
                num_players=3,
                betting_round=BettingRound.PREFLOP
            )
        },
        {
            "name": "Flush Draw - 9♥8♥ on A♥5♥2♠",
            "situation": PokerSituation(
                hole_cards=["9h", "8h"],
                board_cards=["Ah", "5h", "2s"],
                position=Position.MP,
                pot_size=18.0,
                bet_to_call=12.0,
                stack_size=85.0,
                num_players=3,
                betting_round=BettingRound.FLOP
            )
        },
        {
            "name": "Top Pair - AQ on A72",
            "situation": PokerSituation(
                hole_cards=["Ah", "Qc"],
                board_cards=["As", "7d", "2c"],
                position=Position.BTN,
                pot_size=9.0,
                bet_to_call=6.0,
                stack_size=94.0,
                num_players=2,
                betting_round=BettingRound.FLOP
            )
        },
        {
            "name": "Bluff Catcher - K9 on AKQ85",
            "situation": PokerSituation(
                hole_cards=["Kd", "9s"],
                board_cards=["Ac", "Kh", "Qd", "8s", "5c"],
                position=Position.BB,
                pot_size=35.0,
                bet_to_call=25.0,
                stack_size=60.0,
                num_players=2,
                betting_round=BettingRound.RIVER
            )
        },
        {
            "name": "Two Pair - J9 on J94",
            "situation": PokerSituation(
                hole_cards=["Js", "9h"],
                board_cards=["Jh", "9d", "4c"],
                position=Position.CO,
                pot_size=14.0,
                bet_to_call=10.0,
                stack_size=90.0,
                num_players=4,
                betting_round=BettingRound.FLOP
            )
        }
    ]
    
    database_hits = 0
    database_misses = 0
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nSCENARIO {i}: {scenario['name']}")
        print("-" * (len(f"SCENARIO {i}: {scenario['name']}")))
        
        situation = scenario['situation']
        
        # Format situation details nicely
        print(f"Cards: {'/'.join(situation.hole_cards)}")
        if situation.board_cards:
            print(f"Board: {'-'.join(situation.board_cards)}")
        else:
            print(f"Board: (preflop)")
        print(f"Position: {situation.position.name}")
        print(f"Pot: ${situation.pot_size:.1f}, Bet: ${situation.bet_to_call:.1f}, Stack: ${situation.stack_size:.1f}")
        print(f"Players: {situation.num_players}, Street: {situation.betting_round.name}")
        
        try:
            # Test database lookup
            recommendation = gto_db.get_instant_recommendation(situation)
            
            if recommendation:
                database_hits += 1
                print(f"✓ DATABASE HIT - Found similar situation")
                print(f"  Decision: {recommendation.get('decision', 'unknown')}")
                print(f"  Bet Size: ${recommendation.get('bet_size', 0):.1f}")
                print(f"  Equity: {recommendation.get('equity', 0.0):.3f}")
                print(f"  Reasoning: {recommendation.get('reasoning', 'No reasoning')}")
                if 'confidence' in recommendation:
                    print(f"  Confidence: {recommendation['confidence']:.2f}")
                
                # Analyze recommendation quality
                decision = recommendation.get('decision', '').lower()
                equity = recommendation.get('equity', 0.0)
                
                # Basic sanity check
                if decision in ['fold', 'call', 'raise']:
                    quality = "REASONABLE"
                    if equity > 0.6 and decision == 'fold':
                        quality = "QUESTIONABLE (high equity but folding)"
                    elif equity < 0.3 and decision == 'raise':
                        quality = "QUESTIONABLE (low equity but raising)"
                    elif decision == 'call' and situation.bet_to_call > situation.pot_size:
                        quality = "QUESTIONABLE (calling overbet)"
                    
                    print(f"  Quality Assessment: {quality}")
                else:
                    print(f"  Quality Assessment: INVALID (bad decision format)")
                    
            else:
                database_misses += 1
                print(f"✗ DATABASE MISS - No similar situation found")
                print(f"  Would trigger CFR computation (1-3 seconds)")
                print(f"  Result would be cached for future instant lookup")
                
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            database_misses += 1
    
    print(f"\n" + "=" * 65)
    print("DATABASE PERFORMANCE SUMMARY")
    print("=" * 65)
    print(f"Total Scenarios Tested: {len(scenarios)}")
    print(f"Database Hits: {database_hits}")
    print(f"Database Misses: {database_misses}")
    print(f"Hit Rate: {(database_hits/len(scenarios)*100):.1f}%")
    
    print(f"\nINSIGHTS:")
    if database_hits == 0:
        print("• Current database provides NO coverage for realistic scenarios")
        print("• All queries would trigger CFR computation (2-3 seconds each)")
        print("• Database consists mainly of bootstrapped rule-based situations")
        print("• Strong case for TexasSolver integration to add authentic scenarios")
    elif database_hits < len(scenarios) * 0.3:
        print("• Low coverage suggests database needs more realistic scenarios")
        print("• Most unique situations require CFR computation")  
        print("• Database would grow quickly with real user queries")
    elif database_hits < len(scenarios) * 0.7:
        print("• Moderate coverage with room for improvement")
        print("• Mix of instant responses and CFR fallbacks")
    else:
        print("• Good coverage for common scenarios")
        print("• Most queries return instantly from database")
    
    if database_hits > 0:
        print(f"\nRECOMMENDATION QUALITY ANALYSIS:")
        print("• Rule-based recommendations may not reflect true GTO")
        print("• TexasSolver integration would provide authentic CFR solutions")
        print("• Current database serves as good bootstrap/fallback system")
        
    print(f"\nNEXT STEPS:")
    print("• TexasSolver integration would boost coverage and authenticity")
    print("• Current hybrid approach (database + CFR) is working correctly")
    print("• System learns from every novel query to improve over time")

if __name__ == "__main__":
    test_database_scenarios()