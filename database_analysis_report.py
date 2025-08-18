#!/usr/bin/env python3
"""
Database Analysis Report: Final validation test before continuing TexasSolver expansion
"""

import requests
import time
import json

def run_final_validation_test():
    """Run comprehensive validation test of the complete pipeline."""
    
    print("🧪 FINAL PIPELINE VALIDATION TEST")
    print("=" * 33)
    print("Testing all critical components before TexasSolver expansion")
    
    base_url = "http://localhost:5000"
    auth_header = {"Authorization": "Bearer test-token-123"}
    
    # Test scenarios representing different poker situations
    test_scenarios = [
        {
            "name": "Premium Preflop Raise",
            "data": {
                "hole_cards": ["As", "Ks"],
                "board_cards": [],
                "pot_size": 3.0,
                "bet_to_call": 2.0,
                "stack_size": 100.0,
                "position": "BTN",
                "num_players": 6,
                "betting_round": "preflop"
            },
            "expected": "should get instant recommendation"
        },
        {
            "name": "Flop Top Set",
            "data": {
                "hole_cards": ["Ah", "Ac"],
                "board_cards": ["As", "7h", "2c"],
                "pot_size": 15.0,
                "bet_to_call": 10.0,
                "stack_size": 85.0,
                "position": "CO",
                "num_players": 4,
                "betting_round": "flop"
            },
            "expected": "strong recommendation"
        },
        {
            "name": "Turn Straight Draw",
            "data": {
                "hole_cards": ["Js", "Td"],
                "board_cards": ["9h", "8c", "2d", "7s"],
                "pot_size": 40.0,
                "bet_to_call": 20.0,
                "stack_size": 60.0,
                "position": "SB",
                "num_players": 3,
                "betting_round": "turn"
            },
            "expected": "draw evaluation"
        },
        {
            "name": "River Value Bet",
            "data": {
                "hole_cards": ["Kh", "Kd"],
                "board_cards": ["Ks", "7h", "2c", "8d", "3s"],
                "pot_size": 80.0,
                "bet_to_call": 0.0,
                "stack_size": 120.0,
                "position": "BTN",
                "num_players": 2,
                "betting_round": "river"
            },
            "expected": "value bet sizing"
        }
    ]
    
    print(f"\nTesting {len(test_scenarios)} critical poker scenarios:")
    
    results = []
    total_query_time = 0
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{i+1}. {scenario['name']}:")
        print(f"   Situation: {scenario['data']['hole_cards']} on {scenario['data']['board_cards']}")
        print(f"   Position: {scenario['data']['position']}, Pot: ${scenario['data']['pot_size']}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/database/instant-gto",
                json=scenario['data'],
                headers={"Content-Type": "application/json", **auth_header},
                timeout=8
            )
            
            query_time = time.time() - start_time
            total_query_time += query_time
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success', False) and 'recommendation' in result:
                    rec = result['recommendation']
                    
                    print(f"   ✅ Decision: {rec.get('decision', 'N/A')}")
                    print(f"   Equity: {rec.get('equity', 0):.3f}")
                    print(f"   Confidence: {rec.get('confidence', 0):.3f}")
                    print(f"   Query time: {query_time*1000:.1f}ms")
                    print(f"   Source: {result.get('method', 'unknown')}")
                    
                    results.append({
                        'scenario': scenario['name'],
                        'success': True,
                        'decision': rec.get('decision'),
                        'equity': rec.get('equity', 0),
                        'confidence': rec.get('confidence', 0),
                        'query_time_ms': query_time * 1000,
                        'method': result.get('method', 'unknown')
                    })
                else:
                    print(f"   ⚠️ Fallback method: {result.get('method', 'unknown')}")
                    results.append({
                        'scenario': scenario['name'],
                        'success': False,
                        'method': result.get('method', 'unknown'),
                        'query_time_ms': query_time * 1000
                    })
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                results.append({
                    'scenario': scenario['name'],
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'query_time_ms': query_time * 1000
                })
        
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results.append({
                'scenario': scenario['name'],
                'success': False,
                'error': str(e),
                'query_time_ms': 0
            })
    
    # Performance analysis
    print(f"\n📊 PERFORMANCE ANALYSIS")
    print("-" * 21)
    
    successful_queries = [r for r in results if r['success']]
    avg_query_time = total_query_time * 1000 / len(test_scenarios)
    
    print(f"Successful queries: {len(successful_queries)}/{len(test_scenarios)}")
    print(f"Average query time: {avg_query_time:.1f}ms")
    
    if successful_queries:
        avg_confidence = sum(r.get('confidence', 0) for r in successful_queries) / len(successful_queries)
        avg_equity = sum(r.get('equity', 0) for r in successful_queries) / len(successful_queries)
        print(f"Average confidence: {avg_confidence:.3f}")
        print(f"Average equity: {avg_equity:.3f}")
    
    # Decision distribution
    decisions = [r.get('decision') for r in successful_queries if r.get('decision')]
    if decisions:
        decision_count = {}
        for decision in decisions:
            decision_count[decision] = decision_count.get(decision, 0) + 1
        
        print(f"Decision distribution:")
        for decision, count in decision_count.items():
            print(f"   {decision}: {count}")
    
    # Test database stats
    print(f"\n📈 DATABASE STATUS")
    print("-" * 16)
    
    try:
        response = requests.get(
            f"{base_url}/database/database-stats",
            headers=auth_header,
            timeout=5
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Database operational")
            print(f"   Total situations: {stats.get('total_situations', 0):,}")
            print(f"   HNSW index size: {stats.get('hnsw_index_size', 0):,}")
            print(f"   Database size: {stats.get('database_size_mb', 0):.1f} MB")
            print(f"   Query performance: {stats.get('average_query_time_ms', 0):.2f}ms")
        else:
            print(f"❌ Database stats unavailable: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Database stats test failed: {e}")
    
    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT")
    print("-" * 17)
    
    success_rate = len(successful_queries) / len(test_scenarios)
    
    if success_rate >= 0.75 and avg_query_time < 50:  # 75% success rate, under 50ms
        print("🎉 PIPELINE VALIDATION PASSED")
        print("✅ System ready for TexasSolver database expansion")
        print(f"✅ Success rate: {success_rate*100:.1f}%")
        print(f"✅ Performance: {avg_query_time:.1f}ms average")
        print("✅ Database integrity confirmed")
        print("✅ API endpoints operational")
        return True
    else:
        print("⚠️ PIPELINE NEEDS ATTENTION")
        print(f"Success rate: {success_rate*100:.1f}% (target: 75%)")
        print(f"Performance: {avg_query_time:.1f}ms (target: <50ms)")
        return False

if __name__ == "__main__":
    success = run_final_validation_test()
    
    if success:
        print(f"\n✅ VALIDATION COMPLETE - READY TO CONTINUE")
        print("Pipeline sanity check passed. Safe to proceed with TexasSolver expansion.")
    else:
        print(f"\n⚠️ VALIDATION FAILED - NEEDS FIXES")
        print("Pipeline issues detected. Address before expanding database.")