#!/usr/bin/env python3
"""
Challenging Scenario Tests: Test TexasSolver scenario pipeline with realistic data
"""

import requests
import json
import time

def test_working_pipeline():
    """Test the working parts of the pipeline with corrected data."""
    
    print("🧪 TESTING WORKING PIPELINE COMPONENTS")
    print("=" * 38)
    
    base_url = "http://localhost:5000"
    auth_header = {"Authorization": "Bearer test-token-123"}
    
    # Test 1: Database query with proper format
    print("\n1. Testing database query with proper format...")
    
    test_data = {
        "hole_cards": ["As", "Ks"],
        "board_cards": [],
        "pot_size": 3.0,
        "bet_to_call": 2.0,
        "stack_size": 100.0,
        "position": "BTN",  # Valid position
        "num_players": 6,
        "betting_round": "preflop"
    }
    
    try:
        response = requests.post(
            f"{base_url}/database/instant-gto",
            json=test_data,
            headers={"Content-Type": "application/json", **auth_header},
            timeout=15
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Database query successful")
            
            if 'recommendation' in result:
                rec = result['recommendation']
                print(f"Decision: {rec.get('decision', 'N/A')}")
                print(f"Equity: {rec.get('equity', 0):.3f}")
                print(f"Confidence: {rec.get('confidence', 0):.3f}")
            else:
                print("Response format:", json.dumps(result, indent=2))
        else:
            error = response.json() if response.content else {}
            print(f"❌ Query failed: {error}")
    
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    
    # Test 2: Manual analysis with table state format
    print("\n2. Testing manual analysis with proper table state...")
    
    table_state = {
        "table_id": "test_table_001",
        "stakes": "$1/$2",
        "street": "preflop",
        "pot": 3.0,
        "seats": [
            {
                "position": "BTN",
                "name": "Hero",
                "stack": 100.0,
                "cards": ["As", "Ks"],
                "active": True,
                "bet": 2.0
            },
            {
                "position": "BB", 
                "name": "Villain",
                "stack": 98.0,
                "cards": ["", ""],
                "active": True,
                "bet": 2.0
            }
        ],
        "board": [],
        "button_position": "BTN"
    }
    
    try:
        response = requests.post(
            f"{base_url}/manual/solve",
            json=table_state,
            headers={"Content-Type": "application/json", **auth_header},
            timeout=15
        )
        
        print(f"Manual analysis status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Manual analysis successful")
            
            if 'recommendation' in result:
                rec = result['recommendation']
                print(f"Decision: {rec.get('decision', 'N/A')}")
                print(f"Bet size: ${rec.get('bet_size', 0)}")
            
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"Mathematical reasoning: {analysis.get('mathematical_reasoning', 'N/A')[:50]}...")
        else:
            error = response.json() if response.content else {}
            print(f"❌ Manual analysis failed: {error}")
    
    except Exception as e:
        print(f"❌ Manual analysis test failed: {e}")
    
    # Test 3: GUI interface access
    print("\n3. Testing GUI interface...")
    
    try:
        response = requests.get(
            f"{base_url}/unified",
            headers=auth_header,
            timeout=10
        )
        
        print(f"GUI status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            print("✅ GUI accessible")
            
            # Check for key elements
            if "gto recommendation" in html_content.lower():
                print("✅ GTO recommendation interface present")
            if "equity" in html_content.lower():
                print("✅ Equity display present")
            if "confidence" in html_content.lower():
                print("✅ Confidence display present")
        else:
            print(f"❌ GUI not accessible: {response.status_code}")
    
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
    
    # Test 4: Database stats
    print("\n4. Testing database stats...")
    
    try:
        response = requests.get(
            f"{base_url}/database/database-stats",
            headers=auth_header,
            timeout=10
        )
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Database stats accessible")
            print(f"Total situations: {stats.get('total_situations', 0):,}")
            print(f"Database size: {stats.get('database_size_mb', 0):.1f} MB")
            print(f"Query performance: {stats.get('average_query_time_ms', 0):.2f}ms")
        else:
            print(f"❌ Database stats failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Database stats test failed: {e}")
    
    print(f"\n✅ PIPELINE COMPONENT TESTS COMPLETE")

if __name__ == "__main__":
    test_working_pipeline()