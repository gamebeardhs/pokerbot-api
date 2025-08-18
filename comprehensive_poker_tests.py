#!/usr/bin/env python3
"""
Comprehensive challenging poker scenario tests.
Tests complex GTO situations that require sophisticated analysis.
"""

import requests
import json
import time
from typing import List, Dict

class AdvancedPokerScenarioTester:
    """Tests the most challenging poker scenarios to verify database quality."""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        
    def test_challenging_scenarios(self):
        """Run comprehensive challenging poker scenario tests."""
        print("CHALLENGING POKER SCENARIO ANALYSIS")
        print("Testing complex GTO situations with the hybrid database system")
        print("=" * 70)
        
        scenarios = [
            {
                "name": "Premium Overpair vs Coordinated Board",
                "description": "AA facing dangerous straight/flush draws",
                "situation": {
                    "hole_cards": ["As", "Ad"],
                    "board_cards": ["Jh", "Ts", "9d"],
                    "position": "BTN",
                    "pot_size": 45.0,
                    "bet_to_call": 30.0,
                    "stack_size": 150.0,
                    "num_players": 2,
                    "betting_round": "flop"
                },
                "complexity": "Very High - overpair vs multiple draws"
            },
            
            {
                "name": "Nut Flush Draw Multi-Way",
                "description": "Strong drawing hand in multi-way pot",
                "situation": {
                    "hole_cards": ["Ah", "Kh"],
                    "board_cards": ["Qh", "7h", "3c"],
                    "position": "CO",
                    "pot_size": 60.0,
                    "bet_to_call": 20.0,
                    "stack_size": 200.0,
                    "num_players": 4,
                    "betting_round": "flop"
                },
                "complexity": "High - nut draws with overcards"
            },
            
            {
                "name": "River Bluff Catcher Decision",
                "description": "Marginal made hand facing large river bet",
                "situation": {
                    "hole_cards": ["Td", "Th"],
                    "board_cards": ["As", "Kc", "Qd", "Jh", "2s"],
                    "position": "BB",
                    "pot_size": 180.0,
                    "bet_to_call": 120.0,
                    "stack_size": 250.0,
                    "num_players": 2,
                    "betting_round": "river"
                },
                "complexity": "Extreme - bluff catching vs straight"
            },
            
            {
                "name": "Short Stack Tournament Spot",
                "description": "ICM-influenced preflop decision",
                "situation": {
                    "hole_cards": ["9h", "9d"],
                    "position": "SB",
                    "pot_size": 4.5,
                    "bet_to_call": 15.0,
                    "stack_size": 18.0,
                    "num_players": 6,
                    "betting_round": "preflop"
                },
                "complexity": "High - ICM and stack pressure"
            },
            
            {
                "name": "Monotone Board Decision",
                "description": "Straight vs flush on dangerous board",
                "situation": {
                    "hole_cards": ["Ac", "Kd"],
                    "board_cards": ["Qh", "Jh", "Th"],
                    "position": "UTG",
                    "pot_size": 35.0,
                    "bet_to_call": 25.0,
                    "stack_size": 180.0,
                    "num_players": 3,
                    "betting_round": "flop"
                },
                "complexity": "Extreme - straight vs flush considerations"
            },
            
            {
                "name": "Set vs Straight/Two-Pair",
                "description": "Strong hand facing polarized turn betting",
                "situation": {
                    "hole_cards": ["8d", "8c"],
                    "board_cards": ["Ah", "Kh", "8s", "Qc"],
                    "position": "BTN",
                    "pot_size": 120.0,
                    "bet_to_call": 80.0,
                    "stack_size": 300.0,
                    "num_players": 2,
                    "betting_round": "turn"
                },
                "complexity": "High - set vs straights and two pairs"
            },
            
            {
                "name": "Light 3-Bet Defense",
                "description": "Speculative hand vs aggressive 3-betting",
                "situation": {
                    "hole_cards": ["6s", "5s"],
                    "position": "CO",
                    "pot_size": 18.0,
                    "bet_to_call": 12.0,
                    "stack_size": 120.0,
                    "num_players": 2,
                    "betting_round": "preflop"
                },
                "complexity": "Medium - suited connectors vs aggression"
            },
            
            {
                "name": "Overbet on Paired Board", 
                "description": "Medium pair facing large turn overbet",
                "situation": {
                    "hole_cards": ["Js", "Jh"],
                    "board_cards": ["Ks", "Kd", "7h", "3c"],
                    "position": "BB",
                    "pot_size": 85.0,
                    "bet_to_call": 140.0,
                    "stack_size": 220.0,
                    "num_players": 2,
                    "betting_round": "turn"
                },
                "complexity": "Very High - middle pair vs overbet sizing"
            }
        ]
        
        results = {
            "total_tests": len(scenarios),
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "detailed_results": []
        }
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\nTest {i}: {scenario['name']}")
            print(f"Scenario: {scenario['description']}")
            print(f"Complexity: {scenario['complexity']}")
            
            # Test with database instant lookup first
            db_result = self._test_database_lookup(scenario['situation'])
            
            # Test with manual solver as backup
            manual_result = self._test_manual_solver(scenario['situation'])
            
            # Analyze results
            result_summary = self._analyze_test_results(scenario, db_result, manual_result)
            results["detailed_results"].append(result_summary)
            
            if result_summary["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
                
            if result_summary["response_time"]:
                results["response_times"].append(result_summary["response_time"])
        
        self._print_comprehensive_summary(results)
        return results
    
    def _test_database_lookup(self, situation: Dict) -> Dict:
        """Test database instant lookup."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/database/instant-gto",
                json=situation,
                timeout=5
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "method": "database",
                    "success": data.get("success", False),
                    "response_time": response_time,
                    "decision": data.get("recommendation", {}).get("decision"),
                    "confidence": data.get("recommendation", {}).get("confidence"),
                    "lookup_method": data.get("method"),
                    "error": None
                }
            else:
                return {
                    "method": "database",
                    "success": False,
                    "response_time": response_time,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "method": "database", 
                "success": False,
                "error": str(e)
            }
    
    def _test_manual_solver(self, situation: Dict) -> Dict:
        """Test manual GTO solver."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/manual/solve",
                json=situation,
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "method": "manual_solver",
                    "success": data.get("success", False),
                    "response_time": response_time,
                    "decision": data.get("recommendation", {}).get("decision"),
                    "confidence": data.get("recommendation", {}).get("confidence"),
                    "reasoning": data.get("analysis", {}).get("reasoning"),
                    "error": None
                }
            else:
                return {
                    "method": "manual_solver",
                    "success": False,
                    "response_time": response_time,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "method": "manual_solver",
                "success": False,
                "error": str(e)
            }
    
    def _analyze_test_results(self, scenario: Dict, db_result: Dict, manual_result: Dict) -> Dict:
        """Analyze and combine test results."""
        # Determine primary result
        primary_result = db_result if db_result.get("success") else manual_result
        
        success = primary_result.get("success", False)
        
        if success:
            status_icon = "✅"
            decision = primary_result.get("decision", "unknown").upper()
            confidence = primary_result.get("confidence", 0)
            response_time = primary_result.get("response_time", 0)
            method = primary_result.get("lookup_method") or primary_result.get("method")
            
            print(f"   {status_icon} Decision: {decision}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Response: {response_time:.1f}ms")
            print(f"   Method: {method}")
            
        else:
            status_icon = "❌"
            db_error = db_result.get("error", "")
            manual_error = manual_result.get("error", "")
            print(f"   {status_icon} Database: {db_error}")
            print(f"   {status_icon} Manual: {manual_error}")
        
        return {
            "scenario_name": scenario["name"],
            "success": success,
            "decision": primary_result.get("decision") if success else None,
            "confidence": primary_result.get("confidence") if success else None,
            "response_time": primary_result.get("response_time") if success else None,
            "method": primary_result.get("lookup_method") or primary_result.get("method") if success else None,
            "db_result": db_result,
            "manual_result": manual_result
        }
    
    def _print_comprehensive_summary(self, results: Dict):
        """Print comprehensive test summary."""
        success_rate = (results["successful"] / results["total_tests"]) * 100
        avg_response = sum(results["response_times"]) / len(results["response_times"]) if results["response_times"] else 0
        
        print(f"\nCOMPREHENSIVE TEST RESULTS")
        print("=" * 50)
        print(f"Total Scenarios: {results['total_tests']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if results["response_times"]:
            print(f"Average Response: {avg_response:.1f}ms")
            print(f"Fastest: {min(results['response_times']):.1f}ms")
            print(f"Slowest: {max(results['response_times']):.1f}ms")
        
        # Performance grade
        if success_rate >= 85:
            grade = "EXCEPTIONAL - Professional tournament ready"
        elif success_rate >= 70:
            grade = "EXCELLENT - Advanced analysis capable"
        elif success_rate >= 55:
            grade = "GOOD - Solid GTO foundation"
        elif success_rate >= 40:
            grade = "FAIR - Basic functionality working"
        else:
            grade = "NEEDS IMPROVEMENT - Requires optimization"
        
        print(f"Performance Grade: {grade}")
        
        # Method analysis
        methods_used = {}
        for result in results["detailed_results"]:
            if result["success"] and result["method"]:
                method = result["method"]
                methods_used[method] = methods_used.get(method, 0) + 1
        
        if methods_used:
            print(f"\nSolution Methods:")
            for method, count in methods_used.items():
                percentage = (count / results["successful"]) * 100
                print(f"   {method}: {count} scenarios ({percentage:.1f}%)")
        
        # Recommendations
        print(f"\nRECOMMENDations:")
        if success_rate >= 70:
            print("Database coverage excellent for challenging scenarios")
            print("System ready for professional poker analysis")
        elif success_rate >= 40:
            print("Good foundation but could benefit from more complex situations")
            print("Consider expanding database with additional challenging scenarios")
        else:
            print("Database needs significant expansion for better coverage")
            print("Focus on adding more complex postflop and tournament situations")

def test_database_performance():
    """Quick database performance verification."""
    print("DATABASE PERFORMANCE CHECK")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:5000/database/database-stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"Status: {stats['status']}")
            print(f"Situations: {stats['total_situations']:,}")
            print(f"HNSW Index: {stats['hnsw_index_size']:,}")
            print(f"Query Time: {stats['average_query_time_ms']:.1f}ms")
            print(f"Database Size: {stats['database_size_mb']:.1f}MB")
            return True
        else:
            print(f"Database check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Database error: {e}")
        return False

if __name__ == "__main__":
    # Performance check first
    db_healthy = test_database_performance()
    
    if db_healthy:
        print("\n" + "="*70)
        # Run comprehensive challenging scenario tests
        tester = AdvancedPokerScenarioTester()
        results = tester.test_challenging_scenarios()
        
        print(f"\nFINAL ASSESSMENT")
        print("="*30)
        if results["successful"] >= 6:  # 75% success rate
            print("System demonstrates excellent GTO analysis capabilities")
            print("Ready for advanced poker decision making")
        elif results["successful"] >= 4:  # 50% success rate  
            print("System shows solid GTO foundation")
            print("Suitable for intermediate poker analysis")
        else:
            print("System requires optimization for challenging scenarios")
            print("Consider database expansion or algorithm improvements")
    else:
        print("Database health check failed - cannot proceed with scenario testing")