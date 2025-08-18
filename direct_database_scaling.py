#!/usr/bin/env python3
"""
Direct Database Scaling: Test database query performance and fix pipeline issues
"""

import sqlite3
import time
import numpy as np
from app.database.gto_database import gto_db
from app.database.poker_vectorizer import PokerSituation, Position, BettingRound

def test_database_fixes():
    """Test the database query fixes and performance."""
    
    print("🔧 TESTING DATABASE FIXES")
    print("=" * 26)
    
    # Initialize database
    if not gto_db.initialized:
        gto_db.initialize()
    
    # Test scenarios that should hit our database
    test_scenarios = [
        {
            'name': 'Premium Preflop',
            'situation': PokerSituation(
                hole_cards=["As", "Ks"],
                board_cards=[],
                position=Position.BTN,
                pot_size=3.0,
                bet_to_call=2.0,
                stack_size=100.0,
                betting_round=BettingRound.PREFLOP,
                num_players=6
            )
        },
        {
            'name': 'Set on Flop',
            'situation': PokerSituation(
                hole_cards=["Qh", "Qd"],
                board_cards=["Qs", "7h", "2c"],
                position=Position.CO,
                pot_size=12.0,
                bet_to_call=8.0,
                stack_size=85.0,
                betting_round=BettingRound.FLOP,
                num_players=4
            )
        },
        {
            'name': 'Turn Draw',
            'situation': PokerSituation(
                hole_cards=["Ah", "Kh"],
                board_cards=["Qh", "Jd", "9h", "8c"],
                position=Position.SB,
                pot_size=45.0,
                bet_to_call=25.0,
                stack_size=120.0,
                betting_round=BettingRound.TURN,
                num_players=3
            )
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_scenarios):
        print(f"\n{i+1}. Testing {test['name']}:")
        
        start_time = time.time()
        
        try:
            # Test database lookup
            recommendation = gto_db.get_instant_recommendation(test['situation'])
            
            query_time = time.time() - start_time
            
            if recommendation:
                print(f"   ✅ Found recommendation: {recommendation.get('decision', 'N/A')}")
                print(f"   Equity: {recommendation.get('equity', 0):.3f}")
                print(f"   Confidence: {recommendation.get('confidence', 0):.3f}")
                print(f"   Query time: {query_time*1000:.1f}ms")
                
                # Show reasoning snippet
                reasoning = recommendation.get('reasoning', '')
                if reasoning:
                    print(f"   Analysis: {reasoning[:50]}...")
                
                success_count += 1
            else:
                print(f"   ⚠️ No recommendation found (query time: {query_time*1000:.1f}ms)")
        
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
    
    # Test database stats
    print(f"\n📊 DATABASE PERFORMANCE:")
    print("-" * 22)
    
    try:
        conn = sqlite3.connect("gto_database.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        total_count = cursor.fetchone()[0]
        print(f"Total situations: {total_count:,}")
        
        # Test HNSW index
        if gto_db.hnsw_index:
            index_size = gto_db.hnsw_index.get_current_count()
            print(f"HNSW index size: {index_size:,} vectors")
        
        # Performance metrics
        if gto_db.query_count > 0:
            avg_time = gto_db.total_query_time / gto_db.query_count
            print(f"Average query time: {avg_time*1000:.2f}ms")
        
        conn.close()
        
    except Exception as e:
        print(f"Database stats failed: {e}")
    
    print(f"\n✅ DATABASE TEST SUMMARY:")
    print(f"Successful queries: {success_count}/{len(test_scenarios)}")
    print(f"Database contains {total_count:,} TexasSolver scenarios")
    
    return success_count == len(test_scenarios)

def test_vector_encoding():
    """Test vector encoding and HNSW compatibility."""
    
    print(f"\n🔍 TESTING VECTOR ENCODING")
    print("-" * 25)
    
    try:
        if not gto_db.initialized:
            gto_db.initialize()
        
        # Test vectorization
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
        
        vector = gto_db.vectorizer.vectorize_situation(test_situation)
        print(f"✅ Vector dimensions: {len(vector)}")
        print(f"Vector format: {type(vector)}")
        print(f"Sample values: [{vector[0]:.2f}, {vector[1]:.2f}, {vector[2]:.2f}, ...]")
        
        # Test HNSW compatibility
        if gto_db.hnsw_index and gto_db.hnsw_index.get_current_count() > 0:
            query_vector = np.array(vector, dtype=np.float32).reshape(1, -1)
            labels, distances = gto_db.hnsw_index.knn_query(query_vector, k=3)
            
            print(f"✅ HNSW query successful")
            print(f"Result format: labels={type(labels)}, distances={type(distances)}")
            print(f"Top matches: {labels}, distances: {distances}")
        else:
            print("⚠️ HNSW index not available or empty")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector encoding test failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 DIRECT DATABASE SCALING TEST")
    print("=" * 32)
    
    # Test database fixes
    db_success = test_database_fixes()
    
    # Test vector encoding
    vector_success = test_vector_encoding()
    
    if db_success and vector_success:
        print(f"\n🎉 ALL TESTS PASSED")
        print("Database pipeline ready for TexasSolver scenarios")
    else:
        print(f"\n⚠️ ISSUES DETECTED")
        print("Database pipeline needs attention")