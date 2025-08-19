#!/usr/bin/env python3
"""
Comprehensive End-to-End Poker Advisory System Test
Tests all components from database through API to ensure everything works properly
"""

import requests
import json
import time
import sqlite3
import subprocess
import os

def test_database_health():
    """Test database integrity and performance."""
    print("🔍 TESTING DATABASE HEALTH")
    print("=" * 26)
    
    try:
        conn = sqlite3.connect("gto_database.db")
        cursor = conn.cursor()
        
        # Check database structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Database tables: {[t[0] for t in tables]}")
        
        # Check scenario counts
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM gto_situations WHERE id LIKE 'simple_%'")
        simple_count = cursor.fetchone()[0]
        
        print(f"✅ Total scenarios: {total_count:,}")
        print(f"✅ Authentic scenarios: {simple_count:,}")
        
        # Check for data integrity
        cursor.execute("SELECT COUNT(*) FROM gto_situations WHERE hole_cards IS NULL OR reasoning IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"✅ Scenarios with null data: {null_count}")
        
        # Test vector data
        cursor.execute("SELECT vector FROM gto_situations LIMIT 1")
        vector_data = cursor.fetchone()
        if vector_data and vector_data[0]:
            print(f"✅ Vector data present: {len(vector_data[0])} bytes")
        else:
            print(f"❌ Vector data missing or corrupted")
        
        conn.close()
        return total_count > 20000  # Expect at least 20K scenarios
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api_endpoints():
    """Test all API endpoints."""
    print(f"\n🧪 TESTING API ENDPOINTS")
    print("=" * 22)
    
    base_url = "http://localhost:5000"
    headers = {"Authorization": "Bearer test-token-123"}
    
    tests = [
        ("GET", "/health", None, "Health check"),
        ("GET", "/database/database-stats", None, "Database stats"),
        ("POST", "/database/instant-gto", {
            "hole_cards": ["As", "Ks"],
            "board_cards": [],
            "pot_size": 3.0,
            "bet_to_call": 2.0,
            "stack_size": 100.0,
            "position": "BTN",
            "num_players": 6,
            "betting_round": "preflop"
        }, "Instant GTO preflop"),
        ("POST", "/database/instant-gto", {
            "hole_cards": ["Qh", "Qd"],
            "board_cards": ["Qs", "7h", "2c"],
            "pot_size": 12.0,
            "bet_to_call": 8.0,
            "stack_size": 85.0,
            "position": "CO",
            "num_players": 4,
            "betting_round": "flop"
        }, "Instant GTO flop"),
        ("GET", "/unified", None, "Unified interface"),
        ("GET", "/manual", None, "Manual interface")
    ]
    
    passed = 0
    for method, endpoint, data, description in tests:
        try:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            else:
                response = requests.post(f"{base_url}{endpoint}", 
                                       json=data, 
                                       headers={"Content-Type": "application/json", **headers}, 
                                       timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                print(f"✅ {description}: {response.status_code} ({response_time:.1f}ms)")
                
                # Check response content for specific endpoints
                if "gto" in endpoint and response.headers.get('content-type', '').startswith('application/json'):
                    result = response.json()
                    if result.get('success'):
                        rec = result.get('recommendation', {})
                        decision = rec.get('decision', 'N/A')
                        equity = rec.get('equity', 0)
                        print(f"   → Decision: {decision}, Equity: {equity:.3f}")
                    else:
                        print(f"   → Fallback used or no recommendation")
                
                passed += 1
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"❌ {description}: {str(e)[:80]}...")
    
    return passed == len(tests)

def test_gto_decision_quality():
    """Test GTO decision quality and reasoning."""
    print(f"\n🎯 TESTING GTO DECISION QUALITY")
    print("=" * 29)
    
    base_url = "http://localhost:5000"
    headers = {"Authorization": "Bearer test-token-123", "Content-Type": "application/json"}
    
    # Test scenarios with expected reasonable decisions
    test_cases = [
        {
            "name": "Premium pair preflop",
            "data": {
                "hole_cards": ["As", "Ad"],
                "board_cards": [],
                "pot_size": 3.0,
                "bet_to_call": 2.0,
                "stack_size": 100.0,
                "position": "BTN",
                "num_players": 6,
                "betting_round": "preflop"
            },
            "expected_actions": ["raise", "call"]  # Should not fold with AA
        },
        {
            "name": "Weak hand facing large bet",
            "data": {
                "hole_cards": ["7c", "2d"],
                "board_cards": ["As", "Kh", "Qd"],
                "pot_size": 20.0,
                "bet_to_call": 25.0,
                "stack_size": 50.0,
                "position": "SB",
                "num_players": 2,
                "betting_round": "flop"
            },
            "expected_actions": ["fold"]  # Should fold 72o vs large bet on AKQ
        },
        {
            "name": "Strong draw",
            "data": {
                "hole_cards": ["9s", "8s"],
                "board_cards": ["Ts", "7h", "6c"],
                "pot_size": 15.0,
                "bet_to_call": 10.0,
                "stack_size": 75.0,
                "position": "CO",
                "num_players": 3,
                "betting_round": "flop"
            },
            "expected_actions": ["call", "raise"]  # Should play straight draw
        }
    ]
    
    quality_passed = 0
    
    for test_case in test_cases:
        try:
            response = requests.post(f"{base_url}/database/instant-gto", 
                                   json=test_case["data"], 
                                   headers=headers, 
                                   timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    rec = result['recommendation']
                    decision = rec.get('decision', '')
                    equity = rec.get('equity', 0)
                    reasoning = rec.get('reasoning', '')
                    
                    # Check if decision is reasonable
                    if decision in test_case["expected_actions"]:
                        print(f"✅ {test_case['name']}: {decision} (equity: {equity:.3f}) ✓")
                        quality_passed += 1
                    else:
                        print(f"⚠️ {test_case['name']}: {decision} (expected: {test_case['expected_actions']})")
                        print(f"   Reasoning: {reasoning[:80]}...")
                else:
                    print(f"❌ {test_case['name']}: No recommendation returned")
            else:
                print(f"❌ {test_case['name']}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: {str(e)[:60]}...")
    
    return quality_passed >= len(test_cases) * 0.7  # 70% pass rate

def test_web_interface():
    """Test web interface accessibility."""
    print(f"\n🌐 TESTING WEB INTERFACE")
    print("=" * 22)
    
    base_url = "http://localhost:5000"
    
    interfaces = [
        ("/", "Main page"),
        ("/unified", "Unified interface"),
        ("/manual", "Manual interface"),
        ("/training", "Training interface")
    ]
    
    passed = 0
    for endpoint, name in interfaces:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200 and len(response.text) > 1000:  # Basic content check
                print(f"✅ {name}: Accessible and has content")
                passed += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code} or insufficient content")
        except Exception as e:
            print(f"❌ {name}: {str(e)[:60]}...")
    
    return passed >= len(interfaces) * 0.75  # 75% pass rate

def test_performance_benchmarks():
    """Test system performance."""
    print(f"\n⚡ TESTING PERFORMANCE")
    print("=" * 18)
    
    base_url = "http://localhost:5000"
    headers = {"Authorization": "Bearer test-token-123", "Content-Type": "application/json"}
    
    # Test response times
    test_data = {
        "hole_cards": ["Ks", "Qd"],
        "board_cards": ["Js", "Th", "9c"],
        "pot_size": 10.0,
        "bet_to_call": 7.0,
        "stack_size": 60.0,
        "position": "BTN",
        "num_players": 4,
        "betting_round": "flop"
    }
    
    response_times = []
    successful_requests = 0
    
    for i in range(10):
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}/database/instant-gto", 
                                   json=test_data, 
                                   headers=headers, 
                                   timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response_times.append(response_time)
                successful_requests += 1
                
        except Exception as e:
            pass
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"✅ Average response time: {avg_time:.1f}ms")
        print(f"✅ Min/Max response time: {min_time:.1f}ms / {max_time:.1f}ms")
        print(f"✅ Success rate: {successful_requests}/10 ({successful_requests*10}%)")
        
        # Performance criteria
        performance_good = (avg_time < 100 and successful_requests >= 8)
        if performance_good:
            print(f"✅ Performance: GOOD")
        else:
            print(f"⚠️ Performance: Needs improvement")
        
        return performance_good
    else:
        print(f"❌ No successful performance tests")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print(f"🚀 COMPREHENSIVE POKER ADVISORY SYSTEM TEST")
    print("=" * 45)
    print("Testing all components from database to web interface...")
    
    results = {}
    
    # Run all test categories
    results['database'] = test_database_health()
    results['api'] = test_api_endpoints()
    results['gto_quality'] = test_gto_decision_quality()
    results['web_interface'] = test_web_interface()
    results['performance'] = test_performance_benchmarks()
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 14)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    overall_health = passed_tests / total_tests
    print(f"\nOverall System Health: {passed_tests}/{total_tests} ({overall_health*100:.0f}%)")
    
    if overall_health >= 0.8:
        print(f"🎉 SYSTEM STATUS: EXCELLENT")
        print(f"All major components working well. Ready for production use.")
    elif overall_health >= 0.6:
        print(f"⚠️ SYSTEM STATUS: GOOD")
        print(f"Most components working. Minor issues to address.")
    else:
        print(f"❌ SYSTEM STATUS: NEEDS WORK")
        print(f"Multiple components need attention before production use.")
    
    # Specific recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if not results['database']:
        print(f"- Fix database integrity issues")
    if not results['api']:
        print(f"- Resolve API endpoint problems")
    if not results['gto_quality']:
        print(f"- Improve GTO decision logic")
    if not results['web_interface']:
        print(f"- Fix web interface accessibility")
    if not results['performance']:
        print(f"- Optimize system performance")
    
    if all(results.values()):
        print(f"- System is ready for professional poker advisory use!")
    
    return results

if __name__ == "__main__":
    test_results = run_comprehensive_test()