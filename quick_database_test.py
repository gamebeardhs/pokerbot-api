#!/usr/bin/env python3
"""
Quick Database Test: Fast validation of core database functionality
"""

import requests
import time

def quick_api_test():
    """Quick test of API endpoints with corrected database."""
    
    print("⚡ QUICK API VALIDATION")
    print("=" * 21)
    
    base_url = "http://localhost:5000"
    auth_header = {"Authorization": "Bearer test-token-123"}
    
    # Test instant GTO endpoint
    test_data = {
        "hole_cards": ["As", "Ks"],
        "board_cards": [],
        "pot_size": 3.0,
        "bet_to_call": 2.0,
        "stack_size": 100.0,
        "position": "BTN",
        "num_players": 6,
        "betting_round": "preflop"
    }
    
    print("Testing instant GTO query...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{base_url}/database/instant-gto",
            json=test_data,
            headers={"Content-Type": "application/json", **auth_header},
            timeout=5
        )
        
        query_time = time.time() - start_time
        
        print(f"Response time: {query_time*1000:.1f}ms")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API query successful")
            
            if 'recommendation' in result:
                rec = result['recommendation']
                print(f"Decision: {rec.get('decision', 'N/A')}")
                print(f"Equity: {rec.get('equity', 0):.3f}")
                print(f"Confidence: {rec.get('confidence', 0):.3f}")
                print(f"Method: {result.get('method', 'unknown')}")
            else:
                print("Response structure:", list(result.keys()))
        else:
            error = response.json() if response.content else {}
            print(f"❌ API failed: {error}")
    
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    # Test database stats
    print(f"\nTesting database stats...")
    
    try:
        response = requests.get(
            f"{base_url}/database/database-stats",
            headers=auth_header,
            timeout=3
        )
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Database stats available")
            print(f"Situations: {stats.get('total_situations', 0):,}")
            print(f"Size: {stats.get('database_size_mb', 0):.1f} MB")
            print(f"Performance: {stats.get('average_query_time_ms', 0):.2f}ms")
        else:
            print(f"❌ Stats unavailable: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Stats test failed: {e}")

if __name__ == "__main__":
    quick_api_test()