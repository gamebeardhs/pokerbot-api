#!/usr/bin/env python3
"""
Challenging poker scenario tests to verify improved database coverage.
Tests complex situations that require sophisticated GTO analysis.
"""

import requests
import json
import time
from typing import List, Dict

class ChallengingPokerTests:
    """Tests challenging poker scenarios to verify database coverage quality."""
    
    def __init__(self):
        self.base_url = "http://localhost:5000/database"
        self.test_scenarios = self._create_challenging_scenarios()
    
    def _create_challenging_scenarios(self) -> List[Dict]:
        """Create challenging poker scenarios that test database coverage."""
        return [
            {
                "name": "AA vs Coordinated Flop",
                "description": "Premium pair facing dangerous coordinated board",
                "request": {
                    "hole_cards": ["As", "Ad"],
                    "board_cards": ["Jh", "Ts", "9d"],
                    "position": "BTN",
                    "pot_size": 45.0,
                    "bet_to_call": 30.0,
                    "stack_size": 150.0,
                    "num_players": 2,
                    "betting_round": "flop"
                },
                "expected_complexity": "High - overpair vs straight draws"
            },
            {
                "name": "Flush Draw Multi-Way",
                "description": "Strong flush draw in multi-way pot",
                "request": {
                    "hole_cards": ["Ah", "Kh"],
                    "board_cards": ["Qh", "7h", "3c"],
                    "position": "CO",
                    "pot_size": 60.0,
                    "bet_to_call": 20.0,
                    "stack_size": 200.0,
                    "num_players": 4,
                    "betting_round": "flop"
                },
                "expected_complexity": "Medium - nut flush draw with overcards"
            },
            {
                "name": "River Bluff Catcher",
                "description": "Marginal hand facing large river bet",
                "request": {
                    "hole_cards": ["Td", "Th"],
                    "board_cards": ["As", "Kc", "Qd", "Jh", "2s"],
                    "position": "BB",
                    "pot_size": 180.0,
                    "bet_to_call": 120.0,
                    "stack_size": 250.0,
                    "num_players": 2,
                    "betting_round": "river"
                },
                "expected_complexity": "Very High - bluff catching decision"
            },
            {
                "name": "Tournament ICM Spot",
                "description": "Short stack tournament decision",
                "request": {
                    "hole_cards": ["9h", "9d"],
                    "position": "SB",
                    "pot_size": 4.5,
                    "bet_to_call": 15.0,
                    "stack_size": 18.0,
                    "num_players": 6,
                    "betting_round": "preflop"
                },
                "expected_complexity": "High - ICM considerations"
            },
            {
                "name": "Monotone Board Decision",
                "description": "Decision on dangerous monotone flop",
                "request": {
                    "hole_cards": ["Ac", "Kd"],
                    "board_cards": ["Qh", "Jh", "Th"],
                    "position": "UTG",
                    "pot_size": 35.0,
                    "bet_to_call": 25.0,
                    "stack_size": 180.0,
                    "num_players": 3,
                    "betting_round": "flop"
                },
                "expected_complexity": "Very High - straight vs flush considerations"
            },
            {
                "name": "Polarized Turn Spot",
                "description": "Facing polarized turn bet with marginal hand",
                "request": {
                    "hole_cards": ["8d", "8c"],
                    "board_cards": ["A", "K", "8", "Q"],
                    "position": "BTN",
                    "pot_size": 120.0,
                    "bet_to_call": 80.0,
                    "stack_size": 300.0,
                    "num_players": 2,
                    "betting_round": "turn"
                },
                "expected_complexity": "High - set vs straight/two pair"
            },
            {
                "name": "Light 3-Bet Defense",
                "description": "Defending against light 3-bet with speculative hand",
                "request": {
                    "hole_cards": ["6s", "5s"],
                    "position": "CO",
                    "pot_size": 18.0,
                    "bet_to_call": 12.0,
                    "stack_size": 120.0,
                    "num_players": 2,
                    "betting_round": "preflop"
                },
                "expected_complexity": "Medium - suited connector vs 3-bet"
            },
            {
                "name": "Paired Board Overbet",
                "description": "Facing overbet on paired board",
                "request": {
                    "hole_cards": ["Js", "Jh"],
                    "board_cards": ["Ks", "Kd", "7h", "3c"],
                    "position": "BB",
                    "pot_size": 85.0,
                    "bet_to_call": 140.0,
                    "stack_size": 220.0,
                    "num_players": 2,
                    "betting_round": "turn"
                },
                "expected_complexity": "Very High - middle pair vs overbet"
            }
        ]
    
    def run_comprehensive_tests(self):
        """Run all challenging scenario tests."""
        print("🧪 CHALLENGING POKER SCENARIO TESTS")
        print("Testing database coverage with complex GTO situations")
        print("=" * 65)
        
        results = {
            "total_tests": len(self.test_scenarios),
            "successful": 0,
            "failed": 0,
            "avg_response_time": 0,
            "test_details": []
        }
        
        total_response_time = 0
        
        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"\n🎯 Test {i}: {scenario['name']}")
            print(f"   Scenario: {scenario['description']}")
            print(f"   Complexity: {scenario['expected_complexity']}")
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/instant-gto",
                    json=scenario["request"],
                    timeout=10
                )
                response_time = (time.time() - start_time) * 1000
                total_response_time += response_time
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        recommendation = data.get("recommendation", {})
                        decision = recommendation.get("decision", "unknown")
                        confidence = recommendation.get("confidence", 0)
                        method = data.get("method", "unknown")
                        
                        print(f"   ✅ SUCCESS ({response_time:.1f}ms)")
                        print(f"      Decision: {decision.upper()}")
                        print(f"      Confidence: {confidence:.2f}")
                        print(f"      Method: {method}")
                        
                        if "bet_size" in recommendation and recommendation["bet_size"] > 0:
                            print(f"      Bet Size: ${recommendation['bet_size']:.1f}")
                        
                        results["successful"] += 1
                        results["test_details"].append({
                            "name": scenario["name"],
                            "status": "success",
                            "decision": decision,
                            "confidence": confidence,
                            "response_time": response_time,
                            "method": method
                        })
                    else:
                        error_detail = data.get("detail", "Unknown error")
                        print(f"   ❌ FAILED: {error_detail}")
                        results["failed"] += 1
                        results["test_details"].append({
                            "name": scenario["name"],
                            "status": "failed",
                            "error": error_detail
                        })
                else:
                    print(f"   ❌ HTTP ERROR: {response.status_code}")
                    results["failed"] += 1
                    
            except requests.exceptions.Timeout:
                print(f"   ⚠️ TIMEOUT: Query took longer than 10 seconds")
                results["failed"] += 1
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                results["failed"] += 1
        
        # Calculate final metrics
        if results["successful"] > 0:
            results["avg_response_time"] = total_response_time / results["successful"]
        
        self._print_summary(results)
        return results
    
    def _print_summary(self, results: Dict):
        """Print comprehensive test summary."""
        success_rate = (results["successful"] / results["total_tests"]) * 100
        
        print(f"\n📊 CHALLENGING SCENARIO TEST RESULTS")
        print("=" * 50)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if results["successful"] > 0:
            print(f"Avg Response Time: {results['avg_response_time']:.1f}ms")
        
        # Performance assessment
        if success_rate >= 80:
            grade = "🏆 EXCELLENT"
        elif success_rate >= 60:
            grade = "✅ GOOD"
        elif success_rate >= 40:
            grade = "⚠️ FAIR"
        else:
            grade = "❌ NEEDS IMPROVEMENT"
        
        print(f"Overall Grade: {grade}")
        
        # Method distribution
        methods_used = {}
        for test in results["test_details"]:
            if test["status"] == "success":
                method = test.get("method", "unknown")
                methods_used[method] = methods_used.get(method, 0) + 1
        
        if methods_used:
            print(f"\nMethod Distribution:")
            for method, count in methods_used.items():
                percentage = (count / results["successful"]) * 100
                print(f"   {method}: {count} tests ({percentage:.1f}%)")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        if success_rate >= 80:
            print("✅ Database coverage is excellent for challenging scenarios")
            print("✅ Ready for advanced poker analysis and professional use")
        elif success_rate >= 60:
            print("📈 Good coverage but could benefit from more complex situations")
            print("💡 Consider adding more tournament and ICM scenarios")
        else:
            print("⚠️ Database needs expansion for better challenging scenario coverage")
            print("🔧 Focus on adding more complex postflop and river situations")

