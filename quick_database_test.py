#!/usr/bin/env python3
"""
Quick database test to verify system functionality.
"""

import requests
import json
import time

def quick_sanity_check():
    """Comprehensive system sanity check."""
    print("🔍 COMPREHENSIVE SANITY CHECK")
    print("=" * 50)
    
    # Test 1: Database Stats
    try:
        response = requests.get("http://localhost:5000/database/database-stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Database Status: {stats['status']}")
            print(f"✅ Total Situations: {stats['total_situations']:,}")
            print(f"✅ HNSW Index: {stats['hnsw_index_size']:,} elements")
            print(f"✅ Database Size: {stats['database_size_mb']:.2f}MB")
            print(f"✅ Query Time: {stats['average_query_time_ms']:.1f}ms")
        else:
            print(f"❌ Database stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Database stats error: {e}")
        return False
    
    # Test 2: Enhanced GTO Service
    try:
        response = requests.get("http://localhost:5000/enhanced-gto/health", timeout=5)
        if response.status_code == 200:
            print("✅ Enhanced GTO Service: Active")
        else:
            print(f"⚠️ Enhanced GTO Service: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Enhanced GTO Service: {e}")
    
    # Test 3: Manual GTO Solver
    try:
        test_data = {
            "hole_cards": ["As", "Kd"],
            "board_cards": [],
            "position": "BTN",
            "pot_size": 10.0,
            "bet_to_call": 3.0,
            "stack_size": 100.0,
            "betting_round": "preflop"
        }
        
        response = requests.post(
            "http://localhost:5000/manual/solve",
            json=test_data,
            timeout=8
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                rec = data.get("recommendation", {})
                print(f"✅ Manual Solver: {rec.get('decision', 'unknown')} decision")
                print(f"   Confidence: {rec.get('confidence', 0):.2f}")
                print(f"   Method: {data.get('analysis', {}).get('method', 'unknown')}")
            else:
                print(f"⚠️ Manual Solver: {data.get('detail', 'Unknown error')}")
        else:
            print(f"❌ Manual Solver: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Manual Solver error: {e}")
    
    print("\n🎯 CHALLENGING SCENARIO TESTS")
    print("=" * 40)
    
    # Challenging Test 1: Premium pair vs coordinated board
    test_scenarios = [
        {
            "name": "AA vs Straight Draw Board",
            "data": {
                "hole_cards": ["As", "Ad"],
                "board_cards": ["Jh", "Ts", "9d"],
                "position": "BTN",
                "pot_size": 45.0,
                "bet_to_call": 30.0,
                "stack_size": 150.0,
                "betting_round": "flop"
            }
        },
        {
            "name": "KK Preflop vs 3-Bet",
            "data": {
                "hole_cards": ["Kh", "Kd"],
                "position": "CO",
                "pot_size": 18.0,
                "bet_to_call": 12.0,
                "stack_size": 120.0,
                "betting_round": "preflop"
            }
        },
        {
            "name": "Flush Draw Multi-Way",
            "data": {
                "hole_cards": ["Ah", "Kh"],
                "board_cards": ["Qh", "7h", "3c"],
                "position": "MP",
                "pot_size": 35.0,
                "bet_to_call": 15.0,
                "stack_size": 180.0,
                "betting_round": "flop"
            }
        }
    ]
    
    successful_tests = 0
    total_tests = len(test_scenarios)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test {i}: {scenario['name']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:5000/manual/solve",
                json=scenario["data"],
                timeout=8
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    rec = data.get("recommendation", {})
                    decision = rec.get("decision", "unknown")
                    confidence = rec.get("confidence", 0)
                    
                    print(f"   ✅ Decision: {decision.upper()}")
                    print(f"   📊 Confidence: {confidence:.2f}")
                    print(f"   ⚡ Response: {response_time:.1f}ms")
                    successful_tests += 1
                else:
                    print(f"   ❌ Failed: {data.get('detail', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("   ⚠️ Timeout (>8 seconds)")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Final Assessment
    success_rate = (successful_tests / total_tests) * 100
    print(f"\n📊 FINAL ASSESSMENT")
    print("=" * 30)
    print(f"Challenging Tests: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        grade = "🏆 EXCELLENT - Ready for advanced poker analysis"
    elif success_rate >= 60:
        grade = "✅ GOOD - Solid performance with room for optimization"
    elif success_rate >= 40:
        grade = "⚠️ FAIR - Basic functionality working"
    else:
        grade = "❌ NEEDS WORK - System requires debugging"
    
    print(f"Overall Grade: {grade}")
    
    return success_rate >= 60

if __name__ == "__main__":
    result = quick_sanity_check()
    
    if result:
        print("\n🚀 SYSTEM STATUS: OPERATIONAL")
        print("Ready for comprehensive poker analysis and testing!")
    else:
        print("\n⚠️ SYSTEM STATUS: NEEDS ATTENTION") 
        print("Some components may require optimization or debugging")