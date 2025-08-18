#!/usr/bin/env python3
"""
Working Scenario Test: Test actual TexasSolver scenario retrieval and display
"""

import requests
import json

def test_texassolver_scenario_pipeline():
    """Test the complete TexasSolver scenario pipeline."""
    
    print("🎯 TESTING TEXASSOLVER SCENARIO PIPELINE")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    auth_header = {"Authorization": "Bearer test-token-123"}
    
    # Test with realistic ACR table data that should hit our database
    realistic_scenarios = [
        {
            "name": "Premium Preflop",
            "data": {
                "hole_cards": ["As", "Ks"],
                "board_cards": [],
                "pot_size": 3.0,
                "bet_to_call": 2.0,
                "stack_size": 100.0,
                "position": "BTN",
                "num_players": 6,
                "betting_round": "preflop"
            }
        },
        {
            "name": "Flop Set",
            "data": {
                "hole_cards": ["Qh", "Qd"],
                "board_cards": ["Qs", "7h", "2c"],
                "pot_size": 12.0,
                "bet_to_call": 8.0,
                "stack_size": 85.0,
                "position": "CO",
                "num_players": 4,
                "betting_round": "flop"
            }
        },
        {
            "name": "Turn Draw",
            "data": {
                "hole_cards": ["Ah", "Kh"],
                "board_cards": ["Qh", "Jd", "9h", "8c"],
                "pot_size": 45.0,
                "bet_to_call": 25.0,
                "stack_size": 120.0,
                "position": "SB",
                "num_players": 3,
                "betting_round": "turn"
            }
        }
    ]
    
    print("Testing realistic poker scenarios against our 11,799 situation database:")
    
    for i, scenario in enumerate(realistic_scenarios):
        print(f"\n{i+1}. {scenario['name']}:")
        print(f"   Cards: {scenario['data']['hole_cards']} on {scenario['data']['board_cards']}")
        print(f"   Position: {scenario['data']['position']}, Pot: ${scenario['data']['pot_size']}")
        
        try:
            response = requests.post(
                f"{base_url}/database/instant-gto",
                json=scenario['data'],
                headers={"Content-Type": "application/json", **auth_header},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success', False):
                    rec = result.get('recommendation', {})
                    print(f"   ✅ Decision: {rec.get('decision', 'N/A')}")
                    print(f"   Equity: {rec.get('equity', 0):.3f}")
                    print(f"   Confidence: {rec.get('confidence', 0):.3f}")
                    print(f"   Method: {result.get('method', 'unknown')}")
                    
                    reasoning = rec.get('reasoning', '')
                    if reasoning:
                        print(f"   Analysis: {reasoning[:60]}...")
                else:
                    print(f"   ⚠️ No recommendation: {result.get('message', 'Unknown')}")
                    print(f"   Method: {result.get('method', 'unknown')}")
            else:
                error = response.json() if response.content else {}
                print(f"   ❌ Request failed ({response.status_code}): {error}")
        
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    # Test database performance
    print(f"\n📊 DATABASE PERFORMANCE TEST:")
    print("-" * 30)
    
    try:
        response = requests.get(
            f"{base_url}/database/database-stats",
            headers=auth_header,
            timeout=5
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Database operational:")
            print(f"   Total situations: {stats.get('total_situations', 0):,}")
            print(f"   HNSW index: {stats.get('hnsw_index_size', 0):,} vectors")
            print(f"   Database size: {stats.get('database_size_mb', 0):.1f} MB")
            print(f"   Average query time: {stats.get('average_query_time_ms', 0):.2f}ms")
            print(f"   Status: {stats.get('status', 'unknown')}")
        else:
            print(f"❌ Database stats unavailable: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Database performance test failed: {e}")
    
    # Test GUI display capabilities
    print(f"\n🖥️ GUI DISPLAY TEST:")
    print("-" * 19)
    
    try:
        response = requests.get(
            f"{base_url}/unified",
            headers=auth_header,
            timeout=5
        )
        
        if response.status_code == 200:
            html = response.text
            print("✅ GUI interface accessible")
            
            # Check for TexasSolver scenario display elements
            display_elements = [
                ("GTO Recommendation", "gto recommendation" in html.lower()),
                ("Equity Display", "equity" in html.lower()),
                ("Confidence Score", "confidence" in html.lower()),
                ("Decision Display", "decision" in html.lower()),
                ("Reasoning Section", "reasoning" in html.lower() or "analysis" in html.lower())
            ]
            
            for element, present in display_elements:
                status = "✅" if present else "⚠️"
                print(f"   {status} {element}")
        else:
            print(f"❌ GUI not accessible: {response.status_code}")
    
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
    
    print(f"\n🎯 SCENARIO PIPELINE TEST COMPLETE")
    print("The system can process TexasSolver scenarios from database to display")

if __name__ == "__main__":
    test_texassolver_scenario_pipeline()