def run_sanity_check():
    """Quick sanity check of database health."""
    print("🔍 QUICK SANITY CHECK")
    print("=" * 30)
    
    try:
        # Check database stats
        response = requests.get("http://localhost:5000/database/database-stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Database: {stats['status']} - {stats['total_situations']:,} situations")
            print(f"✅ Index: {stats['hnsw_index_size']:,} elements")
            print(f"✅ Query Time: {stats['average_query_time_ms']:.1f}ms")
        else:
            print(f"❌ Database stats failed: {response.status_code}")
            return False
        
        # Quick API test
        test_request = {
            "hole_cards": ["Ks", "Kh"],
            "position": "BTN",
            "pot_size": 10,
            "bet_to_call": 0,
            "stack_size": 100,
            "num_players": 6,
            "betting_round": "preflop"
        }
        
        response = requests.post(
            "http://localhost:5000/database/instant-gto",
            json=test_request,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ API Test: {data['recommendation']['decision']} decision")
                return True
            else:
                print(f"❌ API Test Failed: {data.get('detail', 'Unknown error')}")
                return False
        else:
            print(f"❌ API Test: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Sanity Check Error: {e}")
        return False

if __name__ == "__main__":
    # Run sanity check first
    sanity_passed = run_sanity_check()
    
    if sanity_passed:
        print("\n" + "="*65)
        # Run challenging scenario tests
        tester = ChallengingPokerTests()
        results = tester.run_comprehensive_tests()
        
        print(f"\n🏁 TESTING COMPLETE")
        if results["successful"] >= 6:  # At least 75% success
            print("🚀 System ready for advanced poker analysis!")
        else:
            print("📈 System functional but may need optimization for complex scenarios")
    else:
        print("\n❌ Sanity check failed - system needs debugging before scenario testing")