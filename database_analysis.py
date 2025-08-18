#!/usr/bin/env python3
"""
Database Analysis: Comprehensive sanity check of the entire TexasSolver pipeline
"""

import sqlite3
import json
import time
import requests
from app.database.gto_database import gto_db
from app.database.poker_vectorizer import PokerSituation, Position, BettingRound

def sanity_check_database():
    """Complete sanity check of database integrity and content."""
    
    print("🔍 COMPREHENSIVE DATABASE SANITY CHECK")
    print("=" * 37)
    
    issues = []
    
    try:
        # 1. Database file integrity
        conn = sqlite3.connect("gto_database.db")
        cursor = conn.cursor()
        
        # Check schema
        cursor.execute("PRAGMA table_info(gto_situations)")
        columns = cursor.fetchall()
        expected_columns = ['id', 'vector', 'hole_cards', 'board_cards', 'position', 
                          'pot_size', 'bet_to_call', 'stack_size', 'betting_round',
                          'recommendation', 'bet_size', 'equity', 'reasoning', 
                          'cfr_confidence', 'metadata', 'created_at']
        
        actual_columns = [col[1] for col in columns]
        missing_columns = set(expected_columns) - set(actual_columns)
        
        if missing_columns:
            issues.append(f"Missing database columns: {missing_columns}")
        else:
            print("✅ Database schema complete")
        
        # 2. Data integrity checks
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        total_count = cursor.fetchone()[0]
        print(f"✅ Database contains {total_count:,} scenarios")
        
        # Check for null values in critical fields
        cursor.execute("""
            SELECT COUNT(*) FROM gto_situations 
            WHERE recommendation IS NULL OR equity IS NULL OR cfr_confidence IS NULL
        """)
        null_count = cursor.fetchone()[0]
        
        if null_count > 0:
            issues.append(f"Found {null_count} scenarios with null critical fields")
        else:
            print("✅ No null values in critical fields")
        
        # 3. Data quality checks
        cursor.execute("""
            SELECT MIN(equity), MAX(equity), AVG(equity),
                   MIN(cfr_confidence), MAX(cfr_confidence), AVG(cfr_confidence)
            FROM gto_situations
        """)
        min_eq, max_eq, avg_eq, min_conf, max_conf, avg_conf = cursor.fetchone()
        
        print(f"✅ Equity range: {min_eq:.3f} - {max_eq:.3f} (avg: {avg_eq:.3f})")
        print(f"✅ Confidence range: {min_conf:.3f} - {max_conf:.3f} (avg: {avg_conf:.3f})")
        
        if min_eq < 0 or max_eq > 1:
            issues.append(f"Invalid equity values: {min_eq} - {max_eq}")
        
        if min_conf < 0 or max_conf > 1:
            issues.append(f"Invalid confidence values: {min_conf} - {max_conf}")
        
        # 4. Decision distribution
        cursor.execute("""
            SELECT recommendation, COUNT(*) 
            FROM gto_situations 
            GROUP BY recommendation 
            ORDER BY COUNT(*) DESC
        """)
        decisions = cursor.fetchall()
        
        print("✅ Decision distribution:")
        for decision, count in decisions:
            percentage = (count / total_count) * 100
            print(f"   {decision}: {count:,} ({percentage:.1f}%)")
        
        # 5. Source analysis
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN reasoning LIKE '%TexasSolver%' THEN 'TexasSolver'
                    WHEN reasoning LIKE '%scaling%' THEN 'Scaling Engine'
                    WHEN reasoning LIKE '%rapid%' THEN 'Rapid Import'
                    WHEN reasoning LIKE '%efficient%' THEN 'Efficient Import'
                    WHEN reasoning LIKE '%Worker%' THEN 'Multi-threaded'
                    ELSE 'Other'
                END as source,
                COUNT(*)
            FROM gto_situations 
            GROUP BY source
            ORDER BY COUNT(*) DESC
        """)
        sources = cursor.fetchall()
        
        print("✅ Source distribution:")
        for source, count in sources:
            percentage = (count / total_count) * 100
            print(f"   {source}: {count:,} ({percentage:.1f}%)")
        
        conn.close()
        
    except Exception as e:
        issues.append(f"Database check failed: {e}")
    
    return issues

def sanity_check_hnsw_index():
    """Check HNSW index integrity and performance."""
    
    print(f"\n🔍 HNSW INDEX SANITY CHECK")
    print("-" * 26)
    
    issues = []
    
    try:
        if not gto_db.initialized:
            gto_db.initialize()
        
        if gto_db.hnsw_index is None:
            issues.append("HNSW index not initialized")
            return issues
        
        index_count = gto_db.hnsw_index.get_current_count()
        print(f"✅ HNSW index contains {index_count:,} vectors")
        
        # Test query performance
        test_situation = PokerSituation(
            hole_cards=["As", "Ks"],
            board_cards=[],
            position=Position.BTN,
            pot_size=3.0,
            bet_to_call=2.0,
            stack_size=100.0,
            betting_round=BettingRound.PREFLOP,
            num_players=6
        )
        
        start_time = time.time()
        recommendation = gto_db.get_instant_recommendation(test_situation)
        query_time = time.time() - start_time
        
        if recommendation:
            print(f"✅ Query successful in {query_time*1000:.1f}ms")
            print(f"   Decision: {recommendation.get('decision', 'N/A')}")
            print(f"   Confidence: {recommendation.get('confidence', 0):.3f}")
        else:
            issues.append("HNSW query returned no results")
        
        # Test multiple queries for consistency
        query_times = []
        for i in range(5):
            start = time.time()
            result = gto_db.get_instant_recommendation(test_situation)
            query_times.append(time.time() - start)
        
        avg_time = sum(query_times) * 1000 / len(query_times)
        print(f"✅ Average query time: {avg_time:.1f}ms")
        
        if avg_time > 10:  # 10ms threshold
            issues.append(f"Query performance degraded: {avg_time:.1f}ms")
        
    except Exception as e:
        issues.append(f"HNSW check failed: {e}")
    
    return issues

def sanity_check_api_endpoints():
    """Check API endpoints are working correctly."""
    
    print(f"\n🔍 API ENDPOINTS SANITY CHECK")
    print("-" * 29)
    
    issues = []
    base_url = "http://localhost:5000"
    auth_header = {"Authorization": "Bearer test-token-123"}
    
    # Test database endpoint
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
    
    try:
        response = requests.post(
            f"{base_url}/database/instant-gto",
            json=test_data,
            headers={"Content-Type": "application/json", **auth_header},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                print("✅ Database endpoint working")
            else:
                issues.append(f"Database endpoint returned: {result.get('method', 'unknown')}")
        else:
            issues.append(f"Database endpoint failed: {response.status_code}")
    
    except Exception as e:
        issues.append(f"Database endpoint test failed: {e}")
    
    # Test stats endpoint
    try:
        response = requests.get(
            f"{base_url}/database/database-stats",
            headers=auth_header,
            timeout=3
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats endpoint working: {stats.get('total_situations', 0):,} situations")
        else:
            issues.append(f"Stats endpoint failed: {response.status_code}")
    
    except Exception as e:
        issues.append(f"Stats endpoint test failed: {e}")
    
    # Test GUI endpoint
    try:
        response = requests.get(
            f"{base_url}/unified",
            headers=auth_header,
            timeout=3
        )
        
        if response.status_code == 200:
            print("✅ GUI endpoint accessible")
        else:
            issues.append(f"GUI endpoint failed: {response.status_code}")
    
    except Exception as e:
        issues.append(f"GUI endpoint test failed: {e}")
    
    return issues

def comprehensive_sanity_check():
    """Run complete sanity check on entire pipeline."""
    
    all_issues = []
    
    # Check each component
    db_issues = sanity_check_database()
    hnsw_issues = sanity_check_hnsw_index()
    api_issues = sanity_check_api_endpoints()
    
    all_issues.extend(db_issues)
    all_issues.extend(hnsw_issues)
    all_issues.extend(api_issues)
    
    # Summary
    print(f"\n📊 SANITY CHECK SUMMARY")
    print("=" * 23)
    
    if not all_issues:
        print("🎉 ALL SANITY CHECKS PASSED")
        print("Pipeline is fully operational and ready for TexasSolver expansion")
        return True
    else:
        print("⚠️ ISSUES DETECTED:")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
        return False

if __name__ == "__main__":
    success = comprehensive_sanity_check()
    exit(0 if success else 1)