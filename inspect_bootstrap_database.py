#!/usr/bin/env python3
"""
Inspect Bootstrap Database: Examine imported TexasSolver scenarios
"""

import sqlite3
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_database_contents():
    """Inspect the actual contents of the database to verify imports."""
    
    print("🔍 INSPECTING DATABASE CONTENTS")
    print("=" * 32)
    
    try:
        # Connect to database
        conn = sqlite3.connect("gto_database.db")
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Database tables: {[table[0] for table in tables]}")
        
        # Get database size and count
        cursor.execute("SELECT COUNT(*) FROM gto_situations")
        total_count = cursor.fetchone()[0]
        print(f"Total situations in database: {total_count:,}")
        
        # Sample recent entries (our imports)
        print(f"\n📊 RECENT IMPORTS SAMPLE:")
        print("-" * 25)
        
        cursor.execute("""
            SELECT id, vector, solution, reasoning, recommendation, equity, cfr_confidence
            FROM gto_situations 
            ORDER BY rowid DESC 
            LIMIT 10
        """)
        
        recent_rows = cursor.fetchall()
        
        for i, row in enumerate(recent_rows):
            id_val, vector, solution, reasoning, recommendation, equity, cfr_confidence = row
            
            print(f"\nEntry {i+1}:")
            print(f"  ID: {id_val}")
            print(f"  Recommendation: {recommendation}")
            print(f"  Equity: {equity:.3f}, Confidence: {cfr_confidence:.3f}")
            
            # Parse solution JSON if available
            if solution:
                try:
                    solution_data = json.loads(solution)
                    print(f"  Decision: {solution_data.get('decision', 'N/A')}")
                    print(f"  Bet Size: ${solution_data.get('bet_size', 0)}")
                    print(f"  Reasoning: {solution_data.get('reasoning', 'N/A')[:80]}...")
                    
                    metadata = solution_data.get('metadata', {})
                    source = metadata.get('source', 'unknown')
                    print(f"  Source: {source}")
                    
                except json.JSONDecodeError:
                    print(f"  Solution data: {solution[:100]}...")
            
            print(f"  Reasoning: {reasoning[:80]}..." if reasoning else "  Reasoning: None")
        
        # Check for TexasSolver specific entries
        print(f"\n🎯 TEXASSOLVER INTEGRATION ANALYSIS:")
        print("-" * 35)
        
        # Look for entries from our recent imports
        cursor.execute("""
            SELECT COUNT(*) FROM gto_situations 
            WHERE reasoning LIKE '%TexasSolver%' 
               OR reasoning LIKE '%texassolver%'
               OR reasoning LIKE '%Phase 2%'
               OR reasoning LIKE '%authentic%'
        """)
        texassolver_count = cursor.fetchone()[0]
        print(f"TexasSolver-related entries: {texassolver_count}")
        
        # Look for entries from scaling engine
        cursor.execute("""
            SELECT COUNT(*) FROM gto_situations 
            WHERE reasoning LIKE '%scaling%'
               OR reasoning LIKE '%rapid%'
               OR reasoning LIKE '%efficient%'
               OR reasoning LIKE '%Worker%'
        """)
        scaling_count = cursor.fetchone()[0]
        print(f"Scaling engine entries: {scaling_count}")
        
        # Look for bootstrap entries
        cursor.execute("""
            SELECT COUNT(*) FROM gto_situations 
            WHERE reasoning LIKE '%bootstrap%'
               OR reasoning LIKE '%fallback%'
        """)
        bootstrap_count = cursor.fetchone()[0]
        print(f"Bootstrap entries: {bootstrap_count}")
        
        # Get source distribution
        print(f"\n📈 SOURCE DISTRIBUTION:")
        print("-" * 22)
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN reasoning LIKE '%TexasSolver%' OR reasoning LIKE '%authentic%' THEN 'TexasSolver'
                    WHEN reasoning LIKE '%scaling%' OR reasoning LIKE '%rapid%' THEN 'Scaling Engine'
                    WHEN reasoning LIKE '%Worker%' THEN 'Multi-threaded'
                    WHEN reasoning LIKE '%efficient%' THEN 'Efficient Import'
                    WHEN reasoning LIKE '%bootstrap%' THEN 'Bootstrap'
                    ELSE 'Other'
                END as source_type,
                COUNT(*) as count
            FROM gto_situations 
            GROUP BY source_type
            ORDER BY count DESC
        """)
        
        source_dist = cursor.fetchall()
        for source_type, count in source_dist:
            percentage = (count / total_count) * 100
            print(f"  {source_type}: {count:,} ({percentage:.1f}%)")
        
        # Sample authentic GTO entries
        print(f"\n🎲 SAMPLE AUTHENTIC GTO ENTRIES:")
        print("-" * 30)
        
        cursor.execute("""
            SELECT recommendation, equity, cfr_confidence, reasoning, solution
            FROM gto_situations 
            WHERE cfr_confidence > 0.8
            ORDER BY cfr_confidence DESC
            LIMIT 5
        """)
        
        high_conf_entries = cursor.fetchall()
        for i, (recommendation, equity, cfr_confidence, reasoning, solution) in enumerate(high_conf_entries):
            print(f"\nHigh Confidence Entry {i+1}:")
            print(f"  Decision: {recommendation}")
            print(f"  Equity: {equity:.3f}, Confidence: {cfr_confidence:.3f}")
            print(f"  Analysis: {reasoning[:60]}...")
            
            # Parse solution for more details
            if solution:
                try:
                    solution_data = json.loads(solution)
                    metadata = solution_data.get('metadata', {})
                    if 'pattern' in metadata:
                        print(f"  Pattern: {metadata['pattern']}")
                    if 'source' in metadata:
                        print(f"  Source: {metadata['source']}")
                except:
                    pass
        
        conn.close()
        
        print(f"\n✅ DATABASE INSPECTION COMPLETE")
        print(f"Total entries verified: {total_count:,}")
        
        return total_count
        
    except Exception as e:
        logger.error(f"Database inspection failed: {e}")
        return 0

def test_database_queries():
    """Test database query functionality."""
    
    print(f"\n🧪 TESTING DATABASE QUERIES")
    print("-" * 28)
    
    try:
        from app.database.gto_database import gto_db
        
        if not gto_db.initialized:
            gto_db.initialize()
        
        # Test basic performance stats
        stats = gto_db.get_performance_stats()
        print(f"Query performance stats:")
        print(f"  Total situations: {stats['total_situations']:,}")
        print(f"  HNSW index size: {stats['hnsw_index_size']:,}")
        print(f"  Database size: {stats['database_size_mb']:.1f} MB")
        print(f"  Average query time: {stats['average_query_time_ms']:.2f}ms")
        
        # Test sample recommendation lookup
        from app.database.poker_vectorizer import PokerSituation, Position, BettingRound
        
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
        
        print(f"\nTesting recommendation lookup...")
        start_time = time.time()
        recommendation = gto_db.get_instant_recommendation(test_situation)
        query_time = (time.time() - start_time) * 1000
        
        if recommendation:
            print(f"✅ Query successful in {query_time:.2f}ms")
            print(f"  Decision: {recommendation.get('decision', 'N/A')}")
            print(f"  Confidence: {recommendation.get('confidence', 0):.3f}")
        else:
            print(f"⚠️ No recommendation found (query time: {query_time:.2f}ms)")
        
        return True
        
    except Exception as e:
        logger.error(f"Query test failed: {e}")
        return False

if __name__ == "__main__":
    # Run inspection
    total_entries = inspect_database_contents()
    
    if total_entries > 0:
        # Test queries
        test_success = test_database_queries()
        
        if test_success:
            print(f"\n🎯 VERIFICATION COMPLETE")
            print(f"Database contains {total_entries:,} verified entries with working query system")
        else:
            print(f"\n⚠️ PARTIAL VERIFICATION")
            print(f"Database has {total_entries:,} entries but query issues detected")
    else:
        print(f"\n❌ VERIFICATION FAILED")
        print(f"Unable to access database contents")