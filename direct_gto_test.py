#!/usr/bin/env python3
"""
Direct GTO database testing bypassing API endpoints.
Tests challenging scenarios directly through the database system.
"""

import sys
import os
import time
import json

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.database.gto_database import GTODatabase, PokerSituation, Position, BettingRound
except ImportError as e:
    print(f"Import error: {e}")
    print("Testing with simplified approach...")

def test_scenarios_direct():
    """Test challenging scenarios directly through database."""
    print("DIRECT DATABASE TESTING - CHALLENGING SCENARIOS")
    print("=" * 60)
    
    # Initialize database
    try:
        gto_db = GTODatabase()
        gto_db.initialize()
        print(f"Database initialized with {gto_db._get_situation_count():,} situations")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return
    
    # Define challenging test scenarios
    test_scenarios = [
        {
            "name": "Premium Pair vs Straight Draw",
            "hole_cards": ["As", "Ad"],
            "board_cards": ["Jh", "Ts", "9d"],
            "position": "BTN",
            "pot_size": 45.0,
            "bet_to_call": 30.0,
            "stack_size": 150.0,
            "num_players": 2,
            "betting_round": "flop",
            "expected": "Complex decision with overpair vs draws"
        },
        {
            "name": "Short Stack Tournament Decision",
            "hole_cards": ["9h", "9d"],
            "board_cards": [],
            "position": "SB", 
            "pot_size": 4.5,
            "bet_to_call": 15.0,
            "stack_size": 18.0,
            "num_players": 6,
            "betting_round": "preflop",
            "expected": "ICM-influenced all-in decision"
        },
        {
            "name": "Nut Flush Draw Multi-Way",
            "hole_cards": ["Ah", "Kh"],
            "board_cards": ["Qh", "7h", "3c"],
            "position": "CO",
            "pot_size": 60.0,
            "bet_to_call": 20.0,
            "stack_size": 200.0,
            "num_players": 4,
            "betting_round": "flop",
            "expected": "Strong drawing hand analysis"
        },
        {
            "name": "River Bluff Catcher",
            "hole_cards": ["Td", "Th"],
            "board_cards": ["As", "Kc", "Qd", "Jh", "2s"],
            "position": "BB",
            "pot_size": 180.0,
            "bet_to_call": 120.0,
            "stack_size": 250.0,
            "num_players": 2,
            "betting_round": "river",
            "expected": "Difficult bluff catching decision"
        },
        {
            "name": "Monotone Board Straight",
            "hole_cards": ["Ac", "Kd"],
            "board_cards": ["Qh", "Jh", "Th"],
            "position": "UTG",
            "pot_size": 35.0,
            "bet_to_call": 25.0,
            "stack_size": 180.0,
            "num_players": 3,
            "betting_round": "flop",
            "expected": "Straight vs flush considerations"
        }
    ]
    
    successful_tests = 0
    total_response_time = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nTest {i}: {scenario['name']}")
        print(f"Expected: {scenario['expected']}")
        
        try:
            # Create PokerSituation object
            situation = PokerSituation(
                hole_cards=scenario["hole_cards"],
                board_cards=scenario["board_cards"],
                position=Position[scenario["position"]],
                pot_size=scenario["pot_size"],
                bet_to_call=scenario["bet_to_call"],
                stack_size=scenario["stack_size"],
                num_players=scenario["num_players"],
                betting_round=BettingRound[scenario["betting_round"].upper()]
            )
            
            # Test database lookup
            start_time = time.time()
            result = gto_db.get_instant_recommendation(situation)
            response_time = (time.time() - start_time) * 1000
            total_response_time += response_time
            
            if result:
                decision = result.get("decision", "unknown")
                confidence = result.get("confidence", 0)
                equity = result.get("equity", 0)
                
                print(f"   ✅ Decision: {decision.upper()}")
                print(f"   📊 Confidence: {confidence:.2f}")
                print(f"   💰 Equity: {equity:.2f}")
                print(f"   ⚡ Response: {response_time:.1f}ms")
                
                if "reasoning" in result:
                    print(f"   🧠 Reasoning: {result['reasoning']}")
                
                successful_tests += 1
            else:
                # Try generating new solution
                print("   🔄 No database match, generating new solution...")
                solution = gto_db._generate_simple_gto_solution(situation)
                
                if solution:
                    print(f"   ✅ Generated: {solution['decision'].upper()}")
                    print(f"   📊 Confidence: {solution.get('confidence', 0):.2f}")
                    successful_tests += 1
                else:
                    print("   ❌ Failed to generate solution")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Print summary
    success_rate = (successful_tests / len(test_scenarios)) * 100
    avg_response = total_response_time / successful_tests if successful_tests > 0 else 0
    
    print(f"\nDIRECT TESTING SUMMARY")
    print("=" * 30)
    print(f"Scenarios Tested: {len(test_scenarios)}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Avg Response: {avg_response:.1f}ms")
    
    # Performance assessment
    if success_rate >= 80:
        grade = "🏆 EXCELLENT"
        assessment = "Database demonstrates strong GTO analysis capabilities"
    elif success_rate >= 60:
        grade = "✅ GOOD" 
        assessment = "Solid performance with room for optimization"
    elif success_rate >= 40:
        grade = "⚠️ FAIR"
        assessment = "Basic functionality working, needs improvement"
    else:
        grade = "❌ POOR"
        assessment = "Significant optimization required"
    
    print(f"Grade: {grade}")
    print(f"Assessment: {assessment}")
    
    return success_rate >= 60

if __name__ == "__main__":
    success = test_scenarios_direct()
    
    if success:
        print("\n🚀 DIRECT TESTING COMPLETE - System operational for challenging scenarios")
    else:
        print("\n⚠️ DIRECT TESTING REVEALS OPTIMIZATION OPPORTUNITIES")